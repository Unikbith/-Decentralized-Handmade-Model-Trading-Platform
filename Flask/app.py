from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt,
    decode_token
)
from flask_apscheduler import APScheduler
from cryptography.fernet import Fernet   #加密
from minio import Minio
from minio.error import S3Error
import redis
from celery import Celery
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
import uuid
from contextlib import contextmanager
import time
import json
from datetime import datetime, timedelta
from functools import wraps
import random
import requests

# AI客服商品缓存（仅缓存商品对象列表，索引放Redis）
_goods_cache = {
    'data': None,
    'updated_at': 0
}
_GOODS_CACHE_TTL = 300  # 缓存有效期5分钟
app = Flask(__name__)

CORS(
    app,
    supports_credentials=True,
    resources={r"/api/*": {"origins": [
        "https://localhost",
        "https://127.0.0.1",
        "https://animemodelshop"
    ]}},
    methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 50  # 连接池大小
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 100  # 最大溢出连接数
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30  # 获取连接超时时间
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600  # 连接回收时间
app.config['SQLALCHEMY_ECHO'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 上传文件最大50MB

app.config['JWT_SECRET_KEY'] = 'vue_jwt'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)  # Token有效期7天
app.config['JWT_ALGORITHM'] = 'HS256'

app.config['CELERY_RESULT_BACKEND'] = 'redis://127.0.0.1:6379/1'
app.config['CELERY_BROKER_URL'] = 'redis://127.0.0.1:6379/1'


# 定时任务调度器配置
class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'

app.config.from_object(Config)

SMTP_HOST = 'smtp.qq.com'
SMTP_PORT = 587
SMTP_USER = ''  # 发件邮箱
SMTP_PASSWORD = ''  # 邮箱授权码

#智谱AI配置
ZHIPU_API_KEY = ''  #智谱AI API Key
ZHIPU_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'



# Redis分布式锁
class RedisLock:
    """Redis分布式锁"""
    def __init__(self, key, timeout=10):
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.value = str(uuid.uuid4())  # 唯一标识，防止误删其他客户端的锁

    def acquire(self, retry=3, delay=0.1):
        """尝试获取锁，支持重试"""
        for _ in range(retry):
            if redis_client.set(self.key, self.value, nx=True, ex=self.timeout):
                return True
            time.sleep(delay)
        return False

    def release(self):
        """释放锁"""
        lua = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            redis_client.eval(lua, 1, self.key, self.value)
        except:
            pass


@contextmanager
def distributed_lock(key, timeout=10):
    """分布式锁上下文管理器，使用with语句自动获取/释放锁"""
    lock = RedisLock(key, timeout)
    if not lock.acquire():
        raise Exception(f"获取锁失败: {key}")
    try:
        yield
    finally:
        lock.release()


# 权限装饰器
def admin_required(fn):
    """管理员权限装饰器：要求JWT中role为admin"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'code': 403, 'msg': '无管理员权限'}), 403
        return fn(*args, **kwargs)
    return wrapper


#  缓存装饰器
def cache(key_prefix, expire=3600):
    """缓存装饰器：基于Redis缓存GET请求结果"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 根据参数构造缓存键
            cache_key = f"{key_prefix}:default"
            if args:
                cache_key = f"{key_prefix}:{args[0]}"
            elif kwargs.get('id'):
                cache_key = f"{key_prefix}:{kwargs.get('id')}"

            # 命中缓存则直接返回
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify({'code': 200, 'data': json.loads(cached_data)})

            # 未命中则执行函数并写入缓存
            result = func(*args, **kwargs)
            try:
                if hasattr(result, 'json') and result.json['code'] == 200:
                    redis_client.setex(cache_key, expire, json.dumps(result.json['data'], ensure_ascii=False))
            except Exception as e:
                print(f"缓存写入失败: {e}")
            return result

        return wrapper

    return decorator


#验证码与邮件发送
def generate_code():
    """生成6位数字验证码"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def send_email(email, code):
    """发送QQ邮箱验证码"""
    sender = SMTP_USER
    nickname = "次元模仓"
    encoded_nickname = Header(nickname, 'utf-8').encode()
    from_header = f"{encoded_nickname} <{sender}>"

    msg = MIMEText(f'您的注册验证码是：{code}，5分钟内有效，请勿泄露。', 'plain', 'utf-8')
    msg['From'] = from_header
    msg['To'] = email
    msg['Subject'] = Header('【次元模仓】注册验证码', 'utf-8')

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()  # 启用TLS加密
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(sender, [email], msg.as_string())
        print(f" 验证码发送成功至：{email}")
        return True
    except Exception as e:
        print(f" 邮件发送失败: {e}")
        return False


# 密码加解密
def encrypt_password(password):
    """加密密码（Fernet对称加密）"""
    return cipher_suite.encrypt(password.encode()).decode()


def decrypt_password(encrypted_password):
    """解密密码"""
    return cipher_suite.decrypt(encrypted_password.encode()).decode()

# 库存操作函数
def deduct_stock_redis(goods_id, num):
    """Redis原子扣减库存，并同步数据库"""
    stock_key = f"goods_stock:{goods_id}"
    try:
        current_stock = redis_client.get(stock_key)
        if not current_stock:
            # Redis中无缓存，从数据库加载
            goods = Goods.query.get(goods_id)
            if not goods:
                return False
            current_stock = goods.stock
            redis_client.set(stock_key, current_stock)

        current_stock = int(current_stock)
        if current_stock < num:
            return False  # 库存不足

        new_stock = current_stock - num
        redis_client.set(stock_key, new_stock)

        # 同步更新数据库库存
        goods = Goods.query.get(goods_id)
        if goods:
            goods.stock = new_stock
            db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"扣减库存失败: {e}")
        return False


# 订单超时取消函数
def cancel_expired_orders():
    """定时任务：取消超时未支付的订单，恢复库存和购物车"""
    with app.app_context():
        expired_time = datetime.now() - timedelta(minutes=15)
        expired_orders = Order.query.filter(
            Order.status == 'pending_pay',
            Order.created_at < expired_time
        ).all()
        for order in expired_orders:
            print(f"自动取消超时订单: {order.order_no}")
            order.status = 'cancelled'
            for item in order.items:
                with distributed_lock(f"goods_{item.goods_id}", timeout=5):
                    goods = Goods.query.get(item.goods_id)
                    if goods:
                        goods.stock += item.num
                        redis_client.incrby(f"goods_stock:{item.goods_id}", item.num)
                # 恢复购物车中的商品数量
                existing_cart = Cart.query.filter_by(user_id=order.user_id, goods_id=item.goods_id).first()
                if existing_cart:
                    existing_cart.num += item.num
                else:
                    new_cart = Cart(user_id=order.user_id, goods_id=item.goods_id, num=item.num)
                    db.session.add(new_cart)
        if expired_orders:
            db.session.commit()
            print(f"已自动取消 {len(expired_orders)} 个超时订单")


jwt = JWTManager(app)  # JWT管理器
scheduler = APScheduler()  # 定时任务调度器
scheduler.init_app(app)

redis_client = redis.Redis(  # Redis客户端
    host='127.0.0.1',
    port=6379,
    db=0,
    decode_responses=True
)

# SQLAlchemy数据库实例
db = SQLAlchemy(app)

MINIO_ENDPOINT = '127.0.0.1:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
MINIO_BUCKET = 'goods-images'

minio_client = Minio(
    MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY, secure=False
)
# 创建bucket并设置公开读策略
if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)
policy = """{
  "Version": "2012-10-17",
  "Statement": [{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetObject"],"Resource":["arn:aws:s3:::%s/*"]}]
}""" % MINIO_BUCKET
minio_client.set_bucket_policy(MINIO_BUCKET, policy)

# 密码加密密钥

# 自动生成并保存至文件，确保重启后密钥一致
if not os.path.exists('secret.key'):
    key = Fernet.generate_key()
    with open('secret.key', 'wb') as f:
        f.write(key)
with open('secret.key', 'rb') as f:
    cipher_suite = Fernet(f.read())

#  Elasticsearch客户端
ES_HOST = '127.0.0.1'
ES_PORT = 9200
es_client = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}", timeout=30)


#  Celery异步任务
def make_celery(app):
    """创建Celery实例并配置时区与超时"""
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND'),
        broker=app.config.get('CELERY_BROKER_URL')
    )
    celery.conf.update(
        timezone='Asia/Shanghai',
        enable_utc=False,
        task_soft_time_limit=30,  # 软超时30秒
        task_time_limit=60,  # 硬超时60秒
    )
    return celery


celery = make_celery(app)

def fix_image_url(url):
    """HTTP URL 转换成相对路径，配合 Nginx HTTPS 代理"""
    if not url:
        return url
    if url.startswith('http://127.0.0.1:9000/goods-images/'):
        return '/goods-images/' + url.split('/goods-images/', 1)[1]
    if url.startswith('http://localhost:9000/goods-images/'):
        return '/goods-images/' + url.split('/goods-images/', 1)[1]
    return url


# 用户账号表
class User(db.Model):
    """用户账号表"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_banned = db.Column(db.Integer, default=0)
    apply_status = db.Column(db.String(20), default='none')  #  入驻申请状态
    apply_time = db.Column(db.DateTime, nullable=True)  # 入驻申请时间
    info = db.relationship('UserInfo', backref='user', uselist=False, cascade='all, delete-orphan')


# 用户详细信息表
class UserInfo(db.Model):
    """用户详细信息表"""
    __tablename__ = 'user_info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    avatar = db.Column(db.String(255), default='')
    birthday = db.Column(db.String(20), default='')
    gender = db.Column(db.String(10), default='secret')
    email = db.Column(db.String(100), default='')
    phone = db.Column(db.String(20), default='')
    receiver_name = db.Column(db.String(50), default='')
    address = db.Column(db.Text, default='')


# 商品表
class Goods(db.Model):
    """商品表"""
    __tablename__ = 'goods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=1)
    images = db.Column(db.Text, nullable=False)  # 逗号分隔的图片URL
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=True)  # 上架/下架
    brand = db.Column(db.String(50), nullable=True)
    ip = db.Column(db.String(50), nullable=True)  # 所属IP
    charactername = db.Column(db.String(50), nullable=True)  # 角色名
    merchant_id = db.Column(db.Integer, nullable=False)  # 商家用户ID
    merchant_name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


# 购物车表
class Cart(db.Model):
    """购物车表"""
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    num = db.Column(db.Integer, default=1, nullable=False)
    goods = db.relationship('Goods', backref='cart_items', lazy='joined')


# 收藏表
class Collect(db.Model):
    """用户收藏表"""
    __tablename__ = 'collects'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    goods = db.relationship('Goods', backref='collect_items', lazy='joined')


# 浏览历史表
class History(db.Model):
    """浏览历史表"""
    __tablename__ = 'user_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    browse_time = db.Column(db.DateTime, server_default=db.func.now())
    goods = db.relationship('Goods', backref='history_items', lazy='joined')


# 评论表
class Comment(db.Model):
    """商品评论表"""
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', backref='comments', lazy='joined')


# 订单主表
class Order(db.Model):
    """订单主表"""
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    receiver_name = db.Column(db.String(50), default='')
    receiver_phone = db.Column(db.String(20), default='')
    receiver_address = db.Column(db.String(255), default='')
    status = db.Column(db.String(20),default='pending_pay')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    items = db.relationship('OrderItem', backref='order', lazy='joined', cascade='all, delete-orphan')


# 订单商品明细表
class OrderItem(db.Model):
    """订单商品明细表"""
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    goods_name = db.Column(db.String(100), nullable=False)
    goods_image = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    num = db.Column(db.Integer, nullable=False)


#  售后申请表
class ReturnRequest(db.Model):
    """售后申请表"""
    __tablename__ = 'return_requests'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    merchant_id = db.Column(db.Integer, nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    order = db.relationship('Order', backref='return_requests', lazy='joined')
    user = db.relationship('User', backref='return_requests', lazy='joined')
    goods = db.relationship('Goods', backref='return_requests', lazy='joined')


# 通知记录表
class NotificationLog(db.Model):
    """用户通知记录表"""
    __tablename__ = 'notification_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, server_default=db.func.now())
    status = db.Column(db.String(20), default='pending')
    user = db.relationship('User', backref='notifications', lazy='joined')
    goods = db.relationship('Goods', backref='notifications', lazy='joined')
    order = db.relationship('Order', backref='notifications', lazy='joined')


#  热门搜索关键词快照表
class SearchKeywordSnapshot(db.Model):
    """热门搜索关键词快照"""
    __tablename__ = 'search_keyword_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, server_default=db.func.now())


# 订单状态分布快照表
class OrderStatusSnapshot(db.Model):
    """订单状态分布快照（24小时更新一次）"""
    __tablename__ = 'order_status_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(20), nullable=False)
    count = db.Column(db.Integer, default=0)
    today_orders = db.Column(db.Integer, default=0)
    today_revenue = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, server_default=db.func.now())

#  同步商品到ES索引
def sync_goods_to_es(goods_id):
    """将单条商品数据同步到ES索引"""
    try:
        goods = Goods.query.get(goods_id)
        if not goods:
            return
        doc = {
            "name": goods.name,
            "price": float(goods.price),
            "stock": goods.stock,
            "image": fix_image_url(goods.images.split(',')[0]) if goods.images else "",
            "description": goods.description or "",
            "category": goods.category or "",
            "status": goods.status or "",
            "brand": goods.brand or "",
            "ip": goods.ip or "",
            "charactername": goods.charactername or "",
            "merchant_name": goods.merchant_name
        }
        es_client.index(index="goods_index", id=str(goods.id), body=doc)
    except Exception as e:
        print(f"同步商品到ES失败: {e}")


# 从ES中删除商品
def delete_goods_from_es(goods_id):
    """从ES中删除商品"""
    try:
        es_client.delete(index="goods_index", id=str(goods_id))
    except NotFoundError:
        print(f"ES中未找到商品{goods_id}")
    except Exception as e:
        print(f"删除ES商品失败: {e}")


# 请求监控采集 (before_request / after_request)
from flask import g as flask_g

@app.before_request
def monitor_before_request():
    """记录请求开始时间"""
    flask_g.monitor_start = time.time()


@app.after_request
def monitor_after_request(response):
    """采集请求指标，存入Redis"""
    try:
        # 排除静态文件和前端路由
        path = request.path
        if not path.startswith('/api/'):
            return response

        duration = int((time.time() - flask_g.monitor_start) * 1000)  # 毫秒级耗时
        size = len(response.get_data()) if hasattr(response, 'get_data') else 0
        status = response.status_code
        ip = request.remote_addr or '0.0.0.0'
        now = datetime.now()

        # 构造指标
        metric = json.dumps({
            'path': path,
            'method': request.method,
            'status': status,
            'duration': duration,
            'size': size,
            'ip': ip,
            'time': now.strftime('%Y-%m-%d %H:%M:%S')
        })

        # 推入Redis原始数据列表
        redis_client.lpush('monitor:raw', metric)
        redis_client.ltrim('monitor:raw', 0, 1999)

        # 分钟级计数器
        minute_key = now.strftime('%Y%m%d%H%M')
        redis_client.incr(f'monitor:minute:{minute_key}:total')
        if status >= 400:
            redis_client.incr(f'monitor:minute:{minute_key}:error')
        redis_client.incrby(f'monitor:minute:{minute_key}:bytes', size)
        redis_client.incrby(f'monitor:minute:{minute_key}:duration', duration)

        # 设置分钟key过期时间
        for suffix in ['total', 'error', 'bytes', 'duration']:
            redis_client.expire(f'monitor:minute:{minute_key}:{suffix}', 7200)

        # IP访问计数
        redis_client.zincrby('monitor:ip_count', 1, ip)

        # 接口访问计数
        redis_client.zincrby('monitor:path_count', 1, path)

        # 活跃用户追踪
        try:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token_str = auth_header[7:]
                decoded = decode_token(token_str)
                user_id = decoded.get('sub')
                if user_id and user_id != '0':  # 排除管理员
                    today_key = now.strftime('%Y%m%d')
                    hour_key = now.strftime('%Y%m%d%H')
                    redis_client.sadd(f'monitor:active_users:{today_key}', user_id)
                    redis_client.sadd(f'monitor:active_hour:{hour_key}', user_id)
                    redis_client.expire(f'monitor:active_users:{today_key}', 86400 * 3)
                    redis_client.expire(f'monitor:active_hour:{hour_key}', 7200)
        except Exception:
            pass

    except Exception as e:
        print(f"监控采集异常: {e}")

    return response


# JWT钩子
@jwt.invalid_token_loader
def invalid_token_callback(error):
    """token无效时"""
    return jsonify({'code': 401, 'msg': f'Token无效: {error}'}), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """token过期"""
    return jsonify({'code': 401, 'msg': '登录已过期，请重新登录'}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    """缺少token"""
    return jsonify({'code': 401, 'msg': '请先登录，缺少Token'}), 401


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    """检查token是否在黑名单中（用于登出）"""
    jti = jwt_payload['jti']
    return redis_client.get(f"jwt_blacklist:{jti}") is not None


#  Celery异步任务
@celery.task
def sync_goods_to_es_async(goods_id):
    """异步同步商品到ES"""
    with app.app_context():
        sync_goods_to_es(goods_id)


# 异步取消超时订单
@celery.task
def cancel_expired_order_task(order_id):
    """异步取消超时订单（延迟执行）"""
    with app.app_context():
        order = Order.query.get(order_id)
        if not order or order.status != 'pending_pay':
            return
        print(f"自动取消超时订单: {order.order_no}")
        order.status = 'cancelled'
        # 恢复库存
        for item in order.items:
            goods = Goods.query.get(item.goods_id)
            if goods:
                goods.stock += item.num
                redis_client.incrby(f"goods_stock:{item.goods_id}", item.num)
        # 恢复购物车
        for item in order.items:
            existing_cart = Cart.query.filter_by(user_id=order.user_id, goods_id=item.goods_id).first()
            if existing_cart:
                existing_cart.num += item.num
            else:
                new_cart = Cart(user_id=order.user_id, goods_id=item.goods_id, num=item.num)
                db.session.add(new_cart)
        db.session.commit()
        return f"订单{order_id}已取消"


# -降价通知
@celery.task
def notify_price_drop(goods_id, old_price, new_price):
    """降价通知：发送给所有购物车中有该商品的用户"""
    with app.app_context():
        try:
            goods = Goods.query.get(goods_id)
            if not goods:
                return
            cart_users = Cart.query.filter_by(goods_id=goods_id).all()
            for cart_item in cart_users:
                user_id = cart_item.user_id
                # 24小时内去重，避免重复通知
                dedup_key = f"notify:price_drop:{goods_id}:{user_id}"
                if redis_client.exists(dedup_key):
                    continue
                content = f"【次元模仓】您购物车中的「{goods.name}」降价啦！从 ¥{old_price} 降到 ¥{new_price}，快去看看吧！"
                log = NotificationLog(
                    user_id=user_id,
                    goods_id=goods_id,
                    type='price_drop',
                    content=content,
                    status='sent'
                )
                db.session.add(log)
                redis_client.setex(dedup_key, 86400, '1')  # 去重标记24小时
            db.session.commit()
            return f"降价通知已处理，商品ID: {goods_id}"
        except Exception as e:
            db.session.rollback()
            print(f"降价通知任务失败: {e}")
            raise


# 下架通知
@celery.task
def notify_off_shelf(goods_id):
    """下架通知：通知所有购物车中有该商品的用户"""
    with app.app_context():
        try:
            goods = Goods.query.get(goods_id)
            if not goods:
                return
            cart_users = Cart.query.filter_by(goods_id=goods_id).all()
            for cart_item in cart_users:
                user_id = cart_item.user_id
                dedup_key = f"notify:off_shelf:{goods_id}:{user_id}"
                if redis_client.exists(dedup_key):
                    continue
                content = f"【次元模仓】很抱歉，您购物车中的「{goods.name}」已被商家下架，请及时处理。"
                log = NotificationLog(
                    user_id=user_id,
                    goods_id=goods_id,
                    type='off_shelf',
                    content=content,
                    status='sent'
                )
                db.session.add(log)
                user_info = UserInfo.query.filter_by(user_id=user_id).first()
                redis_client.setex(dedup_key, 86400, '1')
            db.session.commit()
            return f"下架通知已处理，商品ID: {goods_id}"
        except Exception as e:
            db.session.rollback()
            print(f"下架通知任务失败: {e}")
            raise


# 发货通知
@celery.task
def notify_shipment(order_id):
    """商家发货通知"""
    with app.app_context():
        try:
            order = Order.query.get(order_id)
            if not order:
                return
            first_item = order.items[0] if order.items else None
            if not first_item:
                print(f"订单 {order_id} 无商品项，无法发送发货通知")
                return
            user_id = order.user_id
            goods_name = first_item.goods_name
            dedup_key = f"notify:shipment:{order_id}:{user_id}"
            if redis_client.exists(dedup_key):
                return
            content = f"【次元模仓】您的订单 {order.order_no} 已发货！商品「{goods_name}」正在配送中，请注意查收。"
            log = NotificationLog(
                user_id=user_id,
                goods_id=first_item.goods_id,
                type='shipment',
                content=content,
                status='sent',
                order_id=order_id
            )
            db.session.add(log)
            user_info = UserInfo.query.filter_by(user_id=user_id).first()
            redis_client.setex(dedup_key, 86400, '1')
            db.session.commit()
            return f"发货通知已发送，订单ID: {order_id}"
        except Exception as e:
            db.session.rollback()
            print(f"发货通知任务失败: {e}")
            raise


# 商品更新通知
@celery.task
def notify_goods_update(goods_id, old_name, new_name):
    """商品名称更新通知"""
    with app.app_context():
        try:
            goods = Goods.query.get(goods_id)
            if not goods:
                return
            cart_users = Cart.query.filter_by(goods_id=goods_id).all()
            for cart_item in cart_users:
                user_id = cart_item.user_id
                dedup_key = f"notify:goods_update:{goods_id}:{user_id}"
                if redis_client.exists(dedup_key):
                    continue
                content = f"【次元模仓】您购物车中的商品「{old_name}」已更新为「{new_name}」，快去看看吧！"
                log = NotificationLog(
                    user_id=user_id,
                    goods_id=goods_id,
                    type='goods_update',
                    content=content,
                    status='sent'
                )
                db.session.add(log)
                user_info = UserInfo.query.filter_by(user_id=user_id).first()
                redis_client.setex(dedup_key, 86400, '1')
            db.session.commit()
            return f"商品更新通知已处理，商品ID: {goods_id}"
        except Exception as e:
            db.session.rollback()
            print(f"商品更新通知任务失败: {e}")
            raise

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    """校验验证码，创建用户和用户详情"""
    try:
        data = request.get_json()
        nickname = data.get('nickname', '')
        username = data.get('username', '')
        password = data.get('password', '')
        role = data.get('role', '')
        email = data.get('email', '')
        code = data.get('code', '')

        if not all([nickname, username, password, role, email, code]):
            return jsonify({'code': 400, 'msg': '请完善所有信息'})

        # 校验验证码
        stored_code = redis_client.get(f"code:{email}")
        if not stored_code or stored_code != code:
            return jsonify({'code': 400, 'msg': '验证码错误或已过期'})

        if User.query.filter_by(username=username).first():
            return jsonify({'code': 400, 'msg': '用户名已存在'})

        new_user = User(
            nickname=nickname,
            username=username,
            password=encrypt_password(password),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()

        # 追踪新注册用户（监控统计）
        try:
            today_key = datetime.now().strftime('%Y%m%d')
            redis_client.incr(f'monitor:new_registrations:{today_key}')
            redis_client.expire(f'monitor:new_registrations:{today_key}', 86400 * 7)
        except Exception:
            pass

        # 自动创建用户详情记录
        if not new_user.info:
            user_info = UserInfo(user_id=new_user.id, email=email)
            db.session.add(user_info)
            db.session.commit()

        redis_client.delete(f"code:{email}")  # 注册成功后清除验证码
        return jsonify({'code': 200, 'msg': '注册成功！'})
    except Exception as e:
        db.session.rollback()
        print(f"注册失败：{e}")
        return jsonify({'code': 500, 'msg': '服务器异常，注册失败'})


# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    """用户登录，返回JWT token"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        user = User.query.filter_by(username=username, role=role).first()
        if not user:
            return jsonify({'code': 400, 'msg': '用户名/密码/角色错误'})
        try:
            decrypted = decrypt_password(user.password)
        except Exception:
            return jsonify({'code': 400, 'msg': '用户名/密码/角色错误'})
        if decrypted != password:
            return jsonify({'code': 400, 'msg': '用户名/密码/角色错误'})

        # 检查封禁状态
        if user.is_banned:
            return jsonify({'code': 403, 'msg': '您的账号已被封禁，请联系管理员'}), 403

        access_token = create_access_token(identity=str(user.id),additional_claims={'id': user.id, 'role': role, 'nickname': user.nickname})
        return jsonify({
            'code': 200,
            'msg': '登录成功',
            'token': access_token,
            'nickname': user.nickname,
            'role': role,
            'userId': user.id
        })
    except Exception as e:
        print(f"登录错误: {e}")
        return jsonify({'code': 500, 'msg': f'登录失败: {str(e)}'}), 500


# 用户登出
@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    """登出：将当前token加入黑名单"""
    jti = get_jwt()['jti']
    redis_client.setex(f"jwt_blacklist:{jti}", app.config['JWT_ACCESS_TOKEN_EXPIRES'], 1)
    return jsonify({'code': 200, 'msg': '登出成功'})


# 发送注册验证码
@app.route('/api/send_code', methods=['POST'])
def send_code():
    """发送邮箱验证码（用于注册）"""
    data = request.get_json()
    email = data.get('email', '')
    if '@qq.com' not in email:
        return jsonify({'code': 400, 'msg': '请输入有效的QQ邮箱'})
    code = generate_code()
    redis_client.setex(f"code:{email}", 300, code)  # 验证码5分钟有效
    if send_email(email, code):
        return jsonify({'code': 200, 'msg': '验证码已发送到QQ邮箱'})
    else:
        return jsonify({'code': 500, 'msg': '验证码发送失败，请检查邮箱'})


# 管理员登录
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员专用登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username != 'admin' or password != 'admin':
        return jsonify({'code': 400, 'msg': '账号或密码错误'}), 400
    access_token = create_access_token(
        identity='0',
        additional_claims={'id': 0, 'role': 'admin', 'nickname': '管理员'}
    )
    return jsonify({
        'code': 200,
        'msg': '登录成功',
        'token': access_token,
        'nickname': '管理员',
        'role': 'admin',
        'userId': 0
    })

# 发送QQ邮箱验证码
@app.route('/api/reset-password-send', methods=['POST'])
def reset_password_send_code():
    """发送找回密码验证码"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()

        if not username:
            return jsonify({'code': 400, 'msg': '请输入账号'}), 400
        if not email or '@' not in email:
            return jsonify({'code': 400, 'msg': '请输入有效的邮箱'}), 400

        # 查找该用户名对应的用户
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'code': 400, 'msg': '账号不存在'}), 400

        # 验证邮箱是否与该用户匹配
        user_info = UserInfo.query.filter_by(user_id=user.id).first()
        if not user_info or user_info.email != email:
            return jsonify({'code': 400, 'msg': '账号与邮箱不匹配'}), 400

        # 生成验证码并存入Redis
        code = generate_code()
        redis_client.setex(f"reset_code:{username}:{email}", 300, code)

        # 发送邮件
        msg = MIMEText(f'您的找回密码验证码是：{code}，5分钟内有效，请勿泄露。', 'plain', 'utf-8')
        msg['From'] = f"{Header('次元模仓', 'utf-8').encode()} <{SMTP_USER}>"
        msg['To'] = email
        msg['Subject'] = Header('【次元模仓】找回密码验证码', 'utf-8')

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [email], msg.as_string())

        return jsonify({'code': 200, 'msg': '验证码已发送到邮箱'})
    except Exception as e:
        print(f"发送找回密码验证码失败: {e}")
        return jsonify({'code': 500, 'msg': '验证码发送失败'}), 500


#  重置密码
@app.route('/api/reset-password-reset', methods=['POST'])
def reset_password():
    """重置密码"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        new_password = data.get('newPassword', '').strip()

        if not all([username, email, code, new_password]):
            return jsonify({'code': 400, 'msg': '请完善所有信息'}), 400

        if len(new_password) < 6:
            return jsonify({'code': 400, 'msg': '密码长度不能少于6位'}), 400

        # 验证验证码
        stored_code = redis_client.get(f"reset_code:{username}:{email}")
        if not stored_code or stored_code != code:
            return jsonify({'code': 400, 'msg': '验证码错误或已过期'}), 400

        # 查找用户
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'code': 400, 'msg': '账号不存在'}), 400

        # 再次验证邮箱
        user_info = UserInfo.query.filter_by(user_id=user.id).first()
        if not user_info or user_info.email != email:
            return jsonify({'code': 400, 'msg': '账号与邮箱不匹配'}), 400

        # 检查新密码是否与旧密码相同
        if decrypt_password(user.password) == new_password:
            return jsonify({'code': 400, 'msg': '新密码不能与当前密码相同'}), 400

        # 重置密码
        user.password = encrypt_password(new_password)
        redis_client.delete(f"reset_code:{username}:{email}")
        db.session.commit()

        return jsonify({'code': 200, 'msg': '密码重置成功，请登录'})
    except Exception as e:
        db.session.rollback()
        print(f"重置密码失败: {e}")
        return jsonify({'code': 500, 'msg': '重置密码失败'}), 500

# 上传商品图片
@app.route('/api/upload/image', methods=['POST'])
@jwt_required()
def upload_image():
    """上传商品图片到MinIO，返回图片URL"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '请选择图片'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '文件名不能为空'})
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    file_name = f"{uuid.uuid4().hex}.{file_ext}"  # UUID命名避免冲突
    try:
        minio_client.put_object(MINIO_BUCKET, file_name, file, length=-1, part_size=10 * 1024 * 1024,
                                content_type=f"image/{file_ext}")
        return jsonify({'code': 200, 'msg': '上传成功', 'url': f"/goods-images/{file_name}"})
    except S3Error as e:
        print(f"MinIO错误: {e}")
        return jsonify({'code': 500, 'msg': '图片上传失败'})


# 发布商品
@app.route('/api/goods/publish', methods=['POST'])
@jwt_required()
def publish_goods():
    """商家发布新商品"""
    user = get_jwt()
    if user['role'] != 'merchant':
        return jsonify({'code': 403, 'msg': '仅商家可发布'})
    data = request.get_json()
    user_obj = User.query.get(user['id'])
    if not user_obj:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    # 校验入驻审核状态
    if user_obj.apply_status != 'approved':
        if user_obj.apply_status == 'none':
            return jsonify({'code': 403, 'msg': '请先提交入驻申请，等待管理员审核通过后再发布商品'}), 403
        elif user_obj.apply_status == 'pending':
            return jsonify({'code': 403, 'msg': '您的入驻申请正在审核中，请等待管理员审核通过'}), 403
        elif user_obj.apply_status == 'rejected':
            return jsonify({'code': 403, 'msg': '您的入驻申请已被拒绝，无法发布商品，如有疑问请联系管理员'}), 403
    data = request.get_json()
    required_fields = ['name', 'price', 'images']
    if not all([data.get(field) for field in required_fields]):
        return jsonify({'code': 400, 'msg': '请完善商品名称、价格、图片'})
    new_goods = Goods(
        name=data['name'],
        price=data['price'],
        stock=data.get('stock', 1),
        images=','.join(data['images']),
        description=data.get('description', ''),
        category=data.get('category', ''),
        status=data.get('status', ''),
        brand=data.get('brand', ''),
        ip=data.get('ip', ''),
        charactername=data.get('character', ''),
        merchant_id=user['id'],
        merchant_name=user.get('nickname', '商家')
    )
    try:
        db.session.add(new_goods)
        db.session.commit()
        sync_goods_to_es_async.delay(new_goods.id)  # 异步同步到ES
        return jsonify({'code': 200, 'msg': '上架成功', 'goods_id': new_goods.id})
    except Exception as e:
        db.session.rollback()
        print(f"发布商品错误: {e}")
        return jsonify({'code': 500, 'msg': '上架失败'})


#  获取商品列表（分页+缓存）
@app.route('/api/goods/list', methods=['GET'])
@cache(key_prefix='goods_list', expire=600)
def get_goods_list():
    """分页获取商品列表（带缓存，10分钟过期）"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    pagination = Goods.query.order_by(Goods.created_at.desc()).paginate(page=page, per_page=size)
    goods = pagination.items

    res = [{
        'id': g.id,
        'name': g.name,
        'price': float(g.price),
        'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
        'description': g.description,
        'category': g.category,
        'status': g.status,
        'brand': g.brand,
        'ip': g.ip,
        'charactername': g.charactername,
        'merchant_name': g.merchant_name
    } for g in goods]
    return jsonify({
        'code': 200,
        'data': res,
        'pagination': {
            'total': pagination.total,
            'page': page,
            'size': size,
            'pages': pagination.pages
        }
    })


#  ES全文搜索商品
@app.route('/api/goods/search', methods=['GET'])
def search_goods():
    """基于ES的全文搜索商品"""
    try:
        q = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        if not q:
            return jsonify({'code': 400, 'msg': '搜索关键词不能为空'})
        # 追踪搜索关键词（监控统计）
        try:
            today_key = datetime.now().strftime('%Y%m%d')
            redis_client.zincrby(f'monitor:search_keywords:{today_key}', 1, q)
            redis_client.expire(f'monitor:search_keywords:{today_key}', 86400 * 7)
        except Exception:
            pass
        from_ = (page - 1) * size
        # 多字段匹配搜索
        search_body = {
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["name", "description", "category", "brand", "ip", "charactername"],
                    "type": "best_fields"
                }
            },
            "from": from_,
            "size": size
        }
        result = es_client.search(index='goods_index', body=search_body)
        hits = result['hits']['hits']
        res = []

        for hit in hits:
            source = hit['_source']
            res.append({
                'id': int(hit['_id']),
                'name': source.get('name', ''),
                'price': source.get('price', 0),
                'image': fix_image_url(source.get('image', '')),
                'description': source.get('description', ''),
                'category': source.get('category', ''),
                'status': source.get('status', ''),
                'brand': source.get('brand', ''),
                'ip': source.get('ip', ''),
                'charactername': source.get('charactername', ''),
                'merchant_name': source.get('merchant_name', '')
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"搜索商品错误: {e}")
        return jsonify({'code': 500, 'msg': '搜索失败'})


# 获取商品筛选选项
@app.route('/api/goods/options', methods=['GET'])
def get_goods_options():
    """获取商品筛选选项（分类、品牌、IP列表）"""
    try:
        # 从数据库中获取所有不重复的值
        categories = db.session.query(Goods.category).filter(
            Goods.category != None,
            Goods.category != ''
        ).distinct().all()
        brands = db.session.query(Goods.brand).filter(
            Goods.brand != None,
            Goods.brand != ''
        ).distinct().all()
        ips = db.session.query(Goods.ip).filter(
            Goods.ip != None,
            Goods.ip != ''
        ).distinct().all()

        return jsonify({
            'code': 200,
            'data': {
                'categories': [c[0] for c in categories if c[0]],
                'brands': [b[0] for b in brands if b[0]],
                'ips': [i[0] for i in ips if i[0]]
            }
        })
    except Exception as e:
        print(f"获取商品选项错误: {e}")
        return jsonify({'code': 500, 'msg': '获取选项失败'})


# 获取商品详情
@app.route('/api/goods/detail/<int:id>', methods=['GET'])
@cache(key_prefix='goods_detail', expire=1800)
def get_goods_detail(id):
    """获取商品详情，同时自动记录浏览历史"""
    g = Goods.query.get_or_404(id)
    merchant_avatar = ''
    merchant_user = User.query.get(g.merchant_id)
    if merchant_user and merchant_user.info:
        merchant_avatar = merchant_user.info.avatar

    # 自动记录浏览足迹
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        try:
            decoded = decode_token(token.split(' ')[1])
            user_id = int(decoded['sub'])
            existing_history = History.query.filter_by(user_id=user_id, goods_id=id).first()
            if existing_history:
                existing_history.browse_time = datetime.now()  # 更新浏览时间
            else:
                new_history = History(user_id=user_id, goods_id=id)
                db.session.add(new_history)
            db.session.commit()
        except Exception as e:
            print(f"自动记录足迹失败: {e}")

    images = [fix_image_url(img) for img in g.images.split(',')] if g.images else []
    return jsonify({
        'code': 200,
        'data': {
            'id': g.id,
            'name': g.name,
            'price': float(g.price),
            'stock': g.stock,
            'images': images,
            'description': g.description,
            'category': g.category,
            'status': g.status,
            'brand': g.brand,
            'ip': g.ip,
            'character': g.charactername,
            'merchant_name': g.merchant_name,
            'merchant_avatar': fix_image_url(merchant_avatar),
            'created_at': g.created_at.strftime('%Y-%m-%d')
        }
    })


# 获取商家自己的商品列表
@app.route('/api/goods/merchant', methods=['GET'])
@jwt_required()
def get_merchant_goods():
    """商家获取自己发布的商品列表"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可访问'})
        goods = Goods.query.filter_by(merchant_id=user['id']).order_by(Goods.created_at.desc()).all()

        res = [{
            'id': g.id,
            'name': g.name,
            'price': float(g.price),
            'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
            'status': g.status,
            'category': g.category
        } for g in goods]
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取商家商品错误: {e}")
        return jsonify({'code': 500, 'msg': '获取商品失败'})


#更新商品信息-
@app.route('/api/goods/update/<int:id>', methods=['POST'])
@jwt_required()
def update_goods(id):
    """商家更新商品信息，同时触发价格/下架/名称变更通知"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'})
        goods = Goods.query.get_or_404(id)
        if goods.merchant_id != user['id']:
            return jsonify({'code': 403, 'msg': '无权修改该商品'})
        data = request.get_json()
        old_price = float(goods.price)
        old_status = goods.status
        old_name = goods.name

        # 更新商品字段
        goods.name = data.get('name', goods.name)
        goods.price = data.get('price', goods.price)
        goods.stock = data.get('stock', goods.stock)
        goods.images = ','.join(data.get('images', [])) if data.get('images') else goods.images
        goods.description = data.get('description', goods.description)
        goods.category = data.get('category', goods.category)
        goods.status = data.get('status', goods.status)
        goods.brand = data.get('brand', goods.brand)
        goods.ip = data.get('ip', goods.ip)
        goods.charactername = data.get('character', goods.charactername)
        db.session.commit()

        # 同步Redis库存缓存
        new_stock = data.get('stock')
        if new_stock is not None:
            redis_client.set(f"goods_stock:{id}", new_stock)
        # 清除商品列表和详情缓存
        redis_client.delete('goods_list:default')
        redis_client.delete(f'goods_detail:{id}')
        sync_goods_to_es(id)

        # 降价通知：新价格低于旧价格时触发
        new_price = data.get('price')
        if new_price is not None and float(new_price) < old_price:
            notify_price_drop.delay(id, old_price, float(new_price))

        # 下架通知：状态从非下架变为下架时触发
        new_status = data.get('status')
        if old_status != '下架' and new_status == '下架':
            notify_off_shelf.delay(id)

        # 商品名称变更通知
        new_name = data.get('name')
        if new_name is not None and new_name != old_name:
            notify_goods_update.delay(id, old_name, new_name)

        return jsonify({'code': 200, 'msg': '更新成功'})
    except Exception as e:
        db.session.rollback()
        print(f"更新商品错误: {e}")
        return jsonify({'code': 500, 'msg': '更新失败'})


# 删除商品
@app.route('/api/goods/delete/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_goods(id):
    """商家删除商品"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'})
        goods = Goods.query.get_or_404(id)
        if goods.merchant_id != user['id']:
            return jsonify({'code': 403, 'msg': '无权删除该商品'})

        # 删除关联数据：购物车、收藏、浏览记录
        Cart.query.filter_by(goods_id=id).delete()
        Collect.query.filter_by(goods_id=id).delete()
        History.query.filter_by(goods_id=id).delete()

        # 删除商品
        db.session.delete(goods)
        db.session.commit()

        # 清除Redis缓存
        redis_client.delete(f"goods_stock:{id}")
        redis_client.delete('goods_list:default')
        redis_client.delete(f'goods_detail:{id}')

        # 从ES中删除
        try:
            es_client.delete(index='goods_index', id=str(id))
        except:
            pass

        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"删除商品错误: {e}")
        return jsonify({'code': 500, 'msg': '删除失败'})

# 获取购物车列表
@app.route('/api/cart/list', methods=['GET'])
@jwt_required()
def cart_list():
    """获取当前用户的购物车列表"""
    try:
        user_id = int(get_jwt_identity())
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        res = []
        for item in cart_items:
            g = item.goods
            res.append({
                'id': item.id,
                'goods_id': g.id,
                'name': g.name,
                'price': float(g.price),
                'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
                'num': item.num,
                'stock': g.stock,
                'status': g.status
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取购物车错误: {e}")
        return jsonify({'code': 500, 'msg': '获取购物车失败'})


# 添加商品到购物车
@app.route('/api/cart/add', methods=['POST'])
@jwt_required()
def cart_add():
    """添加商品到购物车"""
    try:
        user_id = int(get_jwt_identity())
        goods_id = request.get_json().get('goods_id')
        goods = Goods.query.get(goods_id)
        if not goods:
            return jsonify({'code': 404, 'msg': '商品不存在'})
        if goods.status == '下架':
            return jsonify({'code': 400, 'msg': '商品已下架'})
        if goods.stock <= 0:
            return jsonify({'code': 400, 'msg': '商品已售罄'})
        item = Cart.query.filter_by(user_id=user_id, goods_id=goods_id).first()
        if item:
            item.num += 1
        else:
            item = Cart(user_id=user_id, goods_id=goods_id, num=1)
            db.session.add(item)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '加入购物车成功'})
    except Exception as e:
        db.session.rollback()
        print(f"加入购物车错误: {e}")
        return jsonify({'code': 500, 'msg': '加入购物车失败'})


# 修改购物车商品数量
@app.route('/api/cart/update', methods=['POST'])
@jwt_required()
def cart_update():
    """修改购物车中商品数量"""
    try:
        data = request.get_json()
        item = Cart.query.get(data['id'])
        if not item:
            return jsonify({'code': 404, 'msg': '购物车项不存在'})
        item.num = data['num']
        db.session.commit()
        return jsonify({'code': 200, 'msg': '修改成功'})
    except Exception as e:
        print(f"修改数量错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '修改失败'})


# 删除购物车单项
@app.route('/api/cart/delete/<int:id>', methods=['DELETE'])
@jwt_required()
def cart_delete(id):
    """删除购物车中的单个商品"""
    try:
        item = Cart.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        print(f"删除商品错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除失败'})


#  清空购物车
@app.route('/api/cart/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """支付成功后调用"""
    try:
        user_id = int(get_jwt_identity())
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({'code': 200, 'msg': '支付成功，购物车已清空'})
    except Exception as e:
        db.session.rollback()
        print(f"清空购物车错误: {e}")
        return jsonify({'code': 500, 'msg': '支付失败，请重试'})

@app.route('/api/collect/add', methods=['POST'])
@jwt_required()
def add_collect():
    """添加收藏"""
    try:
        user_id = int(get_jwt_identity())
        goods_id = request.get_json().get('goods_id')
        if not goods_id:
            return jsonify({'code': 400, 'msg': '商品ID不能为空'}), 400
        goods = Goods.query.get(goods_id)
        if not goods:
            return jsonify({'code': 404, 'msg': '商品不存在'}), 404
        exist = Collect.query.filter_by(user_id=user_id, goods_id=goods_id).first()
        if exist:
            return jsonify({'code': 400, 'msg': '已收藏该商品'}), 400
        new_collect = Collect(user_id=user_id, goods_id=goods_id)
        db.session.add(new_collect)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '收藏成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f'添加收藏失败: {e}')
        return jsonify({'code': 500, 'msg': '收藏失败'}), 500


@app.route('/api/collect/delete', methods=['POST'])
@jwt_required()
def delete_collect():
    """取消收藏"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        collect_id = data.get('id')
        goods_id = data.get('goods_id')
        if not collect_id and not goods_id:
            return jsonify({'code': 400, 'msg': '参数错误'}), 400
        if collect_id:
            collect = Collect.query.get(collect_id)
        else:
            collect = Collect.query.filter_by(user_id=user_id, goods_id=goods_id).first()
        if not collect:
            return jsonify({'code': 404, 'msg': '收藏记录不存在'}), 404
        db.session.delete(collect)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '取消收藏成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f'取消收藏失败: {e}')
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


#  获取收藏列表
@app.route('/api/collect/list', methods=['GET'])
@jwt_required()
def get_collect_list():
    """获取当前用户的收藏列表"""
    try:
        user_id = int(get_jwt_identity())
        collects = Collect.query.filter_by(user_id=user_id).order_by(Collect.created_at.desc()).all()
        res = []
        for item in collects:
            g = item.goods
            res.append({
                'id': item.id,
                'goods_id': g.id,
                'name': g.name,
                'price': float(g.price),
                'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({'code': 200, 'data': res}), 200
    except Exception as e:
        print(f'获取收藏列表失败: {e}')
        return jsonify({'code': 500, 'msg': '获取失败'}), 500


# 检查收藏状态
@app.route('/api/collect/check', methods=['GET'])
@jwt_required()
def check_collect():
    """检查当前用户是否收藏了某商品"""
    try:
        user_id = int(get_jwt_identity())
        goods_id = request.args.get('goods_id')
        if not goods_id:
            return jsonify({'code': 400, 'msg': '商品ID不能为空'}), 400
        exist = Collect.query.filter_by(user_id=user_id, goods_id=goods_id).first()
        return jsonify({'code': 200, 'data': {'is_collected': exist is not None}}), 200
    except Exception as e:
        print(f'检查收藏状态失败: {e}')
        return jsonify({'code': 500, 'msg': '检查失败'}), 500

# 添加浏览记录
@app.route('/api/user/history/add', methods=['POST'])
@jwt_required()
def add_history():
    """手动添加浏览记录"""
    try:
        user_id = int(get_jwt_identity())
        goods_id = request.get_json().get('goods_id')
        if not goods_id:
            return jsonify({'code': 400, 'msg': '商品ID不能为空'})
        goods = Goods.query.get(goods_id)
        if not goods:
            return jsonify({'code': 404, 'msg': '商品不存在'})
        existing_history = History.query.filter_by(user_id=user_id, goods_id=goods_id).first()
        if existing_history:
            existing_history.browse_time = datetime.now()  # 更新浏览时间
        else:
            new_history = History(user_id=user_id, goods_id=goods_id)
            db.session.add(new_history)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '足迹记录成功'})
    except Exception as e:
        print(f"记录足迹错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '记录足迹失败'})


#  获取浏览历史列表
@app.route('/api/user/history', methods=['GET'])
@jwt_required()
def get_history():
    """获取当前用户的浏览历史列表"""
    try:
        user_id = int(get_jwt_identity())
        history_list = History.query.filter_by(user_id=user_id).order_by(History.browse_time.desc()).all()
        res = []
        for item in history_list:
            g = item.goods
            res.append({
                'id': item.id,
                'goodsId': g.id,
                'name': g.name,
                'price': float(g.price),
                'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
                'browseTime': item.browse_time.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取足迹错误: {e}")
        return jsonify({'code': 500, 'msg': '获取足迹失败'})

@app.route('/api/user/history/delete', methods=['POST'])
@jwt_required()
def delete_history():
    """删除单条浏览记录"""
    try:
        history_id = request.get_json().get('id')
        history = History.query.get(history_id)
        if not history:
            return jsonify({'code': 404, 'msg': '足迹不存在'})
        db.session.delete(history)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        print(f"删除足迹错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除失败'})


# 清空所有浏览记录
@app.route('/api/user/history/clear', methods=['POST'])
@jwt_required()
def clear_history():
    """清空所有浏览记录"""
    try:
        user_id = int(get_jwt_identity())
        History.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({'code': 200, 'msg': '清空成功'})
    except Exception as e:
        print(f"清空足迹错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '清空失败'})

# 记录用户行为
@app.route('/api/user/behavior', methods=['POST'])
@jwt_required()
def record_user_behavior():
    """
    行为权重：浏览=1，收藏=3，购买=5
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        goods_id = data.get('goods_id')
        behavior_type = data.get('type', 'view')

        if not goods_id:
            return jsonify({'code': 400, 'msg': '商品ID不能为空'})

        goods = Goods.query.get(goods_id)
        if not goods:
            return jsonify({'code': 404, 'msg': '商品不存在'})

        # 权重映射
        weight_map = {'view': 1, 'collect': 3, 'purchase': 5}
        weight = weight_map.get(behavior_type, 1)

        # 使用Redis存储用户行为权重
        pipe = redis_client.pipeline()
        if goods.ip:
            key = f'user_pref:{user_id}:ip'
            pipe.zincrby(key, weight, goods.ip)
        if goods.charactername:
            key = f'user_pref:{user_id}:character'
            pipe.zincrby(key, weight, goods.charactername)
        if goods.category:
            key = f'user_pref:{user_id}:category'
            pipe.zincrby(key, weight, goods.category)
        if goods.brand:
            key = f'user_pref:{user_id}:brand'
            pipe.zincrby(key, weight, goods.brand)
        pipe.execute()

        return jsonify({'code': 200, 'msg': '记录成功'})
    except Exception as e:
        print(f"记录用户行为错误: {e}")
        return jsonify({'code': 500, 'msg': '记录失败'})


# 猜你喜欢推荐
@app.route('/api/recommend/personal', methods=['GET'])
@jwt_required()
def get_personal_recommend():
    """
    有权重记录时，偏好相关商品概率更高，但所有商品都有机会出现
    """
    try:
        user_id = int(get_jwt_identity())
        # 获取所有在售商品
        all_goods = Goods.query.filter(Goods.status != '下架').all()
        if not all_goods:
            return jsonify({'code': 200, 'data': []})

        # 获取用户偏好权重
        ip_prefs = redis_client.zrevrange(f'user_pref:{user_id}:ip', 0, 5, withscores=True)
        char_prefs = redis_client.zrevrange(f'user_pref:{user_id}:character', 0, 5, withscores=True)
        cate_prefs = redis_client.zrevrange(f'user_pref:{user_id}:category', 0, 5, withscores=True)

        # 构建偏好字典
        pref_weights = {}
        for k, score in list(ip_prefs) + list(char_prefs) + list(cate_prefs):
            if k:
                keyword = k.decode() if isinstance(k, bytes) else k
                pref_weights[keyword] = pref_weights.get(keyword, 0) + score

        # 为每个商品计算分数
        goods_scores = []
        base_score = 1  # 基础分

        for g in all_goods:
            score = base_score
            # 根据商品属性匹配偏好关键词，增加分数
            if g.ip and g.ip in pref_weights:
                score += pref_weights[g.ip] * 2
            if g.charactername and g.charactername in pref_weights:
                score += pref_weights[g.charactername] * 2
            if g.category and g.category in pref_weights:
                score += pref_weights[g.category]
            if g.brand and g.brand in pref_weights:
                score += pref_weights.get(g.brand, 0)
            # 商品名称包含偏好关键词也加分
            for keyword, weight in pref_weights.items():
                if keyword.lower() in g.name.lower():
                    score += weight * 0.5

            goods_scores.append((g, score))

        # 按分数加权随机选择一个商品
        total_score = sum(score for _, score in goods_scores)
        rand_val = random.random() * total_score
        cumulative = 0
        selected_goods = goods_scores[0][0]  # 默认第一个
        for g, score in goods_scores:
            cumulative += score
            if rand_val <= cumulative:
                selected_goods = g
                break

        goods_data = {
            'id': selected_goods.id,
            'name': selected_goods.name,
            'price': float(selected_goods.price),
            'image': fix_image_url(selected_goods.images.split(',')[0]) if selected_goods.images else '',
            'ip': selected_goods.ip,
            'charactername': selected_goods.charactername
        }

        return jsonify({'code': 200, 'data': [goods_data]})
    except Exception as e:
        print(f"猜你喜欢错误: {e}")
        return jsonify({'code': 500, 'msg': '获取推荐失败'})


#  AI客服
#  Redis商品索引构建
def rebuild_redis_goods_index(goods_list):
    """将商品多字段索引写入Redis，支持按字段加权搜索"""
    pipe = redis_client.pipeline()
    # 清除旧索引
    for key in redis_client.keys('ai_index:*'):
        pipe.delete(key)
    pipe.delete('ai_index:goods_map')

    goods_map = {}
    for g in goods_list:
        price = float(g.price) if g.price else 0
        goods_map[str(g.id)] = json.dumps({
            'id': g.id,
            'name': g.name or '',
            'price': price,
            'ip': g.ip or '',
            'charactername': g.charactername or '',
            'brand': g.brand or '',
            'category': g.category or '',
            'image': fix_image_url(g.images.split(',')[0]) if g.images else ''
        }, ensure_ascii=False)

        # 按字段类型分别建索引，权重不同
        field_weights = {
            'ip': 5,            # IP匹配权重最高
            'charactername': 5, # 角色名匹配权重最高
            'name': 4,          # 商品名次之
            'brand': 3,         # 品牌再次
            'category': 2       # 分类最低
        }
        for field, weight in field_weights.items():
            val = getattr(g, field, None)
            if val and val.strip():
                key = val.strip().lower()
                redis_key = f'ai_index:field:{field}:{key}'
                pipe.sadd(redis_key, g.id)
                pipe.expire(redis_key, 600)

    pipe.execute()
    # 存储商品详情映射
    redis_client.hset('ai_index:goods_map', mapping=goods_map)
    redis_client.expire('ai_index:goods_map', 600)
    print(f"[Redis索引] 已构建，共 {len(goods_list)} 个商品")


def get_cached_goods():
    """获取缓存的商品列表，索引从Redis读取"""
    import time
    now = time.time()

    if _goods_cache['data'] is not None and (now - _goods_cache['updated_at']) < _GOODS_CACHE_TTL:
        return _goods_cache['data']

    # 重新加载
    try:
        goods_list = Goods.query.filter(Goods.status != '下架').all()
        _goods_cache['data'] = goods_list
        _goods_cache['updated_at'] = now
        # 同步构建Redis索引
        rebuild_redis_goods_index(goods_list)
        print(f"[商品缓存] 已更新，共 {len(goods_list)} 个商品")
    except Exception as e:
        print(f"[商品缓存] 加载失败: {e}")
        if _goods_cache['data'] is not None:
            return _goods_cache['data']
        return []

    return _goods_cache['data']


@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """AI客服对话接口：AI做意图分析+对话，有购买意图时Redis加权搜索推荐商品"""
    import re
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])

        if not user_message:
            return jsonify({'code': 400, 'msg': '消息不能为空'})

        # 确保商品缓存和Redis索引可用
        get_cached_goods()

        # 调用AI：同时完成意图分析 + 对话回复
        headers = {
            "Authorization": f"Bearer {ZHIPU_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = """你是次元模仓AI客服，负责手办、模型咨询。
你需要判断用户意图并回复。

【意图判断规则】
- 如果用户有购买/寻找商品的意图（如：想买、推荐、有没有、找、看看、想要、需要等），判定为"purchase"
- 如果用户只是闲聊/问订单/问售后等，判定为"chat"

【回复格式】
第一行输出意图标记，第二行开始是回复内容：
purchase:关键词1,关键词2,关键词3
回复内容...

chat
回复内容

示例：
purchase:初音未来,200
为您找到了初音相关的手办，请看推荐~

chat
关于订单问题，请在"我的订单"中查看。"""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-5:]:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})

        chat_payload = {
            "model": "glm-4.5-air",
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.6
        }

        ai_reply = ""
        goods_data = None

        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    ZHIPU_API_URL,
                    headers=headers,
                    json=chat_payload,
                    timeout=20
                )
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.Timeout) as e:
                print(f"[AI重试] 第{attempt + 1}次超时: {e}")
                if attempt == max_retries - 1:
                    raise

        if response.status_code == 200:
            result = response.json()
            raw_reply = result['choices'][0]['message']['content']
            print(f"[AI原始回复] {raw_reply}")

            # 解析AI回复：提取意图和关键词
            lines = raw_reply.strip().split('\n', 1)
            first_line = lines[0].strip()
            reply_body = lines[1].strip() if len(lines) > 1 else first_line

            if first_line.lower().startswith('purchase:'):
                # 有购买意图，提取关键词
                keywords_str = first_line[len('purchase:'):].strip()
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                print(f"[意图分析] 购买意图，关键词: {keywords}")

                # 用关键词在Redis中进行多字段加权搜索
                goods_data = search_by_redis_index(keywords, user_message)
                ai_reply = reply_body

                # 清除回复中可能残留的商品编号
                ai_reply = re.sub(r'\[RECOMMEND:\d+\]', '', ai_reply).strip()
                ai_reply = re.sub(r'商品[ID编号：:]*\d+', '', ai_reply).strip()

            elif first_line.lower() == 'chat':
                # 无购买意图，纯对话
                ai_reply = reply_body
                print(f"[意图分析] 普通对话")
            else:
                # 解析失败，直接用原始回复
                ai_reply = raw_reply
                print(f"[意图分析] 解析失败，使用原始回复")
        else:
            print(f"智谱AI调用失败: {response.status_code}")
            ai_reply = get_fallback_reply(user_message)

        if not ai_reply:
            ai_reply = get_fallback_reply(user_message)

        return jsonify({
            'code': 200,
            'data': {
                'reply': ai_reply,
                'goods': goods_data
            }
        })

    except Exception as e:
        print(f"AI客服错误: {e}")
        import traceback
        traceback.print_exc()
        fallback_reply = get_fallback_reply(user_message if 'user_message' in dir() else '')
        return jsonify({'code': 200, 'data': {'reply': fallback_reply, 'goods': None}})


# Redis多字段加权搜索
def search_by_redis_index(keywords, user_message=''):
    """使用AI提取的关键词在Redis多字段索引中进行加权搜索
    keywords: AI提取的关键词列表，如 ['初音未来', '200']
    user_message: 原始用户消息，用于提取预算等额外信息
    """
    import re
    try:
        if not keywords:
            return None

        # 从原始消息中提取预算信息
        budget_max = None
        budget_match = re.search(r'(\d+)\s*[元块]?', user_message)
        if budget_match and any(w in user_message for w in ['预算', '以内', '以下', '不超过', '只有', '就', '左右', '块钱']):
            budget_max = int(budget_match.group(1))
        # 也从关键词中提取预算（AI可能把数字作为关键词）
        for kw in keywords:
            if kw.isdigit() and int(kw) >= 10:
                budget_max = int(kw)

        # 从Redis获取所有字段索引key
        all_index_keys = redis_client.keys('ai_index:field:*')
        if not all_index_keys:
            return None

        # 字段权重定义
        field_weights = {
            'ip': 5,            # IP匹配权重最高
            'charactername': 5, # 角色名匹配权重最高
            'name': 4,          # 商品名次之
            'brand': 3,         # 品牌再次
            'category': 2       # 分类最低
        }

        # 对每个关键词，在Redis索引中查找匹配的商品并计算加权得分
        goods_scores = {}  # {goods_id: total_score}

        for keyword in keywords:
            kw_lower = keyword.lower()

            for redis_key in all_index_keys:
                # 解析字段名和索引词: ai_index:field:{field}:{index_word}
                parts = redis_key.split(':', 3)
                if len(parts) < 4:
                    continue
                field = parts[2]
                index_word = parts[3]

                # 双向匹配：关键词包含索引词，或索引词包含关键词
                if kw_lower in index_word or index_word in kw_lower:
                    weight = field_weights.get(field, 1)

                    # 关键词越长匹配越精确，额外加分
                    length_bonus = min(len(kw_lower), 3)
                    weight += length_bonus

                    # 获取该索引词下的所有商品ID
                    member_ids = redis_client.smembers(redis_key)
                    for gid in member_ids:
                        gid = int(gid)
                        if gid not in goods_scores:
                            goods_scores[gid] = 0
                        goods_scores[gid] += weight

        if not goods_scores:
            return None

        # 从Redis获取商品详情并应用预算过滤
        candidates = []
        for gid, score in goods_scores.items():
            raw = redis_client.hget('ai_index:goods_map', str(gid))
            if not raw:
                continue
            g = json.loads(raw)
            price = g.get('price', 0)

            # 预算过滤
            if budget_max:
                if price > budget_max * 1.2:
                    score -= 20  # 超预算20%以上大幅扣分
                elif price > budget_max:
                    score -= 5   # 微超预算轻微扣分
                else:
                    # 预算内加分，越接近预算上限越好
                    ratio = price / budget_max if budget_max > 0 else 0
                    score += int(5 * ratio)

            if score > 0:
                candidates.append((g, score))

        if not candidates:
            # 放宽条件：取原始分数最高的
            for gid, score in goods_scores.items():
                raw = redis_client.hget('ai_index:goods_map', str(gid))
                if raw:
                    candidates.append((json.loads(raw), score))

        if not candidates:
            return None

        # 按分数排序，取最高分
        candidates.sort(key=lambda x: x[1], reverse=True)
        best = candidates[0][0]
        print(f"[Redis搜索] 关键词:{keywords} → 匹配商品: {best['name']}, 分数: {candidates[0][1]}")
        return best

    except Exception as e:
        print(f"[Redis搜索] 异常: {e}")
        import traceback
        traceback.print_exc()
        return None


# AI服务不可用时的预设回复
def get_fallback_reply(message):
    """降级回复：当AI服务不可用时使用预设回复"""
    if not message:
        return "您好，请问有什么可以帮您？"

    message = message.lower()

    if '订单' in message or '发货' in message:
        return '关于订单问题，您可以在"我的订单"中查看详情。如有其他问题，请详细描述，我们会尽快处理。'
    elif '退款' in message or '退货' in message:
        return '退款/退货申请请在订单详情中提交售后申请，商家会在1-3个工作日内处理。'
    elif '商品' in message or '手办' in message:
        return '关于商品问题，您可以在商品详情页查看更多信息，或直接联系商家咨询。'
    elif '支付' in message:
        return '支付问题请联系客服或在工作时间咨询。'
    elif '收藏' in message:
        return '您可以在商品详情页点击收藏按钮，收藏的商品在个人中心的"我的收藏"中查看。'
    else:
        return '感谢您的咨询，我们会尽快为您处理！'


# 获取商品评论列表
@app.route('/api/comments/list/<int:goods_id>', methods=['GET'])
def get_comments_list(goods_id):
    """获取某商品的所有评论"""
    try:
        comments = Comment.query.filter_by(goods_id=goods_id).order_by(Comment.created_at.desc()).all()
        res = []
        for c in comments:
            user_info = c.user.info if c.user.info else None
            res.append({
                'id': c.id,
                'user_id': c.user_id,
                'username': c.user.nickname,
                'avatar': fix_image_url(user_info.avatar) if user_info else '',
                'content': c.content,
                'time': c.created_at.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取评论失败: {e}")
        return jsonify({'code': 500, 'msg': '获取评论失败'})


# 发表评论
@app.route('/api/comments/add', methods=['POST'])
@jwt_required()
def add_comment():
    """发表评论"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        goods_id = data.get('goods_id')
        content = data.get('content', '').strip()
        if not goods_id or not content:
            return jsonify({'code': 400, 'msg': '商品ID和评论内容不能为空'})
        goods = Goods.query.get(goods_id)
        if not goods:
            return jsonify({'code': 404, 'msg': '商品不存在'})
        new_comment = Comment(user_id=user_id, goods_id=goods_id, content=content)
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '评论成功'})
    except Exception as e:
        db.session.rollback()
        print(f"发表评论失败: {e}")
        return jsonify({'code': 500, 'msg': '发表评论失败'})


# 删除评论
@app.route('/api/comments/delete/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """删除自己的评论"""
    try:
        current_user_id = int(get_jwt_identity())
        comment = Comment.query.get_or_404(comment_id)
        if str(comment.user_id) != str(current_user_id):
            return jsonify({'code': 403, 'msg': '无权限删除他人评论'}), 403
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '评论删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"删除评论失败: {e}")
        return jsonify({'code': 500, 'msg': '删除失败'}), 500


# 从购物车创建订单
@app.route('/api/order/create', methods=['POST'])
@jwt_required()
def create_order():
    """从购物车创建订单，扣减库存，清空购物车，并启动延迟取消任务"""
    cart_snapshot = []
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        if not cart_items:
            return jsonify({'code': 400, 'msg': '购物车为空'}), 400

        cart_snapshot = [(item.goods_id, item.num) for item in cart_items]
        user_info = UserInfo.query.filter_by(user_id=user_id).first()

        # 收货信息：优先使用请求参数，否则从用户资料中取
        receiver_name = data.get('name', '')
        receiver_phone = data.get('phone', '')
        receiver_address = data.get('address', '')

        if not receiver_name and user_info:
            receiver_name = user_info.receiver_name
        if not receiver_phone and user_info:
            receiver_phone = user_info.phone
        if not receiver_address and user_info:
            receiver_address = user_info.address

        # 逐项扣减库存
        for item in cart_items:
            if not deduct_stock_redis(item.goods_id, item.num):
                return jsonify({'code': 400, 'msg': f'商品"{item.goods.name}"库存不足'}), 400

        total_price = sum([item.goods.price * item.num for item in cart_items])
        order_no = f"ORD{int(time.time())}{random.randint(1000, 9999)}"  # 订单号：时间戳+随机数

        new_order = Order(
            order_no=order_no,
            user_id=user_id,
            total_price=total_price,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            receiver_address=receiver_address
        )
        db.session.add(new_order)
        db.session.flush()  # 获取new_order.id

        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                goods_id=item.goods_id,
                goods_name=item.goods.name,
                goods_image=fix_image_url(item.goods.images.split(',')[0]) if item.goods.images else '',
                price=item.goods.price,
                num=item.num
            )
            db.session.add(order_item)

        Cart.query.filter_by(user_id=user_id).delete()  # 清空购物车
        db.session.commit()

        # 延迟5秒执行超时取消任务（模拟支付超时）
        cancel_expired_order_task.apply_async(args=[new_order.id], countdown=5)

        return jsonify({'code': 200, 'msg': '订单创建成功', 'order_no': order_no, 'order_id': new_order.id}), 200
    except Exception as e:
        # 异常时回滚Redis库存
        for goods_id, num in cart_snapshot:
            redis_client.incrby(f"goods_stock:{goods_id}", num)
        db.session.rollback()
        print(f"创建订单错误: {e}")
        return jsonify({'code': 500, 'msg': '创建订单失败'}), 500


# 取消订单
@app.route('/api/order/cancel/<string:order_no>', methods=['POST'])
@jwt_required()
def cancel_order(order_no):
    """用户取消待支付订单，恢复库存并退回购物车"""
    try:
        user_id = int(get_jwt_identity())
        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'}), 404
        if order.status != 'pending_pay':
            return jsonify({'code': 400, 'msg': '只能取消待支付的订单'}), 400

        order.status = 'cancelled'
        # 恢复库存（加分布式锁防止并发问题）
        for item in order.items:
            with distributed_lock(f"goods_{item.goods_id}", timeout=5):
                goods = Goods.query.get(item.goods_id)
                if goods:
                    goods.stock += item.num
                    redis_client.incrby(f"goods_stock:{item.goods_id}", item.num)
        # 恢复购物车
        for item in order.items:
            existing_cart = Cart.query.filter_by(user_id=user_id, goods_id=item.goods_id).first()
            if existing_cart:
                existing_cart.num += item.num
            else:
                new_cart = Cart(user_id=user_id, goods_id=item.goods_id, num=item.num)
                db.session.add(new_cart)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '订单已取消，商品已返回购物车'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"取消订单错误: {e}")
        return jsonify({'code': 500, 'msg': '取消订单失败，请稍后重试'}), 500


# 删除订单
@app.route('/api/order/delete/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id):
    """仅限用户且订单为待支付或已取消时，会恢复库存和购物车"""
    try:
        user_id = int(get_jwt_identity())
        user = get_jwt()
        order = Order.query.get_or_404(order_id)

        # 待支付或已取消的订单需要恢复库存和购物车
        if order.status in ('pending_pay', 'cancelled'):
            for item in order.items:
                with distributed_lock(f"goods_{item.goods_id}", timeout=5):
                    goods = Goods.query.get(item.goods_id)
                    if goods:
                        goods.stock += item.num
                        redis_client.incrby(f"goods_stock:{item.goods_id}", item.num)
            for item in order.items:
                existing_cart = Cart.query.filter_by(user_id=order.user_id, goods_id=item.goods_id).first()
                if existing_cart:
                    existing_cart.num += item.num
                else:
                    new_cart = Cart(user_id=order.user_id, goods_id=item.goods_id, num=item.num)
                    db.session.add(new_cart)

        db.session.delete(order)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '订单删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"删除订单错误: {e}")
        return jsonify({'code': 500, 'msg': '删除失败'}), 500


# 确认支付
@app.route('/api/order/confirm/<string:order_no>', methods=['POST'])
@jwt_required()
def confirm_pay(order_no):
    """用户模拟支付：将订单状态从待支付改为待发货"""
    try:
        user_id = int(get_jwt_identity())
        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'}), 404
        if str(order.user_id) != str(user_id):
            return jsonify({'code': 403, 'msg': '无权操作'}), 403
        if order.status != 'pending_pay':
            return jsonify({'code': 400, 'msg': '订单状态错误'}), 400
        order.status = 'pending_ship'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '支付成功，等待商家发货'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"确认支付错误: {e}")
        return jsonify({'code': 500, 'msg': '支付失败'}), 500


# 公开支付确认（无需登录）
@app.route('/api/order/confirm-public/<string:order_no>', methods=['POST'])
def confirm_pay_public(order_no):
    """公开支付确认（无需登录，用于外部支付回调）"""
    try:
        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'}), 404
        if order.status == 'cancelled':
            return jsonify({'code': 400, 'msg': '订单已超时取消，请重新下单'}), 400
        if order.status != 'pending_pay':
            return jsonify({'code': 400, 'msg': f'订单状态错误，当前状态：{order.status}'}), 400
        order.status = 'pending_ship'
        db.session.commit()
        print(f"✅ 订单 {order_no} 支付成功，状态已更新为: {order.status}")
        return jsonify({'code': 200, 'msg': ' 支付成功！等待商家发货'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"公开支付错误: {e}")
        return jsonify({'code': 500, 'msg': '支付失败，请重试'}), 500


@app.route('/api/order/list', methods=['GET'])
@jwt_required()
def get_order_list():
    """获取订单列表"""
    try:
        user_id = int(get_jwt_identity())
        user = get_jwt()
        status = request.args.get('status', '')

        if user['role'] == 'merchant':
            # 商家只能看到包含自己商品的订单
            merchant_id = user['id']
            order_items = OrderItem.query.join(Goods).filter(Goods.merchant_id == merchant_id).all()
            order_ids = list(set([item.order_id for item in order_items]))
            query = Order.query.filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc())
        else:
            query = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc())

        if status:
            if status == 'refund':
                query = query.filter(Order.status.in_(['refund', 'refunded']))
            else:
                query = query.filter_by(status=status)

        orders = query.all()
        res = []
        for order in orders:
            items = []
            merchant_total = 0.0
            for item in order.items:
                if user['role'] == 'merchant':
                    # 只展示自己的商品
                    goods = Goods.query.get(item.goods_id)
                    if goods and goods.merchant_id == user['id']:
                        item_data = {
                            'id': item.id,
                            'goods_id': item.goods_id,
                            'name': item.goods_name,
                            'image': fix_image_url(item.goods_image),
                            'price': float(item.price),
                            'num': item.num
                        }
                        items.append(item_data)
                        merchant_total += item_data['price'] * item_data['num']
                else:
                    items.append({
                        'id': item.id,
                        'goods_id': item.goods_id,
                        'name': item.goods_name,
                        'image': fix_image_url(item.goods_image),
                        'price': float(item.price),
                        'num': item.num
                    })
            res.append({
                'id': order.id,
                'order_no': order.order_no,
                'total_price': merchant_total if user['role'] == 'merchant' else float(order.total_price),
                'status': order.status,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'items': items,
                'receiver_name': order.receiver_name,
                'receiver_phone': order.receiver_phone,
                'receiver_address': order.receiver_address
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取订单列表错误: {e}")
        return jsonify({'code': 500, 'msg': '获取订单失败'})


# 确认收货
@app.route('/api/order/receive/<int:order_id>', methods=['POST'])
@jwt_required()
def receive_order(order_id):
    """用户确认收货"""
    try:
        user_id = int(get_jwt_identity())
        order = Order.query.get_or_404(order_id)
        if str(order.user_id) != str(user_id):
            return jsonify({'code': 403, 'msg': '无权操作'})
        if order.status != 'pending_receive':
            return jsonify({'code': 400, 'msg': '订单状态错误'})
        order.status = 'completed'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '确认收货成功'})
    except Exception as e:
        db.session.rollback()
        print(f"确认收货错误: {e}")
        return jsonify({'code': 500, 'msg': '确认收货失败'})


# 商家发货
@app.route('/api/order/ship/<int:order_id>', methods=['POST'])
@jwt_required()
def ship_order(order_id):
    """商家发货"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'}), 403
        order = Order.query.get_or_404(order_id)
        if order.status != 'pending_ship':
            return jsonify({'code': 400, 'msg': '订单状态错误，无法发货'}), 400

        # 校验订单中是否包含该商家的商品
        has_merchant_goods = False
        for item in order.items:
            goods = Goods.query.get(item.goods_id)
            if goods and goods.merchant_id == user['id']:
                has_merchant_goods = True
                break
        if not has_merchant_goods:
            return jsonify({'code': 403, 'msg': '无权操作非本店订单'}), 403

        order.status = 'pending_receive'
        db.session.commit()
        notify_shipment.delay(order_id)  # 异步发送发货通知
        return jsonify({'code': 200, 'msg': '发货成功，等待用户确认收货'})
    except Exception as e:
        db.session.rollback()
        print(f"发货错误: {e}")
        return jsonify({'code': 500, 'msg': '发货失败'})


# 公开查询订单
@app.route('/api/order/public/<string:order_no>', methods=['GET'])
def get_order_public(order_no):
    """公开查询订单信息"""
    try:
        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'}), 404
        return jsonify({
            'code': 200,
            'data': {
                'order_no': order.order_no,
                'total_price': float(order.total_price),
                'status': order.status
            }
        }), 200
    except Exception as e:
        print(f"查询订单错误: {e}")
        return jsonify({'code': 500, 'msg': '查询订单失败'})

#申请售后
@app.route('/api/order/return/apply', methods=['POST'])
@jwt_required()
def apply_return():
    """退款/退货/换货"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        order_id = data.get('order_id')
        return_type = data.get('type')
        reason = data.get('reason', '').strip()

        if not all([order_id, return_type]):
            return jsonify({'code': 400, 'msg': '订单ID和售后类型不能为空'}), 400
        if not reason:
            return jsonify({'code': 400, 'msg': '请填写售后原因'}), 400
        valid_types = ['refund', 'return', 'exchange']
        if return_type not in valid_types:
            return jsonify({'code': 400, 'msg': '售后类型不合法'}), 400

        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在或无权限操作'}), 404
        if order.status not in ('completed', 'pending_receive'):
            return jsonify({'code': 400, 'msg': '仅已完成或待收货订单可申请售后'}), 400

        # 防止重复申请
        exist_return = ReturnRequest.query.filter_by(order_id=order_id, user_id=user_id).first()
        if exist_return:
            return jsonify({'code': 400, 'msg': '该订单已申请售后，请勿重复申请'}), 400

        if not order.items:
            return jsonify({'code': 400, 'msg': '订单商品不存在'}), 400
        order_item = order.items[0]
        goods = Goods.query.get(order_item.goods_id)
        if not goods:
            return jsonify({'code': 400, 'msg': '商品不存在'}), 400

        return_req = ReturnRequest(
            order_id=order_id,
            user_id=user_id,
            merchant_id=goods.merchant_id,
            goods_id=order_item.goods_id,
            type=return_type,
            reason=reason,
            status='pending'
        )
        order.status = 'refund'  # 订单状态变更为退款中
        db.session.add(return_req)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '售后申请提交成功，等待商家审核', 'data': {'return_id': return_req.id}})
    except Exception as e:
        db.session.rollback()
        print(f"售后申请接口异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '售后申请失败，服务器异常'}), 500


# ----- 9.10.12 获取售后列表 -----
@app.route('/api/order/return/list', methods=['GET'])
@jwt_required()
def get_return_list():
    """获取售后申请列表（用户或商家）"""
    try:
        user_id = int(get_jwt_identity())
        user = get_jwt()
        status = request.args.get('status', '')

        if user['role'] == 'merchant':
            returns = ReturnRequest.query.filter_by(merchant_id=user['id']).order_by(
                ReturnRequest.created_at.desc()).all()
        else:
            returns = ReturnRequest.query.filter_by(user_id=user_id).order_by(ReturnRequest.created_at.desc()).all()

        if status:
            returns = [r for r in returns if r.status == status]

        res = []
        for ret in returns:
            res.append({
                'id': ret.id,
                'order_id': ret.order_id,
                'order_no': ret.order.order_no,
                'goods_name': ret.goods.name,
                'goods_image': fix_image_url(ret.goods.images.split(',')[0]) if ret.goods.images else '',
                'type': ret.type,
                'reason': ret.reason,
                'status': ret.status,
                'created_at': ret.created_at.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"查询售后列表异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '获取售后列表失败'})


# ----- 9.10.13 商家审核售后 -----
@app.route('/api/order/return/audit', methods=['POST'])
@jwt_required()
def audit_return():
    """商家审核售后申请（同意/拒绝）"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可审核售后'}), 403

        data = request.get_json()
        return_id = data.get('return_id')
        audit_status = data.get('status')

        if not all([return_id, audit_status]):
            return jsonify({'code': 400, 'msg': '审核参数不能为空'}), 400

        return_req = ReturnRequest.query.get(return_id)
        if not return_req or return_req.merchant_id != user['id']:
            return jsonify({'code': 404, 'msg': '售后记录不存在或无权限操作'}), 404
        if return_req.status != 'pending':
            return jsonify({'code': 400, 'msg': '该售后已处理，请勿重复操作'}), 400

        return_req.status = audit_status
        order = return_req.order
        if audit_status == 'rejected':
            order.status = 'completed'  # 拒绝后恢复为已完成
        elif audit_status in ['approved', 'refunded']:
            order.status = 'refunded'  # 同意退款
        db.session.commit()
        return jsonify({'code': 200, 'msg': '售后审核操作成功'})
    except Exception as e:
        db.session.rollback()
        print(f"售后审核异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '审核失败，服务器异常'}), 500


# 商家获取售后列表
@app.route('/api/order/return/merchant', methods=['GET'])
@jwt_required()
def get_merchant_returns():
    """商家获取针对自己店铺的售后申请列表"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可访问'}), 403
        returns = ReturnRequest.query.filter_by(merchant_id=user['id']).order_by(ReturnRequest.created_at.desc()).all()
        res = []
        for ret in returns:
            user_obj = User.query.get(ret.user_id)
            res.append({
                'id': ret.id,
                'order_id': ret.order_id,
                'order_no': ret.order.order_no,
                'goods_name': ret.goods.name,
                'goods_image': fix_image_url(ret.goods.images.split(',')[0]) if ret.goods.images else '',
                'type': ret.type,
                'reason': ret.reason,
                'status': ret.status,
                'user_nickname': user_obj.nickname if user_obj else '未知用户',
                'total_price': float(ret.order.total_price) if ret.order else 0,
                'created_at': ret.created_at.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取商家售后列表异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '获取售后列表失败'})


#  用户获取售后列表
@app.route('/api/order/return/user', methods=['GET'])
@jwt_required()
def get_user_returns():
    """用户获取自己的售后申请列表"""
    try:
        user_id = int(get_jwt_identity())
        returns = ReturnRequest.query.filter_by(user_id=user_id).order_by(ReturnRequest.created_at.desc()).all()
        res = []
        for ret in returns:
            res.append({
                'id': ret.id,
                'order_id': ret.order_id,
                'order_no': ret.order.order_no,
                'goods_name': ret.goods.name,
                'goods_image': fix_image_url(ret.goods.images.split(',')[0]) if ret.goods.images else '',
                'type': ret.type,
                'reason': ret.reason,
                'status': ret.status,
                'created_at': ret.created_at.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取用户售后列表异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '获取售后列表失败'})


# 商家同意售后
@app.route('/api/order/return/approve/<int:return_id>', methods=['POST'])
@jwt_required()
def approve_return(return_id):
    """商家同意售后申请（简化版，实际已包含在audit中，保留兼容）"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'}), 403
        return_req = ReturnRequest.query.get(return_id)
        if not return_req or return_req.merchant_id != user['id']:
            return jsonify({'code': 404, 'msg': '售后记录不存在或无权限'}), 404
        if return_req.status != 'pending':
            return jsonify({'code': 400, 'msg': '该售后已处理'}), 400
        return_req.status = 'approved'
        return_req.order.status = 'refund'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已同意售后申请'})
    except Exception as e:
        db.session.rollback()
        print(f"同意售后异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


# 商家拒绝售后
@app.route('/api/order/return/reject/<int:return_id>', methods=['POST'])
@jwt_required()
def reject_return(return_id):
    """商家拒绝售后申请"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'}), 403
        return_req = ReturnRequest.query.get(return_id)
        if not return_req or return_req.merchant_id != user['id']:
            return jsonify({'code': 404, 'msg': '售后记录不存在或无权限'}), 404
        if return_req.status != 'pending':
            return jsonify({'code': 400, 'msg': '该售后已处理'}), 400
        return_req.status = 'rejected'
        return_req.order.status = 'completed'  # 拒绝后恢复为已完成
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已拒绝售后申请'})
    except Exception as e:
        db.session.rollback()
        print(f"拒绝售后异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


# 商家确认退款
@app.route('/api/order/return/refund/<int:return_id>', methods=['POST'])
@jwt_required()
def complete_refund(return_id):
    """售后状态从approved变为refunded"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'}), 403
        return_req = ReturnRequest.query.get(return_id)
        if not return_req or return_req.merchant_id != user['id']:
            return jsonify({'code': 404, 'msg': '售后记录不存在或无权限'}), 404
        if return_req.status != 'approved':
            return jsonify({'code': 400, 'msg': '仅已同意的售后可确认退款'}), 400
        return_req.status = 'refunded'
        return_req.order.status = 'refunded'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '退款已完成'})
    except Exception as e:
        db.session.rollback()
        print(f"确认退款异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500

# 获取用户信息
@app.route('/api/user/info', methods=['GET'])
@jwt_required()
def user_info():
    """获取当前登录用户的详细信息"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'})
        info = user.info
        if not info:
            info = UserInfo(user_id=user.id)
            db.session.add(info)
            db.session.commit()

        # 构造结构化地址（省/市/区/详细地址）
        address_struct = {
            'name': info.receiver_name,
            'phone': info.phone,
            'province': '', 'city': '', 'district': '', 'detail': info.address
        }
        # 简单解析地址字符串
        address_parts = info.address.split('省')
        if len(address_parts) > 1:
            address_struct['province'] = address_parts[0] + '省'
            remaining = address_parts[1]
            city_parts = remaining.split('市')
            if len(city_parts) > 1:
                address_struct['city'] = city_parts[0] + '市'
                remaining = city_parts[1]
                district_parts = remaining.split('区')
                if len(district_parts) > 1:
                    address_struct['district'] = district_parts[0] + '区'
                    address_struct['detail'] = district_parts[1]
                else:
                    address_struct['detail'] = remaining
            else:
                address_struct['detail'] = remaining

        return jsonify({
            'code': 200,
            'data': {
                'nickname': user.nickname,
                'avatar': fix_image_url(info.avatar),
                'birthday': info.birthday,
                'gender': info.gender,
                'phone': info.phone,
                'receiverName': info.receiver_name,
                'address': info.address,
                'address_struct': address_struct
            }
        })
    except Exception as e:
        print(f"获取用户信息错误: {e}")
        return jsonify({'code': 500, 'msg': f'服务器错误: {str(e)}'})


# 更新用户资料
@app.route('/api/user/update', methods=['POST'])
@jwt_required()
def update_info():
    """生日、性别、收货人、电话、地址"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        info = UserInfo.query.filter_by(user_id=user_id).first()
        if not info:
            return jsonify({'code': 404, 'msg': '用户信息不存在'})
        info.birthday = data.get('birthday', '')
        info.gender = data.get('gender', 'secret')
        info.receiver_name = data.get('receiverName', data.get('name', ''))
        info.phone = data.get('phone', '')
        # 支持结构化地址或纯文本地址
        if 'address_struct' in data:
            addr = data['address_struct']
            info.address = f"{addr.get('province', '')}{addr.get('city', '')}{addr.get('district', '')}{addr.get('detail', '')}"
        elif 'address' in data and data['address']:
            info.address = data['address']
        db.session.commit()
        return jsonify({'code': 200, 'msg': '保存成功'})
    except Exception as e:
        print(f"更新信息错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '保存失败'})

@app.route('/api/user/update-nickname', methods=['POST'])
@jwt_required()
def update_nickname():
    """修改用户昵称"""
    try:
        user_id = int(get_jwt_identity())
        nickname = request.get_json().get('nickname')
        if not nickname:
            return jsonify({'code': 400, 'msg': '昵称不能为空'})
        user = User.query.get(user_id)
        user.nickname = nickname
        db.session.commit()
        return jsonify({'code': 200, 'msg': '修改成功'})
    except Exception as e:
        print(f"修改昵称错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '修改失败'})


# 更新头像
@app.route('/api/user/update-avatar', methods=['POST'])
@jwt_required()
def update_avatar():
    """更新用户头像URL"""
    try:
        user_id = int(get_jwt_identity())
        avatar = request.get_json().get('avatar')
        info = UserInfo.query.filter_by(user_id=user_id).first()
        if not info:
            return jsonify({'code': 404, 'msg': '用户信息不存在'})
        info.avatar = fix_image_url(avatar)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '头像更新成功'})
    except Exception as e:
        print(f"更新头像错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '头像更新失败'})


#  修改密码
@app.route('/api/user/update-password', methods=['POST'])
@jwt_required()
def update_password():
    """需验证原密码"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        old_pwd = data.get('oldPassword')
        new_pwd = data.get('newPassword')
        user = User.query.get(user_id)
        if decrypt_password(user.password) != old_pwd:
            return jsonify({'code': 400, 'msg': '原密码错误'})
        user.password = encrypt_password(new_pwd)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '修改成功，请重新登录'})
    except Exception as e:
        print(f"修改密码错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '修改失败'})


@app.route('/api/merchant/apply', methods=['POST'])
@jwt_required()
def merchant_apply():
    """商家提交入驻申请"""
    try:
        user_claims = get_jwt()
        user_id = user_claims['id']
        user = User.query.get(user_id)

        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404

        if user.role != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家角色可申请入驻'}), 403

        if user.apply_status == 'pending':
            return jsonify({'code': 400, 'msg': '您的入驻申请正在审核中，请耐心等待'}), 400

        if user.apply_status == 'approved':
            return jsonify({'code': 400, 'msg': '您已通过入驻审核，无需重复申请'}), 400

        user.apply_status = 'pending'
        user.apply_time = datetime.now()
        db.session.commit()

        return jsonify({'code': 200, 'msg': '入驻申请已提交，请等待管理员审核'})
    except Exception as e:
        db.session.rollback()
        print(f"提交入驻申请失败: {e}")
        return jsonify({'code': 500, 'msg': '提交申请失败，请稍后重试'}), 500


# 获取入驻申请状态
@app.route('/api/merchant/apply-status', methods=['GET'])
@jwt_required()
def get_merchant_apply_status():
    """获取当前商家的入驻申请状态"""
    try:
        user_claims = get_jwt()
        user_id = user_claims['id']
        user = User.query.get(user_id)

        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404

        return jsonify({
            'code': 200,
            'data': {
                'apply_status': user.apply_status or 'none',
                'apply_time': user.apply_time.strftime('%Y-%m-%d %H:%M:%S') if user.apply_time else None
            }
        })
    except Exception as e:
        print(f"获取入驻状态失败: {e}")
        return jsonify({'code': 500, 'msg': '获取状态失败'}), 500

# 用户管理
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    """管理员获取所有用户列表"""
    try:
        users = User.query.all()
        data = []
        for user in users:
            data.append({
                'id': user.id,
                'nickname': user.nickname,
                'username': user.username,
                'role': user.role,
                'is_banned': user.is_banned,
                'apply_status': user.apply_status or 'none',
                'apply_time': user.apply_time.strftime('%Y-%m-%d %H:%M') if user.apply_time else '',
                'phone': user.info.phone if user.info else '',
                'avatar': fix_image_url(user.info.avatar) if user.info else '',
                'receiver_name': user.info.receiver_name if user.info else '',
                'address': user.info.address if user.info else ''
            })
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        print(f"管理员获取用户列表错误: {e}")
        return jsonify({'code': 500, 'msg': '获取用户列表失败'}), 500


@app.route('/api/admin/user/delete/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_user(id):
    """管理员删除用户（级联删除相关数据）"""
    try:
        user = User.query.get_or_404(id)
        UserInfo.query.filter_by(user_id=id).delete()
        Cart.query.filter_by(user_id=id).delete()
        History.query.filter_by(user_id=id).delete()
        Comment.query.filter_by(user_id=id).delete()
        ReturnRequest.query.filter_by(user_id=id).delete()
        NotificationLog.query.filter_by(user_id=id).delete()
        Order.query.filter_by(user_id=id).delete()
        db.session.delete(user)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员删除用户错误: {e}")
        return jsonify({'code': 500, 'msg': '删除用户失败'}), 500


@app.route('/api/admin/user/update/<int:id>', methods=['POST'])
@admin_required
def admin_update_user(id):
    """管理员修改用户信息"""
    try:
        user = User.query.get_or_404(id)
        data = request.get_json()

        # 处理 User 表字段
        if 'nickname' in data and data['nickname'].strip():
            user.nickname = data['nickname'].strip()
        if 'role' in data:
            allowed_roles = ['user', 'merchant']
            if data['role'] not in allowed_roles:
                return jsonify({'code': 400, 'msg': '无效角色，仅支持普通用户和商家'}), 400
            user.role = data['role']

        # 处理 UserInfo 表字段
        user_info = user.info
        if not user_info:
            # 如果用户没有 UserInfo 记录，自动创建
            user_info = UserInfo(user_id=user.id)
            db.session.add(user_info)

        if 'avatar' in data:
            user_info.avatar = fix_image_url(data['avatar'].strip())
        if 'phone' in data:
            user_info.phone = data['phone'].strip()
        if 'address' in data:
            user_info.address = data['address'].strip()

        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户信息修改成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员修改用户错误: {e}")
        return jsonify({'code': 500, 'msg': '修改用户信息失败'}), 500


@app.route('/api/admin/merchant/approve/<int:user_id>', methods=['POST'])
@admin_required
def admin_approve_merchant(user_id):
    """管理员通过商家入驻申请"""
    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404

        if user.role != 'merchant':
            return jsonify({'code': 400, 'msg': '该用户不是商家角色'}), 400

        if user.apply_status != 'pending':
            return jsonify({'code': 400, 'msg': '该商家未提交申请或已审核'}), 400

        user.apply_status = 'approved'
        db.session.commit()

        return jsonify({'code': 200, 'msg': '已通过该商家的入驻申请'})
    except Exception as e:
        db.session.rollback()
        print(f"通过入驻申请失败: {e}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


@app.route('/api/admin/merchant/reject/<int:user_id>', methods=['POST'])
@admin_required
def admin_reject_merchant(user_id):
    """管理员拒绝商家入驻申请"""
    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404

        if user.role != 'merchant':
            return jsonify({'code': 400, 'msg': '该用户不是商家角色'}), 400

        if user.apply_status != 'pending':
            return jsonify({'code': 400, 'msg': '该商家未提交申请或已审核'}), 400

        user.apply_status = 'rejected'
        db.session.commit()

        return jsonify({'code': 200, 'msg': '已拒绝该商家的入驻申请'})
    except Exception as e:
        db.session.rollback()
        print(f"拒绝入驻申请失败: {e}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


@app.route('/api/admin/user/detail/<int:id>', methods=['GET'])
@admin_required
def admin_get_user_detail(id):
    """管理员获取单个用户的详细信息"""
    try:
        user = User.query.get_or_404(id)
        user_info = user.info

        # 统计用户相关数据
        order_count = Order.query.filter_by(user_id=id).count()
        cart_count = Cart.query.filter_by(user_id=id).count()
        collect_count = Collect.query.filter_by(user_id=id).count()
        comment_count = Comment.query.filter_by(user_id=id).count()

        data = {
            'id': user.id,
            'nickname': user.nickname,
            'username': user.username,
            'role': user.role,
            'is_banned': user.is_banned,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'created_at') else '未知',
            'info': {
                'avatar': fix_image_url(user_info.avatar) if user_info else '',
                'birthday': user_info.birthday if user_info else '',
                'gender': user_info.gender if user_info else '',
                'email': user_info.email if user_info else '',
                'phone': user_info.phone if user_info else '',
                'receiver_name': user_info.receiver_name if user_info else '',
                'address': user_info.address if user_info else ''
            },
            'stats': {
                'order_count': order_count,
                'cart_count': cart_count,
                'collect_count': collect_count,
                'comment_count': comment_count
            }
        }
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        print(f"管理员获取用户详情错误: {e}")
        return jsonify({'code': 500, 'msg': '获取用户详情失败'}), 500


@app.route('/api/admin/user/ban/<int:id>', methods=['POST'])
@admin_required
def admin_ban_user(id):
    """管理员封禁用户"""
    try:
        user = User.query.get_or_404(id)

        user.is_banned = True
        db.session.commit()

        return jsonify({'code': 200, 'msg': '用户封禁成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员封禁用户错误: {e}")
        return jsonify({'code': 500, 'msg': '封禁用户失败'}), 500


@app.route('/api/admin/user/unban/<int:id>', methods=['POST'])
@admin_required
def admin_unban_user(id):
    """管理员解封用户"""
    try:
        user = User.query.get_or_404(id)
        user.is_banned = False
        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户解封成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员解封用户错误: {e}")
        return jsonify({'code': 500, 'msg': '解封用户失败'}), 500


#  管理员商品管理
@app.route('/api/admin/goods', methods=['GET'])
@admin_required
def admin_get_goods():
    """管理员获取所有商品列表"""
    try:
        goods = Goods.query.order_by(Goods.created_at.desc()).all()
        data = []
        for g in goods:
            data.append({
                'id': g.id,
                'name': g.name,
                'price': float(g.price),
                'stock': g.stock,
                'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
                'category': g.category,
                'status': g.status,
                'merchant_name': g.merchant_name,
                'brand': g.brand,
                'ip': g.ip,
                'charactername': g.charactername,
                'description': g.description
            })
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        print(f"管理员获取商品列表错误: {e}")
        return jsonify({'code': 500, 'msg': '获取商品列表失败'}), 500

#管理员删除商品
@app.route('/api/admin/goods/delete/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_goods(id):
    """并清除ES索引和缓存"""
    try:
        goods = Goods.query.get_or_404(id)
        # 级联删除关联数据
        Cart.query.filter_by(goods_id=id).delete()
        History.query.filter_by(goods_id=id).delete()
        Comment.query.filter_by(goods_id=id).delete()
        ReturnRequest.query.filter_by(goods_id=id).delete()
        NotificationLog.query.filter_by(goods_id=id).delete()
        OrderItem.query.filter_by(goods_id=id).delete()
        delete_goods_from_es(id)
        redis_client.delete(f"goods_stock:{id}")
        redis_client.delete(f'goods_detail:{id}')
        redis_client.delete('goods_list:default')
        db.session.delete(goods)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '商品删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员删除商品错误: {e}")
        return jsonify({'code': 500, 'msg': '删除商品失败'}), 500


@app.route('/api/admin/goods/update/<int:id>', methods=['POST'])
@admin_required
def admin_update_goods(id):
    """管理员修改商品信息"""
    try:
        goods = Goods.query.get_or_404(id)
        data = request.get_json()
        goods.name = data.get('name', goods.name)
        goods.price = data.get('price', goods.price)
        goods.stock = data.get('stock', goods.stock)
        goods.category = data.get('category', goods.category)
        goods.status = data.get('status', goods.status)
        goods.brand = data.get('brand', goods.brand)
        goods.ip = data.get('ip', goods.ip)
        goods.charactername = data.get('charactername', goods.charactername)
        goods.description = data.get('description', goods.description)
        # 同步Redis缓存和ES索引
        redis_client.set(f"goods_stock:{id}", goods.stock)
        redis_client.delete(f'goods_detail:{id}')
        redis_client.delete('goods_list:default')
        sync_goods_to_es(id)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '商品修改成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员修改商品错误: {e}")
        return jsonify({'code': 500, 'msg': '修改商品失败'}), 500


@app.route('/api/admin/goods/status/<int:id>', methods=['POST'])
@admin_required
def admin_toggle_goods_status(id):
    """管理员切换商品 上架/下架 状态"""
    try:
        goods = Goods.query.get_or_404(id)
        old_status = goods.status
        stock = goods.stock
        if old_status == "下架":
            if stock <= 0:
                goods.status = "缺货"
            else:
                goods.status = "现货"
        else:
            goods.status = "下架"
        db.session.commit()
        # 清理 Redis 缓存
        redis_client.delete('goods_list:default')
        redis_client.delete(f'goods_detail:{id}')
        # 同步数据到 Elasticsearch
        sync_goods_to_es(id)

        # 下架操作触发异步通知告知购物车用户
        if goods.status == "下架":
            notify_off_shelf.delay(id)
        return jsonify({'code': 200, 'msg': '商品状态切换成功'})
    except Exception as e:
        db.session.rollback()
        print(f"商品上下架操作失败: {e}")
        return jsonify({'code': 500, 'msg': '操作失败，服务器异常'}), 500


# 管理员订单管理
@app.route('/api/admin/orders', methods=['GET'])
@admin_required
def admin_get_orders():
    """可按状态筛选"""
    try:
        status = request.args.get('status', '')
        query = Order.query.order_by(Order.created_at.desc())
        if status:
            query = query.filter_by(status=status)
        orders = query.all()
        data = []
        for order in orders:
            user = User.query.get(order.user_id)
            user_nickname = user.nickname if user else '未知用户'
            data.append({
                'id': order.id,
                'order_no': order.order_no,
                'user_id': order.user_id,
                'user_nickname': user_nickname,
                'receiver_name': order.receiver_name,
                'receiver_phone': order.receiver_phone,
                'receiver_address': order.receiver_address,
                'total_price': float(order.total_price),
                'status': order.status,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        print(f"管理员获取订单列表错误: {e}")
        return jsonify({'code': 500, 'msg': '获取订单列表失败'}), 500


@app.route('/api/admin/order/update/<int:id>', methods=['POST'])
@admin_required
def admin_update_order(id):
    """管理员修改订单信息（收货人、总价、状态等）"""
    try:
        order = Order.query.get_or_404(id)
        data = request.get_json()
        order.receiver_name = data.get('receiver_name', order.receiver_name)
        order.receiver_phone = data.get('receiver_phone', order.receiver_phone)
        order.receiver_address = data.get('receiver_address', order.receiver_address)
        order.total_price = data.get('total_price', order.total_price)
        order.status = data.get('status', order.status)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '订单修改成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员修改订单错误: {e}")
        return jsonify({'code': 500, 'msg': '修改订单失败'}), 500


@app.route('/api/admin/order/delete/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_order(id):
    """管理员删除订单（同时删除关联售后）"""
    try:
        order = Order.query.get_or_404(id)
        ReturnRequest.query.filter_by(order_id=id).delete()
        db.session.delete(order)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '订单删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员删除订单错误: {e}")
        return jsonify({'code': 500, 'msg': '删除订单失败'}), 500


# 获取通知列表
@app.route('/api/user/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """获取当前用户的所有通知"""
    try:
        user_id = int(get_jwt_identity())
        notifications = NotificationLog.query.filter_by(user_id=user_id).order_by(NotificationLog.sent_at.desc()).all()
        res = []
        for n in notifications:
            res.append({
                'id': n.id,
                'type': n.type,
                'content': n.content,
                'status': n.status,
                'goods_id': n.goods_id,
                'order_id': n.order_id,
                'goods_name': n.goods.name if n.goods else '',
                'goods_image': fix_image_url(n.goods.images.split(',')[0]) if n.goods and n.goods.images else '',
                'sent_at': n.sent_at.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取通知错误: {e}")
        return jsonify({'code': 500, 'msg': '获取通知失败'})

@app.route('/api/user/notifications/read/<int:notification_id>', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """将通知标记为已读"""
    try:
        user_id = int(get_jwt_identity())
        notification = NotificationLog.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            return jsonify({'code': 404, 'msg': '通知不存在'})
        notification.status = 'read'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已标记为已读'})
    except Exception as e:
        print(f"标记通知错误: {e}")
        return jsonify({'code': 500, 'msg': '操作失败'})

@app.route('/api/user/notifications/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """获取未读通知数量"""
    try:
        user_id = int(get_jwt_identity())
        count = NotificationLog.query.filter_by(user_id=user_id, status='sent').count()
        return jsonify({'code': 200, 'data': {'count': count}})
    except Exception as e:
        print(f"获取未读数错误: {e}")
        return jsonify({'code': 500, 'msg': '获取失败'})


# 实时监控数据
@app.route('/api/admin/monitor/realtime', methods=['GET'])
@admin_required
def monitor_realtime():
    """最近60分钟实时数据"""
    try:
        minutes = []
        now = datetime.now()
        for i in range(59, -1, -1):
            t = now - timedelta(minutes=i)
            key = t.strftime('%Y%m%d%H%M')
            total = int(redis_client.get(f'monitor:minute:{key}:total') or 0)
            errors = int(redis_client.get(f'monitor:minute:{key}:error') or 0)
            duration_sum = int(redis_client.get(f'monitor:minute:{key}:duration') or 0)
            avg_dur = int(duration_sum / total) if total > 0 else 0
            minutes.append({
                'time': t.strftime('%H:%M'),
                'total': total,
                'errors': errors,
                'avg_duration': avg_dur
            })

        # 今日汇总
        today_total = sum(m['total'] for m in minutes)
        today_errors = sum(m['errors'] for m in minutes)
        today_avg = int(sum(m['avg_duration'] * m['total'] for m in minutes) / today_total) if today_total > 0 else 0

        return jsonify({
            'code': 200,
            'data': {
                'timeline': minutes,
                'summary': {
                    'total_requests': today_total,
                    'avg_duration': today_avg,
                    'error_rate': round(today_errors / today_total * 100, 2) if today_total > 0 else 0
                }
            }
        })
    except Exception as e:
        print(f"获取实时监控数据错误: {e}")
        return jsonify({'code': 500, 'msg': '获取监控数据失败'}), 500


# 用户活跃度
@app.route('/api/admin/monitor/user-activity', methods=['GET'])
@admin_required
def monitor_user_activity():
    """用户活跃度：今日活跃用户、新注册、每小时活跃趋势"""
    try:
        today_key = datetime.now().strftime('%Y%m%d')
        active_users = redis_client.scard(f'monitor:active_users:{today_key}')
        new_registrations = int(redis_client.get(f'monitor:new_registrations:{today_key}') or 0)

        # 每小时活跃用户趋势
        hourly = []
        now = datetime.now()
        for i in range(23, -1, -1):
            h = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
            hour_key = h.strftime('%Y%m%d%H')
            count = redis_client.scard(f'monitor:active_hour:{hour_key}')
            hourly.append({'hour': h.strftime('%H:00'), 'count': count})

        return jsonify({
            'code': 200,
            'data': {
                'active_users': active_users,
                'new_registrations': new_registrations,
                'hourly_trend': hourly
            }
        })
    except Exception as e:
        print(f"获取用户活跃度错误: {e}")
        return jsonify({'code': 500, 'msg': '获取数据失败'}), 500


#  商品热度排行
@app.route('/api/admin/monitor/product-ranking', methods=['GET'])
@admin_required
def monitor_product_ranking():
    """商品热度排行：销量Top10"""
    try:
        # 销量Top10
        from sqlalchemy import func
        sales = db.session.query(
            Goods.name, func.sum(OrderItem.num).label('count')
        ).join(OrderItem, OrderItem.goods_id == Goods.id
               ).join(Order, Order.id == OrderItem.order_id
                      ).filter(Order.status != 'cancelled'
                               ).group_by(Goods.id, Goods.name
                                          ).order_by(func.sum(OrderItem.num).desc()
                                                     ).limit(10).all()
        by_sales = [{'name': s.name, 'count': int(s.count)} for s in sales]

        return jsonify({
            'code': 200,
            'data': {'by_sales': by_sales}
        })
    except Exception as e:
        print(f"获取商品排行错误: {e}")
        return jsonify({'code': 500, 'msg': '获取数据失败'}), 500


# 订单交易概览
@app.route('/api/admin/monitor/order-overview', methods=['GET'])
@admin_required
def monitor_order_overview():
    """订单交易概览：从MySQL快照读取"""
    try:
        snapshots = OrderStatusSnapshot.query.all()
        if not snapshots:
            # 快照为空时实时计算一次并写入，使用Redis锁防止并发重复刷新
            lock_key = 'monitor:order_status:refresh_lock'
            if redis_client.set(lock_key, '1', nx=True, ex=60):
                try:
                    scheduled_refresh_order_status()
                    snapshots = OrderStatusSnapshot.query.all()
                finally:
                    redis_client.delete(lock_key)
            else:
                # 其他请求正在刷新，等待后读取
                import time
                time.sleep(0.5)
                snapshots = OrderStatusSnapshot.query.all()

        status_dist = [{'name': s.status_name, 'value': s.count} for s in snapshots]
        today_orders = snapshots[0].today_orders if snapshots else 0
        today_revenue = snapshots[0].today_revenue if snapshots else 0.0

        return jsonify({
            'code': 200,
            'data': {
                'today_orders': today_orders,
                'today_revenue': round(today_revenue, 2),
                'status_distribution': status_dist
            }
        })
    except Exception as e:
        print(f"获取订单概览错误: {e}")
        return jsonify({'code': 500, 'msg': '获取数据失败'}), 500


# 搜索关键词排行
@app.route('/api/admin/monitor/search-keywords', methods=['GET'])
@admin_required
def monitor_search_keywords():
    """搜索关键词排行Top10：从MySQL快照读取"""
    try:
        snapshots = SearchKeywordSnapshot.query.order_by(SearchKeywordSnapshot.count.desc()).all()
        if not snapshots:
            # 快照为空时实时计算一次并写入
            scheduled_refresh_search_keywords()
            snapshots = SearchKeywordSnapshot.query.order_by(SearchKeywordSnapshot.count.desc()).all()

        result = [{'keyword': s.keyword, 'count': s.count} for s in snapshots]
        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        print(f"获取搜索关键词错误: {e}")
        return jsonify({'code': 500, 'msg': '获取数据失败'}), 500


# 每分钟取消超时订单
@scheduler.task('interval', id='cancel_expired_orders_task', minutes=1, misfire_grace_time=300)
def scheduled_cancel_expired_orders():
    """每分钟执行一次，取消超时未支付的订单"""
    cancel_expired_orders()


#  每7天刷新搜索关键词快照
@scheduler.task('interval', id='refresh_search_keywords_task', days=7, misfire_grace_time=3600)
def scheduled_refresh_search_keywords():
    """每7天执行一次，聚合Redis中7天的搜索关键词数据并持久化到MySQL"""
    try:
        # 聚合最近7天的搜索关键词
        keyword_totals = {}
        for i in range(7):
            day = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            data = redis_client.zrevrange(f'monitor:search_keywords:{day}', 0, -1, withscores=True)
            for kw, count in data:
                kw_str = kw.decode() if isinstance(kw, bytes) else kw
                keyword_totals[kw_str] = keyword_totals.get(kw_str, 0) + int(count)

        # 取Top10写入MySQL
        top10 = sorted(keyword_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        with app.app_context():
            SearchKeywordSnapshot.query.delete()
            for keyword, count in top10:
                db.session.add(SearchKeywordSnapshot(keyword=keyword, count=count))
            db.session.commit()
        print(" 热门搜索关键词快照已更新（7天周期）")
    except Exception as e:
        print(f"更新搜索关键词快照错误: {e}")


# 每24小时刷新订单状态快照
@scheduler.task('interval', id='refresh_order_status_task', hours=24, misfire_grace_time=3600)
def scheduled_refresh_order_status():
    """每24小时执行一次，统计今日订单状态分布并持久化到MySQL"""
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = Order.query.filter(Order.created_at >= today_start).all()
        today_order_count = len(today_orders)

        paid_statuses = ('pending_ship', 'pending_receive', 'completed')
        today_revenue = sum(float(o.total_price) for o in today_orders if o.status in paid_statuses)

        status_labels = {
            'pending_pay': '待付款', 'pending_ship': '待发货',
            'pending_receive': '待收货', 'completed': '已完成',
            'cancelled': '已取消', 'refund': '退款中', 'refunded': '已退款'
        }
        status_map = {}
        for o in today_orders:
            label = status_labels.get(o.status, o.status)
            status_map[label] = status_map.get(label, 0) + 1

        with app.app_context():
            OrderStatusSnapshot.query.delete()
            for name, count in status_map.items():
                db.session.add(OrderStatusSnapshot(
                    status_name=name, count=count,
                    today_orders=today_order_count,
                    today_revenue=round(today_revenue, 2)
                ))
            db.session.commit()
        print("订单状态分布快照已更新（24小时周期）")
    except Exception as e:
        print(f"更新订单状态分布快照错误: {e}")

# 初始化数据库表与ES索引
with app.app_context():
    db.create_all()
    # 如果ES索引不存在则创建
    if not es_client.indices.exists(index="goods_index"):
        mapping = {
            "mappings": {
                "properties": {
                    "name": {"type": "text"},
                    "price": {"type": "float"},
                    "stock": {"type": "integer"},
                    "image": {"type": "keyword"},
                    "description": {"type": "text"},
                    "category": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "brand": {"type": "keyword"},
                    "ip": {"type": "keyword"},
                    "charactername": {"type": "keyword"},
                    "merchant_name": {"type": "keyword"}
                }
            }
        }
        es_client.indices.create(index="goods_index", body=mapping)

# 避免Flask debug模式重复启动调度器    启动定时任务
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    scheduler.start()


# 前端静态文件路由
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """提供 Vue 前端页面（history 路由模式支持）"""
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist')
    # 如果请求的是静态文件（css, js, img 等），直接返回
    if path and os.path.exists(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, path)
    # 否则返回 index.html，让 Vue Router 处理路由
    return send_from_directory(dist_dir, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

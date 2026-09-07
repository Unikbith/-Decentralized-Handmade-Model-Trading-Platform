"""商品：图片上传、发布、列表、搜索、详情、商家管理与更新"""
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required
from minio.error import S3Error

from ..config import MINIO_BUCKET
from ..extensions import db, es_client, minio_client, redis_client
from ..models import Cart, Collect, Goods, History, User
from ..services import es_service
from ..tasks import (notify_goods_update, notify_off_shelf, notify_price_drop,
                     sync_goods_to_es_async)
from ..utils.decorators import cache
from ..utils.image import fix_image_url

bp = Blueprint('goods', __name__, url_prefix='/api/goods')
# 图片上传为独立蓝图，保持原有 /api/upload/image 路径不变
bp_upload = Blueprint('upload', __name__, url_prefix='/api')


@bp_upload.route('/upload/image', methods=['POST'])
@jwt_required()
def upload_image():
    """上传商品图片到 MinIO，返回图片 URL"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '请选择图片'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '文件名不能为空'})
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    file_name = f"{uuid.uuid4().hex}.{file_ext}"
    try:
        minio_client.put_object(MINIO_BUCKET, file_name, file, length=-1,
                                part_size=10 * 1024 * 1024,
                                content_type=f"image/{file_ext}")
        return jsonify({'code': 200, 'msg': '上传成功', 'url': f"/goods-images/{file_name}"})
    except S3Error as e:
        print(f"MinIO错误: {e}")
        return jsonify({'code': 500, 'msg': '图片上传失败'})


@bp.route('/publish', methods=['POST'])
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
        messages = {
            'none': '请先提交入驻申请，等待管理员审核通过后再发布商品',
            'pending': '您的入驻申请正在审核中，请等待管理员审核通过',
            'rejected': '您的入驻申请已被拒绝，无法发布商品，如有疑问请联系管理员',
        }
        return jsonify({'code': 403, 'msg': messages.get(user_obj.apply_status, '入驻审核未通过')}), 403

    required_fields = ['name', 'price', 'images']
    if not all(data.get(field) for field in required_fields):
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
        merchant_name=user.get('nickname', '商家'),
    )
    try:
        db.session.add(new_goods)
        db.session.commit()
        sync_goods_to_es_async.delay(new_goods.id)
        return jsonify({'code': 200, 'msg': '上架成功', 'goods_id': new_goods.id})
    except Exception as e:
        db.session.rollback()
        print(f"发布商品错误: {e}")
        return jsonify({'code': 500, 'msg': '上架失败'})


@bp.route('/list', methods=['GET'])
@cache(key_prefix='goods_list', expire=600)
def get_goods_list():
    """分页获取商品列表（带缓存，10 分钟过期）"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    pagination = Goods.query.order_by(Goods.created_at.desc()).paginate(page=page, per_page=size)
    res = [serialize_goods_item(g) for g in pagination.items]
    return jsonify({
        'code': 200,
        'data': res,
        'pagination': {
            'total': pagination.total, 'page': page, 'size': size, 'pages': pagination.pages,
        },
    })


@bp.route('/search', methods=['GET'])
def search_goods():
    """基于 ES 的全文搜索商品"""
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

        search_body = {
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["name", "description", "category", "brand", "ip", "charactername"],
                    "type": "best_fields",
                }
            },
            "from": (page - 1) * size,
            "size": size,
        }
        result = es_client.search(index='goods_index', body=search_body)
        res = []
        for hit in result['hits']['hits']:
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
                'merchant_name': source.get('merchant_name', ''),
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"搜索商品错误: {e}")
        return jsonify({'code': 500, 'msg': '搜索失败'})


@bp.route('/options', methods=['GET'])
def get_goods_options():
    """获取商品筛选选项（分类、品牌、IP 列表）"""
    try:
        query = lambda col: db.session.query(col).filter(
            col != None, col != ''
        ).distinct().all()
        categories, brands, ips = query(Goods.category), query(Goods.brand), query(Goods.ip)
        return jsonify({
            'code': 200,
            'data': {
                'categories': [c[0] for c in categories if c[0]],
                'brands': [b[0] for b in brands if b[0]],
                'ips': [i[0] for i in ips if i[0]],
            },
        })
    except Exception as e:
        print(f"获取商品选项错误: {e}")
        return jsonify({'code': 500, 'msg': '获取选项失败'})


@bp.route('/detail/<int:id>', methods=['GET'])
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
            user_id = int(decode_token(token.split(' ')[1])['sub'])
            existing_history = History.query.filter_by(user_id=user_id, goods_id=id).first()
            if existing_history:
                existing_history.browse_time = datetime.now()
            else:
                db.session.add(History(user_id=user_id, goods_id=id))
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
            'created_at': g.created_at.strftime('%Y-%m-%d'),
        },
    })


@bp.route('/merchant', methods=['GET'])
@jwt_required()
def get_merchant_goods():
    """商家获取自己发布的商品列表"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可访问'})
        goods = Goods.query.filter_by(merchant_id=user['id']).order_by(Goods.created_at.desc()).all()
        res = [{
            'id': g.id, 'name': g.name, 'price': float(g.price),
            'image': first_image(g.images), 'status': g.status, 'category': g.category,
        } for g in goods]
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取商家商品错误: {e}")
        return jsonify({'code': 500, 'msg': '获取商品失败'})


@bp.route('/update/<int:id>', methods=['POST'])
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

        # 同步 Redis 库存缓存并清理列表/详情缓存
        if data.get('stock') is not None:
            redis_client.set(f"goods_stock:{id}", data['stock'])
        redis_client.delete('goods_list:default')
        redis_client.delete(f'goods_detail:{id}')
        es_service.sync_goods_to_es(id)

        # 业务变更通知
        if data.get('price') is not None and float(data['price']) < old_price:
            notify_price_drop.delay(id, old_price, float(data['price']))
        if old_status != '下架' and data.get('status') == '下架':
            notify_off_shelf.delay(id)
        if data.get('name') is not None and data['name'] != old_name:
            notify_goods_update.delay(id, old_name, data['name'])

        return jsonify({'code': 200, 'msg': '更新成功'})
    except Exception as e:
        db.session.rollback()
        print(f"更新商品错误: {e}")
        return jsonify({'code': 500, 'msg': '更新失败'})


@bp.route('/delete/<int:id>', methods=['DELETE'])
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

        db.session.delete(goods)
        db.session.commit()

        # 清理缓存并同步 ES
        redis_client.delete(f"goods_stock:{id}")
        redis_client.delete('goods_list:default')
        redis_client.delete(f'goods_detail:{id}')
        es_service.delete_goods_from_es(id)

        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"删除商品错误: {e}")
        return jsonify({'code': 500, 'msg': '删除失败'})


# ==================== 序列化工具 ====================

def first_image(images):
    """取逗号分隔图片列表的首张并转换 URL"""
    return fix_image_url(images.split(',')[0]) if images else ''


def serialize_goods_item(g):
    """商品列表项序列化"""
    return {
        'id': g.id, 'name': g.name, 'price': float(g.price),
        'image': first_image(g.images), 'description': g.description,
        'category': g.category, 'status': g.status, 'brand': g.brand,
        'ip': g.ip, 'charactername': g.charactername, 'merchant_name': g.merchant_name,
    }

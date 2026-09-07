"""商品域：商品、购物车、收藏、浏览历史、评论"""
from ..extensions import db


class Goods(db.Model):
    """商品表"""
    __tablename__ = 'goods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=1)
    images = db.Column(db.Text, nullable=False)  # 逗号分隔的图片 URL
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=True)  # 上架/下架
    brand = db.Column(db.String(50), nullable=True)
    ip = db.Column(db.String(50), nullable=True)  # 所属 IP
    charactername = db.Column(db.String(50), nullable=True)  # 角色名
    merchant_id = db.Column(db.Integer, nullable=False)  # 商家用户 ID
    merchant_name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Cart(db.Model):
    """购物车表"""
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    num = db.Column(db.Integer, default=1, nullable=False)
    goods = db.relationship('Goods', backref='cart_items', lazy='joined')


class Collect(db.Model):
    """用户收藏表"""
    __tablename__ = 'collects'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    goods = db.relationship('Goods', backref='collect_items', lazy='joined')


class History(db.Model):
    """浏览历史表"""
    __tablename__ = 'user_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    browse_time = db.Column(db.DateTime, server_default=db.func.now())
    goods = db.relationship('Goods', backref='history_items', lazy='joined')


class Comment(db.Model):
    """商品评论表"""
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', backref='comments', lazy='joined')

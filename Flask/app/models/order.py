"""订单域：订单主表、订单明细、售后申请"""
from ..extensions import db


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
    status = db.Column(db.String(20), default='pending_pay')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    items = db.relationship('OrderItem', backref='order', lazy='joined', cascade='all, delete-orphan')


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

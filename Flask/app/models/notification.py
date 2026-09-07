"""用户通知记录"""
from ..extensions import db


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

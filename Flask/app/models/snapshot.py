"""监控统计快照表"""
from ..extensions import db


class SearchKeywordSnapshot(db.Model):
    """热门搜索关键词快照"""
    __tablename__ = 'search_keyword_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, server_default=db.func.now())


class OrderStatusSnapshot(db.Model):
    """订单状态分布快照"""
    __tablename__ = 'order_status_snapshots'
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(20), nullable=False)
    count = db.Column(db.Integer, default=0)
    today_orders = db.Column(db.Integer, default=0)
    today_revenue = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, server_default=db.func.now())

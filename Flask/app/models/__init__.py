"""数据模型：导入全部模型，确保 SQLAlchemy 注册到 db.Model"""
from .goods import Cart, Collect, Comment, Goods, History
from .notification import NotificationLog
from .order import Order, OrderItem, ReturnRequest
from .snapshot import OrderStatusSnapshot, SearchKeywordSnapshot
from .user import User, UserInfo

__all__ = [
    'User', 'UserInfo',
    'Goods', 'Cart', 'Collect', 'History', 'Comment',
    'Order', 'OrderItem', 'ReturnRequest',
    'NotificationLog',
    'SearchKeywordSnapshot', 'OrderStatusSnapshot',
]

"""订单核心业务：状态统计、库存/购物车恢复、超时取消"""
from datetime import datetime, timedelta

from ..extensions import db, redis_client
from ..models import Cart, Goods, Order
from ..utils.lock import distributed_lock

# 订单状态 → 中文标签
ORDER_STATUS_LABELS = {
    'pending_pay': '待付款', 'pending_ship': '待发货',
    'pending_receive': '待收货', 'completed': '已完成',
    'cancelled': '已取消', 'refund': '退款中', 'refunded': '已退款',
}

# 计入今日交易额的订单状态
PAID_STATUSES = ('pending_ship', 'pending_receive', 'completed')


def order_status_distribution(orders):
    """统计订单状态分布：[{'name': 中文状态, 'value': 数量}]"""
    status_map = {}
    for o in orders:
        label = ORDER_STATUS_LABELS.get(o.status, o.status)
        status_map[label] = status_map.get(label, 0) + 1
    return [{'name': name, 'value': count} for name, count in status_map.items()]


def today_order_summary():
    """今日订单数、交易额、状态分布"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = Order.query.filter(Order.created_at >= today_start).all()
    revenue = sum(float(o.total_price) for o in today_orders if o.status in PAID_STATUSES)
    return len(today_orders), round(revenue, 2), order_status_distribution(today_orders)


def restore_stock_and_cart(order, user_id=None):
    """恢复订单占用库存（带分布式锁）并将商品退回购物车"""
    user_id = user_id or order.user_id
    for item in order.items:
        with distributed_lock(f"goods_{item.goods_id}", timeout=5):
            goods = Goods.query.get(item.goods_id)
            if goods:
                goods.stock += item.num
                redis_client.incrby(f"goods_stock:{item.goods_id}", item.num)
    for item in order.items:
        existing_cart = Cart.query.filter_by(user_id=user_id, goods_id=item.goods_id).first()
        if existing_cart:
            existing_cart.num += item.num
        else:
            db.session.add(Cart(user_id=user_id, goods_id=item.goods_id, num=item.num))


def cancel_expired_orders():
    """取消超时（15 分钟）未支付的订单，恢复库存和购物车"""
    expired_time = datetime.now() - timedelta(minutes=15)
    expired_orders = Order.query.filter(
        Order.status == 'pending_pay',
        Order.created_at < expired_time,
    ).all()
    for order in expired_orders:
        print(f"自动取消超时订单: {order.order_no}")
        order.status = 'cancelled'
        restore_stock_and_cart(order)
    if expired_orders:
        db.session.commit()
        print(f"已自动取消 {len(expired_orders)} 个超时订单")

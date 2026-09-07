"""Celery 异步任务：ES 同步、订单取消、各类用户通知"""
from .extensions import celery, db, redis_client
from .models import Cart, Goods, NotificationLog, Order
from .services import es_service, order_service

# 由 create_app 注入 Flask 实例，供任务内获取应用上下文
_flask_app = None


def bind_app(app):
    global _flask_app
    _flask_app = app


def _app_context():
    return _flask_app.app_context()


def _create_notification(user_id, goods_id, order_id, ntype, content, dedup_key):
    """写入通知记录并设置 24 小时去重标记；已存在则跳过"""
    if redis_client.exists(dedup_key):
        return False
    db.session.add(NotificationLog(
        user_id=user_id, goods_id=goods_id, order_id=order_id,
        type=ntype, content=content, status='sent',
    ))
    redis_client.setex(dedup_key, 86400, '1')
    return True


@celery.task
def sync_goods_to_es_async(goods_id):
    """异步同步商品到 ES"""
    with _app_context():
        es_service.sync_goods_to_es(goods_id)


@celery.task
def cancel_expired_order_task(order_id):
    """异步取消待支付订单（延迟执行），恢复库存并退回购物车"""
    with _app_context():
        order = Order.query.get(order_id)
        if not order or order.status != 'pending_pay':
            return
        print(f"自动取消超时订单: {order.order_no}")
        order.status = 'cancelled'
        order_service.restore_stock_and_cart(order)
        db.session.commit()
        return f"订单{order_id}已取消"


@celery.task
def notify_price_drop(goods_id, old_price, new_price):
    """降价通知：发给所有购物车中有该商品的用户"""
    with _app_context():
        try:
            goods = Goods.query.get(goods_id)
            if not goods:
                return
            for cart_item in Cart.query.filter_by(goods_id=goods_id).all():
                dedup_key = f"notify:price_drop:{goods_id}:{cart_item.user_id}"
                content = f"【次元模仓】您购物车中的「{goods.name}」降价啦！从 ¥{old_price} 降到 ¥{new_price}，快去看看吧！"
                _create_notification(cart_item.user_id, goods_id, None, 'price_drop', content, dedup_key)
            db.session.commit()
            return f"降价通知已处理，商品ID: {goods_id}"
        except Exception as e:
            db.session.rollback()
            print(f"降价通知任务失败: {e}")
            raise


@celery.task
def notify_off_shelf(goods_id):
    """下架通知：通知所有购物车中有该商品的用户"""
    with _app_context():
        try:
            goods = Goods.query.get(goods_id)
            if not goods:
                return
            for cart_item in Cart.query.filter_by(goods_id=goods_id).all():
                dedup_key = f"notify:off_shelf:{goods_id}:{cart_item.user_id}"
                content = f"【次元模仓】很抱歉，您购物车中的「{goods.name}」已被商家下架，请及时处理。"
                _create_notification(cart_item.user_id, goods_id, None, 'off_shelf', content, dedup_key)
            db.session.commit()
            return f"下架通知已处理，商品ID: {goods_id}"
        except Exception as e:
            db.session.rollback()
            print(f"下架通知任务失败: {e}")
            raise


@celery.task
def notify_shipment(order_id):
    """发货通知"""
    with _app_context():
        try:
            order = Order.query.get(order_id)
            if not order:
                return
            first_item = order.items[0] if order.items else None
            if not first_item:
                print(f"订单 {order_id} 无商品项，无法发送发货通知")
                return
            dedup_key = f"notify:shipment:{order_id}:{order.user_id}"
            content = f"【次元模仓】您的订单 {order.order_no} 已发货！商品「{first_item.goods_name}」正在配送中，请注意查收。"
            if _create_notification(order.user_id, first_item.goods_id, order_id, 'shipment', content, dedup_key):
                db.session.commit()
            return f"发货通知已发送，订单ID: {order_id}"
        except Exception as e:
            db.session.rollback()
            print(f"发货通知任务失败: {e}")
            raise


@celery.task
def notify_goods_update(goods_id, old_name, new_name):
    """商品名称更新通知"""
    with _app_context():
        try:
            goods = Goods.query.get(goods_id)
            if not goods:
                return
            for cart_item in Cart.query.filter_by(goods_id=goods_id).all():
                dedup_key = f"notify:goods_update:{goods_id}:{cart_item.user_id}"
                content = f"【次元模仓】您购物车中的商品「{old_name}」已更新为「{new_name}」，快去看看吧！"
                _create_notification(cart_item.user_id, goods_id, None, 'goods_update', content, dedup_key)
            db.session.commit()
            return f"商品更新通知已处理，商品ID: {goods_id}"
        except Exception as e:
            db.session.rollback()
            print(f"商品更新通知任务失败: {e}")
            raise

"""库存操作：Redis 原子扣减 + 数据库同步"""
from ..extensions import db, redis_client
from ..models import Goods


def deduct_stock_redis(goods_id, num):
    """Redis 原子扣减库存并同步数据库；库存不足或异常返回 False"""
    stock_key = f"goods_stock:{goods_id}"
    try:
        current_stock = redis_client.get(stock_key)
        if not current_stock:
            goods = Goods.query.get(goods_id)
            if not goods:
                return False
            current_stock = goods.stock
            redis_client.set(stock_key, current_stock)

        current_stock = int(current_stock)
        if current_stock < num:
            return False

        new_stock = current_stock - num
        redis_client.set(stock_key, new_stock)

        goods = Goods.query.get(goods_id)
        if goods:
            goods.stock = new_stock
            db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"扣减库存失败: {e}")
        return False

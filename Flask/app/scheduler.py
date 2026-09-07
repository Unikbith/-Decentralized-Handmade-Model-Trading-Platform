"""APScheduler 定时任务：超时订单、搜索关键词与订单状态快照"""
import os
from datetime import datetime, timedelta

from .extensions import db, redis_client, scheduler
from .models import OrderStatusSnapshot, SearchKeywordSnapshot
from .services import order_service


@scheduler.task('interval', id='cancel_expired_orders_task', minutes=1, misfire_grace_time=300)
def scheduled_cancel_expired_orders():
    """每分钟执行一次，取消超时未支付的订单"""
    order_service.cancel_expired_orders()


@scheduler.task('interval', id='refresh_search_keywords_task', days=7, misfire_grace_time=3600)
def scheduled_refresh_search_keywords():
    """每 7 天聚合 Redis 近 7 天搜索关键词 Top10 持久化到 MySQL"""
    try:
        keyword_totals = {}
        for i in range(7):
            day = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            data = redis_client.zrevrange(f'monitor:search_keywords:{day}', 0, -1, withscores=True)
            for kw, count in data:
                kw_str = kw.decode() if isinstance(kw, bytes) else kw
                keyword_totals[kw_str] = keyword_totals.get(kw_str, 0) + int(count)

        top10 = sorted(keyword_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        SearchKeywordSnapshot.query.delete()
        for keyword, count in top10:
            db.session.add(SearchKeywordSnapshot(keyword=keyword, count=count))
        db.session.commit()
        print("热门搜索关键词快照已更新（7天周期）")
    except Exception as e:
        print(f"更新搜索关键词快照错误: {e}")


@scheduler.task('interval', id='refresh_order_status_task', minutes=5, misfire_grace_time=300)
def scheduled_refresh_order_status():
    """每 5 分钟统计今日订单状态分布并持久化到 MySQL（快照表备用）"""
    try:
        today_order_count, today_revenue, status_dist = order_service.today_order_summary()
        OrderStatusSnapshot.query.delete()
        for item in status_dist:
            db.session.add(OrderStatusSnapshot(
                status_name=item['name'], count=item['value'],
                today_orders=today_order_count, today_revenue=today_revenue,
            ))
        db.session.commit()
        print("订单状态分布快照已更新")
    except Exception as e:
        print(f"更新订单状态分布快照错误: {e}")


def start_scheduler(app):
    """启动定时任务（debug 模式避免重复启动）"""
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        scheduler.start()

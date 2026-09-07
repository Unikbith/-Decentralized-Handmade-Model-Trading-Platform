"""管理后台：用户、商家、商品、订单管理与实时监控看板"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..extensions import db, redis_client
from ..models import (
    Cart, Collect, Comment, Goods, History, NotificationLog, Order,
    OrderItem, ReturnRequest, SearchKeywordSnapshot, User, UserInfo,
)
from ..scheduler import scheduled_refresh_search_keywords
from ..services.es_service import delete_goods_from_es, sync_goods_to_es
from ..tasks import notify_off_shelf
from ..utils.decorators import admin_required
from ..utils.image import fix_image_url

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

ORDER_STATUS_LABELS = {
    'pending_pay': '待付款', 'pending_ship': '待发货',
    'pending_receive': '待收货', 'completed': '已完成',
    'cancelled': '已取消', 'refund': '退款中', 'refunded': '已退款',
}
PAID_STATUSES = ('pending_ship', 'pending_receive', 'completed')


def _user_summary(user):
    info = user.info
    return {
        'id': user.id,
        'nickname': user.nickname,
        'username': user.username,
        'role': user.role,
        'is_banned': user.is_banned,
        'apply_status': user.apply_status or 'none',
        'apply_time': user.apply_time.strftime('%Y-%m-%d %H:%M') if user.apply_time else '',
        'phone': info.phone if info else '',
        'avatar': fix_image_url(info.avatar) if info else '',
        'receiver_name': info.receiver_name if info else '',
        'address': info.address if info else '',
    }


# ---------------- 用户管理 ----------------

@bp.route('/users', methods=['GET'])
@admin_required
def admin_get_users():
    """管理员获取所有用户列表"""
    try:
        return jsonify({'code': 200, 'data': [_user_summary(u) for u in User.query.all()]})
    except Exception as e:
        print(f"管理员获取用户列表错误: {e}")
        return jsonify({'code': 500, 'msg': '获取用户列表失败'}), 500


@bp.route('/user/delete/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_user(id):
    """管理员删除用户（级联删除相关数据）"""
    try:
        user = User.query.get_or_404(id)
        UserInfo.query.filter_by(user_id=id).delete()
        Cart.query.filter_by(user_id=id).delete()
        History.query.filter_by(user_id=id).delete()
        Comment.query.filter_by(user_id=id).delete()
        ReturnRequest.query.filter_by(user_id=id).delete()
        NotificationLog.query.filter_by(user_id=id).delete()
        Order.query.filter_by(user_id=id).delete()
        db.session.delete(user)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员删除用户错误: {e}")
        return jsonify({'code': 500, 'msg': '删除用户失败'}), 500


@bp.route('/user/update/<int:id>', methods=['POST'])
@admin_required
def admin_update_user(id):
    """管理员修改用户信息"""
    try:
        user = User.query.get_or_404(id)
        data = request.get_json()

        if data.get('nickname', '').strip():
            user.nickname = data['nickname'].strip()
        if 'role' in data:
            if data['role'] not in ('user', 'merchant'):
                return jsonify({'code': 400, 'msg': '无效角色，仅支持普通用户和商家'}), 400
            user.role = data['role']

        user_info = user.info or UserInfo(user_id=user.id)
        if not user.info:
            db.session.add(user_info)
        if 'avatar' in data:
            user_info.avatar = fix_image_url(data['avatar'].strip())
        if 'phone' in data:
            user_info.phone = data['phone'].strip()
        if 'address' in data:
            user_info.address = data['address'].strip()

        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户信息修改成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员修改用户错误: {e}")
        return jsonify({'code': 500, 'msg': '修改用户信息失败'}), 500


@bp.route('/user/detail/<int:id>', methods=['GET'])
@admin_required
def admin_get_user_detail(id):
    """管理员获取单个用户的详细信息与统计数据"""
    try:
        user = User.query.get_or_404(id)
        user_info = user.info
        data = {
            'id': user.id,
            'nickname': user.nickname,
            'username': user.username,
            'role': user.role,
            'is_banned': user.is_banned,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'created_at') else '未知',
            'info': {
                'avatar': fix_image_url(user_info.avatar) if user_info else '',
                'birthday': user_info.birthday if user_info else '',
                'gender': user_info.gender if user_info else '',
                'email': user_info.email if user_info else '',
                'phone': user_info.phone if user_info else '',
                'receiver_name': user_info.receiver_name if user_info else '',
                'address': user_info.address if user_info else '',
            },
            'stats': {
                'order_count': Order.query.filter_by(user_id=id).count(),
                'cart_count': Cart.query.filter_by(user_id=id).count(),
                'collect_count': Collect.query.filter_by(user_id=id).count(),
                'comment_count': Comment.query.filter_by(user_id=id).count(),
            },
        }
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        print(f"管理员获取用户详情错误: {e}")
        return jsonify({'code': 500, 'msg': '获取用户详情失败'}), 500


@bp.route('/user/ban/<int:id>', methods=['POST'])
@admin_required
def admin_ban_user(id):
    """管理员封禁用户"""
    try:
        User.query.get_or_404(id).is_banned = True
        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户封禁成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员封禁用户错误: {e}")
        return jsonify({'code': 500, 'msg': '封禁用户失败'}), 500


@bp.route('/user/unban/<int:id>', methods=['POST'])
@admin_required
def admin_unban_user(id):
    """管理员解封用户"""
    try:
        User.query.get_or_404(id).is_banned = False
        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户解封成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员解封用户错误: {e}")
        return jsonify({'code': 500, 'msg': '解封用户失败'}), 500


# ---------------- 商家审核 ----------------

def _audit_merchant(user_id, status, ok_msg):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404
    if user.role != 'merchant':
        return jsonify({'code': 400, 'msg': '该用户不是商家角色'}), 400
    if user.apply_status != 'pending':
        return jsonify({'code': 400, 'msg': '该商家未提交申请或已审核'}), 400
    user.apply_status = status
    db.session.commit()
    return jsonify({'code': 200, 'msg': ok_msg})


@bp.route('/merchant/approve/<int:user_id>', methods=['POST'])
@admin_required
def admin_approve_merchant(user_id):
    """管理员通过商家入驻申请"""
    try:
        return _audit_merchant(user_id, 'approved', '已通过该商家的入驻申请')
    except Exception as e:
        db.session.rollback()
        print(f"通过入驻申请失败: {e}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


@bp.route('/merchant/reject/<int:user_id>', methods=['POST'])
@admin_required
def admin_reject_merchant(user_id):
    """管理员拒绝商家入驻申请"""
    try:
        return _audit_merchant(user_id, 'rejected', '已拒绝该商家的入驻申请')
    except Exception as e:
        db.session.rollback()
        print(f"拒绝入驻申请失败: {e}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


# ---------------- 商品管理 ----------------

def _goods_summary(g):
    return {
        'id': g.id,
        'name': g.name,
        'price': float(g.price),
        'stock': g.stock,
        'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
        'category': g.category,
        'status': g.status,
        'merchant_name': g.merchant_name,
        'brand': g.brand,
        'ip': g.ip,
        'charactername': g.charactername,
        'description': g.description,
    }


@bp.route('/goods', methods=['GET'])
@admin_required
def admin_get_goods():
    """管理员获取所有商品列表"""
    try:
        goods = Goods.query.order_by(Goods.created_at.desc()).all()
        return jsonify({'code': 200, 'data': [_goods_summary(g) for g in goods]})
    except Exception as e:
        print(f"管理员获取商品列表错误: {e}")
        return jsonify({'code': 500, 'msg': '获取商品列表失败'}), 500


@bp.route('/goods/delete/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_goods(id):
    """删除商品，同步清除 ES 索引与 Redis 缓存"""
    try:
        goods = Goods.query.get_or_404(id)
        Cart.query.filter_by(goods_id=id).delete()
        History.query.filter_by(goods_id=id).delete()
        Comment.query.filter_by(goods_id=id).delete()
        ReturnRequest.query.filter_by(goods_id=id).delete()
        NotificationLog.query.filter_by(goods_id=id).delete()
        OrderItem.query.filter_by(goods_id=id).delete()
        delete_goods_from_es(id)
        redis_client.delete(f"goods_stock:{id}", f'goods_detail:{id}', 'goods_list:default')
        db.session.delete(goods)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '商品删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员删除商品错误: {e}")
        return jsonify({'code': 500, 'msg': '删除商品失败'}), 500


@bp.route('/goods/update/<int:id>', methods=['POST'])
@admin_required
def admin_update_goods(id):
    """管理员修改商品信息，同步缓存与 ES 索引"""
    try:
        goods = Goods.query.get_or_404(id)
        data = request.get_json()
        goods.name = data.get('name', goods.name)
        goods.price = data.get('price', goods.price)
        goods.stock = data.get('stock', goods.stock)
        goods.category = data.get('category', goods.category)
        goods.status = data.get('status', goods.status)
        goods.brand = data.get('brand', goods.brand)
        goods.ip = data.get('ip', goods.ip)
        goods.charactername = data.get('charactername', goods.charactername)
        goods.description = data.get('description', goods.description)
        redis_client.set(f"goods_stock:{id}", goods.stock)
        redis_client.delete(f'goods_detail:{id}', 'goods_list:default')
        sync_goods_to_es(id)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '商品修改成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员修改商品错误: {e}")
        return jsonify({'code': 500, 'msg': '修改商品失败'}), 500


@bp.route('/goods/status/<int:id>', methods=['POST'])
@admin_required
def admin_toggle_goods_status(id):
    """管理员切换商品 上架/下架 状态"""
    try:
        goods = Goods.query.get_or_404(id)
        if goods.status == "下架":
            goods.status = "缺货" if goods.stock <= 0 else "现货"
        else:
            goods.status = "下架"
        db.session.commit()
        redis_client.delete('goods_list:default', f'goods_detail:{id}')
        sync_goods_to_es(id)
        if goods.status == "下架":
            notify_off_shelf.delay(id)
        return jsonify({'code': 200, 'msg': '商品状态切换成功'})
    except Exception as e:
        db.session.rollback()
        print(f"商品上下架操作失败: {e}")
        return jsonify({'code': 500, 'msg': '操作失败，服务器异常'}), 500


# ---------------- 订单管理 ----------------

@bp.route('/orders', methods=['GET'])
@admin_required
def admin_get_orders():
    """管理员获取订单列表（可按状态筛选）"""
    try:
        query = Order.query.order_by(Order.created_at.desc())
        status = request.args.get('status', '')
        if status:
            query = query.filter_by(status=status)
        data = [{
            'id': o.id,
            'order_no': o.order_no,
            'user_id': o.user_id,
            'user_nickname': (User.query.get(o.user_id).nickname if User.query.get(o.user_id) else '未知用户'),
            'receiver_name': o.receiver_name,
            'receiver_phone': o.receiver_phone,
            'receiver_address': o.receiver_address,
            'total_price': float(o.total_price),
            'status': o.status,
            'created_at': o.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        } for o in query.all()]
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        print(f"管理员获取订单列表错误: {e}")
        return jsonify({'code': 500, 'msg': '获取订单列表失败'}), 500


@bp.route('/order/update/<int:id>', methods=['POST'])
@admin_required
def admin_update_order(id):
    """管理员修改订单信息（收货人、总价、状态等）"""
    try:
        order = Order.query.get_or_404(id)
        data = request.get_json()
        order.receiver_name = data.get('receiver_name', order.receiver_name)
        order.receiver_phone = data.get('receiver_phone', order.receiver_phone)
        order.receiver_address = data.get('receiver_address', order.receiver_address)
        order.total_price = data.get('total_price', order.total_price)
        order.status = data.get('status', order.status)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '订单修改成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员修改订单错误: {e}")
        return jsonify({'code': 500, 'msg': '修改订单失败'}), 500


@bp.route('/order/delete/<int:id>', methods=['DELETE'])
@admin_required
def admin_delete_order(id):
    """管理员删除订单（同时删除关联售后）"""
    try:
        order = Order.query.get_or_404(id)
        ReturnRequest.query.filter_by(order_id=id).delete()
        db.session.delete(order)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '订单删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"管理员删除订单错误: {e}")
        return jsonify({'code': 500, 'msg': '删除订单失败'}), 500


# ---------------- 监控看板 ----------------

@bp.route('/monitor/realtime', methods=['GET'])
@admin_required
def monitor_realtime():
    """最近60分钟实时请求指标"""
    try:
        now = datetime.now()
        minutes = []
        for i in range(59, -1, -1):
            t = now - timedelta(minutes=i)
            key = t.strftime('%Y%m%d%H%M')
            total = int(redis_client.get(f'monitor:minute:{key}:total') or 0)
            errors = int(redis_client.get(f'monitor:minute:{key}:error') or 0)
            duration_sum = int(redis_client.get(f'monitor:minute:{key}:duration') or 0)
            minutes.append({
                'time': t.strftime('%H:%M'),
                'total': total,
                'errors': errors,
                'avg_duration': int(duration_sum / total) if total > 0 else 0,
            })

        today_total = sum(m['total'] for m in minutes)
        today_errors = sum(m['errors'] for m in minutes)
        return jsonify({
            'code': 200,
            'data': {
                'timeline': minutes,
                'summary': {
                    'total_requests': today_total,
                    'avg_duration': int(sum(m['avg_duration'] * m['total'] for m in minutes) / today_total) if today_total > 0 else 0,
                    'error_rate': round(today_errors / today_total * 100, 2) if today_total > 0 else 0,
                },
            }
        })
    except Exception as e:
        print(f"获取实时监控数据错误: {e}")
        return jsonify({'code': 500, 'msg': '获取监控数据失败'}), 500


@bp.route('/monitor/user-activity', methods=['GET'])
@admin_required
def monitor_user_activity():
    """用户活跃度：今日活跃、新增注册、每小时趋势"""
    try:
        today_key = datetime.now().strftime('%Y%m%d')
        now = datetime.now()
        hourly = []
        for i in range(23, -1, -1):
            h = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
            hour_key = h.strftime('%Y%m%d%H')
            hourly.append({
                'hour': h.strftime('%H:00'),
                'count': redis_client.scard(f'monitor:active_hour:{hour_key}'),
            })
        return jsonify({
            'code': 200,
            'data': {
                'active_users': redis_client.scard(f'monitor:active_users:{today_key}'),
                'new_registrations': int(redis_client.get(f'monitor:new_registrations:{today_key}') or 0),
                'hourly_trend': hourly,
            }
        })
    except Exception as e:
        print(f"获取用户活跃度错误: {e}")
        return jsonify({'code': 500, 'msg': '获取数据失败'}), 500


@bp.route('/monitor/product-ranking', methods=['GET'])
@admin_required
def monitor_product_ranking():
    """商品热度排行：销量 Top10"""
    try:
        sales = db.session.query(
            Goods.name, func.sum(OrderItem.num).label('count')
        ).join(OrderItem, OrderItem.goods_id == Goods.id
               ).join(Order, Order.id == OrderItem.order_id
                      ).filter(Order.status != 'cancelled'
                               ).group_by(Goods.id, Goods.name
                                          ).order_by(func.sum(OrderItem.num).desc()
                                                     ).limit(10).all()
        return jsonify({
            'code': 200,
            'data': {'by_sales': [{'name': s.name, 'count': int(s.count)} for s in sales]},
        })
    except Exception as e:
        print(f"获取商品排行错误: {e}")
        return jsonify({'code': 500, 'msg': '获取数据失败'}), 500


@bp.route('/monitor/order-overview', methods=['GET'])
@admin_required
def monitor_order_overview():
    """订单交易概览：今日订单数、交易额与状态分布"""
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = Order.query.filter(Order.created_at >= today_start).all()
        status_map = {}
        for o in today_orders:
            label = ORDER_STATUS_LABELS.get(o.status, o.status)
            status_map[label] = status_map.get(label, 0) + 1
        return jsonify({
            'code': 200,
            'data': {
                'today_orders': len(today_orders),
                'today_revenue': round(sum(float(o.total_price) for o in today_orders if o.status in PAID_STATUSES), 2),
                'status_distribution': [{'name': n, 'value': c} for n, c in status_map.items()],
            }
        })
    except Exception as e:
        print(f"获取订单概览错误: {e}")
        return jsonify({'code': 500, 'msg': '获取数据失败'}), 500


@bp.route('/monitor/search-keywords', methods=['GET'])
@admin_required
def monitor_search_keywords():
    """搜索关键词排行 Top10：从 MySQL 快照读取，为空时实时刷新"""
    try:
        snapshots = SearchKeywordSnapshot.query.order_by(SearchKeywordSnapshot.count.desc()).all()
        if not snapshots:
            scheduled_refresh_search_keywords()
            snapshots = SearchKeywordSnapshot.query.order_by(SearchKeywordSnapshot.count.desc()).all()
        return jsonify({
            'code': 200,
            'data': [{'keyword': s.keyword, 'count': s.count} for s in snapshots],
        })
    except Exception as e:
        print(f"获取搜索关键词错误: {e}")
        return jsonify({'code': 500, 'msg': '获取数据失败'}), 500

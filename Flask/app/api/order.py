"""订单：创建、取消、删除、支付、列表、收货、发货、公开查询、售后"""
import random
import time

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..extensions import db, redis_client
from ..models import Cart, Goods, Order, OrderItem, ReturnRequest, User, UserInfo
from ..services import order_service, stock_service
from ..tasks import cancel_expired_order_task, notify_shipment
from ..utils.image import fix_image_url

bp = Blueprint('order', __name__, url_prefix='/api/order')


@bp.route('/create', methods=['POST'])
@jwt_required()
def create_order():
    """从购物车创建订单，扣减库存，清空购物车，启动延迟取消任务"""
    cart_snapshot = []
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        if not cart_items:
            return jsonify({'code': 400, 'msg': '购物车为空'}), 400

        cart_snapshot = [(item.goods_id, item.num) for item in cart_items]
        user_info = UserInfo.query.filter_by(user_id=user_id).first()

        # 收货信息：优先请求参数，其次用户资料
        receiver_name = data.get('name', '') or (user_info.receiver_name if user_info else '')
        receiver_phone = data.get('phone', '') or (user_info.phone if user_info else '')
        receiver_address = data.get('address', '') or (user_info.address if user_info else '')

        # 逐项扣减库存
        for item in cart_items:
            if not stock_service.deduct_stock_redis(item.goods_id, item.num):
                return jsonify({'code': 400, 'msg': f'商品"{item.goods.name}"库存不足'}), 400

        total_price = sum(item.goods.price * item.num for item in cart_items)
        order_no = f"ORD{int(time.time())}{random.randint(1000, 9999)}"

        new_order = Order(
            order_no=order_no, user_id=user_id, total_price=total_price,
            receiver_name=receiver_name, receiver_phone=receiver_phone,
            receiver_address=receiver_address,
        )
        db.session.add(new_order)
        db.session.flush()

        for item in cart_items:
            db.session.add(OrderItem(
                order_id=new_order.id, goods_id=item.goods_id,
                goods_name=item.goods.name,
                goods_image=fix_image_url(item.goods.images.split(',')[0]) if item.goods.images else '',
                price=item.goods.price, num=item.num,
            ))

        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        # 延迟 5 秒执行超时取消任务（模拟支付超时）
        cancel_expired_order_task.apply_async(args=[new_order.id], countdown=5)
        return jsonify({'code': 200, 'msg': '订单创建成功',
                        'order_no': order_no, 'order_id': new_order.id}), 200
    except Exception as e:
        # 异常时回滚 Redis 库存
        for goods_id, num in cart_snapshot:
            redis_client.incrby(f"goods_stock:{goods_id}", num)
        db.session.rollback()
        print(f"创建订单错误: {e}")
        return jsonify({'code': 500, 'msg': '创建订单失败'}), 500


@bp.route('/cancel/<string:order_no>', methods=['POST'])
@jwt_required()
def cancel_order(order_no):
    """用户取消待支付订单，恢复库存并退回购物车"""
    try:
        user_id = int(get_jwt_identity())
        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'}), 404
        if order.status != 'pending_pay':
            return jsonify({'code': 400, 'msg': '只能取消待支付的订单'}), 400
        order.status = 'cancelled'
        order_service.restore_stock_and_cart(order, user_id)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '订单已取消，商品已返回购物车'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"取消订单错误: {e}")
        return jsonify({'code': 500, 'msg': '取消订单失败，请稍后重试'}), 500


@bp.route('/delete/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id):
    """删除订单；待支付或已取消的订单会恢复库存和购物车"""
    try:
        get_jwt_identity()
        order = Order.query.get_or_404(order_id)
        if order.status in ('pending_pay', 'cancelled'):
            order_service.restore_stock_and_cart(order)
        db.session.delete(order)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '订单删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"删除订单错误: {e}")
        return jsonify({'code': 500, 'msg': '删除失败'}), 500


@bp.route('/confirm/<string:order_no>', methods=['POST'])
@jwt_required()
def confirm_pay(order_no):
    """用户模拟支付：待支付 → 待发货"""
    try:
        user_id = int(get_jwt_identity())
        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'}), 404
        if str(order.user_id) != str(user_id):
            return jsonify({'code': 403, 'msg': '无权操作'}), 403
        if order.status != 'pending_pay':
            return jsonify({'code': 400, 'msg': '订单状态错误'}), 400
        order.status = 'pending_ship'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '支付成功，等待商家发货'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"确认支付错误: {e}")
        return jsonify({'code': 500, 'msg': '支付失败'}), 500


@bp.route('/confirm-public/<string:order_no>', methods=['POST'])
def confirm_pay_public(order_no):
    """公开支付确认（无需登录，用于外部支付回调）"""
    try:
        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'}), 404
        if order.status == 'cancelled':
            return jsonify({'code': 400, 'msg': '订单已超时取消，请重新下单'}), 400
        if order.status != 'pending_pay':
            return jsonify({'code': 400, 'msg': f'订单状态错误，当前状态：{order.status}'}), 400
        order.status = 'pending_ship'
        db.session.commit()
        print(f"订单 {order_no} 支付成功，状态已更新为: {order.status}")
        return jsonify({'code': 200, 'msg': '支付成功！等待商家发货'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"公开支付错误: {e}")
        return jsonify({'code': 500, 'msg': '支付失败，请重试'}), 500


@bp.route('/list', methods=['GET'])
@jwt_required()
def get_order_list():
    """获取订单列表（商家仅展示包含自己商品的订单）"""
    try:
        user = get_jwt()
        user_id = int(get_jwt_identity())
        status = request.args.get('status', '')

        if user['role'] == 'merchant':
            order_items = OrderItem.query.join(Goods).filter(Goods.merchant_id == user['id']).all()
            order_ids = list({item.order_id for item in order_items})
            query = Order.query.filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc())
        else:
            query = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc())

        if status:
            query = query.filter(Order.status.in_(['refund', 'refunded'])) if status == 'refund' \
                else query.filter_by(status=status)

        res = []
        for order in query.all():
            items = []
            merchant_total = 0.0
            for item in order.items:
                if user['role'] == 'merchant':
                    goods = Goods.query.get(item.goods_id)
                    if not goods or goods.merchant_id != user['id']:
                        continue
                    merchant_total += float(item.price) * item.num
                items.append({
                    'id': item.id, 'goods_id': item.goods_id, 'name': item.goods_name,
                    'image': fix_image_url(item.goods_image),
                    'price': float(item.price), 'num': item.num,
                })
            res.append({
                'id': order.id, 'order_no': order.order_no,
                'total_price': merchant_total if user['role'] == 'merchant' else float(order.total_price),
                'status': order.status,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'items': items,
                'receiver_name': order.receiver_name,
                'receiver_phone': order.receiver_phone,
                'receiver_address': order.receiver_address,
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取订单列表错误: {e}")
        return jsonify({'code': 500, 'msg': '获取订单失败'})


@bp.route('/receive/<int:order_id>', methods=['POST'])
@jwt_required()
def receive_order(order_id):
    """用户确认收货"""
    try:
        user_id = int(get_jwt_identity())
        order = Order.query.get_or_404(order_id)
        if str(order.user_id) != str(user_id):
            return jsonify({'code': 403, 'msg': '无权操作'})
        if order.status != 'pending_receive':
            return jsonify({'code': 400, 'msg': '订单状态错误'})
        order.status = 'completed'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '确认收货成功'})
    except Exception as e:
        db.session.rollback()
        print(f"确认收货错误: {e}")
        return jsonify({'code': 500, 'msg': '确认收货失败'})


@bp.route('/ship/<int:order_id>', methods=['POST'])
@jwt_required()
def ship_order(order_id):
    """商家发货"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'}), 403
        order = Order.query.get_or_404(order_id)
        if order.status != 'pending_ship':
            return jsonify({'code': 400, 'msg': '订单状态错误，无法发货'}), 400

        has_merchant_goods = any(
            (g := Goods.query.get(item.goods_id)) and g.merchant_id == user['id']
            for item in order.items
        )
        if not has_merchant_goods:
            return jsonify({'code': 403, 'msg': '无权操作非本店订单'}), 403

        order.status = 'pending_receive'
        db.session.commit()
        notify_shipment.delay(order_id)
        return jsonify({'code': 200, 'msg': '发货成功，等待用户确认收货'})
    except Exception as e:
        db.session.rollback()
        print(f"发货错误: {e}")
        return jsonify({'code': 500, 'msg': '发货失败'})


@bp.route('/public/<string:order_no>', methods=['GET'])
def get_order_public(order_no):
    """公开查询订单信息"""
    try:
        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在'}), 404
        return jsonify({'code': 200, 'data': {
            'order_no': order.order_no, 'total_price': float(order.total_price), 'status': order.status,
        }}), 200
    except Exception as e:
        print(f"查询订单错误: {e}")
        return jsonify({'code': 500, 'msg': '查询订单失败'})


# ==================== 售后 ====================

VALID_RETURN_TYPES = ('refund', 'return', 'exchange')


@bp.route('/return/apply', methods=['POST'])
@jwt_required()
def apply_return():
    """申请退款/退货/换货"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        order_id = data.get('order_id')
        return_type = data.get('type')
        reason = data.get('reason', '').strip()

        if not all([order_id, return_type]):
            return jsonify({'code': 400, 'msg': '订单ID和售后类型不能为空'}), 400
        if not reason:
            return jsonify({'code': 400, 'msg': '请填写售后原因'}), 400
        if return_type not in VALID_RETURN_TYPES:
            return jsonify({'code': 400, 'msg': '售后类型不合法'}), 400

        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return jsonify({'code': 404, 'msg': '订单不存在或无权限操作'}), 404
        if order.status not in ('completed', 'pending_receive'):
            return jsonify({'code': 400, 'msg': '仅已完成或待收货订单可申请售后'}), 400
        if ReturnRequest.query.filter_by(order_id=order_id, user_id=user_id).first():
            return jsonify({'code': 400, 'msg': '该订单已申请售后，请勿重复申请'}), 400
        if not order.items:
            return jsonify({'code': 400, 'msg': '订单商品不存在'}), 400

        order_item = order.items[0]
        goods = Goods.query.get(order_item.goods_id)
        if not goods:
            return jsonify({'code': 400, 'msg': '商品不存在'}), 400

        return_req = ReturnRequest(
            order_id=order_id, user_id=user_id, merchant_id=goods.merchant_id,
            goods_id=order_item.goods_id, type=return_type, reason=reason, status='pending',
        )
        order.status = 'refund'  # 订单状态变更为退款中
        db.session.add(return_req)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '售后申请提交成功，等待商家审核',
                        'data': {'return_id': return_req.id}})
    except Exception as e:
        db.session.rollback()
        print(f"售后申请接口异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '售后申请失败，服务器异常'}), 500


def _serialize_return(ret):
    """售后记录序列化"""
    return {
        'id': ret.id, 'order_id': ret.order_id, 'order_no': ret.order.order_no,
        'goods_name': ret.goods.name,
        'goods_image': fix_image_url(ret.goods.images.split(',')[0]) if ret.goods.images else '',
        'type': ret.type, 'reason': ret.reason, 'status': ret.status,
        'created_at': ret.created_at.strftime('%Y-%m-%d %H:%M'),
    }


@bp.route('/return/list', methods=['GET'])
@jwt_required()
def get_return_list():
    """获取售后申请列表（用户或商家）"""
    try:
        user = get_jwt()
        user_id = int(get_jwt_identity())
        status = request.args.get('status', '')
        if user['role'] == 'merchant':
            returns = ReturnRequest.query.filter_by(merchant_id=user['id']).order_by(
                ReturnRequest.created_at.desc()).all()
        else:
            returns = ReturnRequest.query.filter_by(user_id=user_id).order_by(
                ReturnRequest.created_at.desc()).all()
        if status:
            returns = [r for r in returns if r.status == status]
        return jsonify({'code': 200, 'data': [_serialize_return(r) for r in returns]})
    except Exception as e:
        print(f"查询售后列表异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '获取售后列表失败'})


@bp.route('/return/audit', methods=['POST'])
@jwt_required()
def audit_return():
    """商家审核售后申请（同意/拒绝）"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可审核售后'}), 403

        data = request.get_json()
        return_id = data.get('return_id')
        audit_status = data.get('status')
        if not all([return_id, audit_status]):
            return jsonify({'code': 400, 'msg': '审核参数不能为空'}), 400

        return_req = ReturnRequest.query.get(return_id)
        if not return_req or return_req.merchant_id != user['id']:
            return jsonify({'code': 404, 'msg': '售后记录不存在或无权限操作'}), 404
        if return_req.status != 'pending':
            return jsonify({'code': 400, 'msg': '该售后已处理，请勿重复操作'}), 400

        return_req.status = audit_status
        if audit_status == 'rejected':
            return_req.order.status = 'completed'
        elif audit_status in ('approved', 'refunded'):
            return_req.order.status = 'refunded'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '售后审核操作成功'})
    except Exception as e:
        db.session.rollback()
        print(f"售后审核异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '审核失败，服务器异常'}), 500


@bp.route('/return/merchant', methods=['GET'])
@jwt_required()
def get_merchant_returns():
    """商家获取针对自己店铺的售后申请列表"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可访问'}), 403
        returns = ReturnRequest.query.filter_by(merchant_id=user['id']).order_by(
            ReturnRequest.created_at.desc()).all()
        res = []
        for ret in returns:
            user_obj = User.query.get(ret.user_id)
            item = _serialize_return(ret)
            item.update({
                'user_nickname': user_obj.nickname if user_obj else '未知用户',
                'total_price': float(ret.order.total_price) if ret.order else 0,
            })
            res.append(item)
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取商家售后列表异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '获取售后列表失败'})


@bp.route('/return/user', methods=['GET'])
@jwt_required()
def get_user_returns():
    """用户获取自己的售后申请列表"""
    try:
        user_id = int(get_jwt_identity())
        returns = ReturnRequest.query.filter_by(user_id=user_id).order_by(
            ReturnRequest.created_at.desc()).all()
        return jsonify({'code': 200, 'data': [_serialize_return(r) for r in returns]})
    except Exception as e:
        print(f"获取用户售后列表异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '获取售后列表失败'})


@bp.route('/return/approve/<int:return_id>', methods=['POST'])
@jwt_required()
def approve_return(return_id):
    """商家同意售后申请（简化版，兼容保留）"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'}), 403
        return_req = ReturnRequest.query.get(return_id)
        if not return_req or return_req.merchant_id != user['id']:
            return jsonify({'code': 404, 'msg': '售后记录不存在或无权限'}), 404
        if return_req.status != 'pending':
            return jsonify({'code': 400, 'msg': '该售后已处理'}), 400
        return_req.status = 'approved'
        return_req.order.status = 'refund'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已同意售后申请'})
    except Exception as e:
        db.session.rollback()
        print(f"同意售后异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


@bp.route('/return/reject/<int:return_id>', methods=['POST'])
@jwt_required()
def reject_return(return_id):
    """商家拒绝售后申请"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'}), 403
        return_req = ReturnRequest.query.get(return_id)
        if not return_req or return_req.merchant_id != user['id']:
            return jsonify({'code': 404, 'msg': '售后记录不存在或无权限'}), 404
        if return_req.status != 'pending':
            return jsonify({'code': 400, 'msg': '该售后已处理'}), 400
        return_req.status = 'rejected'
        return_req.order.status = 'completed'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已拒绝售后申请'})
    except Exception as e:
        db.session.rollback()
        print(f"拒绝售后异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


@bp.route('/return/refund/<int:return_id>', methods=['POST'])
@jwt_required()
def complete_refund(return_id):
    """售后状态从 approved 变为 refunded"""
    try:
        user = get_jwt()
        if user['role'] != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家可操作'}), 403
        return_req = ReturnRequest.query.get(return_id)
        if not return_req or return_req.merchant_id != user['id']:
            return jsonify({'code': 404, 'msg': '售后记录不存在或无权限'}), 404
        if return_req.status != 'approved':
            return jsonify({'code': 400, 'msg': '仅已同意的售后可确认退款'}), 400
        return_req.status = 'refunded'
        return_req.order.status = 'refunded'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '退款已完成'})
    except Exception as e:
        db.session.rollback()
        print(f"确认退款异常: {str(e)}")
        return jsonify({'code': 500, 'msg': '操作失败'}), 500

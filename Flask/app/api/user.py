"""用户中心：资料查询/更新、修改密码、商家入驻申请、通知中心"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..extensions import db
from ..models import NotificationLog, User, UserInfo
from ..utils.crypto import decrypt_password, encrypt_password
from ..utils.image import fix_image_url

bp_user = Blueprint('user', __name__, url_prefix='/api/user')
bp_merchant = Blueprint('merchant', __name__, url_prefix='/api/merchant')


def _parse_address(address):
    """将纯文本地址解析为省/市/区/详细地址结构"""
    struct = {'name': '', 'phone': '', 'province': '', 'city': '', 'district': '', 'detail': address}
    parts = address.split('省')
    if len(parts) > 1:
        struct['province'] = parts[0] + '省'
        remaining = parts[1]
        city_parts = remaining.split('市')
        if len(city_parts) > 1:
            struct['city'] = city_parts[0] + '市'
            remaining = city_parts[1]
            district_parts = remaining.split('区')
            if len(district_parts) > 1:
                struct['district'] = district_parts[0] + '区'
                struct['detail'] = district_parts[1]
            else:
                struct['detail'] = remaining
        else:
            struct['detail'] = remaining
    return struct


def _get_or_create_info(user_id):
    info = UserInfo.query.filter_by(user_id=user_id).first()
    if not info:
        info = UserInfo(user_id=user_id)
        db.session.add(info)
        db.session.commit()
    return info


@bp_user.route('/info', methods=['GET'])
@jwt_required()
def user_info():
    """获取当前登录用户的详细信息"""
    try:
        user = User.query.get(int(get_jwt_identity()))
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'})
        info = _get_or_create_info(user.id)
        address_struct = _parse_address(info.address)
        address_struct['name'] = info.receiver_name
        address_struct['phone'] = info.phone

        return jsonify({
            'code': 200,
            'data': {
                'nickname': user.nickname,
                'avatar': fix_image_url(info.avatar),
                'birthday': info.birthday,
                'gender': info.gender,
                'phone': info.phone,
                'receiverName': info.receiver_name,
                'address': info.address,
                'address_struct': address_struct,
            }
        })
    except Exception as e:
        print(f"获取用户信息错误: {e}")
        return jsonify({'code': 500, 'msg': f'服务器错误: {str(e)}'})


@bp_user.route('/update', methods=['POST'])
@jwt_required()
def update_info():
    """更新生日、性别、收货人、电话、地址"""
    try:
        info = _get_or_create_info(int(get_jwt_identity()))
        data = request.get_json()
        info.birthday = data.get('birthday', '')
        info.gender = data.get('gender', 'secret')
        info.receiver_name = data.get('receiverName', data.get('name', ''))
        info.phone = data.get('phone', '')
        if 'address_struct' in data:
            addr = data['address_struct']
            info.address = f"{addr.get('province', '')}{addr.get('city', '')}{addr.get('district', '')}{addr.get('detail', '')}"
        elif data.get('address'):
            info.address = data['address']
        db.session.commit()
        return jsonify({'code': 200, 'msg': '保存成功'})
    except Exception as e:
        db.session.rollback()
        print(f"更新信息错误: {e}")
        return jsonify({'code': 500, 'msg': '保存失败'})


@bp_user.route('/update-nickname', methods=['POST'])
@jwt_required()
def update_nickname():
    """修改用户昵称"""
    try:
        nickname = request.get_json().get('nickname')
        if not nickname:
            return jsonify({'code': 400, 'msg': '昵称不能为空'})
        user = User.query.get(int(get_jwt_identity()))
        user.nickname = nickname
        db.session.commit()
        return jsonify({'code': 200, 'msg': '修改成功'})
    except Exception as e:
        db.session.rollback()
        print(f"修改昵称错误: {e}")
        return jsonify({'code': 500, 'msg': '修改失败'})


@bp_user.route('/update-avatar', methods=['POST'])
@jwt_required()
def update_avatar():
    """更新用户头像URL"""
    try:
        avatar = request.get_json().get('avatar')
        info = _get_or_create_info(int(get_jwt_identity()))
        info.avatar = fix_image_url(avatar)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '头像更新成功'})
    except Exception as e:
        db.session.rollback()
        print(f"更新头像错误: {e}")
        return jsonify({'code': 500, 'msg': '头像更新失败'})


@bp_user.route('/update-password', methods=['POST'])
@jwt_required()
def update_password():
    """修改密码（需验证原密码）"""
    try:
        data = request.get_json()
        user = User.query.get(int(get_jwt_identity()))
        if decrypt_password(user.password) != data.get('oldPassword'):
            return jsonify({'code': 400, 'msg': '原密码错误'})
        user.password = encrypt_password(data.get('newPassword'))
        db.session.commit()
        return jsonify({'code': 200, 'msg': '修改成功，请重新登录'})
    except Exception as e:
        db.session.rollback()
        print(f"修改密码错误: {e}")
        return jsonify({'code': 500, 'msg': '修改失败'})


@bp_user.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """获取当前用户的所有通知"""
    try:
        notifications = NotificationLog.query.filter_by(user_id=int(get_jwt_identity())) \
            .order_by(NotificationLog.sent_at.desc()).all()
        res = [{
            'id': n.id, 'type': n.type, 'content': n.content, 'status': n.status,
            'goods_id': n.goods_id, 'order_id': n.order_id,
            'goods_name': n.goods.name if n.goods else '',
            'goods_image': fix_image_url(n.goods.images.split(',')[0]) if n.goods and n.goods.images else '',
            'sent_at': n.sent_at.strftime('%Y-%m-%d %H:%M'),
        } for n in notifications]
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取通知错误: {e}")
        return jsonify({'code': 500, 'msg': '获取通知失败'})


@bp_user.route('/notifications/read/<int:notification_id>', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """将通知标记为已读"""
    try:
        notification = NotificationLog.query.filter_by(
            id=notification_id, user_id=int(get_jwt_identity())).first()
        if not notification:
            return jsonify({'code': 404, 'msg': '通知不存在'})
        notification.status = 'read'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已标记为已读'})
    except Exception as e:
        print(f"标记通知错误: {e}")
        return jsonify({'code': 500, 'msg': '操作失败'})


@bp_user.route('/notifications/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """获取未读通知数量"""
    try:
        count = NotificationLog.query.filter_by(
            user_id=int(get_jwt_identity()), status='sent').count()
        return jsonify({'code': 200, 'data': {'count': count}})
    except Exception as e:
        print(f"获取未读数错误: {e}")
        return jsonify({'code': 500, 'msg': '获取失败'})


@bp_merchant.route('/apply', methods=['POST'])
@jwt_required()
def merchant_apply():
    """商家提交入驻申请"""
    try:
        user = User.query.get(get_jwt()['id'])
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404
        if user.role != 'merchant':
            return jsonify({'code': 403, 'msg': '仅商家角色可申请入驻'}), 403
        if user.apply_status == 'pending':
            return jsonify({'code': 400, 'msg': '您的入驻申请正在审核中，请耐心等待'}), 400
        if user.apply_status == 'approved':
            return jsonify({'code': 400, 'msg': '您已通过入驻审核，无需重复申请'}), 400
        user.apply_status = 'pending'
        user.apply_time = datetime.now()
        db.session.commit()
        return jsonify({'code': 200, 'msg': '入驻申请已提交，请等待管理员审核'})
    except Exception as e:
        db.session.rollback()
        print(f"提交入驻申请失败: {e}")
        return jsonify({'code': 500, 'msg': '提交申请失败，请稍后重试'}), 500


@bp_merchant.route('/apply-status', methods=['GET'])
@jwt_required()
def get_merchant_apply_status():
    """获取当前商家的入驻申请状态"""
    try:
        user = User.query.get(get_jwt()['id'])
        if not user:
            return jsonify({'code': 404, 'msg': '用户不存在'}), 404
        return jsonify({
            'code': 200,
            'data': {
                'apply_status': user.apply_status or 'none',
                'apply_time': user.apply_time.strftime('%Y-%m-%d %H:%M:%S') if user.apply_time else None,
            }
        })
    except Exception as e:
        print(f"获取入驻状态失败: {e}")
        return jsonify({'code': 500, 'msg': '获取状态失败'}), 500

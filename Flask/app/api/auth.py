"""认证：注册、登录、登出、验证码、重置密码、管理员登录"""
import smtplib
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required

from ..config import SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER
from ..extensions import db, redis_client
from ..models import User, UserInfo
from ..utils.crypto import decrypt_password, encrypt_password
from ..utils.email import generate_code, send_email

bp = Blueprint('auth', __name__, url_prefix='/api')


@bp.route('/register', methods=['POST'])
def register():
    """校验验证码，创建用户和用户详情"""
    try:
        data = request.get_json()
        nickname = data.get('nickname', '')
        username = data.get('username', '')
        password = data.get('password', '')
        role = data.get('role', '')
        email = data.get('email', '')
        code = data.get('code', '')

        if not all([nickname, username, password, role, email, code]):
            return jsonify({'code': 400, 'msg': '请完善所有信息'})

        stored_code = redis_client.get(f"code:{email}")
        if not stored_code or stored_code != code:
            return jsonify({'code': 400, 'msg': '验证码错误或已过期'})

        if User.query.filter_by(username=username).first():
            return jsonify({'code': 400, 'msg': '用户名已存在'})

        new_user = User(nickname=nickname, username=username,
                        password=encrypt_password(password), role=role)
        db.session.add(new_user)
        db.session.commit()

        # 追踪新注册用户（监控统计）
        try:
            today_key = datetime.now().strftime('%Y%m%d')
            redis_client.incr(f'monitor:new_registrations:{today_key}')
            redis_client.expire(f'monitor:new_registrations:{today_key}', 86400 * 7)
        except Exception:
            pass

        if not new_user.info:
            db.session.add(UserInfo(user_id=new_user.id, email=email))
            db.session.commit()

        redis_client.delete(f"code:{email}")
        return jsonify({'code': 200, 'msg': '注册成功！'})
    except Exception as e:
        db.session.rollback()
        print(f"注册失败：{e}")
        return jsonify({'code': 500, 'msg': '服务器异常，注册失败'})


@bp.route('/login', methods=['POST'])
def login():
    """用户登录，返回 JWT token"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        user = User.query.filter_by(username=username, role=role).first()
        if not user:
            return jsonify({'code': 400, 'msg': '用户名/密码/角色错误'})
        try:
            decrypted = decrypt_password(user.password)
        except Exception:
            return jsonify({'code': 400, 'msg': '用户名/密码/角色错误'})
        if decrypted != password:
            return jsonify({'code': 400, 'msg': '用户名/密码/角色错误'})

        if user.is_banned:
            return jsonify({'code': 403, 'msg': '您的账号已被封禁，请联系管理员'}), 403

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'id': user.id, 'role': role, 'nickname': user.nickname},
        )
        return jsonify({
            'code': 200, 'msg': '登录成功', 'token': access_token,
            'nickname': user.nickname, 'role': role, 'userId': user.id,
        })
    except Exception as e:
        print(f"登录错误: {e}")
        return jsonify({'code': 500, 'msg': f'登录失败: {str(e)}'}), 500


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """登出：将当前 token 加入黑名单"""
    jti = get_jwt()['jti']
    redis_client.setex(f"jwt_blacklist:{jti}", 7 * 24 * 3600, 1)
    return jsonify({'code': 200, 'msg': '登出成功'})


@bp.route('/send_code', methods=['POST'])
def send_code():
    """发送邮箱验证码（用于注册）"""
    data = request.get_json()
    email = data.get('email', '')
    if '@qq.com' not in email:
        return jsonify({'code': 400, 'msg': '请输入有效的QQ邮箱'})
    code = generate_code()
    redis_client.setex(f"code:{email}", 300, code)
    if send_email(email, code):
        return jsonify({'code': 200, 'msg': '验证码已发送到QQ邮箱'})
    return jsonify({'code': 500, 'msg': '验证码发送失败，请检查邮箱'})


@bp.route('/admin/login', methods=['POST'])
def admin_login():
    """管理员专用登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username != 'admin' or password != 'admin':
        return jsonify({'code': 400, 'msg': '账号或密码错误'}), 400
    access_token = create_access_token(
        identity='0',
        additional_claims={'id': 0, 'role': 'admin', 'nickname': '管理员'},
    )
    return jsonify({
        'code': 200, 'msg': '登录成功', 'token': access_token,
        'nickname': '管理员', 'role': 'admin', 'userId': 0,
    })


@bp.route('/reset-password-send', methods=['POST'])
def reset_password_send_code():
    """发送找回密码验证码"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()

        if not username:
            return jsonify({'code': 400, 'msg': '请输入账号'}), 400
        if not email or '@' not in email:
            return jsonify({'code': 400, 'msg': '请输入有效的邮箱'}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'code': 400, 'msg': '账号不存在'}), 400

        user_info = UserInfo.query.filter_by(user_id=user.id).first()
        if not user_info or user_info.email != email:
            return jsonify({'code': 400, 'msg': '账号与邮箱不匹配'}), 400

        code = generate_code()
        redis_client.setex(f"reset_code:{username}:{email}", 300, code)

        msg = MIMEText(f'您的找回密码验证码是：{code}，5分钟内有效，请勿泄露。', 'plain', 'utf-8')
        msg['From'] = f"{Header('次元模仓', 'utf-8').encode()} <{SMTP_USER}>"
        msg['To'] = email
        msg['Subject'] = Header('【次元模仓】找回密码验证码', 'utf-8')

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [email], msg.as_string())

        return jsonify({'code': 200, 'msg': '验证码已发送到邮箱'})
    except Exception as e:
        print(f"发送找回密码验证码失败: {e}")
        return jsonify({'code': 500, 'msg': '验证码发送失败'}), 500


@bp.route('/reset-password-reset', methods=['POST'])
def reset_password():
    """重置密码"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        new_password = data.get('newPassword', '').strip()

        if not all([username, email, code, new_password]):
            return jsonify({'code': 400, 'msg': '请完善所有信息'}), 400
        if len(new_password) < 6:
            return jsonify({'code': 400, 'msg': '密码长度不能少于6位'}), 400

        stored_code = redis_client.get(f"reset_code:{username}:{email}")
        if not stored_code or stored_code != code:
            return jsonify({'code': 400, 'msg': '验证码错误或已过期'}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'code': 400, 'msg': '账号不存在'}), 400

        user_info = UserInfo.query.filter_by(user_id=user.id).first()
        if not user_info or user_info.email != email:
            return jsonify({'code': 400, 'msg': '账号与邮箱不匹配'}), 400

        if decrypt_password(user.password) == new_password:
            return jsonify({'code': 400, 'msg': '新密码不能与当前密码相同'}), 400

        user.password = encrypt_password(new_password)
        redis_client.delete(f"reset_code:{username}:{email}")
        db.session.commit()
        return jsonify({'code': 200, 'msg': '密码重置成功，请登录'})
    except Exception as e:
        db.session.rollback()
        print(f"重置密码失败: {e}")
        return jsonify({'code': 500, 'msg': '重置密码失败'}), 500

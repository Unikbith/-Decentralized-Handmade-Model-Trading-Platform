"""用户账号与用户详情"""
from ..extensions import db


class User(db.Model):
    """用户账号表"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_banned = db.Column(db.Integer, default=0)
    apply_status = db.Column(db.String(20), default='none')  # 入驻申请状态
    apply_time = db.Column(db.DateTime, nullable=True)  # 入驻申请时间
    info = db.relationship('UserInfo', backref='user', uselist=False, cascade='all, delete-orphan')


class UserInfo(db.Model):
    """用户详细信息表"""
    __tablename__ = 'user_info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    avatar = db.Column(db.String(255), default='')
    birthday = db.Column(db.String(20), default='')
    gender = db.Column(db.String(10), default='secret')
    email = db.Column(db.String(100), default='')
    phone = db.Column(db.String(20), default='')
    receiver_name = db.Column(db.String(50), default='')
    address = db.Column(db.Text, default='')

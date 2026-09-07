"""API 蓝图注册中心：集中注册各业务模块蓝图"""
from . import (
    admin, auth, cart, chat, collect, comment, goods, history, order,
    recommend, user,
)

# (蓝图, 模块名) 列表，供 create_app 批量注册
BLUEPRINTS = [
    (auth.bp, 'auth'),
    (goods.bp_upload, 'upload'),
    (goods.bp, 'goods'),
    (cart.bp, 'cart'),
    (collect.bp, 'collect'),
    (history.bp, 'history'),
    (recommend.bp, 'recommend'),
    (chat.bp, 'chat'),
    (comment.bp, 'comment'),
    (order.bp, 'order'),
    (user.bp_user, 'user'),
    (user.bp_merchant, 'merchant'),
    (admin.bp, 'admin'),
]


def register_blueprints(app):
    for bp, name in BLUEPRINTS:
        app.register_blueprint(bp)

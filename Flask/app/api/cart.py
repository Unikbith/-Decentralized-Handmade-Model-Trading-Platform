"""购物车：列表、添加、修改数量、删除、清空"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Cart, Goods
from ..utils.image import fix_image_url

bp = Blueprint('cart', __name__, url_prefix='/api/cart')


@bp.route('/list', methods=['GET'])
@jwt_required()
def cart_list():
    """获取当前用户的购物车列表"""
    try:
        user_id = int(get_jwt_identity())
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        res = []
        for item in cart_items:
            g = item.goods
            res.append({
                'id': item.id, 'goods_id': g.id, 'name': g.name,
                'price': float(g.price),
                'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
                'num': item.num, 'stock': g.stock, 'status': g.status,
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取购物车错误: {e}")
        return jsonify({'code': 500, 'msg': '获取购物车失败'})


@bp.route('/add', methods=['POST'])
@jwt_required()
def cart_add():
    """添加商品到购物车"""
    try:
        user_id = int(get_jwt_identity())
        goods_id = request.get_json().get('goods_id')
        goods = Goods.query.get(goods_id)
        if not goods:
            return jsonify({'code': 404, 'msg': '商品不存在'})
        if goods.status == '下架':
            return jsonify({'code': 400, 'msg': '商品已下架'})
        if goods.stock <= 0:
            return jsonify({'code': 400, 'msg': '商品已售罄'})
        item = Cart.query.filter_by(user_id=user_id, goods_id=goods_id).first()
        if item:
            item.num += 1
        else:
            db.session.add(Cart(user_id=user_id, goods_id=goods_id, num=1))
        db.session.commit()
        return jsonify({'code': 200, 'msg': '加入购物车成功'})
    except Exception as e:
        db.session.rollback()
        print(f"加入购物车错误: {e}")
        return jsonify({'code': 500, 'msg': '加入购物车失败'})


@bp.route('/update', methods=['POST'])
@jwt_required()
def cart_update():
    """修改购物车中商品数量"""
    try:
        data = request.get_json()
        item = Cart.query.get(data['id'])
        if not item:
            return jsonify({'code': 404, 'msg': '购物车项不存在'})
        item.num = data['num']
        db.session.commit()
        return jsonify({'code': 200, 'msg': '修改成功'})
    except Exception as e:
        print(f"修改数量错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '修改失败'})


@bp.route('/delete/<int:id>', methods=['DELETE'])
@jwt_required()
def cart_delete(id):
    """删除购物车中的单个商品"""
    try:
        item = Cart.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        print(f"删除商品错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除失败'})


@bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """清空购物车（支付成功后调用）"""
    try:
        user_id = int(get_jwt_identity())
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({'code': 200, 'msg': '支付成功，购物车已清空'})
    except Exception as e:
        db.session.rollback()
        print(f"清空购物车错误: {e}")
        return jsonify({'code': 500, 'msg': '支付失败，请重试'})

"""收藏：添加、取消、列表、状态检查"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Collect, Goods
from ..utils.image import fix_image_url

bp = Blueprint('collect', __name__, url_prefix='/api/collect')


@bp.route('/add', methods=['POST'])
@jwt_required()
def add_collect():
    """添加收藏"""
    try:
        user_id = int(get_jwt_identity())
        goods_id = request.get_json().get('goods_id')
        if not goods_id:
            return jsonify({'code': 400, 'msg': '商品ID不能为空'}), 400
        goods = Goods.query.get(goods_id)
        if not goods:
            return jsonify({'code': 404, 'msg': '商品不存在'}), 404
        if Collect.query.filter_by(user_id=user_id, goods_id=goods_id).first():
            return jsonify({'code': 400, 'msg': '已收藏该商品'}), 400
        db.session.add(Collect(user_id=user_id, goods_id=goods_id))
        db.session.commit()
        return jsonify({'code': 200, 'msg': '收藏成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f'添加收藏失败: {e}')
        return jsonify({'code': 500, 'msg': '收藏失败'}), 500


@bp.route('/delete', methods=['POST'])
@jwt_required()
def delete_collect():
    """取消收藏"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        collect_id = data.get('id')
        goods_id = data.get('goods_id')
        if not collect_id and not goods_id:
            return jsonify({'code': 400, 'msg': '参数错误'}), 400
        collect = (Collect.query.get(collect_id) if collect_id
                   else Collect.query.filter_by(user_id=user_id, goods_id=goods_id).first())
        if not collect:
            return jsonify({'code': 404, 'msg': '收藏记录不存在'}), 404
        db.session.delete(collect)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '取消收藏成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f'取消收藏失败: {e}')
        return jsonify({'code': 500, 'msg': '操作失败'}), 500


@bp.route('/list', methods=['GET'])
@jwt_required()
def get_collect_list():
    """获取当前用户的收藏列表"""
    try:
        user_id = int(get_jwt_identity())
        collects = Collect.query.filter_by(user_id=user_id).order_by(Collect.created_at.desc()).all()
        res = []
        for item in collects:
            g = item.goods
            res.append({
                'id': item.id, 'goods_id': g.id, 'name': g.name,
                'price': float(g.price),
                'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return jsonify({'code': 200, 'data': res}), 200
    except Exception as e:
        print(f'获取收藏列表失败: {e}')
        return jsonify({'code': 500, 'msg': '获取失败'}), 500


@bp.route('/check', methods=['GET'])
@jwt_required()
def check_collect():
    """检查当前用户是否收藏了某商品"""
    try:
        user_id = int(get_jwt_identity())
        goods_id = request.args.get('goods_id')
        if not goods_id:
            return jsonify({'code': 400, 'msg': '商品ID不能为空'}), 400
        exist = Collect.query.filter_by(user_id=user_id, goods_id=goods_id).first()
        return jsonify({'code': 200, 'data': {'is_collected': exist is not None}}), 200
    except Exception as e:
        print(f'检查收藏状态失败: {e}')
        return jsonify({'code': 500, 'msg': '检查失败'}), 500

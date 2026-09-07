"""浏览历史：添加、列表、删除单条、清空"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Goods, History
from ..utils.image import fix_image_url

bp = Blueprint('history', __name__, url_prefix='/api/user/history')


@bp.route('/add', methods=['POST'])
@jwt_required()
def add_history():
    """手动添加浏览记录"""
    try:
        user_id = int(get_jwt_identity())
        goods_id = request.get_json().get('goods_id')
        if not goods_id:
            return jsonify({'code': 400, 'msg': '商品ID不能为空'})
        if not Goods.query.get(goods_id):
            return jsonify({'code': 404, 'msg': '商品不存在'})
        existing = History.query.filter_by(user_id=user_id, goods_id=goods_id).first()
        if existing:
            existing.browse_time = datetime.now()
        else:
            db.session.add(History(user_id=user_id, goods_id=goods_id))
        db.session.commit()
        return jsonify({'code': 200, 'msg': '足迹记录成功'})
    except Exception as e:
        print(f"记录足迹错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '记录足迹失败'})


@bp.route('', methods=['GET'])
@jwt_required()
def get_history():
    """获取当前用户的浏览历史列表"""
    try:
        user_id = int(get_jwt_identity())
        history_list = History.query.filter_by(user_id=user_id).order_by(History.browse_time.desc()).all()
        res = []
        for item in history_list:
            g = item.goods
            res.append({
                'id': item.id, 'goodsId': g.id, 'name': g.name,
                'price': float(g.price),
                'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
                'browseTime': item.browse_time.strftime('%Y-%m-%d %H:%M'),
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取足迹错误: {e}")
        return jsonify({'code': 500, 'msg': '获取足迹失败'})


@bp.route('/delete', methods=['POST'])
@jwt_required()
def delete_history():
    """删除单条浏览记录"""
    try:
        history_id = request.get_json().get('id')
        history = History.query.get(history_id)
        if not history:
            return jsonify({'code': 404, 'msg': '足迹不存在'})
        db.session.delete(history)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        print(f"删除足迹错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除失败'})


@bp.route('/clear', methods=['POST'])
@jwt_required()
def clear_history():
    """清空所有浏览记录"""
    try:
        user_id = int(get_jwt_identity())
        History.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({'code': 200, 'msg': '清空成功'})
    except Exception as e:
        print(f"清空足迹错误: {e}")
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '清空失败'})

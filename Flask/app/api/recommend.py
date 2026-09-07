"""个性化推荐：用户行为记录 + 猜你喜欢"""
import random

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import redis_client
from ..models import Goods
from ..utils.image import fix_image_url

bp = Blueprint('recommend', __name__, url_prefix='/api')


# 行为类型 → 权重
BEHAVIOR_WEIGHTS = {'view': 1, 'collect': 3, 'purchase': 5}


@bp.route('/user/behavior', methods=['POST'])
@jwt_required()
def record_user_behavior():
    """记录用户对商品各维度的行为权重（浏览=1，收藏=3，购买=5）"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        goods_id = data.get('goods_id')
        behavior_type = data.get('type', 'view')
        if not goods_id:
            return jsonify({'code': 400, 'msg': '商品ID不能为空'})

        goods = Goods.query.get(goods_id)
        if not goods:
            return jsonify({'code': 404, 'msg': '商品不存在'})

        weight = BEHAVIOR_WEIGHTS.get(behavior_type, 1)
        pipe = redis_client.pipeline()
        for field, value in (('ip', goods.ip), ('character', goods.charactername),
                             ('category', goods.category), ('brand', goods.brand)):
            if value:
                pipe.zincrby(f'user_pref:{user_id}:{field}', weight, value)
        pipe.execute()
        return jsonify({'code': 200, 'msg': '记录成功'})
    except Exception as e:
        print(f"记录用户行为错误: {e}")
        return jsonify({'code': 500, 'msg': '记录失败'})


@bp.route('/recommend/personal', methods=['GET'])
@jwt_required()
def get_personal_recommend():
    """有权重记录时，偏好相关商品概率更高，但所有商品都有机会出现"""
    try:
        user_id = int(get_jwt_identity())
        all_goods = Goods.query.filter(Goods.status != '下架').all()
        if not all_goods:
            return jsonify({'code': 200, 'data': []})

        # 聚合用户偏好权重
        pref_weights = {}
        for key in ('ip', 'character', 'category'):
            for k, score in redis_client.zrevrange(f'user_pref:{user_id}:{key}', 0, 5, withscores=True):
                if k:
                    keyword = k.decode() if isinstance(k, bytes) else k
                    pref_weights[keyword] = pref_weights.get(keyword, 0) + score

        # 为每个商品计算加权分数
        goods_scores = []
        for g in all_goods:
            score = 1  # 基础分
            if g.ip and g.ip in pref_weights:
                score += pref_weights[g.ip] * 2
            if g.charactername and g.charactername in pref_weights:
                score += pref_weights[g.charactername] * 2
            if g.category and g.category in pref_weights:
                score += pref_weights[g.category]
            if g.brand and g.brand in pref_weights:
                score += pref_weights[g.brand]
            for keyword, weight in pref_weights.items():
                if keyword.lower() in g.name.lower():
                    score += weight * 0.5
            goods_scores.append((g, score))

        # 按分数加权随机选择
        total_score = sum(s for _, s in goods_scores)
        rand_val = random.random() * total_score
        cumulative = 0
        selected = goods_scores[0][0]
        for g, score in goods_scores:
            cumulative += score
            if rand_val <= cumulative:
                selected = g
                break

        goods_data = {
            'id': selected.id, 'name': selected.name, 'price': float(selected.price),
            'image': fix_image_url(selected.images.split(',')[0]) if selected.images else '',
            'ip': selected.ip, 'charactername': selected.charactername,
        }
        return jsonify({'code': 200, 'data': [goods_data]})
    except Exception as e:
        print(f"猜你喜欢错误: {e}")
        return jsonify({'code': 500, 'msg': '获取推荐失败'})

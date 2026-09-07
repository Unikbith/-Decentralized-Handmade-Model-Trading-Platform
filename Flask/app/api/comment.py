"""商品评论：列表、发表、删除"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Comment, Goods
from ..utils.image import fix_image_url

bp = Blueprint('comment', __name__, url_prefix='/api/comments')


@bp.route('/list/<int:goods_id>', methods=['GET'])
def get_comments_list(goods_id):
    """获取某商品的所有评论"""
    try:
        comments = Comment.query.filter_by(goods_id=goods_id).order_by(Comment.created_at.desc()).all()
        res = []
        for c in comments:
            user_info = c.user.info if c.user.info else None
            res.append({
                'id': c.id, 'user_id': c.user_id, 'username': c.user.nickname,
                'avatar': fix_image_url(user_info.avatar) if user_info else '',
                'content': c.content, 'time': c.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return jsonify({'code': 200, 'data': res})
    except Exception as e:
        print(f"获取评论失败: {e}")
        return jsonify({'code': 500, 'msg': '获取评论失败'})


@bp.route('/add', methods=['POST'])
@jwt_required()
def add_comment():
    """发表评论"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        goods_id = data.get('goods_id')
        content = data.get('content', '').strip()
        if not goods_id or not content:
            return jsonify({'code': 400, 'msg': '商品ID和评论内容不能为空'})
        if not Goods.query.get(goods_id):
            return jsonify({'code': 404, 'msg': '商品不存在'})
        db.session.add(Comment(user_id=user_id, goods_id=goods_id, content=content))
        db.session.commit()
        return jsonify({'code': 200, 'msg': '评论成功'})
    except Exception as e:
        db.session.rollback()
        print(f"发表评论失败: {e}")
        return jsonify({'code': 500, 'msg': '发表评论失败'})


@bp.route('/delete/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """删除自己的评论"""
    try:
        current_user_id = int(get_jwt_identity())
        comment = Comment.query.get_or_404(comment_id)
        if str(comment.user_id) != str(current_user_id):
            return jsonify({'code': 403, 'msg': '无权限删除他人评论'}), 403
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '评论删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"删除评论失败: {e}")
        return jsonify({'code': 500, 'msg': '删除失败'}), 500

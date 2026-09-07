"""AI 客服对话接口"""
from flask import Blueprint, jsonify, request

from ..services import ai_service

bp = Blueprint('chat', __name__, url_prefix='/api')


@bp.route('/chat', methods=['POST'])
def chat_with_ai():
    """AI 客服：意图分析 + 对话回复，有购买意图时推荐商品"""
    reply, goods_data, error_msg = ai_service.handle_chat(request.get_json())
    if error_msg:
        return jsonify({'code': 400, 'msg': error_msg})
    return jsonify({'code': 200, 'data': {'reply': reply, 'goods': goods_data}})

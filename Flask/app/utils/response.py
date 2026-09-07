"""统一 API 响应格式（保持与历史接口兼容的 msg 字段）"""
from flask import jsonify


def success_response(data=None, message='操作成功'):
    """兼容历史 app.utils 的成功响应"""
    return jsonify({'code': 200, 'message': message, 'data': data})


def error_response(message='操作失败', status_code=400):
    """兼容历史 app.utils 的失败响应"""
    return jsonify({'code': status_code, 'message': message, 'data': None}), status_code

from flask import jsonify

def success_response(data=None, message="操作成功"):
    response = {
        'success': True,
        'message': message,
        'data': data
    }
    return jsonify(response)

def error_response(message="操作失败", status_code=400):
    response = {
        'success': False,
        'message': message,
        'data': None
    }
    return jsonify(response), status_code
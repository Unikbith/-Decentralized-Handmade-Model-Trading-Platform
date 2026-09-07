"""通用装饰器：管理员权限校验、Redis 结果缓存"""
import json
from functools import wraps

from flask import jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from ..extensions import redis_client


def admin_required(fn):
    """管理员权限装饰器：要求 JWT 中 role 为 admin"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'code': 403, 'msg': '无管理员权限'}), 403
        return fn(*args, **kwargs)
    return wrapper


def cache(key_prefix, expire=3600):
    """基于 Redis 缓存 GET 请求结果，仅缓存 code==200 的响应"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:default"
            if args:
                cache_key = f"{key_prefix}:{args[0]}"
            elif kwargs.get('id'):
                cache_key = f"{key_prefix}:{kwargs.get('id')}"

            cached_data = redis_client.get(cache_key)
            if cached_data:
                return jsonify({'code': 200, 'data': json.loads(cached_data)})

            result = func(*args, **kwargs)
            try:
                if hasattr(result, 'json') and result.json['code'] == 200:
                    redis_client.setex(cache_key, expire, json.dumps(result.json['data'], ensure_ascii=False))
            except Exception as e:
                print(f"缓存写入失败: {e}")
            return result
        return wrapper
    return decorator

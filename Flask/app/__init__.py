"""Flask 应用工厂：组装配置、扩展、蓝图、钩子与前端静态服务"""
import os

from flask import send_from_directory
from flask_cors import CORS

from . import config, hooks, scheduler, tasks
from .api import register_blueprints
from .extensions import celery, db, es_client, jwt, scheduler as sched_ext


def _init_extensions(app):
    db.init_app(app)
    jwt.init_app(app)
    sched_ext.init_app(app)
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
    )


def _init_cors(app):
    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": [
            "https://localhost",
            "https://127.0.0.1",
            "https://animemodelshop",
        ]}},
        methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )


def _init_indexes(app):
    """初始化数据库表与 ES 索引"""
    with app.app_context():
        db.create_all()
        if not es_client.indices.exists(index="goods_index"):
            es_client.indices.create(index="goods_index", body={
                "mappings": {
                    "properties": {
                        "name": {"type": "text"},
                        "price": {"type": "float"},
                        "stock": {"type": "integer"},
                        "image": {"type": "keyword"},
                        "description": {"type": "text"},
                        "category": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "brand": {"type": "keyword"},
                        "ip": {"type": "keyword"},
                        "charactername": {"type": "keyword"},
                        "merchant_name": {"type": "keyword"},
                    }
                }
            })


def _serve_frontend(app):
    """提供 Vue 前端页面（history 路由模式支持）"""
    dist_dir = str(config.DIST_DIR)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and os.path.exists(os.path.join(dist_dir, path)):
            return send_from_directory(dist_dir, path)
        return send_from_directory(dist_dir, 'index.html')


def create_app():
    app = Flask(__name__)
    app.config.from_object(config.Config)

    _init_cors(app)
    _init_extensions(app)
    register_blueprints(app)
    hooks.register_hooks(app)

    # Celery 任务绑定 Flask 实例，以获取应用上下文
    tasks.bind_app(app)

    _init_indexes(app)
    _serve_frontend(app)
    scheduler.start_scheduler(app)
    return app

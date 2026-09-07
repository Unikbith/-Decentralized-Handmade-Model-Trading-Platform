"""全局配置：所有服务地址、密钥、应用参数集中管理"""
from datetime import timedelta
from pathlib import Path

# 项目根目录（Flask/）
BASE_DIR = Path(__file__).resolve().parents[1]


class Config:
    """Flask 应用配置"""
    # ---- 数据库 ----
    SQLALCHEMY_DATABASE_URI = ''  # 例: mysql+pymysql://user:pass@host:3306/db
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 50
    SQLALCHEMY_MAX_OVERFLOW = 100
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_ECHO = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 上传文件最大 50MB

    # ---- JWT ----
    JWT_SECRET_KEY = 'vue_jwt'  # TODO: 生产环境请通过环境变量注入
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_ALGORITHM = 'HS256'

    # ---- Celery ----
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/1'
    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/1'

    # ---- 定时任务 ----
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'


# ===================== 外部服务 =====================

# QQ 邮箱 SMTP
SMTP_HOST = 'smtp.qq.com'
SMTP_PORT = 587
SMTP_USER = ''          # 发件邮箱
SMTP_PASSWORD = ''      # 邮箱授权码

# 智谱 AI
ZHIPU_API_KEY = ''      # 智谱AI API Key
ZHIPU_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'

# Redis
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_DB = 0

# MinIO 对象存储（默认本地开发凭据）
MINIO_ENDPOINT = '127.0.0.1:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
MINIO_BUCKET = 'goods-images'

# Elasticsearch
ES_HOST = '127.0.0.1'
ES_PORT = 9200

# 前端构建产物目录（Flask/dist）
DIST_DIR = BASE_DIR / 'dist'

"""第三方扩展实例：集中创建后供各模块导入，避免循环依赖"""
import redis
from celery import Celery
from elasticsearch import Elasticsearch
from flask_apscheduler import APScheduler
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from minio import Minio

from . import config

db = SQLAlchemy()
jwt = JWTManager()
scheduler = APScheduler()

redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    decode_responses=True,
)

minio_client = Minio(
    config.MINIO_ENDPOINT,
    access_key=config.MINIO_ACCESS_KEY,
    secret_key=config.MINIO_SECRET_KEY,
    secure=False,
)

es_client = Elasticsearch(f"http://{config.ES_HOST}:{config.ES_PORT}", timeout=30)

celery = Celery('app')

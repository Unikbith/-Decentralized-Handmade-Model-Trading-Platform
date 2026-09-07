# Flask 后端（工程化重构版）

基于 **Flask + SQLAlchemy + Redis + Elasticsearch + MinIO + Celery + APScheduler** 的电商后端，
由原单体 `app.py` 重构为分层工程结构，接口路径与响应格式完全兼容原版。

## 目录结构

```
Flask/
├── run.py                  # 入口：python run.py 启动
├── requirements.txt        # 依赖清单
├── .gitignore
├── app/
│   ├── __init__.py         # 应用工厂 create_app()
│   ├── config.py           # 全局配置（密钥留空占位，勿提交真实凭据）
│   ├── extensions.py       # 第三方扩展实例（db/jwt/redis/es/minio/celery/scheduler）
│   ├── hooks.py            # 全局请求钩子（请求监控）与 JWT 回调
│   ├── scheduler.py        # APScheduler 定时任务（超时订单/关键词快照/订单快照）
│   ├── tasks.py            # Celery 异步任务（ES 同步/各类通知）
│   ├── api/                # 路由蓝图层：只做参数解析与响应
│   │   ├── __init__.py     # 蓝图注册中心
│   │   ├── auth.py         # 认证：注册/登录/登出/验证码/重置密码
│   │   ├── goods.py        # 商品：上传/发布/列表/搜索/详情/商家管理
│   │   ├── cart.py         # 购物车
│   │   ├── collect.py      # 收藏
│   │   ├── history.py      # 浏览历史
│   │   ├── recommend.py    # 行为记录 + 个性化推荐
│   │   ├── comment.py      # 评论
│   │   ├── chat.py         # AI 客服
│   │   ├── order.py        # 订单 + 售后
│   │   ├── user.py         # 用户中心 + 商家申请 + 通知
│   │   └── admin.py        # 管理后台 + 监控看板
│   ├── models/             # 数据模型（13 张表，按业务域拆分）
│   │   ├── user.py         # users / user_info
│   │   ├── goods.py        # goods / cart / collect / history / comment
│   │   ├── order.py        # orders / order_items / return_requests
│   │   ├── notification.py # notification_logs
│   │   └── snapshot.py     # 搜索关键词 / 订单状态快照
│   ├── services/           # 业务服务层：可复用的核心逻辑
│   │   ├── order_service.py
│   │   ├── stock_service.py
│   │   ├── es_service.py
│   │   └── ai_service.py
│   └── utils/              # 工具层
│       ├── crypto.py       # 密码加解密（Fernet）
│       ├── decorators.py   # admin_required / cache
│       ├── email.py        # 邮箱验证码
│       ├── image.py        # 图片 URL 处理
│       ├── lock.py         # Redis 分布式锁
│       └── response.py     # 统一响应
```

## 分层约定

| 层 | 职责 | 依赖方向 |
|---|---|---|
| `api/` | HTTP 入参解析、鉴权、响应输出 | 依赖 services/models |
| `services/` | 核心业务逻辑（订单/库存/ES/AI），无 Flask 上下文耦合 | 依赖 models |
| `models/` | ORM 数据表定义 | 依赖 extensions |
| `utils/` | 无状态工具函数/装饰器 | 依赖 extensions |
| `tasks.py` | Celery 异步任务 | 依赖 services |
| `scheduler.py` | 定时任务 | 依赖 services |

## 启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境（app/config.py）
#    - SQLALCHEMY_DATABASE_URI：MySQL 连接串
#    - SMTP_USER / SMTP_PASSWORD：QQ 邮箱授权码
#    - ZHIPU_API_KEY：智谱 AI Key
#    - 本地需运行 Redis / MinIO / Elasticsearch

# 3. 启动
python run.py
```

## 安全说明

- `secret.key`、`.env` 已加入 `.gitignore`，密钥类配置在 `config.py` 中留空占位，请通过环境变量或本地配置注入。
- 上传接口经 Nginx HTTPS 代理，MinIO 内部地址由 `utils/image.py::fix_image_url` 转为相对路径。

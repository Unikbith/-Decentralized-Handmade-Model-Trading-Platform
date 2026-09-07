# 次元模仓 · 分布式手办模型交易平台

基于 **Vue3 + Flask** 的全栈电商交易平台，集成 MySQL、Redis、Elasticsearch、MinIO、Celery、APScheduler 等中间件，并接入智谱 GLM-4.5-Air 大模型实现 AI 智能客服与个性化推荐。

> 开发周期：2025.10 – 2026.05
> ~~第一次做的比较大且全面的项目，过程中解决了跨域、JWT Token 过期处理、库存超卖、路由权限守卫等问题，也让我认识到自己的不足，还需要更多实际动手的开发经验~~

---

## 功能特性

- **前台商城**：商品浏览、多维度筛选、全文搜索、商品详情、购物车、订单结算、确认支付、收藏、评论、浏览历史
- **个性化推荐（猜你喜欢）**：记录用户行为（IP/角色/分类浏览）建立 Redis 权重，加权随机推荐商品
- **AI 智能客服**：智谱 GLM-4.5-Air 意图分析，识别购买意图并提取关键词，联动商品搜索与推荐
- **三级角色体系**：用户 / 商家 / 管理员，路由级权限守卫
- **商家中心**：商品发布与上下架管理、订单处理、售后审核
- **管理后台**：用户 / 商品 / 订单 / 售后全量管理，ECharts 数据可视化监控看板（订单趋势、分类分布、关键词热度等）
- **异步与定时**：Celery 异步任务（ES 同步、通知推送），APScheduler 定时取消超时订单、快照统计

---

## 技术栈

### 前端（`Vue/`）

| 分类 | 技术 |
|---|---|
| 框架 | Vue 3（Composition API）+ Vite 7 |
| 状态管理 | Pinia |
| 路由 | Vue Router（路由懒加载 + 三级权限守卫） |
| UI | Element Plus + unplugin-vue-components 按需引入 |
| 数据可视化 | ECharts 6 |
| HTTP | Axios（请求/响应拦截器，JWT 鉴权与 401 自动跳转） |
| 其他 | Swiper 轮播、qrcode.vue 扫码支付、v-region 地区选择 |

### 后端（`Flask/`）

| 分类 | 技术 |
|---|---|
| 框架 | Flask 2.3 + SQLAlchemy ORM（13 张数据表） |
| 认证 | JWT 双 Token（access + refresh） |
| 缓存 / 锁 | Redis（热点缓存、用户行为权重、分布式锁防超卖） |
| 搜索 | Elasticsearch 8 + ik 中文分词 |
| 对象存储 | MinIO（商品图片） |
| 异步任务 | Celery 5.3 |
| 定时任务 | APScheduler |
| AI | 智谱 GLM-4.5-Air（意图分析 / 关键词提取） |
| 密码安全 | bcrypt + Fernet 加密 |

---

## 项目结构

```
├── Flask/                  # 后端（工程化分层，由单体 app.py 重构而来）
│   ├── run.py              # 入口
│   └── app/
│       ├── config.py       # 配置（密钥留空占位）
│       ├── extensions.py   # 扩展实例（db/jwt/redis/es/minio/celery/scheduler）
│       ├── hooks.py        # 全局请求钩子与 JWT 回调
│       ├── scheduler.py    # 定时任务
│       ├── tasks.py        # Celery 异步任务
│       ├── api/            # 路由蓝图（12 个模块）
│       ├── models/         # ORM 模型（按业务域拆分）
│       ├── services/       # 业务服务层（订单/库存/ES/AI）
│       └── utils/          # 工具（加密/装饰器/邮箱/图片/锁/响应）
│
└── Vue/                    # 前端
    └── src/
        ├── api/            # Axios 封装
        ├── components/     # 通用组件（商品卡片/分页/导航栏等）
        ├── config/         # 环境配置（API 地址/支付网关）
        ├── router/         # 路由与权限守卫
        ├── views/          # 页面视图
        │   ├── admin/      # 管理后台
        │   └── base/       # 基础字典管理
        └── utils/          # 通用工具
```

---

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 20.19+ / 22.12+
- MySQL 8.0+、Redis、Elasticsearch 8（含 ik 分词器）、MinIO

### 1. 启动后端

```bash
cd Flask

# 安装依赖
pip install -r requirements.txt

# 配置 app/config.py：数据库连接串、SMTP 邮箱授权码、智谱 API Key、
# 以及 Redis / MinIO / Elasticsearch 服务地址

# 启动服务（create_app 首次运行自动建表）
python run.py     # 默认 http://127.0.0.1:5000
```

### 2. 启动前端

```bash
cd Vue

npm install
npm run dev       # 开发服务器，默认 http://localhost:5173
```

> 前端 `src/config/index.js` 中 `API_BASE_URL` 留空表示走同源请求，由部署层（Nginx）反向代理 `/api` 到后端；支付网关地址为占位，上线前请替换为实际支付域名。

### 3. 生产部署

使用仓库内 `Flask/nginx_https.conf` 配置 Nginx：静态资源托管 `Vue/dist`，`/api` 反向代理到后端服务，并启用 HTTPS。

---

## 架构与设计要点

- **JWT 双 Token**：短期 access token + 长期 refresh token，无感续期，401 自动刷新
- **库存防超卖**：Redis 预扣库存 + Lua/分布式锁保证原子性，下单失败自动回滚
- **中文搜索**：Elasticsearch + ik 分词器，商品名称/IP/角色/分类多字段检索
- **热点缓存**：商品列表、详情等热点数据 Redis 缓存，失效主动刷新
- **异步解耦**：ES 索引同步、订单超时取消、站内通知均走 Celery 异步队列
- **定时任务**：APScheduler 每分钟处理超时订单，定期生成搜索关键词与订单状态快照
- **AI 推荐**：意图分析提取关键词 → Redis 多字段加权 → 加权随机推荐

---

## API 概览

后端共 80+ 个接口，按蓝图模块组织（前缀 `/api`）：

| 模块 | 主要接口 |
|---|---|
| 认证 auth | `POST /auth/register` `POST /auth/login` `POST /auth/logout` `POST /auth/send_code` `POST /auth/reset_password` |
| 商品 goods | `POST /goods/publish` `GET /goods/list` `GET /goods/search` `GET /goods/<id>` `POST /upload/image` |
| 购物车 cart | `GET /cart/list` `POST /cart/add` `PUT /cart/update` `DELETE /cart/remove` |
| 订单 order | `POST /order/create` `GET /order/list` `POST /order/cancel` `POST /order/confirm` `POST /order/ship` |
| 收藏/历史 | `POST /collect/add` `GET /collect/list` `GET /history/list` |
| 评论 comment | `GET /comment/list` `POST /comment/add` |
| 推荐 recommend | `GET /recommend/personal` `POST /recommend/record` |
| AI 客服 chat | `POST /chat/chat` |
| 管理 admin | `GET /admin/overview` `GET /admin/orders` `GET /admin/users` `PUT /admin/goods/<id>` |

完整接口清单见各蓝图文件 `Flask/app/api/*.py`。

---

## 安全说明

- `secret.key`、`.env`、密钥类配置均已加入 `.gitignore`，`config.py` 中密钥留空占位，请通过环境变量或本地配置注入，切勿提交真实凭据
- 生产环境请使用 Nginx HTTPS，上传接口经反向代理，MinIO 内部地址由 `utils/image.py` 转为相对路径

---

## 页面预览

**AI 客服**：集成了智谱 GLM-4.5-Air 大模型进行意图分析

<img width="auto" height="300" alt="image" src="https://github.com/user-attachments/assets/0c49256d-e1b7-4a01-bb4e-dbc0a7cdb21d" />
<img width="1033" height="120" alt="image" src="https://github.com/user-attachments/assets/b246258f-7e10-4b1d-8f05-b8b90c69a3c8" />

**信息可视化**：使用 ECharts 对数据进行可视化展示

<img width="1891" height="1641" alt="image" src="https://github.com/user-attachments/assets/e976ae70-78c8-406a-94ba-1ab06e580396" />

**个性化推荐（猜你喜欢）**：记录用户行为进行权重计算，推送权重值高的商品卡片

<img width="1854" height="929" alt="image" src="https://github.com/user-attachments/assets/a0b4517c-6998-4ac3-a697-65f3531900a8" />

**平台首页**

<img width="1895" height="2425" alt="image" src="https://github.com/user-attachments/assets/ab09f896-9c38-4b31-9cb2-21f2b07e3a51" />

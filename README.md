# 分布式手办模型交易平台  
## 基于Vue3+Flask的全栈电商交易平台，使用了MySQL、Elasticsearch、MinIO、Celery、Redis等中间件，接入了智谱的GLM-4.5-Air大模型，能够实现AI智能客服的功能。
### 2025.10-2026.05
~~**也算是自己第一次做的比较大且全面的项目，开发过程中遇到了很多问题比如说（跨域问题、JWT Token过期处理、库存超卖、路由权限守卫等），也让我认识到了自己的不足，还需要更多实际动手的开发经验**~~
***  
- 前端：Vue3 Composition API + Vite构建，Pinia状态管理，Vue Router实现路由懒加载及三级权限守卫（用户/商家/管理员），Element Plus组件库统一UI风格，Axios封装请求拦截器统一处理JWT鉴权与401自动跳转，ECharts完成管理后台数据可视化仪表盘
- 后端：Flask + SQLAlchemy ORM设计13张数据表，JWT双Token认证体系，Redis缓存热点数据并实现分布式锁保障库存扣减原子性，Elasticsearch + ik分词器构建商品中文搜索引擎，MinIO对象存储管理商品图片，Celery异步任务队列，APScheduler定时取消超时订单
- AI应用：接入智谱GLM-4.5-Air大模型实现智能客服，AI自动识别用户购买意图并提取关键词，结合Redis多字段加权索引精准推荐商品，提升搜索转化效率
- 自主学习：独立完成前后端全栈开发，从零搭建Vue3工程化项目，自学并集成Redis、Elasticsearch、MinIO、Celery等中间件，通过AI辅助编程加速开发效率
***  
**AI客服** 集成了智谱GLM-4.5-Air大模型进行意图分析
***  
<img width="auto" height="300" alt="image" src="https://github.com/user-attachments/assets/0c49256d-e1b7-4a01-bb4e-dbc0a7cdb21d" />  
<img width="1033" height="120" alt="image" src="https://github.com/user-attachments/assets/b246258f-7e10-4b1d-8f05-b8b90c69a3c8" />  
  
***
**信息可视化**  使用EChart插件对数据进行可视化展示
***  
<img width="1891" height="1641" alt="image" src="https://github.com/user-attachments/assets/e976ae70-78c8-406a-94ba-1ab06e580396" />

  
***  
**个性化推荐（猜你喜欢）**  记录用户行为来进行权重计算推送权重值高的商品卡片
<img width="1854" height="929" alt="image" src="https://github.com/user-attachments/assets/a0b4517c-6998-4ac3-a697-65f3531900a8" />  

***
**平台首页**  
***  
<img width="1895" height="2425" alt="image" src="https://github.com/user-attachments/assets/ab09f896-9c38-4b31-9cb2-21f2b07e3a51" />    

***








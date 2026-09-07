<template>
  <footer class="site-footer">
    <div class="footer-container">
      <div class="footer-content">

        <div class="footer-section">
          <h4 class="section-title">关于我们</h4>
          <ul class="link-list">
            <li><a href="#">关于animemodelshop</a></li>
            <li><a href="#">企业信息</a></li>
            <li><a href="#">网站地图</a></li>
          </ul>
        </div>

        <div class="footer-section">
          <h4 class="section-title">快速链接</h4>
          <ul class="link-list">
            <li><router-link to="/">首页</router-link></li>
            <li><router-link to="/goods">商品列表</router-link></li>
            <li><router-link to="/cart">购物车</router-link></li>
            <li><router-link to="/publish">发布商品</router-link></li>
          </ul>
        </div>

        <div class="footer-section">
          <h4 class="section-title">帮助中心</h4>
          <ul class="link-list">
            <li><a href="#">购买指南</a></li>
            <li><a href="#">配送说明</a></li>
            <li><a href="#">售后政策</a></li>
            <li><a href="#">常见问题</a></li>
          </ul>
        </div>

        <div class="footer-section">
          <h4 class="section-title">联系我们</h4>
          <ul class="contact-list">
            <li>
              <span class="contact-text">uid_6843@163.com</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <p class="copyright">© 2024 AnimeModelShop.</p>
        <div class="footer-links">
          <a href="#">隐私政策</a>
          <span class="separator">|</span>
          <a href="#">用户协议</a>
          <span class="separator">|</span>
          <a href="#">关于我们</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
</script>

<style scoped>
/* ===== 页脚主体 ===== */
.site-footer {
  background: linear-gradient(180deg, #f8fafc 0%, #e8eef5 100%);
  color: #4a5568;
  padding: 48px 0 24px;
  margin-top: auto;
  border-top: 1px solid #dae1e8;
}

.footer-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 40px;
}

/* ===== 页脚内容区域 ===== */
.footer-content {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 40px;
  padding-bottom: 32px;
  border-bottom: 1px solid #dae1e8;
}

.footer-section {
  min-width: 0;
}

/* ===== 通用标题样式 ===== */
.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: #2d3748;
}

/* ===== 链接列表 ===== */
.link-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.link-list li {
  margin-bottom: 10px;
}

.link-list a,
.link-list router-link {
  color: #718096;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s ease;
}

.link-list a:hover,
.link-list router-link:hover {
  color: #fb7299;
  padding-left: 4px;
}

/* ===== 联系方式 ===== */
.contact-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.contact-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  color: #718096;
  font-size: 14px;
}

.contact-text {
  color: #718096;
  font-size: 14px;
}

/* ===== 底部版权区 ===== */
.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.copyright {
  margin: 0;
  color: #a0aec0;
  font-size: 13px;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-links a {
  color: #a0aec0;
  text-decoration: none;
  font-size: 13px;
  transition: color 0.3s ease;
}

.footer-links a:hover {
  color: #fb7299;
}

.footer-links .separator {
  color: #d0d7e0;
  font-size: 12px;
}

/* ===== 响应式适配 ===== */
@media (max-width: 1200px) {
  .footer-content {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .site-footer {
    padding: 32px 0 20px;
  }

  .footer-container {
    padding: 0 20px;
  }

  .footer-content {
    grid-template-columns: 1fr;
    gap: 28px;
  }

  .footer-bottom {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .site-footer {
    padding: 24px 0 16px;
  }

  .footer-container {
    padding: 0 16px;
  }

  .section-title {
    font-size: 15px;
  }
}
</style>
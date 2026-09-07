<template>
  <el-config-provider :locale="zhCn">
    <div v-if="!$route.meta.noGlobalLayout" class="app-container">
      <Navbar />
      <main class="content">
        <router-view />
      </main>
      <Footer />
    </div>

    <router-view v-else />
  </el-config-provider>
</template>

<script setup>
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import Navbar from './components/navbar.vue';
import Footer from './components/Footer.vue';
</script>

<style>
/* 应用容器布局 */
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding-top: 60px;
  background-color: aliceblue;
}

/* 内容区域 */
.content {
  flex: 1;
  margin: 20px auto 0;
  width: 100%;
  max-width: 1500px;
  border-radius: 16px;
  padding: 5px;
  box-sizing: border-box;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .app-container {
    padding-top: 50px;
  }
  .content {
    margin: 10px auto 0;
    padding: 2px;
    border-radius: 8px;
  }
}
</style>

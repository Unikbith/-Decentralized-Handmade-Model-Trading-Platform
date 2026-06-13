<template>
  <div v-if="!$route.meta.noGlobalLayout" class="app-container">
    <Navbar />
    <main class="content">
      <router-view />
    </main>
    <Footer />
  </div>

  <router-view v-else />

  <!-- 全局弹窗 -->
  <ModalProvider ref="modalProviderRef" />
</template>

<script setup>
import Navbar from './components/navbar.vue';
import Footer from './components/Footer.vue';
import { ref } from 'vue'
import ModalProvider from '@/components/ModalProvider.vue'

// 模态框引用
const modalProviderRef = ref(null)
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

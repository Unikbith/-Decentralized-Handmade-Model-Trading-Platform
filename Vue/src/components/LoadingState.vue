<template>
  <div class="loading-wrap">
    <span v-if="spinner" class="spinner"></span>
    <span>{{ message }}</span>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: '正在加载...' },
  spinner: { type: Boolean, default: true }
})
</script>

<style scoped>
.loading-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 80px 0;
  color: #999;
  font-size: 15px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(130, 195, 255, 0.3);
  border-top-color: #82c3ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .loading-wrap {
    padding: 50px 0;
    font-size: 14px;
  }
}
</style>
<template>
  <div class="empty-wrap">
    <!-- 默认展示 message；可通过默认插槽自定义图标/文案/按钮 -->
    <slot>{{ message }}</slot>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: '' }
})
</script>

<style scoped>
.empty-wrap {
  text-align: center;
  padding: 80px 0;
  color: #999;
  font-size: 15px;
}

@media (max-width: 768px) {
  .empty-wrap {
    padding: 50px 0;
    font-size: 14px;
  }
}
</style>
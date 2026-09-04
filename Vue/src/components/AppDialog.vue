<template>
  <Teleport to="body">
    <div v-if="modelValue" class="modal-mask" @click.self="handleClose">
      <div class="modal-content" :style="{ width }" :class="{ 'modal-gradient': gradient }">
        <div class="modal-header">
          <h3>{{ title }}</h3>
          <span class="close-btn" @click="handleClose">&times;</span>
        </div>
        <div class="modal-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="modal-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  width: { type: String, default: '440px' },
  gradient: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

// 弹窗打开时禁止背景滚动
watch(() => props.modelValue, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

const handleClose = () => {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.modal-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  max-width: 90%;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-btn {
  font-size: 24px;
  color: #999;
  cursor: pointer;
  line-height: 1;
}

.close-btn:hover {
  color: #666;
}

.modal-body {
  padding: 20px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  border-top: 1px solid #f0f0f0;
}

/* 渐变标题样式（用于首页猜你喜欢类弹窗） */
.modal-gradient .modal-header {
  background: linear-gradient(135deg, #fb7299, #ff9b7a);
}

.modal-gradient .modal-header h3 {
  color: #fff;
}

.modal-gradient .close-btn {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  font-size: 20px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-gradient .close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
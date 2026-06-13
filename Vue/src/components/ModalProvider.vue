<template>
  <Teleport to="body">
    <!-- ===== 模态框遮罩层 ===== -->
    <div v-if="visible" class="modal-overlay" @click.self="closeOnOverlay && close()">
      <div class="modal-box">
        <!-- ===== 模态框头部 ===== -->
        <div class="modal-header">
          <div class="modal-title-line" :class="'line-' + type"></div>
          <span class="modal-title">{{ title }}</span>
        </div>

        <!-- ===== 模态框内容 ===== -->
        <div class="modal-body">{{ message }}</div>

        <!-- ===== 模态框底部按钮 ===== -->
        <div class="modal-footer">
          <button v-if="showCancel" class="btn-cancel" @click="cancel">{{ cancelText }}</button>
          <button class="btn-confirm" :class="'btn-' + type" @click="confirm">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
// ===== 导入依赖 =====
import { ref, onMounted } from 'vue'
import { setModalInstance } from '@/utils/modal'

// ===== 响应式数据定义 =====
const visible = ref(false)
const title = ref('')
const message = ref('')
const type = ref('info')
const showCancel = ref(false)
const confirmText = ref('确定')
const cancelText = ref('取消')
const closeOnOverlay = ref(false)

let resolvePromise = null

// ===== 显示Alert弹窗 =====
function showAlert(msg, t = '提示', tp = 'info') {
  title.value = t; message.value = msg; type.value = tp
  showCancel.value = false; confirmText.value = '确定'
  visible.value = true
  return new Promise(resolve => { resolvePromise = resolve })
}

// ===== 显示Confirm弹窗 =====
function showConfirm(msg, t = '确认操作') {
  title.value = t; message.value = msg; type.value = 'confirm'
  showCancel.value = true; confirmText.value = '确定'; cancelText.value = '取消'
  visible.value = true
  return new Promise(resolve => { resolvePromise = resolve })
}

// ===== 确认回调 =====
function confirm() {
  visible.value = false
  if (resolvePromise) { resolvePromise(true); resolvePromise = null }
}

// ===== 取消回调 =====
function cancel() {
  visible.value = false
  if (resolvePromise) { resolvePromise(false); resolvePromise = null }
}

// ===== 关闭弹窗 =====
function close() {
  visible.value = false
  if (resolvePromise) { resolvePromise(false); resolvePromise = null }
}

// ===== 生命周期钩子 =====
onMounted(() => { setModalInstance({ showAlert, showConfirm }) })

// ===== 暴露方法 =====
defineExpose({ showAlert, showConfirm })
</script>

<style scoped>
/* ===== 遮罩层 ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

/* ===== 模态框主体 ===== */
.modal-box {
  background: #fff;
  border-radius: 16px;
  padding: 0;
  width: 380px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  animation: modalIn 0.25s ease;
}

@keyframes modalIn {
  from { opacity: 0; transform: translateY(20px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* ===== 头部 ===== */
.modal-header {
  padding: 24px 28px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-title-line {
  width: 4px;
  height: 20px;
  border-radius: 2px;
  flex-shrink: 0;
}

/* ===== 类型指示条颜色 ===== */
.line-info { background: #82c3ff; }
.line-success { background: #67c23a; }
.line-error { background: #f56c6c; }
.line-confirm { background: #e6a23c; }

.modal-title {
  font-size: 17px;
  font-weight: 600;
  color: #1a1a2e;
}

/* ===== 内容区 ===== */
.modal-body {
  padding: 16px 28px 24px;
  font-size: 15px;
  color: #555;
  line-height: 1.7;
  word-break: break-word;
}

/* ===== 底部按钮 ===== */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 28px 20px;
}

.btn-cancel {
  padding: 9px 24px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  background: #fff;
  color: #606266;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}
.btn-cancel:hover {
  border-color: #82c3ff;
  color: #82c3ff;
}

.btn-confirm {
  padding: 9px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  transition: all 0.2s;
}

/* ===== 确认按钮类型颜色 ===== */
.btn-info { background: #82c3ff; }
.btn-info:hover { background: #5fb3ff; }
.btn-success { background: #67c23a; }
.btn-success:hover { background: #5daf34; }
.btn-error { background: #f56c6c; }
.btn-error:hover { background: #e05050; }
.btn-confirm { background: #e6a23c; }
.btn-confirm:hover { background: #d48806; }
</style>

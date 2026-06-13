<template>
  <div class="pagination">
    <button class="page-btn" :disabled="currentPage === 1" @click="handlePrev">上一页</button>
    <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页（共 {{ total }} 条）</span>
    <button class="page-btn" :disabled="currentPage === totalPages" @click="handleNext">下一页</button>
    <div class="page-jump">
      <span>跳至</span>
      <input 
        type="number" 
        v-model="jumpPage" 
        @keyup.enter="handleJump" 
        min="1" 
        :max="totalPages" 
        class="jump-input" 
      />
      <span>页</span>
      <button class="jump-btn" @click="handleJump">确定</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

// Props定义
const props = defineProps({
  currentPage: {
    type: Number,
    default: 1
  },
  total: {
    type: Number,
    default: 0
  },
  pageSize: {
    type: Number,
    default: 10
  }
})

// Emits定义
const emit = defineEmits(['update:currentPage'])

// 响应式数据
const jumpPage = ref('')

// 计算属性：总页数
const totalPages = computed(() => {
  return Math.ceil(props.total / props.pageSize) || 1
})

// 上一页
const handlePrev = () => {
  if (props.currentPage > 1) {
    emit('update:currentPage', props.currentPage - 1)
  }
}

// 下一页
const handleNext = () => {
  if (props.currentPage < totalPages.value) {
    emit('update:currentPage', props.currentPage + 1)
  }
}

// 跳转指定页
const handleJump = () => {
  const page = parseInt(jumpPage.value)
  if (page >= 1 && page <= totalPages.value) {
    emit('update:currentPage', page)
    jumpPage.value = ''
  }
}

// 监听total变化重置页码
watch(() => props.total, () => {
  emit('update:currentPage', 1)
})
</script>

<style scoped>
/* ===== 分页控件 ===== */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.page-btn {
  height: 32px;
  padding: 0 16px;
  background: #fff;
  color: #fb7299;
  border: 1px solid #fb7299;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: #fb7299;
  color: #fff;
}

.page-btn:disabled {
  background: #f5f5f5;
  color: #ccc;
  border-color: #ddd;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}

.page-jump {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 16px;
}

.page-jump span {
  font-size: 14px;
  color: #666;
}

.jump-input {
  width: 60px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  text-align: center;
  outline: none;
  transition: all 0.2s;
}

.jump-input:hover {
  border-color: #fb7299;
}

.jump-input:focus {
  border-color: #fb7299;
  box-shadow: 0 0 0 2px rgba(251, 114, 153, 0.1);
}

.jump-btn {
  height: 32px;
  padding: 0 12px;
  background: #fff;
  color: #fb7299;
  border: 1px solid #fb7299;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.jump-btn:hover {
  background: #fb7299;
  color: #fff;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .pagination {
    flex-wrap: wrap;
    gap: 10px;
  }
  .page-jump {
    margin-left: 0;
    width: 100%;
    justify-content: center;
  }
}
</style>

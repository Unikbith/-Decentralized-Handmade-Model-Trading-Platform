<template>
  <div class="goods-page">
    <!--分类筛选抽屉-->
    <div class="filter-overlay" v-show="showFilter" @click="showFilter = false"></div>
    <div class="filter-drawer" :class="{ open: showFilter }">
      <div class="filter-header">
        <h3 class="filter-title">筛选分类</h3>
        <button class="filter-close" @click="showFilter = false">×</button>
      </div>
      <div class="filter-content">
        <div class="filter-list">
          <button 
            v-for="cate in ['', ...categoryList]" 
            :key="cate || 'all'"
            class="filter-item"
            :class="{ active: selectedCategory === cate }"
            @click="selectCategory(cate)"
          >
            {{ cate || '全部分类' }}
          </button>
        </div>
      </div>
    </div>

    <div class="page-container">
      <div class="page-header">
        <h1 class="page-title">全部商品</h1>
        <div class="filter-wrap">
          <button class="filter-btn" @click="showFilter = true">
            {{ selectedCategory || '全部分类' }}
            <span class="filter-arrow">▼</span>
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading-wrap">
        <p>正在加载商品...</p>
      </div>

      <div v-else-if="filteredGoods.length === 0" class="empty-wrap">
        <p>该分类下暂无商品</p>
      </div>

      <!--商品网格-->
      <div v-else class="goods-grid">
        <GoodsCard 
          v-for="goods in paginatedGoods" 
          :key="goods.id" 
          :goods="goods"
        />
      </div>

      <!--分页控件-->
      <Pagination 
        v-if="filteredGoods.length > 0"
        v-model:currentPage="currentPage" 
        :total="filteredGoods.length" 
        :pageSize="pageSize" 
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import request from '@/api/request'
import GoodsCard from '@/components/goodsCard.vue'
import Pagination from '@/components/Pagination.vue'
import { showAlert } from '@/utils/modal'

//响应式数据定义
const allGoods = ref([])
const loading = ref(false)
const selectedCategory = ref('')
const categoryList = ref([]) // 分类列表
const showFilter = ref(false) // 控制抽屉显示

//分页相关
const currentPage = ref(1)
const pageSize = 10

//获取商品选项列表API请求方法
const getGoodsOptions = async () => {
  try {
    const res = await request.get('/api/goods/options')
    if (res.data.code === 200) {
      categoryList.value = res.data.data.categories || []
    }
  } catch (err) {
    console.error('获取分类选项失败:', err)
  }
}

//获取商品列表API请求方法
const getGoodsList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/goods/list')
    if (res.data.code === 200) {
      allGoods.value = res.data.data
    }
  } catch (err) {
    console.error('获取商品列表失败:', err)
    await showAlert('商品加载失败，请检查后端服务', '', 'error')
  } finally {
    loading.value = false
  }
}

//选择分类
const selectCategory = (cate) => {
  selectedCategory.value = cate
  currentPage.value = 1
  showFilter.value = false
}

//筛选后的商品列表
const filteredGoods = computed(() => {
  if (!selectedCategory.value) return allGoods.value
  return allGoods.value.filter(goods => goods.category === selectedCategory.value)
})

//分页后的商品列表
const paginatedGoods = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredGoods.value.slice(start, start + pageSize)
})

//生命周期钩子
onMounted(() => {
  getGoodsOptions() // 先获取分类选项
  getGoodsList()
})
</script>

<style scoped>
/* ===== 页面布局 ===== */
.goods-page {
  min-height: 100vh;
  padding: 80px 40px 40px;
  box-sizing: border-box;
  background: rgb(234, 243, 251);
  position: relative;
}

/* ===== 筛选遮罩 ===== */
.filter-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  z-index: 9998;
  animation: fadeIn 0.25s ease-out;
}

/* ===== 右侧抽屉 ===== */
.filter-drawer {
  position: fixed;
  top: 0;
  right: -320px;
  width: 320px;
  height: 100vh;
  background: white;
  z-index: 9999;
  transition: right 0.35s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  border-radius: 16px 0 0 16px;
}

.filter-drawer.open {
  right: 0;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #80acee, #6a9bdb);
  color: white;
  border-radius: 16px 0 0 0;
  box-shadow: 0 2px 8px rgba(106, 155, 219, 0.2);
}

.filter-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 0.5px;
}

.filter-close {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 22px;
  cursor: pointer;
  line-height: 1;
  transition: all 0.2s ease;
}

.filter-close:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: rotate(90deg);
}

.filter-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.filter-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-item {
  padding: 14px 20px;
  background: #f8faff;
  border: 2px solid transparent;
  border-radius: 12px;
  font-size: 15px;
  color: #444;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
  font-weight: 500;
}

.filter-item:hover {
  background: #f0f7ff;
  border-color: #80acee;
  color: #6a9bdb;
  transform: translateX(4px);
}

.filter-item.active {
  background: linear-gradient(135deg, #80acee, #6a9bdb);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(128, 172, 238, 0.3);
}

.page-container {
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

/* ===== 页面头部 ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
  letter-spacing: -0.5px;
  position: relative;
}

.page-title::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 0;
  width: 40px;
  height: 3px;
  background: linear-gradient(135deg, #80acee, #6a9bdb);
  border-radius: 2px;
}

/* ===== 筛选器 ===== */
.filter-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: white;
  border: 2px solid #e0e8f5;
  border-radius: 30px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(128, 172, 238, 0.1);
  font-weight: 500;
}

.filter-btn:hover {
  border-color: #80acee;
  box-shadow: 0 4px 16px rgba(128, 172, 238, 0.2);
  transform: translateY(-1px);
}

.filter-arrow {
  font-size: 10px;
  color: #999;
  transition: transform 0.2s ease;
}

.filter-btn:hover .filter-arrow {
  transform: translateY(2px);
  color: #80acee;
}

/* ===== 加载&空状态 ===== */
.loading-wrap, .empty-wrap {
  text-align: center;
  padding: 100px 0;
  color: #999;
  font-size: 16px;
}

/* ===== 商品网格 ===== */
.goods-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ===== 响应式适配 ===== */
@media (max-width: 1200px) {
  .goods-page {
    padding: 80px 30px 40px;
  }
  .goods-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
  .filter-drawer {
    width: 300px;
    right: -300px;
  }
}

@media (max-width: 768px) {
  .goods-page {
    padding: 70px 16px 24px;
  }
  .goods-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  .filter-drawer {
    width: 85vw;
    right: -85vw;
  }
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 480px) {
  .goods-page {
    padding: 60px 12px 16px;
  }
  .goods-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .page-title {
    font-size: 20px;
  }
  .filter-btn {
    padding: 8px 16px;
    font-size: 13px;
  }
  .filter-list {
    gap: 10px;
  }
  .filter-item {
    padding: 12px 16px;
    font-size: 14px;
  }
}
</style>
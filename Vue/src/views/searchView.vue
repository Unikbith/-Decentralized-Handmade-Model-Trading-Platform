<template>
  <div class="search-page">
    <!--搜索栏 -->
    <div class="search-container">
      <input 
        v-model="searchKeyword" 
        type="text" 
        placeholder="搜索商品名称、分类、品牌..." 
        class="search-input"
        @keyup.enter="handleSearch"
        @input="debouncedSearch"
      >
      <button class="search-btn" @click="handleSearch">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
      </button>
    </div>

    <!--加载状态-->
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>正在加载中...</p>
    </div>

    <!--错误状态-->
    <div v-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="handleSearch">重新搜索</button>
    </div>

    <!--商品列表-->
    <div v-if="!loading && !error" class="goods-section">
      <div class="section-header">
        <h3 v-if="searchKeyword.trim()">搜索结果</h3>
        <h3 v-else>推荐商品</h3>
      </div>
      
      <!--空状态-->
      <div v-if="goodsList.length === 0" class="empty">
        <p>暂无相关商品</p>
      </div>

      <!--商品网格-->
      <div v-else class="goods-grid">
        <GoodsCard 
          v-for="goods in goodsList" 
          :key="goods.id" 
          :goods="goods"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import GoodsCard from '@/components/goodsCard.vue'

const router = useRouter()

//响应式数据定义
const searchKeyword = ref('')
const goodsList = ref([])
const loading = ref(false)
const error = ref('')
let timer = null

//随机选取商品
const getRandomGoods = (list, count = 8) => {
  const shuffled = [...list].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, count)
}

//获取推荐商品API请求方法
const getRandomRecommend = async () => {
  loading.value = true
  error.value = ''

  try {
    const res = await request.get('/api/goods/list')
    if (res.data.code === 200) {
      goodsList.value = getRandomGoods(res.data.data || [], 8)
    } else {
      error.value = res.data.msg || '获取商品失败'
    }
  } catch (err) {
    console.error('获取商品失败:', err)
    error.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

//搜索方法
const handleSearch = async () => {
  const keyword = searchKeyword.value.trim()
  
  if (!keyword) {
    getRandomRecommend()
    return
  }

  loading.value = true
  error.value = ''

  try {
    const res = await request.get('/api/goods/search', {
      params: { q: keyword }
    })

    if (res.data.code === 200) {
      goodsList.value = res.data.data || []
    } else {
      error.value = res.data.msg || '搜索失败'
    }
  } catch (err) {
    console.error('搜索请求失败:', err)
    error.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

//防抖搜索
const debouncedSearch = () => {
  clearTimeout(timer)
  timer = setTimeout(() => {
    handleSearch()
  }, 500)
}

//生命周期钩子
onMounted(() => {
  getRandomRecommend()
})

onUnmounted(() => {
  clearTimeout(timer)
})
</script>

<style scoped>
/* ===== 页面布局 ===== */
.search-page {
  min-height: 100vh;
  padding: 80px 40px 40px;
  background: #f8f9fa;
  box-sizing: border-box;
}

/* ===== 搜索栏 ===== */
.search-container {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 12px;
  padding: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
  margin-bottom: 32px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.search-container:focus-within {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  border-color: #fb7299;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 14px 16px;
  font-size: 15px;
  background: transparent;
  color: #1a1a1a;
}

.search-input::placeholder {
  color: #999;
}

.search-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: #fb7299;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-btn:hover {
  background: #f7507f;
}

/* ===== 加载状态 ===== */
.loading {
  text-align: center;
  padding: 80px 20px;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e8e8e8;
  border-top-color: #fb7299;
  border-radius: 50%;
  margin: 0 auto 16px;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== 错误状态 ===== */
.error {
  text-align: center;
  padding: 80px 20px;
  color: #666;
}

.error button {
  margin-top: 16px;
  padding: 10px 24px;
  background: #fb7299;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.error button:hover {
  background: #f7507f;
}

/* ===== 商品区域 ===== */
.goods-section {
  max-width: 1400px;
  margin: 0 auto;
}

.section-header {
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

/* ===== 空状态 ===== */
.empty {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

/* ===== 商品网格 ===== */
.goods-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

/* ===== 响应式适配 ===== */
@media (max-width: 1200px) {
  .search-page {
    padding: 80px 30px 40px;
  }
  .goods-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .search-page {
    padding: 70px 16px 24px;
  }
  .goods-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
}

@media (max-width: 480px) {
  .search-page {
    padding: 60px 12px 16px;
  }
  .search-input {
    padding: 10px 12px;
    font-size: 14px;
  }
  .search-btn {
    width: 38px;
    height: 38px;
  }
  .goods-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}
</style>

<template>
  <div class="home-page">
    <!-- ===== 状态标签栏 ===== -->
    <div class="tab-header">
      <div
        v-for="tab in tabs"
        :key="tab.value"
        :class="['tab-item', { active: activeTab === tab.value }]"
        @click="switchTab(tab.value)"
      >
        {{ tab.label }}
      </div>
    </div>

    <!-- ===== 商品列表区 ===== -->
    <div class="page-container">
      <!-- ===== 加载状态 ===== -->
      <div v-if="loading" class="loading-wrap"><p>正在加载商品...</p></div>

      <!-- ===== 空状态 ===== -->
      <div v-else-if="showGoods.length === 0" class="empty-wrap">
        <p>暂无{{ activeTab === 'preorder' ? '预购' : '现货' }}商品~</p>
      </div>

      <!-- ===== 商品网格 ===== -->
      <div v-else class="goods-grid">
        <GoodsCard v-for="goods in paginatedGoods" :key="goods.id" :goods="goods" />
      </div>

      <!-- ===== 分页控件 ===== -->
      <Pagination 
        v-if="showGoods.length > 0"
        v-model:currentPage="currentPage" 
        :total="showGoods.length" 
        :pageSize="pageSize" 
      />
    </div>
  </div>
</template>

<!-- ===== 脚本区域：状态筛选逻辑 ===== -->
<script setup>
// ===== 导入依赖 =====
import { ref, onMounted, computed, watch } from 'vue'
import request from '@/api/request'
import GoodsCard from '@/components/goodsCard.vue'
import Pagination from '@/components/Pagination.vue'

// ===== 响应式数据定义 =====
const goodsList = ref([])
const loading = ref(false)
const activeTab = ref('stock')
const currentPage = ref(1)
const pageSize = 10

// ===== 标签配置 =====
const tabs = [
  { label: '预购', value: 'preorder' },
  { label: '现货', value: 'stock' }
]

// ===== API请求方法：获取商品列表 =====
const getGoodsList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/goods/list')
    if (res.data.code === 200) goodsList.value = res.data.data
  } catch (err) { console.error('加载失败', err) }
  finally { loading.value = false }
}

// ===== 标签切换方法 =====
const switchTab = (tab) => { activeTab.value = tab }

// ===== 计算属性：按状态筛选商品 =====
const showGoods = computed(() => {
  return goodsList.value.filter(goods => {
    const status = goods.status || ''
    if (activeTab.value === 'stock') return status === '现货' || status === 'stock'
    else return status === '预售' || status === 'preorder'
  })
})

// ===== 计算属性：分页后的商品 =====
const paginatedGoods = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return showGoods.value.slice(start, start + pageSize)
})

// ===== 监听器：标签切换重置页码 =====
watch(activeTab, () => { currentPage.value = 1 })

// ===== 生命周期钩子 =====
onMounted(() => { getGoodsList() })
</script>

<!-- ===== 样式区域：状态筛选页面样式 ===== -->
<style scoped>
/* ===== 页面布局 ===== */
.home-page { min-height: 100vh; background: #f4f4f4; }

/* ===== 状态标签栏 ===== */
.tab-header { display: flex; justify-content: center; background: white; padding: 20px 0; border-bottom: 1px solid #e5e5e5; }
.tab-item { font-size: 22px; padding: 0 30px; cursor: pointer; color: #222; position: relative; }
.tab-item.active { color: #fb7299; font-weight: bold; }
.tab-item.active::after { content: ''; position: absolute; bottom: -20px; left: 0; width: 100%; height: 3px; background: #fb7299; }

/* ===== 商品列表容器 ===== */
.page-container { max-width: 1400px; margin: 0 auto; padding: 20px 40px; }

/* ===== 加载&空状态 ===== */
.loading-wrap, .empty-wrap { text-align: center; padding: 80px 0; color: #999; background: white; border-radius: 6px; }

/* ===== 商品网格 ===== */
.goods-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; }

/* ===== 响应式适配 ===== */
@media (max-width: 1200px) {
  .page-container { padding: 20px 30px; }
  .goods-grid { grid-template-columns: repeat(3, 1fr); gap: 20px; }
}
@media (max-width: 768px) {
  .page-container { padding: 16px; }
  .goods-grid { grid-template-columns: repeat(2, 1fr); gap: 16px; }
}
</style>

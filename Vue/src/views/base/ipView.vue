<template>
  <div class="ip-page">
    <!-- ===== IP标签栏 ===== -->
    <div class="ip-header">
      <div class="ip-tags-wrap">
        <div
          v-for="ip in displayIps"
          :key="ip"
          :class="['ip-tag', { active: activeIp === ip }]"
          @click="selectIp(ip)"
        >
          {{ ip || '全部' }}
        </div>
      </div>

      <!-- ===== 展开/收起按钮 ===== -->
      <div v-if="allIps.length > defaultShowCount" class="toggle-btn" @click="toggleExpand">
        {{ isExpanded ? '收起' : '更多' }}
        <span class="arrow" :class="{ expanded: isExpanded }">▼</span>
      </div>
    </div>

    <!-- ===== 商品列表区 ===== -->
    <div class="page-container">
      <!-- ===== 加载状态 ===== -->
      <div v-if="loading" class="loading-wrap">
        <p>正在加载商品...</p>
      </div>

      <!-- ===== 空状态 ===== -->
      <div v-else-if="showGoods.length === 0" class="empty-wrap">
        <p>暂无{{ activeIp ? activeIp + '相关' : '' }}商品~</p>
      </div>

      <!-- ===== 商品网格 ===== -->
      <div v-else class="goods-grid">
        <GoodsCard
          v-for="goods in paginatedGoods"
          :key="goods.id"
          :goods="goods"
        />
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

<script setup>
// ===== 导入依赖 =====
import { ref, onMounted, computed, watch } from 'vue'
import request from '@/api/request'
import GoodsCard from '@/components/goodsCard.vue'
import Pagination from '@/components/Pagination.vue'

// ===== 响应式数据定义 =====
const goodsList = ref([])
const loading = ref(false)
const activeIp = ref('')
const isExpanded = ref(false)
const defaultShowCount = 5

// ===== 分页相关 =====
const currentPage = ref(1)
const pageSize = 10

// ===== 计算属性：IP列表 =====
const allIps = computed(() => {
  const ips = new Set()
  goodsList.value.forEach(g => {
    if (g.ip) ips.add(g.ip)
  })
  return ['', ...Array.from(ips)]
})

const displayIps = computed(() => {
  if (isExpanded.value) return allIps.value
  const defaultList = allIps.value.slice(0, defaultShowCount)
  if (activeIp.value && !defaultList.includes(activeIp.value)) {
    defaultList.push(activeIp.value)
  }
  return defaultList
})

// ===== API请求方法 =====
const getGoodsList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/goods/list')
    if (res.data.code === 200) {
      goodsList.value = res.data.data
    }
  } catch (err) {
    console.error('加载失败', err)
  } finally {
    loading.value = false
  }
}

const selectIp = (ip) => { activeIp.value = ip }
const toggleExpand = () => { isExpanded.value = !isExpanded.value }

// ===== 计算属性：根据IP筛选商品 =====
const showGoods = computed(() => {
  if (!activeIp.value) return goodsList.value
  return goodsList.value.filter(goods => goods.ip === activeIp.value)
})

// ===== 计算属性：分页后的商品 =====
const paginatedGoods = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return showGoods.value.slice(start, start + pageSize)
})

// ===== 监听IP变化重置页码 =====
watch(activeIp, () => { currentPage.value = 1 })

// ===== 生命周期钩子 =====
onMounted(() => { getGoodsList() })
</script>

<style scoped>
.ip-page { min-height: 100vh; background: #f4f4f4; }
.ip-header {
  background: white;
  padding: 20px 40px;
  border-bottom: 1px solid #e5e5e5;
  position: sticky;
  top: 0;
  z-index: 100;
}
.ip-tags-wrap { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px; }
.ip-tag {
  padding: 8px 20px;
  background: #f5f5f5;
  border-radius: 20px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.ip-tag:hover { background: #fff0f5; color: #fb7299; }
.ip-tag.active { background: #fb7299; color: white; font-weight: 500; }
.toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 16px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 16px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}
.toggle-btn:hover { border-color: #fb7299; color: #fb7299; }
.arrow { display: inline-block; transition: transform 0.2s; font-size: 10px; }
.arrow.expanded { transform: rotate(180deg); }
.page-container { max-width: 1400px; margin: 0 auto; padding: 20px 40px; }
.loading-wrap, .empty-wrap { text-align: center; padding: 80px 0; color: #999; background: white; border-radius: 6px; }
.goods-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; }

@media (max-width: 1200px) {
  .page-container { padding: 20px 30px; }
  .goods-grid { grid-template-columns: repeat(3, 1fr); gap: 20px; }
}
@media (max-width: 768px) {
  .ip-header { padding: 15px 16px; }
  .page-container { padding: 16px; }
  .goods-grid { grid-template-columns: repeat(2, 1fr); gap: 16px; }
  .ip-tag { padding: 6px 16px; font-size: 13px; }
}
</style>

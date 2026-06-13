<template>
  <div class="brand-page">
    <!-- ===== 品牌标签栏 ===== -->
    <div class="brand-header">
      <div class="brand-tags-wrap">
        <div
          v-for="brand in displayBrands"
          :key="brand"
          :class="['brand-tag', { active: activeBrand === brand }]"
          @click="selectBrand(brand)"
        >
          {{ brand || '全部' }}
        </div>
      </div>

      <!-- ===== 展开/收起按钮 ===== -->
      <div v-if="allBrands.length > defaultShowCount" class="toggle-btn" @click="toggleExpand">
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
        <p>暂无{{ activeBrand ? activeBrand + '相关' : '' }}商品~</p>
      </div>

      <!-- ===== 商品网格 ===== -->
      <div v-else class="goods-grid">
        <GoodsCard
          v-for="goods in showGoods"
          :key="goods.id"
          :goods="goods"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
// ===== 导入依赖 =====
import { ref, onMounted, computed } from 'vue'
import request from '@/api/request'
import GoodsCard from '@/components/goodsCard.vue'

// ===== 响应式数据定义 =====
const goodsList = ref([])
const loading = ref(false)
const activeBrand = ref('') // 默认选中"全部"
const isExpanded = ref(false)
const defaultShowCount = 5 // 默认显示前8个品牌

// ===== 计算属性：品牌列表 =====
// 从商品列表中提取所有不重复的品牌
const allBrands = computed(() => {
  const brands = new Set()
  goodsList.value.forEach(g => {
    if (g.brand) brands.add(g.brand)
  })
  return ['', ...Array.from(brands)] // 第一个是空字符串，代表"全部"
})

// 当前显示的品牌列表（根据展开状态）
const displayBrands = computed(() => {
  if (isExpanded.value) {
    return allBrands.value
  }
  const defaultList = allBrands.value.slice(0, defaultShowCount)
  if (activeBrand.value && !defaultList.includes(activeBrand.value)) {
    defaultList.push(activeBrand.value)
  }
  return defaultList
})

// ===== API请求方法：获取商品列表 =====
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

// ===== 品牌选择方法 =====
const selectBrand = (brand) => {
  activeBrand.value = brand
}

// ===== 展开/收起切换 =====
const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

// ===== 计算属性：根据品牌筛选商品 =====
const showGoods = computed(() => {
  if (!activeBrand.value) {
    return goodsList.value
  }
  return goodsList.value.filter(goods => goods.brand === activeBrand.value)
})

// ===== 生命周期钩子 =====
onMounted(() => {
  getGoodsList()
})
</script>

<style scoped>
/* ===== 页面布局 ===== */
.brand-page {
  min-height: 100vh;
  background: #f4f4f4;
}

/* ===== 品牌标签栏 ===== */
.brand-header {
  background: white;
  padding: 20px;
  border-bottom: 1px solid #e5e5e5;
  position: sticky;
  top: 0;
  z-index: 100;
}

.brand-tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 10px;
}

.brand-tag {
  padding: 8px 20px;
  background: #f5f5f5;
  border-radius: 20px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.brand-tag:hover {
  background: #fff0f5;
  color: #fb7299;
}

.brand-tag.active {
  background: #fb7299;
  color: white;
  font-weight: 500;
}

/* ===== 展开/收起按钮 ===== */
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

.toggle-btn:hover {
  border-color: #fb7299;
  color: #fb7299;
}

.arrow {
  display: inline-block;
  transition: transform 0.2s;
  font-size: 10px;
}

.arrow.expanded {
  transform: rotate(180deg);
}

/* ===== 商品列表容器 ===== */
.page-container {
  max-width: 1500px;
  margin: 0 auto;
  padding: 20px;
}

/* ===== 加载&空状态 ===== */
.loading-wrap, .empty-wrap {
  text-align: center;
  padding: 80px 0;
  color: #999;
  background: white;
  border-radius: 6px;
}

/* ===== 商品网格 ===== */
.goods-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

/* ===== 响应式适配 ===== */
@media (max-width: 1200px) {
  .goods-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .goods-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .brand-header {
    padding: 15px;
  }
  .brand-tag {
    padding: 6px 16px;
    font-size: 13px;
  }
}
</style>

<template>
  <div class="filter-page">
    <!-- 标签栏 -->
    <div class="filter-header" :class="headerType === 'line' ? 'header-line' : 'header-pills'">
      <div class="tags-wrap" v-if="headerType === 'pills'">
        <div
          v-for="tag in displayTags"
          :key="tag.value"
          :class="['tag-item', { active: active === tag.value }]"
          @click="select(tag.value)"
        >
          {{ tag.label }}
        </div>
      </div>

      <div class="line-tabs" v-else>
        <div
          v-for="tab in statusTabs"
          :key="tab.value"
          :class="['tab-item', { active: active === tab.value }]"
          @click="select(tab.value)"
        >
          {{ tab.label }}
        </div>
      </div>

      <!-- 展开/收起（仅 pill 模式且标签数超限时显示） -->
      <button
        v-if="showExpand && headerType === 'pills' && allTags.length > defaultShowCount"
        class="toggle-btn"
        @click="isExpanded = !isExpanded"
      >
        {{ isExpanded ? '收起' : '更多' }}
        <span class="arrow" :class="{ expanded: isExpanded }">▼</span>
      </button>
    </div>

    <!-- 商品列表区 -->
    <div class="page-container">
      <div v-if="loading" class="loading-wrap">
        <p>正在加载商品...</p>
      </div>

      <div v-else-if="showGoods.length === 0" class="empty-wrap">
        <p>{{ emptyMsg }}</p>
      </div>

      <div v-else class="goods-grid">
        <GoodsCard v-for="goods in listForRender" :key="goods.id" :goods="goods" />
      </div>

      <Pagination
        v-if="showPagination && showGoods.length > 0"
        v-model:currentPage="currentPage"
        :total="showGoods.length"
        :pageSize="pageSize"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'
import GoodsCard from '@/components/goodsCard.vue'
import Pagination from '@/components/Pagination.vue'

const props = defineProps({
  // 筛选模式：'field' 按商品字段取值打标签；'status' 按状态枚举打标签
  mode: { type: String, default: 'field' },
  // field 模式：商品对象上的属性名，如 brand / charactername / ip
  field: { type: String, default: '' },
  // 头部样式：'pills' 胶囊标签，'line' 居中下划线
  headerType: { type: String, default: 'pills' },
  // 是否需要分页
  showPagination: { type: Boolean, default: false },
  // 标签过多时是否显示"展开/收起"
  showExpand: { type: Boolean, default: true },
  // status 模式下的标签组 [{ label, value }]
  statusTabs: { type: Array, default: () => [] },
})

const goodsList = ref([])
const loading = ref(false)
const active = ref(props.mode === 'status' ? (props.statusTabs[1]?.value ?? '') : '')
const isExpanded = ref(false)
const defaultShowCount = 5
const currentPage = ref(1)
const pageSize = 10

// 全部标签（field 模式每项为 { label, value }；status 模式直接用 statusTabs）
const allTags = computed(() => {
  if (props.mode === 'status') return props.statusTabs
  const values = new Set()
  goodsList.value.forEach(g => { if (g[props.field]) values.add(g[props.field]) })
  return [{ label: '全部', value: '' }, ...[...values].map(v => ({ label: v, value: v }))]
})

// 当前展示的标签（考虑展开状态）
const displayTags = computed(() => {
  if (props.mode === 'status' || isExpanded.value) return allTags.value
  const defaultList = allTags.value.slice(0, defaultShowCount)
  if (active.value && !defaultList.some(t => t.value === active.value)) {
    defaultList.push(allTags.value.find(t => t.value === active.value))
  }
  return defaultList
})

// 按当前选中项筛选商品
const showGoods = computed(() => {
  if (props.mode === 'status') {
    return goodsList.value.filter(g => {
      const status = g.status || ''
      return active.value === 'stock'
        ? (status === '现货' || status === 'stock')
        : (status === '预售' || status === 'preorder')
    })
  }
  if (!active.value) return goodsList.value
  return goodsList.value.filter(g => g[props.field] === active.value)
})

const listForRender = computed(() => {
  if (!props.showPagination) return showGoods.value
  const start = (currentPage.value - 1) * pageSize
  return showGoods.value.slice(start, start + pageSize)
})

const emptyMsg = computed(() => {
  if (props.mode === 'status') return `暂无${active.value === 'preorder' ? '预购' : '现货'}商品~`
  return `暂无${active.value ? active.value + '相关' : ''}商品~`
})

const select = (value) => {
  active.value = value
  currentPage.value = 1
}

const getGoodsList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/goods/list')
    if (res.data.code === 200) goodsList.value = res.data.data
  } catch (err) {
    console.error('加载失败', err)
  } finally {
    loading.value = false
  }
}

onMounted(getGoodsList)
</script>

<style scoped>
/* ===== 页面布局 ===== */
.filter-page { min-height: 100vh; background: #f4f4f4; }

/* ===== 标签栏通用 ===== */
.filter-header {
  background: white;
  border-bottom: 1px solid #e5e5e5;
  position: sticky;
  top: 0;
  z-index: 100;
}

/* ===== 胶囊标签（pills） ===== */
.header-pills { padding: 20px 40px; }
.tags-wrap { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px; }
.tag-item {
  padding: 8px 20px;
  background: #f5f5f5;
  border-radius: 20px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.tag-item:hover { background: #fff0f5; color: #fb7299; }
.tag-item.active { background: #fb7299; color: white; font-weight: 500; }

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

/* ===== 居中下划线标签（line） ===== */
.header-line { padding: 20px 0; }
.line-tabs { display: flex; justify-content: center; }
.tab-item { font-size: 22px; padding: 0 30px; cursor: pointer; color: #222; position: relative; }
.tab-item.active { color: #fb7299; font-weight: bold; }
.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: -20px;
  left: 0;
  width: 100%;
  height: 3px;
  background: #fb7299;
}

/* ===== 商品列表容器 ===== */
.page-container { max-width: 1400px; margin: 0 auto; padding: 20px 40px; }

.loading-wrap,
.empty-wrap {
  text-align: center;
  padding: 80px 0;
  color: #999;
  background: white;
  border-radius: 6px;
}

.goods-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; }

/* ===== 响应式适配 ===== */
@media (max-width: 1200px) {
  .page-container { padding: 20px 30px; }
  .goods-grid { grid-template-columns: repeat(3, 1fr); gap: 20px; }
}
@media (max-width: 768px) {
  .header-pills { padding: 15px 16px; }
  .page-container { padding: 16px; }
  .goods-grid { grid-template-columns: repeat(2, 1fr); gap: 16px; }
  .tag-item { padding: 6px 16px; font-size: 13px; }
}
</style>
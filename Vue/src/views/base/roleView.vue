<template>
  <div class="character-page">
    <!-- ===== 角色标签栏 ===== -->
    <div class="character-header">
      <div class="character-tags-wrap">
        <div
          v-for="character in displayCharacters"
          :key="character"
          :class="['character-tag', { active: activeCharacter === character }]"
          @click="selectCharacter(character)"
        >
          {{ character || '全部' }}
        </div>
      </div>

      <!-- ===== 展开/收起按钮 ===== -->
      <div v-if="allCharacters.length > defaultShowCount" class="toggle-btn" @click="toggleExpand">
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
        <p>暂无{{ activeCharacter ? activeCharacter + '相关' : '' }}商品~</p>
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

<!-- ===== 脚本区域：角色筛选逻辑 ===== -->
<script setup>
// ===== 导入依赖 =====
import { ref, onMounted, computed, watch } from 'vue'
import request from '@/api/request'
import GoodsCard from '@/components/goodsCard.vue'
import Pagination from '@/components/Pagination.vue'

// ===== 响应式数据定义 =====
const goodsList = ref([])
const loading = ref(false)
const activeCharacter = ref('')
const isExpanded = ref(false)
const defaultShowCount = 5
const currentPage = ref(1)
const pageSize = 10

// ===== 计算属性：角色列表 =====
const allCharacters = computed(() => {
  const characters = new Set()
  goodsList.value.forEach(g => { if (g.charactername) characters.add(g.charactername) })
  return ['', ...Array.from(characters)]
})

// ===== 计算属性：当前显示的角色列表 =====
const displayCharacters = computed(() => {
  if (isExpanded.value) return allCharacters.value
  const defaultList = allCharacters.value.slice(0, defaultShowCount)
  if (activeCharacter.value && !defaultList.includes(activeCharacter.value)) defaultList.push(activeCharacter.value)
  return defaultList
})

// ===== API请求方法：获取商品列表 =====
const getGoodsList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/goods/list')
    if (res.data.code === 200) goodsList.value = res.data.data
  } catch (err) { console.error('加载失败', err) }
  finally { loading.value = false }
}

// ===== 角色选择与展开方法 =====
const selectCharacter = (character) => { activeCharacter.value = character }
const toggleExpand = () => { isExpanded.value = !isExpanded.value }

// ===== 计算属性：按角色筛选商品 =====
const showGoods = computed(() => {
  if (!activeCharacter.value) return goodsList.value
  return goodsList.value.filter(goods => goods.charactername === activeCharacter.value)
})

// ===== 计算属性：分页后的商品 =====
const paginatedGoods = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return showGoods.value.slice(start, start + pageSize)
})

// ===== 监听器：角色切换重置页码 =====
watch(activeCharacter, () => { currentPage.value = 1 })

// ===== 生命周期钩子 =====
onMounted(() => { getGoodsList() })
</script>

<!-- ===== 样式区域：角色筛选页面样式 ===== -->
<style scoped>
/* ===== 页面布局 ===== */
.character-page { min-height: 100vh; background: #f4f4f4; }

/* ===== 角色标签栏 ===== */
.character-header { background: white; padding: 20px 40px; border-bottom: 1px solid #e5e5e5; position: sticky; top: 0; z-index: 100; }
.character-tags-wrap { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px; }
.character-tag { padding: 8px 20px; background: #f5f5f5; border-radius: 20px; font-size: 14px; color: #333; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
.character-tag:hover { background: #fff0f5; color: #fb7299; }
.character-tag.active { background: #fb7299; color: white; font-weight: 500; }

/* ===== 展开/收起按钮 ===== */
.toggle-btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 16px; background: none; border: 1px solid #ddd; border-radius: 16px; font-size: 13px; color: #666; cursor: pointer; transition: all 0.2s; }
.toggle-btn:hover { border-color: #fb7299; color: #fb7299; }
.arrow { display: inline-block; transition: transform 0.2s; font-size: 10px; }
.arrow.expanded { transform: rotate(180deg); }

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
  .character-header { padding: 15px 16px; }
  .page-container { padding: 16px; }
  .goods-grid { grid-template-columns: repeat(2, 1fr); gap: 16px; }
  .character-tag { padding: 6px 16px; font-size: 13px; }
}
</style>

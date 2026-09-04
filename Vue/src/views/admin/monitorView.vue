<template>
  <div class="monitor-page">
    <div class="monitor-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack" title="返回管理员后台">
          <img src="@/assets/images/返回.png" alt="返回" />
        </button>
        <h2 class="page-title">流量监控面板</h2>
      </div>
      <button class="refresh-btn" @click="fetchAllData" :disabled="loading">
        <span class="refresh-icon">↻</span> 刷新
      </button>
    </div>

    <!--数据统计卡片-->
    <div class="stat-cards">
      <StatCard label="今日请求量" :value="summary.total_requests" color="blue" />
      <StatCard label="平均响应时间" :value="summary.avg_duration" unit="ms" color="green" />
      <StatCard label="错误率" :value="summary.error_rate" unit="%" color="red" :danger="summary.error_rate > 5" />
      <StatCard label="今日活跃用户" :value="userActivity.active_users" color="purple" />
      <StatCard label="今日新注册" :value="userActivity.new_registrations" color="orange" />
      <StatCard label="今日交易额" :value="`¥${orderOverview.today_revenue}`" color="cyan" />
    </div>

    <!-- 请求量趋势图-->
    <div class="chart-row">
      <div class="chart-card chart-wide">
        <h3 class="chart-title">请求量趋势（最近60分钟）</h3>
        <EChart :option="lineOption" height="280px" />
      </div>
    </div>

    <!--用户活跃趋势  搜索关键词-->
    <div class="chart-row">
      <div class="chart-card">
        <h3 class="chart-title">用户活跃趋势（24小时）</h3>
        <EChart :option="userTrendOption" height="280px" />
      </div>
      <div class="chart-card">
        <h3 class="chart-title">热门搜索关键词 Top10</h3>
        <EChart :option="searchOption" height="280px" />
      </div>
    </div>

    <!--商品销量 订单状态 -->
    <div class="chart-row">
      <div class="chart-card">
        <h3 class="chart-title">商品销量 Top10</h3>
        <EChart :option="productSaleOption" height="280px" />
      </div>
      <div class="chart-card">
        <h3 class="chart-title">今日订单状态分布</h3>
        <EChart :option="orderPieOption" height="280px" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import EChart from '@/components/EChart.vue'
import StatCard from '@/components/StatCard.vue'


const router = useRouter()

const goBack = () => {
  router.push('/admin/dashboard')
}

//响应式数据定义
const loading = ref(false)
const summary = ref({ total_requests: 0, avg_duration: 0, error_rate: 0 })
const timeline = ref([])
const userActivity = ref({ active_users: 0, new_registrations: 0, hourly_trend: [] })
const productRanking = ref({ by_sales: [] })
const orderOverview = ref({ today_orders: 0, today_revenue: 0, status_distribution: [] })
const searchKeywords = ref([])

//API请求方法
const fetchAllData = async () => {
  loading.value = true
  try {
    const [realtimeRes, userRes, productRes, orderRes, searchRes] = await Promise.all([
      request.get('/api/admin/monitor/realtime'),
      request.get('/api/admin/monitor/user-activity'),
      request.get('/api/admin/monitor/product-ranking'),
      request.get('/api/admin/monitor/order-overview'),
      request.get('/api/admin/monitor/search-keywords')
    ])

    if (realtimeRes.data.code === 200) {
      summary.value = realtimeRes.data.data.summary
      timeline.value = realtimeRes.data.data.timeline
    }
    if (userRes.data.code === 200) userActivity.value = userRes.data.data
    if (productRes.data.code === 200) productRanking.value = productRes.data.data
    if (orderRes.data.code === 200) orderOverview.value = orderRes.data.data
    if (searchRes.data.code === 200) searchKeywords.value = searchRes.data.data
  } catch (err) {
    console.error('获取监控数据失败:', err)
  } finally {
    loading.value = false
  }
}

// ===== 各图表 option（数据变化时自动重渲染） =====
const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['请求数', '错误数', '平均耗时'], top: 0, textStyle: { fontSize: 12 } },
  grid: { left: 50, right: 50, top: 36, bottom: 30 },
  xAxis: { type: 'category', data: timeline.value.map(m => m.time), axisLabel: { fontSize: 11 } },
  yAxis: [
    { type: 'value', name: '请求数', axisLabel: { fontSize: 11 } },
    { type: 'value', name: '耗时ms', axisLabel: { fontSize: 11 } }
  ],
  series: [
    { name: '请求数', type: 'line', data: timeline.value.map(m => m.total), smooth: true, areaStyle: { opacity: 0.15 }, itemStyle: { color: '#80acee' } },
    { name: '错误数', type: 'line', data: timeline.value.map(m => m.errors), smooth: true, itemStyle: { color: '#ff4d4f' } },
    { name: '平均耗时', type: 'line', yAxisIndex: 1, data: timeline.value.map(m => m.avg_duration), smooth: true, itemStyle: { color: '#52c41a' }, lineStyle: { type: 'dashed' } }
  ]
}))

const userTrendOption = computed(() => {
  const trend = userActivity.value.hourly_trend || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: trend.map(h => h.hour), axisLabel: { fontSize: 11, interval: 2 } },
    yAxis: { type: 'value', name: '活跃用户', axisLabel: { fontSize: 11 }, minInterval: 1 },
    series: [{
      type: 'line', data: trend.map(h => h.count), smooth: true,
      areaStyle: { opacity: 0.2, color: '#9b59b6' },
      itemStyle: { color: '#9b59b6' }, lineStyle: { width: 2 }
    }]
  }
})

const searchOption = computed(() => {
  const list = [...searchKeywords.value].reverse()
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 120, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value', axisLabel: { fontSize: 11 } },
    yAxis: { type: 'category', data: list.map(i => i.keyword), axisLabel: { fontSize: 11, width: 100, overflow: 'truncate' } },
    series: [{ type: 'bar', data: list.map(i => i.count), itemStyle: { color: '#e67e22', borderRadius: [0, 4, 4, 0] } }]
  }
})

const productSaleOption = computed(() => {
  const list = [...productRanking.value.by_sales].reverse()
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 120, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value', axisLabel: { fontSize: 11 } },
    yAxis: { type: 'category', data: list.map(i => i.name), axisLabel: { fontSize: 11, width: 100, overflow: 'truncate' } },
    series: [{ type: 'bar', data: list.map(i => i.count), itemStyle: { color: '#fb7299', borderRadius: [0, 4, 4, 0] } }]
  }
})

const orderPieOption = computed(() => {
  const colors = ['#faad14', '#80acee', '#52c41a', '#9b59b6', '#999', '#ff4d4f', '#e67e22']
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}单 ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 12 } },
    color: colors,
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '45%'],
      data: orderOverview.value.status_distribution,
      label: { formatter: '{b}\n{d}%', fontSize: 12 }
    }]
  }
})

//生命周期钩子：定时刷新
let refreshTimer = null
onMounted(() => {
  fetchAllData()
  refreshTimer = setInterval(fetchAllData, 30000)
})

onUnmounted(() => {
  clearInterval(refreshTimer)
})
</script>

<style scoped>
/* ===== 页面布局 ===== */
.monitor-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  width: 40px;
  height: 40px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.back-btn img {
  width: 20px;
  height: 20px;
  object-fit: contain;
}
.back-btn:hover {
  background: #e8e8e8;
  color: #333;
  border-color: #bbb;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

/* ===== 刷新按钮 ===== */
.refresh-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 16px;
  font-size: 14px;
  color: #80acee;
  background: #fff;
  border: 1px solid #80acee;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: #80acee;
  color: #fff;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== 统计卡片 ===== */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

/* ===== 图表区域 ===== */
.chart-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.chart-row:first-of-type {
  grid-template-columns: 1fr;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .monitor-page {
    padding: 12px;
  }
  .header-left {
    gap: 10px;
  }
  .back-btn {
    width: 34px;
    height: 34px;
    font-size: 18px;
  }
  .page-title {
    font-size: 16px;
  }
  .stat-cards {
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }
  .chart-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
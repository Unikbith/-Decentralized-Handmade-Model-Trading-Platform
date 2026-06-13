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
      <div class="stat-card card-blue">
        <div class="stat-label">今日请求量</div>
        <div class="stat-value">{{ summary.total_requests }}</div>
      </div>
      <div class="stat-card card-green">
        <div class="stat-label">平均响应时间</div>
        <div class="stat-value">{{ summary.avg_duration }}<span class="stat-unit">ms</span></div>
      </div>
      <div class="stat-card card-red">
        <div class="stat-label">错误率</div>
        <div class="stat-value" :class="{ 'error-text': summary.error_rate > 5 }">{{ summary.error_rate }}<span class="stat-unit">%</span></div>
      </div>
      <div class="stat-card card-purple">
        <div class="stat-label">今日活跃用户</div>
        <div class="stat-value">{{ userActivity.active_users }}</div>
      </div>
      <div class="stat-card card-orange">
        <div class="stat-label">今日新注册</div>
        <div class="stat-value">{{ userActivity.new_registrations }}</div>
      </div>
      <div class="stat-card card-cyan">
        <div class="stat-label">今日交易额</div>
        <div class="stat-value">¥{{ orderOverview.today_revenue }}</div>
      </div>
    </div>

    <!-- 请求量趋势图-->
    <div class="chart-row">
      <div class="chart-card chart-wide">
        <h3 class="chart-title">请求量趋势（最近60分钟）</h3>
        <div ref="lineChartRef" class="chart-container"></div>
      </div>
    </div>

    <!--用户活跃趋势  搜索关键词-->
    <div class="chart-row">
      <div class="chart-card">
        <h3 class="chart-title">用户活跃趋势（24小时）</h3>
        <div ref="userTrendChartRef" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <h3 class="chart-title">热门搜索关键词 Top10</h3>
        <div ref="searchChartRef" class="chart-container"></div>
      </div>
    </div>

    <!--商品销量 订单状态 -->
    <div class="chart-row">
      <div class="chart-card">
        <h3 class="chart-title">商品销量 Top10</h3>
        <div ref="productSaleChartRef" class="chart-container"></div>
      </div>
      <div class="chart-card">
        <h3 class="chart-title">今日订单状态分布</h3>
        <div ref="orderPieChartRef" class="chart-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import request from '@/api/request'


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

//图表DOM引用
const lineChartRef = ref(null)
const userTrendChartRef = ref(null)
const searchChartRef = ref(null)
const productSaleChartRef = ref(null)
const orderPieChartRef = ref(null)

// 图表实例变量
let lineChart = null
let userTrendChart = null
let searchChart = null
let productSaleChart = null
let orderPieChart = null
let refreshTimer = null

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

    await nextTick()
    renderCharts()
  } catch (err) {
    console.error('获取监控数据失败:', err)
  } finally {
    loading.value = false
  }
}

//图表渲染方法
const renderCharts = () => {
  renderLineChart()
  renderUserTrendChart()
  renderSearchChart()
  renderProductSaleChart()
  renderOrderPieChart()
}

const renderLineChart = () => {
  if (!lineChartRef.value) return
  if (!lineChart) lineChart = echarts.init(lineChartRef.value)
  lineChart.setOption({
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
  })
}

const renderUserTrendChart = () => {
  if (!userTrendChartRef.value) return
  if (!userTrendChart) userTrendChart = echarts.init(userTrendChartRef.value)
  const trend = userActivity.value.hourly_trend || []
  userTrendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: trend.map(h => h.hour), axisLabel: { fontSize: 11, interval: 2 } },
    yAxis: { type: 'value', name: '活跃用户', axisLabel: { fontSize: 11 }, minInterval: 1 },
    series: [{
      type: 'line', data: trend.map(h => h.count), smooth: true,
      areaStyle: { opacity: 0.2, color: '#9b59b6' },
      itemStyle: { color: '#9b59b6' }, lineStyle: { width: 2 }
    }]
  })
}

const renderSearchChart = () => {
  if (!searchChartRef.value) return
  if (!searchChart) searchChart = echarts.init(searchChartRef.value)
  const list = [...searchKeywords.value].reverse()
  searchChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 120, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value', axisLabel: { fontSize: 11 } },
    yAxis: { type: 'category', data: list.map(i => i.keyword), axisLabel: { fontSize: 11, width: 100, overflow: 'truncate' } },
    series: [{ type: 'bar', data: list.map(i => i.count), itemStyle: { color: '#e67e22', borderRadius: [0, 4, 4, 0] } }]
  })
}

const renderProductSaleChart = () => {
  if (!productSaleChartRef.value) return
  if (!productSaleChart) productSaleChart = echarts.init(productSaleChartRef.value)
  const list = [...productRanking.value.by_sales].reverse()
  productSaleChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 120, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value', axisLabel: { fontSize: 11 } },
    yAxis: { type: 'category', data: list.map(i => i.name), axisLabel: { fontSize: 11, width: 100, overflow: 'truncate' } },
    series: [{ type: 'bar', data: list.map(i => i.count), itemStyle: { color: '#fb7299', borderRadius: [0, 4, 4, 0] } }]
  })
}

const renderOrderPieChart = () => {
  if (!orderPieChartRef.value) return
  if (!orderPieChart) orderPieChart = echarts.init(orderPieChartRef.value)
  const colors = ['#faad14', '#80acee', '#52c41a', '#9b59b6', '#999', '#ff4d4f', '#e67e22']
  orderPieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}单 ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 12 } },
    color: colors,
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '45%'],
      data: orderOverview.value.status_distribution,
      label: { formatter: '{b}\n{d}%', fontSize: 12 }
    }]
  })
}

//窗口自适应处理
const handleResize = () => {
  lineChart?.resize()
  userTrendChart?.resize()
  searchChart?.resize()
  productSaleChart?.resize()
  orderPieChart?.resize()
}

//生命周期钩子
onMounted(() => {
  fetchAllData()
  refreshTimer = setInterval(fetchAllData, 30000)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearInterval(refreshTimer)
  window.removeEventListener('resize', handleResize)
  lineChart?.dispose()
  userTrendChart?.dispose()
  searchChart?.dispose()
  productSaleChart?.dispose()
  orderPieChart?.dispose()
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

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 18px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-left: 4px solid #ddd;
}

.card-blue { border-left-color: #80acee; }
.card-green { border-left-color: #52c41a; }
.card-red { border-left-color: #ff4d4f; }
.card-purple { border-left-color: #9b59b6; }
.card-orange { border-left-color: #e67e22; }
.card-cyan { border-left-color: #1abc9c; }

.stat-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
}

.stat-unit {
  font-size: 13px;
  font-weight: 400;
  color: #999;
  margin-left: 2px;
}

.error-text {
  color: #ff4d4f;
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

.chart-container {
  width: 100%;
  height: 280px;
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
  .stat-card {
    padding: 12px;
  }
  .stat-value {
    font-size: 18px;
  }
  .chart-row {
    grid-template-columns: 1fr;
  }
  .chart-container {
    height: 220px;
  }
}

@media (max-width: 480px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .stat-value {
    font-size: 16px;
  }
}
</style>

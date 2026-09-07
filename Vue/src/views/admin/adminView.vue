<template>
  <div class="admin-dashboard">
    <div class="container">
      <header class="dashboard-header">
        <h1 class="header-title">管理员后台</h1>
        <div class="header-right">
          <span class="admin-name">欢迎，{{ adminNickname }}</span>
          <button class="btn-logout" @click="handleLogout">退出登录</button>
        </div>
      </header>

      <div class="tab-bar">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: currentTab === tab.key }"
          @click="handleTabChange(tab.key)"
        >{{ tab.label }}</div>
      </div>

      <!--用户管理面板-->
      <div v-if="currentTab === 'users'" class="content-panel">
        <div class="panel-header"><h2 class="panel-title">用户列表</h2></div>
        <div v-if="userList.length" class="table-wrapper">
          <el-table class="admin-table" :data="paginatedUserList" row-key="id" @row-click="openUserDetail">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="nickname" label="昵称" min-width="120" />
            <el-table-column prop="username" label="账号" min-width="130" />
            <el-table-column label="角色" min-width="170">
              <template #default="{ row }">
                <span class="role-tag" :class="row.role">{{ roleText(row.role) }}</span>
                <span v-if="row.is_banned === 1" class="role-tag banned">已封禁</span>
                <span v-if="row.role === 'merchant'" class="role-tag" :class="row.apply_status">{{ applyText(row.apply_status) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="350">
              <template #default="{ row }">
                <button class="btn-edit" @click.stop="openEditUser(row)">编辑</button>
                <button
                  class="btn-ban"
                  :class="{ 'btn-unban': row.is_banned === 1 }"
                  @click.stop="toggleUserBan(row)"
                >{{ row.is_banned === 1 ? '解封' : '封禁' }}</button>
                <button class="btn-delete" @click.stop="deleteUser(row.id)">删除</button>
                <template v-if="row.role === 'merchant' && row.apply_status === 'pending'">
                  <button class="btn-approve-apply" @click.stop="approveMerchant(row.id)">通过入驻</button>
                  <button class="btn-reject-apply" @click.stop="rejectMerchant(row.id)">拒绝入驻</button>
                </template>
              </template>
            </el-table-column>
          </el-table>
          <Pagination
            v-if="userList.length"
            v-model:currentPage="userCurrentPage"
            :total="userList.length"
            :pageSize="userPageSize"
          />
        </div>
        <div v-else class="empty-state"><p>暂无用户</p></div>
      </div>

      <!--商品管理面板-->
      <div v-if="currentTab === 'goods'" class="content-panel">
        <div class="panel-header"><h2 class="panel-title">商品列表</h2></div>
        <div v-if="goodsList.length" class="table-wrapper">
          <el-table class="admin-table" :data="paginatedGoodsList" row-key="id" @row-click="goToGoodsDetail">
            <el-table-column label="商品图" width="80">
              <template #default="{ row }">
                <img :src="row.image" class="goods-thumb" alt="商品图" />
              </template>
            </el-table-column>
            <el-table-column prop="name" label="商品名称" min-width="180" show-overflow-tooltip />
            <el-table-column label="价格" min-width="90">
              <template #default="{ row }">¥{{ row.price.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="stock" label="库存" min-width="80" />
            <el-table-column label="分类" min-width="110">
              <template #default="{ row }">{{ row.category || '未分类' }}</template>
            </el-table-column>
            <el-table-column label="状态" min-width="90">
              <template #default="{ row }">
                <span :class="{ 'out-of-stock': row.stock === 0 }">
                  {{ row.stock === 0 ? '缺货' : (row.status || '未设置') }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="merchant_name" label="商家" min-width="110" show-overflow-tooltip />
            <el-table-column label="操作" width="220">
              <template #default="{ row }">
                <button class="btn-edit" @click.stop="openEditGoods(row)">编辑</button>
                <button
                  class="btn-status"
                  :class="{ 'btn-off': row.status !== '下架' }"
                  @click.stop="toggleGoodsOnlineStatus(row)"
                >{{ row.status === '下架' ? '上架' : '下架' }}</button>
                <button class="btn-delete" @click.stop="deleteGoods(row.id)">删除</button>
              </template>
            </el-table-column>
          </el-table>
          <Pagination
            v-if="goodsList.length"
            v-model:currentPage="goodsCurrentPage"
            :total="goodsList.length"
            :pageSize="goodsPageSize"
          />
        </div>
        <div v-else class="empty-state"><p>暂无商品</p></div>
      </div>

      <!--订单管理面板-->
      <div v-if="currentTab === 'orders'" class="content-panel">
        <div class="panel-header">
          <h2 class="panel-title">订单管理</h2>
          <div class="order-filter">
            <el-select v-model="orderFilterStatus" placeholder="全部状态" @change="filterOrders" class="filter-select">
              <el-option label="全部状态" value="" />
              <el-option v-for="(label, val) in orderStatusOptions" :key="val" :label="label" :value="val" />
            </el-select>
          </div>
        </div>
        <div v-if="orderList.length" class="table-wrapper">
          <el-table class="admin-table order-table" :data="paginatedOrderList" row-key="id">
            <el-table-column prop="order_no" label="订单号" min-width="160" />
            <el-table-column label="下单用户" min-width="150">
              <template #default="{ row }">{{ row.user_nickname }} (ID: {{ row.user_id }})</template>
            </el-table-column>
            <el-table-column prop="receiver_name" label="收货人" min-width="90" />
            <el-table-column prop="receiver_phone" label="联系电话" min-width="110" />
            <el-table-column label="收货地址" min-width="180">
              <template #default="{ row }">
                <span class="address-cell" :title="formatAddress(row.receiver_address)">{{ formatAddress(row.receiver_address) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="总金额" min-width="90">
              <template #default="{ row }">¥{{ row.total_price.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="状态" min-width="90">
              <template #default="{ row }">
                <span class="order-status-tag" :class="row.status">{{ getStatusText(row.status) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" min-width="150" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <div class="order-actions">
                  <button
                    class="btn-edit"
                    @click="openEditOrder(row)"
                    :disabled="row.status === 'cancelled'"
                    :title="row.status === 'cancelled' ? '已取消订单无法修改' : '编辑订单'"
                  >编辑</button>
                  <button
                    class="btn-delete"
                    @click="deleteOrder(row.id)"
                    :title="row.status === 'cancelled' ? '删除已取消订单' : '删除订单'"
                  >删除</button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <Pagination
            v-if="orderList.length"
            v-model:currentPage="orderCurrentPage"
            :total="orderList.length"
            :pageSize="orderPageSize"
          />
        </div>
        <div v-else class="empty-state"><p>暂无订单</p></div>
      </div>
    </div>

    <!--弹窗组件-->
    <EditOrderDialog v-model:visible="showEditOrder" :order="editingOrder" @saved="onOrderSaved" />
    <EditGoodsDialog v-model:visible="showEditGoods" :goods="editingGoods" @saved="onGoodsSaved" />
    <EditUserDialog v-model:visible="showEditUser" :user="editingUser" @saved="onUserSaved" />
    <UserDetailDialog ref="userDetailRef" v-model:visible="showUserDetail" :user-id="userDetailId" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
import { showAlert, showConfirm } from '@/utils/modal'
import Pagination from '@/components/Pagination.vue'
import EditOrderDialog from './components/EditOrderDialog.vue'
import EditGoodsDialog from './components/EditGoodsDialog.vue'
import EditUserDialog from './components/EditUserDialog.vue'
import UserDetailDialog from './components/UserDetailDialog.vue'

const router = useRouter()

// ===== 响应式数据 =====
const adminNickname = ref(sessionStorage.getItem('adminNickname') || '')
const currentTab = ref('users')
const tabs = [
  { key: 'users', label: '用户管理' },
  { key: 'goods', label: '商品管理' },
  { key: 'orders', label: '订单管理' },
  { key: 'monitor', label: '流量监控' }
]
const userList = ref([])
const goodsList = ref([])
const orderList = ref([])
const orderFilterStatus = ref('')

// ===== 分页 =====
const userCurrentPage = ref(1)
const userPageSize = 10
const paginatedUserList = computed(() => {
  const start = (userCurrentPage.value - 1) * userPageSize
  return userList.value.slice(start, start + userPageSize)
})

const goodsCurrentPage = ref(1)
const goodsPageSize = 10
const paginatedGoodsList = computed(() => {
  const start = (goodsCurrentPage.value - 1) * goodsPageSize
  return goodsList.value.slice(start, start + goodsPageSize)
})

const orderCurrentPage = ref(1)
const orderPageSize = 10
const paginatedOrderList = computed(() => {
  const start = (orderCurrentPage.value - 1) * orderPageSize
  return orderList.value.slice(start, start + orderPageSize)
})

// ===== 弹窗状态 =====
const showEditOrder = ref(false)
const editingOrder = ref(null)
const showEditGoods = ref(false)
const editingGoods = ref(null)
const showEditUser = ref(false)
const editingUser = ref(null)
const showUserDetail = ref(false)
const userDetailId = ref(null)
const userDetailRef = ref()

const orderStatusOptions = {
  pending_pay: '待付款',
  pending_ship: '待发货',
  pending_receive: '待收货',
  completed: '已完成',
  refund: '退款/售后',
  refunded: '已退款',
  cancelled: '已取消'
}

// ===== 文本/样式映射工具 =====
const roleText = (role) => role === 'admin' ? '管理员' : (role === 'merchant' ? '商家' : '普通用户')
const applyText = (s) => ({ approved: '已入驻', pending: '审核中', rejected: '已拒绝', none: '未申请' }[s] || '')

const getStatusText = (status) => orderStatusOptions[status] || status

const formatAddress = (address) => {
  if (!address) return ''
  try {
    const addrObj = JSON.parse(address)
    return `${addrObj.province || ''}${addrObj.city || ''}${addrObj.district || ''}${addrObj.detail || ''}`
  } catch (e) {
    return address
  }
}

// ===== 权限校验 =====
const checkAuth = async () => {
  if (!sessionStorage.getItem('adminToken')) {
    await showAlert('请先登录！', '', 'error')
    router.push('/admin/login')
  }
}

// ===== 用户管理 =====
const getUserList = async () => {
  try {
    const res = await request.get('/api/admin/users')
    if (res.data.code === 200) {
      userList.value = res.data.data
      userCurrentPage.value = 1
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('获取用户列表失败，请检查后端服务', '', 'error')
  }
}

const openEditUser = (user) => {
  editingUser.value = user
  showEditUser.value = true
}

// 编辑用户保存后：刷新列表，若详情弹窗打开则同步刷新
const onUserSaved = (id) => {
  showEditUser.value = false
  getUserList()
  if (showUserDetail.value && userDetailRef.value) {
    userDetailRef.value.refresh(id)
  }
}

const openUserDetail = (row) => {
  userDetailId.value = row.id
  showUserDetail.value = true
}

const approveMerchant = async (userId) => {
  if (!(await showConfirm('确定通过该商家的入驻申请吗？通过后该商家即可发布商品。'))) return
  try {
    const res = await request.post(`/api/admin/merchant/approve/${userId}`)
    if (res.data.code === 200) {
      await showAlert('已通过该商家的入驻申请', '', 'success')
      getUserList()
    } else {
      await showAlert(res.data.msg || '操作失败', '', 'error')
    }
  } catch (err) {
    console.error('通过入驻申请失败:', err)
    await showAlert('操作失败，请检查网络连接', '', 'error')
  }
}

const rejectMerchant = async (userId) => {
  if (!(await showConfirm('确定拒绝该商家的入驻申请吗？拒绝后该商家将无法发布商品。'))) return
  try {
    const res = await request.post(`/api/admin/merchant/reject/${userId}`)
    if (res.data.code === 200) {
      await showAlert('已拒绝该商家的入驻申请', '', 'success')
      getUserList()
    } else {
      await showAlert(res.data.msg || '操作失败', '', 'error')
    }
  } catch (err) {
    console.error('拒绝入驻申请失败:', err)
    await showAlert('操作失败，请检查网络连接', '', 'error')
  }
}

const toggleUserBan = async (user) => {
  const action = user.is_banned === 1 ? '解封' : '封禁'
  const tip = user.is_banned === 1 ? '解封后用户可正常登录' : '封禁后用户将无法登录系统'
  if (!(await showConfirm(`确定${action}该用户？${tip}`))) return
  try {
    const url = user.is_banned === 1
      ? `/api/admin/user/unban/${user.id}`
      : `/api/admin/user/ban/${user.id}`
    const res = await request.post(url)
    if (res.data.code === 200) {
      await showAlert(`用户${action}成功`, '', 'success')
      getUserList()
    } else {
      await showAlert(res.data.msg || `${action}失败`, '', 'error')
    }
  } catch (err) {
    await showAlert(`${action}用户失败，请检查接口`, '', 'error')
  }
}

const deleteUser = async (id) => {
  if (!(await showConfirm('确定删除该用户？此操作不可恢复，将删除该用户的所有数据，包括购物车、历史记录、评论、订单和售后申请！'))) return
  try {
    await request.delete(`/api/admin/user/delete/${id}`)
    await showAlert('用户及所有关联数据删除成功', '', 'success')
    getUserList()
  } catch (err) {
    await showAlert('删除失败', '', 'error')
  }
}

// ===== 商品管理 =====
const getGoodsList = async () => {
  try {
    const res = await request.get('/api/admin/goods')
    if (res.data.code === 200) {
      goodsList.value = res.data.data
      goodsCurrentPage.value = 1
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('获取商品列表失败', '', 'error')
  }
}

const openEditGoods = (goods) => {
  editingGoods.value = goods
  showEditGoods.value = true
}

const onGoodsSaved = () => {
  showEditGoods.value = false
  getGoodsList()
}

const deleteGoods = async (id) => {
  if (!(await showConfirm('确定删除该商品？此操作不可恢复'))) return
  try {
    await request.delete(`/api/admin/goods/delete/${id}`)
    await showAlert('删除成功', '', 'success')
    getGoodsList()
  } catch (err) {
    await showAlert('删除失败', '', 'error')
  }
}

const toggleGoodsOnlineStatus = async (goods) => {
  const isOffline = goods.status === '下架'
  const actionText = isOffline ? '上架' : '下架'
  let confirmTip = ''
  if (goods.stock === 0) {
    confirmTip = isOffline ? '该商品库存为0，上架后状态仍为【缺货】，确定继续？' : '该商品库存为0，确定执行下架操作？'
  } else {
    confirmTip = `确定${actionText}该商品？`
  }
  if (!(await showConfirm(confirmTip))) return

  try {
    const res = await request.post(`/api/admin/goods/status/${goods.id}`)
    if (res.data.code === 200) {
      await showAlert(`商品${actionText}成功`, '', 'success')
      getGoodsList()
    } else {
      await showAlert(res.data.msg || `${actionText}失败`, '', 'error')
    }
  } catch (err) {
    await showAlert(`商品${actionText}失败，请检查接口`, '', 'error')
  }
}

const goToGoodsDetail = async (row) => {
  try {
    router.push({ name: 'goodsDetail', params: { id: row.id } })
  } catch (err) {
    console.error('跳转商品详情页失败:', err)
    await showAlert('跳转商品详情页失败，请检查路由配置', '', 'error')
  }
}

// ===== 订单管理 =====
const getOrderList = async () => {
  try {
    const res = await request.get('/api/admin/orders', {
      params: { status: orderFilterStatus.value }
    })
    if (res.data.code === 200) {
      orderList.value = res.data.data
      orderCurrentPage.value = 1
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('获取订单列表失败', '', 'error')
  }
}

const filterOrders = () => {
  getOrderList()
}

const openEditOrder = async (order) => {
  if (order.status === 'cancelled') {
    await showAlert('已取消的订单无法修改信息！', '', 'error')
    return
  }
  editingOrder.value = order
  showEditOrder.value = true
}

const onOrderSaved = () => {
  showEditOrder.value = false
  getOrderList()
}

const deleteOrder = async (id) => {
  const order = orderList.value.find(o => o.id === id)
  const confirmMsg = order && order.status === 'cancelled'
    ? '确定删除该已取消订单？此操作不可恢复'
    : '确定删除该订单？此操作不可恢复，将同时删除所有订单项和关联的售后申请'
  if (!(await showConfirm(confirmMsg))) return

  try {
    await request.delete(`/api/admin/order/delete/${id}`)
    await showAlert('订单删除成功', '', 'success')
    getOrderList()
  } catch (err) {
    await showAlert('删除失败', '', 'error')
  }
}

// ===== 退出登录 =====
const handleLogout = async () => {
  if (!(await showConfirm('确定退出？'))) return
  sessionStorage.removeItem('adminToken')
  sessionStorage.removeItem('adminNickname')
  router.push('/admin/login')
}

// ===== 切换标签加载数据 =====
const handleTabChange = (tab) => {
  if (tab === 'monitor') {
    router.push('/admin/monitor')
    return
  }
  currentTab.value = tab
  if (tab === 'users') getUserList()
  if (tab === 'goods') getGoodsList()
  if (tab === 'orders') getOrderList()
}

// ===== 生命周期钩子 =====
onMounted(() => {
  checkAuth()
  getUserList()
})
</script>

<style scoped>
/* ===== 页面布局 ===== */
.admin-dashboard {
  min-height: 100vh;
  background: #f4f4f4;
  padding: 80px 20px 40px;
  box-sizing: border-box;
}
.container { max-width: 100%; margin: 0 auto; }

/* ===== 顶部导航栏 ===== */
.dashboard-header {
  background: #fff;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header-title { font-size: 20px; font-weight: 600; color: #212121; margin: 0; }
.header-right { display: flex; align-items: center; gap: 16px; }
.admin-name { font-size: 14px; color: #666; }

/* ===== 退出按钮 ===== */
.btn-logout {
  height: 36px; padding: 0 20px; background: #fb7299; color: #fff;
  border: none; border-radius: 8px; font-size: 14px; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
}
.btn-logout:hover { background: #f7507f; }

/* ===== 标签切换栏 ===== */
.tab-bar {
  background: #fff; padding: 0 24px; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); display: flex;
  gap: 32px; margin-bottom: 16px;
}
.tab-item {
  padding: 14px 0; font-size: 15px; color: #666; cursor: pointer;
  border-bottom: 2px solid transparent; transition: all 0.2s;
}
.tab-item:hover { color: #fb7299; }
.tab-item.active { color: #fb7299; border-bottom-color: #fb7299; font-weight: 500; }

/* ===== 内容面板 ===== */
.content-panel {
  background: #fff; padding: 24px; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); min-height: auto;
}
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #eee;
}
.panel-title { font-size: 18px; font-weight: 600; color: #212121; margin: 0; }
.empty-state { text-align: center; padding: 60px 0; color: #999; font-size: 15px; }
.table-wrapper { overflow-x: auto; }

/* ===== Element Plus 表格 · 统一为原 style ===== */
.admin-table {
  --el-table-border-color: #eee;
  --el-table-header-bg-color: #fafafa;
  --el-table-row-hover-bg-color: #f9f9f9;
  width: 100%;
}
.admin-table :deep(.el-table__header th) {
  font-size: 13px; font-weight: 600; color: #666; white-space: nowrap;
}
.admin-table :deep(.el-table__cell) { padding: 12px 10px; font-size: 14px; color: #333; }

/* ===== 商品缩略图 ===== */
.goods-thumb { width: 48px; height: 48px; border-radius: 4px; object-fit: cover; }

/* ===== 订单地址悬浮 ===== */
.address-cell {
  max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  display: inline-block; position: relative; cursor: pointer; vertical-align: middle;
}
.address-cell:hover::after {
  content: attr(title); position: absolute; bottom: 100%; left: 0;
  background: #262626; color: #fff; padding: 6px 10px; border-radius: 4px;
  font-size: 12px; white-space: normal; max-width: 280px; z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* ===== 角色/入驻状态标签 ===== */
.role-tag {
  display: inline-block; padding: 4px 12px; border-radius: 4px;
  font-size: 12px; font-weight: 500; margin-right: 6px;
}
.role-tag.admin { background: #fff2f0; color: #ff4d4f; }
.role-tag.merchant { background: #e6f7ff; color: #1890ff; }
.role-tag.user { background: #f6ffed; color: #52c41a; }
.role-tag.banned { background: #fff2f0; color: #ff4d4f; }
.role-tag.approved { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
.role-tag.pending { background: #fff7e6; color: #faad14; border: 1px solid #ffd591; }
.role-tag.rejected { background: #fff1f0; color: #ff4d4f; border: 1px solid #ffa39e; }
.role-tag.none { background: #f5f5f5; color: #8c8c8c; border: 1px solid #d9d9d9; }

/* ===== 订单状态标签 ===== */
.order-status-tag {
  display: inline-block; padding: 4px 12px; border-radius: 4px;
  font-size: 12px; font-weight: 500; min-width: 55px; text-align: center;
}
.order-status-tag.pending_pay { background: #fff7e6; color: #fa8c16; }
.order-status-tag.pending_ship { background: #e6f7ff; color: #1890ff; }
.order-status-tag.pending_receive { background: #f6ffed; color: #52c41a; }
.order-status-tag.completed { background: #f6ffed; color: #52c41a; }
.order-status-tag.refund { background: #fff2f0; color: #ff4d4f; }
.order-status-tag.refunded { background: #f5f5f5; color: #8c8c8c; }
.order-status-tag.cancelled { background: #f5f5f5; color: #8c8c8c; }

/* ===== 表格操作按钮（通用） ===== */
.btn-edit, .btn-delete, .btn-ban {
  height: 32px; padding: 0 16px; background: #fff; border-radius: 6px;
  font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;
  margin-right: 8px; border: 1px solid;
}
.btn-edit { color: #fb7299; border-color: #fb7299; }
.btn-edit:hover:not(:disabled) { background: #fb7299; color: #fff; }
.btn-edit:disabled { background: #f5f5f5; color: #ccc; border-color: #ddd; cursor: not-allowed; }
.btn-delete { color: #ff4d4f; border-color: #ff4d4f; }
.btn-delete:hover:not(:disabled) { background: #ff4d4f; color: #fff; }
.btn-delete:disabled { background: #f5f5f5; color: #ccc; border-color: #ddd; cursor: not-allowed; }
.btn-ban { color: #ff9800; border-color: #ff9800; }
.btn-ban:hover { background: #ff9800; color: #fff; }
.btn-ban.btn-unban { color: #52c41a; border-color: #52c41a; }
.btn-ban.btn-unban:hover { background: #52c41a; color: #fff; }

.btn-approve-apply, .btn-reject-apply {
  height: 32px; padding: 0 12px; background: #fff; border-radius: 6px;
  font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;
  margin-right: 8px; border: 1px solid;
}
.btn-approve-apply { color: #52c41a; border-color: #52c41a; }
.btn-approve-apply:hover { background: #52c41a; color: #fff; }
.btn-reject-apply { color: #ff4d4f; border-color: #ff4d4f; }
.btn-reject-apply:hover { background: #ff4d4f; color: #fff; }

.btn-status {
  height: 32px; padding: 0 16px; border-radius: 6px; font-size: 13px;
  font-weight: 500; cursor: pointer; transition: all 0.2s; margin: 0 8px;
  border: 1px solid #67c23a; background: #fff; color: #67c23a;
}
.btn-status.btn-off { border-color: #e6a23c; color: #e6a23c; }
.btn-status:hover { background: #67c23a; color: #fff; }
.btn-status.btn-off:hover { background: #e6a23c; color: #fff; }

.order-actions { display: flex; align-items: center; gap: 6px; white-space: nowrap; }

/* ===== 缺货文字 ===== */
.out-of-stock { color: #C53F3F; font-weight: 500; }

/* ===== 订单筛选下拉框 ===== */
.order-filter { display: flex; align-items: center; gap: 10px; }
.filter-select { width: 130px; }

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .admin-dashboard { padding: 70px 8px 20px; }
  .dashboard-header { padding: 12px 14px; flex-direction: column; gap: 10px; align-items: flex-start; }
  .header-title { font-size: 17px; }
  .header-right { width: 100%; justify-content: space-between; }
  .admin-name { font-size: 13px; }
  .btn-logout { height: 32px; padding: 0 14px; font-size: 13px; }
  .tab-bar { padding: 0 10px; gap: 16px; overflow-x: auto; flex-wrap: nowrap; -webkit-overflow-scrolling: touch; }
  .tab-bar::-webkit-scrollbar { display: none; }
  .tab-item { flex-shrink: 0; white-space: nowrap; padding: 12px 0; font-size: 14px; }
  .content-panel { padding: 12px; border-radius: 8px; }
  .panel-header { flex-wrap: wrap; gap: 8px; }
  .panel-title { font-size: 16px; }
  .admin-table { min-width: 900px; }
  .admin-table :deep(.el-table__cell) { padding: 10px 8px; font-size: 12px; }
  .btn-edit, .btn-delete, .btn-ban { height: 28px; padding: 0 10px; font-size: 12px; margin-right: 4px; }
  .btn-approve-apply, .btn-reject-apply { height: 28px; padding: 0 10px; font-size: 12px; margin-right: 4px; }
  .btn-status { height: 28px; padding: 0 10px; font-size: 12px; margin: 0 4px; }
  .goods-thumb { width: 40px; height: 40px; }
  .empty-state { padding: 40px 0; font-size: 14px; }
  .role-tag, .order-status-tag { padding: 2px 8px; font-size: 11px; }
}
</style>
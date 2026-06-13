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
        >
          {{ tab.label }}
        </div>
      </div>

      <!--用户管理面板-->
      <div v-if="currentTab === 'users'" class="content-panel">
        <div class="panel-header">
          <h2 class="panel-title">用户列表</h2>
        </div>
        <div v-if="userList.length === 0" class="empty-state">
          <p>暂无用户</p>
        </div>
        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>昵称</th>
                <th>账号</th>
                <th>角色</th>
                <th>操作</th>
              </tr>
            </thead>
          <tbody>
            <tr v-for="user in paginatedUserList" :key="user.id" class="user-row" @click="openUserDetailModal(user.id)">
              <td>{{ user.id }}</td>
              <td>{{ user.nickname }}</td>
              <td>{{ user.username }}</td>
              <td>
                <span class="role-tag" :class="user.role">{{ user.role === 'admin' ? '管理员' : (user.role === 'merchant' ? '商家' : '普通用户') }}</span>
                <!-- 封禁状态标签 -->
                <span v-if="user.is_banned === 1" class="role-tag banned">已封禁</span>
                <span v-if="user.role === 'merchant' && user.apply_status === 'approved'" class="role-tag approved">已入驻</span>
                <span v-if="user.role === 'merchant' && user.apply_status === 'pending'" class="role-tag pending">审核中</span>
                <span v-if="user.role === 'merchant' && user.apply_status === 'rejected'" class="role-tag rejected">已拒绝</span>
                <span v-if="user.role === 'merchant' && user.apply_status === 'none'" class="role-tag none">未申请</span>
              </td>
              <td>
                <button class="btn-edit" @click.stop="openEditUserModal(user)">编辑</button>
                <button class="btn-ban" 
                  :class="{ 'btn-unban': user.is_banned === 1 }"
                  @click.stop="toggleUserBan(user)">
                  {{ user.is_banned === 1 ? '解封' : '封禁' }}
                </button>
                <button class="btn-delete" @click.stop="deleteUser(user.id)">删除</button>
                <button v-if="user.role === 'merchant' && user.apply_status === 'pending'" 
                        class="btn-approve-apply" 
                        @click.stop="approveMerchant(user.id)">
                  通过入驻
                </button>
                <button v-if="user.role === 'merchant' && user.apply_status === 'pending'" 
                        class="btn-reject-apply" 
                        @click.stop="rejectMerchant(user.id)">
                  拒绝入驻
                </button>
              </td>
            </tr>
          </tbody>
          </table>
          <!-- 用户分页控件 -->
          <Pagination 
            v-if="userList.length > 0"
            v-model:currentPage="userCurrentPage" 
            :total="userList.length" 
            :pageSize="userPageSize" 
          />
        </div>
      </div>

      <!--商品管理面板-->
      <div v-if="currentTab === 'goods'" class="content-panel">
        <div class="panel-header">
          <h2 class="panel-title">商品列表</h2>
        </div>
        <div v-if="goodsList.length === 0" class="empty-state">
          <p>暂无商品</p>
        </div>
        <div v-else class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>商品图</th>
                <th>商品名称</th>
                <th>价格</th>
                <th>库存</th>
                <th>分类</th>
                <th>状态</th>
                <th>商家</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="goods in paginatedGoodsList" 
                :key="goods.id"
                class="goods-row"
                @click="goToGoodsDetail(goods.id)"
              >
                <td>
                  <img :src="goods.image" class="goods-thumb" alt="商品图" />
                </td>
                <td class="goods-name">{{ goods.name }}</td>
                <td>¥{{ goods.price.toFixed(2) }}</td>
                <td>{{ goods.stock || 0 }}</td>
                <td>{{ goods.category || '未分类' }}</td>
                <td>
                  <span :class="{'out-of-stock': goods.stock === 0}">
                    {{ goods.stock === 0 ? '缺货' : (goods.status || '未设置') }}
                  </span>
                </td>
                <td>{{ goods.merchant_name }}</td>
                <td>
                  <button 
                    class="btn-edit" 
                    @click.stop="openEditGoodsModal(goods)"
                  >
                    编辑
                  </button>

                  <button 
                    class="btn-status"
                    :class="{ 'btn-off': goods.status !== '下架' }"
                    @click.stop="toggleGoodsOnlineStatus(goods)"
                  >
                    {{ goods.status === '下架' ? '上架' : '下架' }}
                  </button>

                  <button 
                    class="btn-delete" 
                    @click.stop="deleteGoods(goods.id)"
                  >
                    删除
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <!-- 商品分页控件 -->
          <Pagination 
            v-if="goodsList.length > 0"
            v-model:currentPage="goodsCurrentPage" 
            :total="goodsList.length" 
            :pageSize="goodsPageSize" 
          />
        </div>
      </div>

      <!--订单管理面板-->
      <div v-if="currentTab === 'orders'" class="content-panel">
        <div class="panel-header">
          <h2 class="panel-title">订单管理</h2>
          <div class="order-filter">
            <select v-model="orderFilterStatus" @change="filterOrders" class="filter-select">
              <option value="">全部状态</option>
              <option value="pending_pay">待付款</option>
              <option value="pending_ship">待发货</option>
              <option value="pending_receive">待收货</option>
              <option value="completed">已完成</option>
              <option value="refund">退款/售后</option>
              <option value="refunded">已退款</option>
              <option value="cancelled">已取消</option>
            </select>
          </div>
        </div>
        <div v-if="orderList.length === 0" class="empty-state">
          <p>暂无订单</p>
        </div>
        <div v-else class="table-wrapper">
          <table class="data-table order-table">
            <thead>
              <tr>
                <th>订单号</th>
                <th>下单用户</th>
                <th>收货人</th>
                <th>联系电话</th>
                <th>收货地址</th>
                <th>总金额</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in paginatedOrderList" :key="order.id">
                <td>{{ order.order_no }}</td>
                <td>{{ order.user_nickname }} (ID: {{ order.user_id }})</td>
                <td>{{ order.receiver_name }}</td>
                <td>{{ order.receiver_phone }}</td>
                <td class="address-cell" :title="formatAddress(order.receiver_address)">{{ formatAddress(order.receiver_address) }}</td>
                <td>¥{{ order.total_price.toFixed(2) }}</td>
                <td>
                  <span class="order-status-tag" :class="order.status">
                    {{ getStatusText(order.status) }}
                  </span>
                </td>
                <td>{{ order.created_at }}</td>
                <td>
                  <div class="order-actions">
                    <button 
                      class="btn-edit" 
                      @click="openEditOrderModal(order)"
                      :disabled="order.status === 'cancelled'"
                      :title="order.status === 'cancelled' ? '已取消订单无法修改' : '编辑订单'"
                    >
                      编辑
                    </button>
                    <button 
                      class="btn-delete" 
                      @click="deleteOrder(order.id)"
                      :title="order.status === 'cancelled' ? '删除已取消订单' : '删除订单'"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <!-- 分页控件 -->
          <Pagination 
            v-if="orderList.length > 0"
            v-model:currentPage="orderCurrentPage" 
            :total="orderList.length" 
            :pageSize="orderPageSize" 
          />
        </div>
      </div>

    </div>

    <!--编辑订单弹窗 -->
    <div v-if="showEditOrderModal" class="modal-mask" @click.self="closeEditOrderModal">
      <div class="modal-content edit-order-modal">
        <div class="modal-header">
          <h3>编辑订单信息</h3>
          <span class="close-btn" @click="closeEditOrderModal">×</span>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>订单号</label>
            <input type="text" v-model="editingOrder.order_no" disabled class="disabled-input" />
          </div>
          <div class="form-group">
            <label>收货人姓名</label>
            <input type="text" v-model="editingOrder.receiver_name" placeholder="请输入收货人姓名" />
          </div>
          <div class="form-group">
            <label>联系电话</label>
            <input type="text" v-model="editingOrder.receiver_phone" placeholder="请输入联系电话" maxlength="11" />
          </div>
          <div class="form-group">
            <label>收货地区</label>
            <div class="area-selects">
              <select v-model="selectedOrderProvince" @change="onOrderProvinceChange">
                <option value="">请选择省</option>
                <option v-for="p in orderProvinces" :key="p.value" :value="p.value">
                  {{ p.label }}
                </option>
              </select>
              <select v-model="selectedOrderCity" @change="onOrderCityChange" :disabled="!selectedOrderProvince">
                <option value="">请选择市</option>
                <option v-for="c in orderCities" :key="c.value" :value="c.value">
                  {{ c.label }}
                </option>
              </select>
              <select v-model="selectedOrderDistrict" :disabled="!selectedOrderCity">
                <option value="">请选择区</option>
                <option v-for="d in orderDistricts" :key="d.value" :value="d.value">
                  {{ d.label }}
                </option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>详细地址</label>
            <textarea v-model="editingOrder.receiver_detail" placeholder="请输入详细地址" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>订单总金额</label>
            <input type="number" v-model="editingOrder.total_price" placeholder="请输入订单总金额" step="0.01" min="0" />
          </div>
          <div class="form-group">
            <label>订单状态</label>
            <select v-model="editingOrder.status" class="status-select">
              <option value="pending_pay">待付款</option>
              <option value="pending_ship">待发货</option>
              <option value="pending_receive">待收货</option>
              <option value="completed">已完成</option>
              <option value="refund">退款/售后</option>
              <option value="refunded">已退款</option>
            </select>
            <p class="form-tip">修改订单状态会同步更新用户端显示</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeEditOrderModal">取消</button>
          <button class="confirm-btn" @click="saveOrder" :disabled="isSavingOrder">
            {{ isSavingOrder ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>

    <!--编辑商品弹窗 -->
    <div v-if="showEditGoodsModal" class="modal-mask" @click.self="closeEditGoodsModal">
      <div class="modal-content edit-goods-modal">
        <div class="modal-header">
          <h3>编辑商品信息</h3>
          <span class="close-btn" @click="closeEditGoodsModal">×</span>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>商品ID</label>
            <input type="text" v-model="editingGoods.id" disabled />
          </div>
          <div class="form-group">
            <label>商品名称</label>
            <input type="text" v-model="editingGoods.name" placeholder="请输入商品名称" />
          </div>
          <div class="form-group">
            <label>商品价格</label>
            <input type="number" v-model="editingGoods.price" placeholder="请输入商品价格" step="0.01" min="0" />
          </div>
          <div class="form-group">
            <label>商品库存</label>
            <input type="number" v-model="editingGoods.stock" placeholder="请输入商品库存" min="0" @input="handleStockChange" />
          </div>
          <div class="form-group">
            <label>商品分类</label>
            <select v-model="editingGoods.category" class="status-select">
              <option value="">未分类</option>
              <option value="景品">景品</option>
              <option value="Q版手办">Q版手办</option>
              <option value="可动手办">可动手办</option>
              <option value="盒蛋">盒蛋</option>
              <option value="雕像">雕像</option>
              <option value="拼装模型">拼装模型</option>
              <option value="原创/同人作品">原创/同人作品</option>
              <option value="GK白模/手办">GK白模/手办</option>
            </select>
          </div>
          <div class="form-group">
            <label>商品状态</label>
            <select v-model="editingGoods.status" class="status-select">
              <option v-if="editingGoods.stock === 0" value="缺货">缺货</option>
              <template v-else>
                <option value="现货">现货</option>
                <option value="预售">预售</option>
                <option value="下架">下架</option>
              </template>
            </select>
            <p v-if="editingGoods.stock === 0" class="form-tip">库存为0时，商品状态自动为"缺货"</p>
          </div>
          <div class="form-group">
            <label>商品品牌</label>
            <input type="text" v-model="editingGoods.brand" placeholder="请输入商品品牌" />
          </div>
          <div class="form-group">
            <label>IP名称</label>
            <input type="text" v-model="editingGoods.ip" placeholder="请输入IP名称" />
          </div>
          <div class="form-group">
            <label>角色名称</label>
            <input type="text" v-model="editingGoods.charactername" placeholder="请输入角色名称" />
          </div>
          <div class="form-group">
            <label>商品描述</label>
            <textarea v-model="editingGoods.description" placeholder="请输入商品描述" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeEditGoodsModal">取消</button>
          <button class="confirm-btn" @click="saveGoods" :disabled="isSavingGoods">
            {{ isSavingGoods ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>

    <!--编辑用户弹窗-->
    <div v-if="showEditUserModal" class="modal-mask" @click.self="closeEditUserModal">
      <div class="modal-content edit-user-modal">
        <div class="modal-header">
          <h3>编辑用户信息</h3>
          <span class="close-btn" @click="closeEditUserModal">×</span>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户ID</label>
            <input type="text" v-model="editingUser.id" disabled class="disabled-input" />
          </div>
          <div class="form-group">
            <label>用户账号</label>
            <input type="text" v-model="editingUser.username" disabled class="disabled-input" />
          </div>
          <div class="form-group">
            <label>用户昵称</label>
            <input type="text" v-model="editingUser.nickname" placeholder="请输入用户昵称" />
          </div>
          <div class="form-group">
            <label>用户角色</label>
            <select v-model="editingUser.role" class="status-select">
              <option value="user">普通用户</option>
              <option value="merchant">商家</option>
            </select>
          </div>
          <div class="form-group">
            <label>头像URL</label>
            <input type="text" v-model="editingUser.avatar" placeholder="请输入头像链接" />
            <div v-if="editingUser.avatar" class="avatar-preview">
              <img :src="editingUser.avatar" alt="头像预览" />
            </div>
          </div>
          <div class="form-group">
            <label>手机号</label>
            <input type="text" v-model="editingUser.phone" placeholder="请输入手机号" maxlength="11" />
          </div>
          <div class="form-group">
            <label>收货地址</label>
            <textarea v-model="editingUser.address" placeholder="请输入收货地址" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeEditUserModal">取消</button>
          <button class="confirm-btn" @click="saveUser" :disabled="isSavingUser">
            {{ isSavingUser ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!--用户详情弹窗-->
  <div v-if="showUserDetailModal" class="modal-mask" @click.self="closeUserDetailModal">
    <div class="modal-content user-detail-modal">
      <div class="modal-header">
        <h3>用户详情</h3>
        <span class="close-btn" @click="closeUserDetailModal">×</span>
      </div>
      <div class="modal-body">
        <div class="detail-item">
          <label>用户ID：</label>
          <span>{{ userDetail.id }}</span>
        </div>
        <div class="detail-item">
          <label>账号：</label>
          <span>{{ userDetail.username }}</span>
        </div>
        <div class="detail-item">
          <label>昵称：</label>
          <span>{{ userDetail.nickname }}</span>
        </div>
        <div class="detail-item">
          <label>角色：</label>
          <span>{{ userDetail.role === 'merchant' ? '商家' : '普通用户' }}</span>
        </div>
        <div class="detail-item">
          <label>封禁状态：</label>
          <span :class="userDetail.is_banned === 1 ? 'status-banned' : 'status-normal'">
            {{ userDetail.is_banned === 1 ? '已封禁' : '正常' }}
          </span>
        </div>
        <div class="detail-item">
          <label>头像：</label>
          <img v-if="userDetail.avatar" :src="userDetail.avatar" class="detail-avatar" />
          <span v-else>未设置</span>
        </div>
        <div class="detail-item">
          <label>手机号：</label>
          <span>{{ userDetail.phone || '未设置' }}</span>
        </div>
        <div class="detail-item">
          <label>收货地址：</label>
          <span>{{ userDetail.address || '未设置' }}</span>
        </div>
      </div>
      <div class="modal-footer">
        <button class="confirm-btn" @click="closeUserDetailModal">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { regionData } from "element-china-area-data"
import { showAlert, showConfirm } from '@/utils/modal'
import Pagination from '@/components/Pagination.vue'

//根据标签查找地区编码
const findRegionValueByLabel = (data, targetLabel) => {
  if (!targetLabel) return ''
  for (const item of data) {
    if (item.label === targetLabel) return item.value
    if (item.children && item.children.length) {
      const childValue = findRegionValueByLabel(item.children, targetLabel)
      if (childValue) return childValue
    }
  }
  return ''
}

const router = useRouter()

//响应式数据定义
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

//分页
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

const editingStatus = reactive({})

//订单地址三级选择变量
const selectedOrderProvince = ref("")
const selectedOrderCity = ref("")
const selectedOrderDistrict = ref("")

//省市区级联数据
const orderProvinces = computed(() => {
  return regionData.map(item => ({
    value: item.value,
    label: item.label,
  }))
})
const orderCities = computed(() => {
  if (!selectedOrderProvince.value) return []
  const province = regionData.find(p => p.value === selectedOrderProvince.value)
  if (province && province.children) {
    return province.children.map(c => ({
      value: c.value,
      label: c.label,
    }))
  }
  return []
})
const orderDistricts = computed(() => {
  if (!selectedOrderCity.value) return []
  const province = regionData.find(p => p.value === selectedOrderProvince.value)
  if (province) {
    const city = province.children?.find(c => c.value === selectedOrderCity.value)
    if (city && city.children) {
      return city.children.map(d => ({
        value: d.value,
        label: d.label,
      }))
    }
  }
  return []
})

//根据文字标签查找编码
const findValueByLabel = (list, label) => {
  if (!label || !list) return ""
  for (const item of list) {
    if (item.label === label) return item.value
    if (item.children) {
      const res = findValueByLabel(item.children, label)
      if (res) return res
    }
  }
  return ""
}

//省市区切换事件
const onOrderProvinceChange = () => {
  selectedOrderCity.value = ""
  selectedOrderDistrict.value = ""
}
const onOrderCityChange = () => {
  selectedOrderDistrict.value = ""
}

//地址格式化方法
const formatAddress = (address) => {
  if (!address) return ''
  try {
    const addrObj = JSON.parse(address)
    return `${addrObj.province || ''}${addrObj.city || ''}${addrObj.district || ''}${addrObj.detail || ''}`
  } catch (e) {
    return address
  }
}

// 编辑订单相关数据
const showEditOrderModal = ref(false)
const editingOrder = reactive({
  id: null,
  order_no: '',
  receiver_name: '',
  receiver_phone: '',
  receiver_address: '',
  receiver_province: '',
  receiver_city: '',
  receiver_district: '',
  receiver_detail: '',
  total_price: 0,
  status: ''
})
const isSavingOrder = ref(false)

//编辑商品相关数据
const showEditGoodsModal = ref(false)
const editingGoods = reactive({
  id: null,
  name: '',
  price: 0,
  stock: 0,
  category: '',
  status: '',
  brand: '',
  ip: '',
  charactername: '',
  description: ''
})
const isSavingGoods = ref(false)

//编辑用户相关数据
const showEditUserModal = ref(false)
const editingUser = reactive({
  id: null,
  username: '',
  nickname: '',
  role: '',
  avatar: '',
  phone: '',
  address: ''
})
const isSavingUser = ref(false)

//用户详情弹窗数据
const showUserDetailModal = ref(false)
const userDetail = reactive({
  id: null,
  username: '',
  nickname: '',
  role: '',
  is_banned: 0,
  avatar: '',
  phone: '',
  address: ''
})

//监听器：库存变化自动设置缺货状态
watch(() => editingGoods.stock, (newStock, oldStock) => {
  if (newStock === 0) {
    editingGoods.status = '缺货'
  } else if (oldStock === 0 && newStock > 0) {
    if (editingGoods.status === '缺货') {
      editingGoods.status = '现货'
    }
  }
})

//权限检查方法
const checkAuth = async () => {
  if (!sessionStorage.getItem('adminToken')) {
    await showAlert('请先登录！', '', 'error')
    router.push('/admin/login')
  }
}

//订单状态文本转换
const getStatusText = (status) => {
  const statusMap = {
    'pending_pay': '待付款',
    'pending_ship': '待发货',
    'pending_receive': '待收货',
    'completed': '已完成',
    'refund': '退款/售后',
    'refunded': '已退款',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

//用户管理
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

//用户编辑弹窗操作
const openEditUserModal = (user) => {
  editingUser.id = user.id
  editingUser.username = user.username || ''
  editingUser.nickname = user.nickname || ''
  editingUser.role = user.role || 'user'
  editingUser.avatar = user.avatar || ''
  editingUser.phone = user.phone || ''
  editingUser.address = user.address || ''
  showEditUserModal.value = true
}

const closeEditUserModal = () => {
  showEditUserModal.value = false
  editingUser.id = null
  editingUser.username = ''
  editingUser.nickname = ''
  editingUser.role = ''
  editingUser.avatar = ''
  editingUser.phone = ''
  editingUser.address = ''
}

//用户详情弹窗操作
const openUserDetailModal = async (userId) => {
  try {
    const res = await request.get(`/api/admin/user/detail/${userId}`)
    if (res.data.code === 200) {
      const user = res.data.data
      userDetail.id = user.id
      userDetail.username = user.username || ''
      userDetail.nickname = user.nickname || ''
      userDetail.role = user.role || 'user'
      userDetail.is_banned = user.is_banned || 0
      // 从 user.info 中取头像、手机号、地址
      userDetail.avatar = user.info?.avatar || ''
      userDetail.phone = user.info?.phone || ''
      userDetail.address = user.info?.address || ''
      showUserDetailModal.value = true
    } else {
      await showAlert(res.data.msg || '获取用户详情失败', '', 'error')
    }
  } catch (err) {
    await showAlert('获取用户详情失败，请检查接口', '', 'error')
  }
}

const closeUserDetailModal = () => {
  showUserDetailModal.value = false
}

//商家入驻审核方法
const approveMerchant = async (userId) => {
  if (!(await showConfirm('确定通过该商家的入驻申请吗？通过后该商家即可发布商品。'))) return
  
  try {
    const res = await request.post(`/api/admin/merchant/approve/${userId}`)
    if (res.data.code === 200) {
      await showAlert('已通过该商家的入驻申请', '', 'success')
      getUserList()  // 刷新用户列表
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
      getUserList()  // 刷新用户列表
    } else {
      await showAlert(res.data.msg || '操作失败', '', 'error')
    }
  } catch (err) {
    console.error('拒绝入驻申请失败:', err)
    await showAlert('操作失败，请检查网络连接', '', 'error')
  }
}

//保存用户修改
const saveUser = async () => {
  if (!editingUser.nickname.trim()) return await showAlert('请输入用户昵称', '', 'error')
  if (!['user', 'merchant', 'admin'].includes(editingUser.role)) return await showAlert('请选择有效用户角色', '', 'error')
  if (editingUser.phone && !/^1[3-9]\d{9}$/.test(editingUser.phone.trim())) {
    return await showAlert('请输入正确的11位手机号码', '', 'error')
  }

  isSavingUser.value = true
  try {
    const res = await request.post(`/api/admin/user/update/${editingUser.id}`, {
      nickname: editingUser.nickname.trim(),
      role: editingUser.role,
      avatar: editingUser.avatar.trim(),
      phone: editingUser.phone.trim(),
      address: editingUser.address.trim()
    })

    if (res.data.code === 200) {
      await showAlert('用户信息修改成功', '', 'success')
      closeEditUserModal()
      getUserList()
      // 如果用户详情弹窗打开，同步刷新数据
      if (showUserDetailModal.value) {
        openUserDetailModal(editingUser.id)
      }
    } else {
      await showAlert(res.data.msg || '修改失败', '', 'error')
    }
  } catch (err) {
    console.error('保存用户失败', err)
    await showAlert('修改用户信息失败，请检查后端接口', '', 'error')
  } finally {
    isSavingUser.value = false
  }
}

//用户封禁/解封操作
const toggleUserBan = async (user) => {
  const action = user.is_banned === 1 ? '解封' : '封禁'
  const tip = user.is_banned === 1 ? '解封后用户可正常登录' : '封禁后用户将无法登录系统'
  if (!(await showConfirm(`确定${action}该用户？${tip}`))) return

  try {
    const url = user.is_banned === 1
      ? `/api/admin/user/unban/${user.id}`  // 解封接口
      : `/api/admin/user/ban/${user.id}`    // 封禁接口

    const res = await request.post(url)
    if (res.data.code === 200) {
      await showAlert(`用户${action}成功`, '', 'success')
      getUserList()  // 刷新列表
    } else {
      await showAlert(res.data.msg || `${action}失败`, '', 'error')
    }
  } catch (err) {
    await showAlert(`${action}用户失败，请检查接口`, '', 'error')
  }
}

//删除用户
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

//商品管理
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

//删除商品
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

//商品上下架状态切换
const toggleGoodsOnlineStatus = async (goods) => {
  // 区分文案与提示
  const isOffline = goods.status === '下架'
  const actionText = isOffline ? '上架' : '下架'
  let confirmTip = ''

  if (goods.stock === 0) {
    if (!isOffline) {
      confirmTip = '该商品库存为0，确定执行下架操作？'
    } else {
      confirmTip = '该商品库存为0，上架后状态仍为【缺货】，确定继续？'
    }
  } else {
    confirmTip = `确定${actionText}该商品？`
  }

  // 确认弹窗
  if (!(await showConfirm(confirmTip))) return

  try {
    const res = await request.post(`/api/admin/goods/status/${goods.id}`)
    if (res.data.code === 200) {
      await showAlert(`商品${actionText}成功`, '', 'success')
      // 刷新商品列表
      getGoodsList()
    } else {
      await showAlert(res.data.msg || `${actionText}失败`, '', 'error')
    }
  } catch (err) {
    await showAlert(`商品${actionText}失败，请检查接口`, '', 'error')
  }
}


//订单管理
const getOrderList = async () => {
  try {
    const res = await request.get('/api/admin/orders', {
      params: { status: orderFilterStatus.value }
    })
    if (res.data.code === 200) {
      orderList.value = res.data.data
      orderCurrentPage.value = 1
      orderList.value.forEach(order => {
        editingStatus[order.id] = order.status
      })
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('获取订单列表失败', '', 'error')
  }
}

//订单筛选
const filterOrders = () => {
  getOrderList()
}

// 编辑订单弹窗操作
const openEditOrderModal = async (order) => {
  if (order.status === 'cancelled') {
    await showAlert('已取消的订单无法修改信息！', '', 'error')
    return
  }
  editingOrder.id = order.id
  editingOrder.order_no = order.order_no || ''
  editingOrder.receiver_name = order.receiver_name || ''
  editingOrder.receiver_phone = order.receiver_phone || ''
  editingOrder.receiver_detail = ''
  editingOrder.receiver_province = ''
  editingOrder.receiver_city = ''
  editingOrder.receiver_district = ''

  try {
    const addrObj = JSON.parse(order.receiver_address)
    editingOrder.receiver_province = addrObj.province || ''
    editingOrder.receiver_city = addrObj.city || ''
    editingOrder.receiver_district = addrObj.district || ''
    editingOrder.receiver_detail = addrObj.detail || ''
  } catch (e) {
    editingOrder.receiver_detail = order.receiver_address || ''
  }

  selectedOrderProvince.value = findRegionValueByLabel(regionData, editingOrder.receiver_province)
  if (selectedOrderProvince.value) {
    const provinceObj = regionData.find(p => p.value === selectedOrderProvince.value)
    if (provinceObj && provinceObj.children) {
      selectedOrderCity.value = findRegionValueByLabel(provinceObj.children, editingOrder.receiver_city)
      if (selectedOrderCity.value) {
        const cityObj = provinceObj.children.find(c => c.value === selectedOrderCity.value)
        if (cityObj && cityObj.children) {
          selectedOrderDistrict.value = findRegionValueByLabel(cityObj.children, editingOrder.receiver_district)
        }
      }
    }
  }

  editingOrder.total_price = parseFloat(order.total_price) || 0
  const validStatuses = ['pending_pay', 'pending_ship', 'pending_receive', 'completed', 'refund', 'refunded']
  editingOrder.status = validStatuses.includes(order.status) ? order.status : 'pending_pay'
  showEditOrderModal.value = true
}

const closeEditOrderModal = () => {
  showEditOrderModal.value = false
  editingOrder.id = null
  editingOrder.order_no = ''
  editingOrder.receiver_name = ''
  editingOrder.receiver_phone = ''
  editingOrder.receiver_address = ''
  editingOrder.receiver_province = ''
  editingOrder.receiver_city = ''
  editingOrder.receiver_district = ''
  editingOrder.receiver_detail = ''
  editingOrder.total_price = 0
  editingOrder.status = ''
  selectedOrderProvince.value = ''
  selectedOrderCity.value = ''
  selectedOrderDistrict.value = ''
}

//保存订单修改
const saveOrder = async () => {
  const originalOrder = orderList.value.find(o => o.id === editingOrder.id)
  if (originalOrder && originalOrder.status === 'cancelled') {
    await showAlert('已取消的订单无法修改信息！', '', 'error')
    closeEditOrderModal()
    return
  }

  if (!editingOrder.receiver_name.trim()) return await showAlert('请输入收货人姓名', '', 'error')
  if (!editingOrder.receiver_phone.trim()) return await showAlert('请输入联系电话', '', 'error')
  if (!/^1[3-9]\d{9}$/.test(editingOrder.receiver_phone.trim())) return await showAlert('请输入正确的11位手机号码', '', 'error')

  const pLabel = orderProvinces.value.find(p => p.value === selectedOrderProvince.value)?.label || ''
  const cLabel = orderCities.value.find(c => c.value === selectedOrderCity.value)?.label || ''
  const dLabel = orderDistricts.value.find(d => d.value === selectedOrderDistrict.value)?.label || ''

  if (!pLabel || !cLabel || !dLabel) {
    await showAlert('请选择完整的省市区', '', 'error')
    return
  }
  if (!editingOrder.receiver_detail.trim()) {
    await showAlert('请输入详细地址', '', 'error')
    return
  }
  if (editingOrder.total_price < 0) {
    await showAlert('订单总金额不能为负数', '', 'error')
    return
  }

  const addressJson = JSON.stringify({
    province: pLabel,
    city: cLabel,
    district: dLabel,
    detail: editingOrder.receiver_detail.trim()
  })

  const validStatuses = ['pending_pay', 'pending_ship', 'pending_receive', 'completed', 'refund', 'refunded']
  if (!validStatuses.includes(editingOrder.status)) {
    await showAlert('无效的订单状态', '', 'error')
    return
  }

  isSavingOrder.value = true
  try {
    const res = await request.post(`/api/admin/order/update/${editingOrder.id}`, {
      receiver_name: editingOrder.receiver_name.trim(),
      receiver_phone: editingOrder.receiver_phone.trim(),
      receiver_address: addressJson,
      total_price: parseFloat(editingOrder.total_price.toFixed(2)),
      status: editingOrder.status
    })

    if (res.data.code === 200) {
      await showAlert('订单信息修改成功', '', 'success')
      closeEditOrderModal()
      getOrderList()
    } else {
      await showAlert(res.data.msg || '修改失败', '', 'error')
    }
  } catch (err) {
    console.error('保存订单失败', err)
    await showAlert('修改订单信息失败，请稍后重试', '', 'error')
  } finally {
    isSavingOrder.value = false
  }
}

//编辑商品弹窗操作
const openEditGoodsModal = (goods) => {
  editingGoods.id = goods.id
  editingGoods.name = goods.name
  editingGoods.price = goods.price
  editingGoods.stock = goods.stock || 0
  editingGoods.category = goods.category || ''
  editingGoods.status = goods.stock === 0 ? '缺货' : (goods.status || '现货')
  editingGoods.brand = goods.brand || ''
  editingGoods.ip = goods.ip || ''
  editingGoods.charactername = goods.charactername || ''
  editingGoods.description = goods.description || ''
  showEditGoodsModal.value = true
}

const closeEditGoodsModal = () => {
  showEditGoodsModal.value = false
  editingGoods.id = null
  editingGoods.name = ''
  editingGoods.price = 0
  editingGoods.stock = 0
  editingGoods.category = ''
  editingGoods.status = ''
  editingGoods.brand = ''
  editingGoods.ip = ''
  editingGoods.charactername = ''
  editingGoods.description = ''
}

//库存变化处理
const handleStockChange = () => {
  const oldStock = editingGoods.stock
  editingGoods.stock = parseInt(editingGoods.stock) || 0
  
  // 库存变化时自动调整状态
  if (editingGoods.stock === 0) {
    editingGoods.status = '缺货'
  } else if (oldStock === 0 && editingGoods.stock > 0) {
    if (editingGoods.status === '缺货') {
      editingGoods.status = '现货'
    }
  }
}

//保存商品修改
const saveGoods = async () => {
  if (!editingGoods.name.trim()) return await showAlert('请输入商品名称', '', 'error')
  if (editingGoods.price < 0) return await showAlert('商品价格不能为负数', '', 'error')
  if (editingGoods.stock < 0) return await showAlert('商品库存不能为负数', '', 'error')

  const finalStatus = editingGoods.stock === 0 ? '缺货' : editingGoods.status

  isSavingGoods.value = true
  try {
    const res = await request.post(`/api/admin/goods/update/${editingGoods.id}`, {
      name: editingGoods.name.trim(),
      price: parseFloat(editingGoods.price),
      stock: parseInt(editingGoods.stock),
      category: editingGoods.category.trim(),
      status: finalStatus,
      brand: editingGoods.brand.trim(),
      ip: editingGoods.ip.trim(),
      character: editingGoods.charactername.trim(),
      description: editingGoods.description.trim()
    })

    if (res.data.code === 200) {
      await showAlert('商品信息修改成功', '', 'success')
      closeEditGoodsModal()
      getGoodsList()
    } else {
      await showAlert(res.data.msg || '修改失败', '', 'error')
    }
  } catch (err) {
    await showAlert('修改商品信息失败，请稍后重试', '', 'error')
  } finally {
    isSavingGoods.value = false
  }
}

//删除订单
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

//跳转到商品详情
const goToGoodsDetail = async (goodsId) => {
  try {
    router.push({
      name: 'goodsDetail',
      params: { id: goodsId }
    })
  } catch (err) {
    console.error('跳转商品详情页失败:', err)
    await showAlert('跳转商品详情页失败，请检查路由配置', '', 'error')
  }
}

//退出登录
const handleLogout = async () => {
  if (!(await showConfirm('确定退出？'))) return
  sessionStorage.removeItem('adminToken')
  sessionStorage.removeItem('adminNickname')
  router.push('/admin/login')
}

//切换标签加载数据
const handleTabChange = (tab) => {
  // 流量监控标签直接跳转到监控页面
  if (tab === 'monitor') {
    router.push('/admin/monitor')
    return
  }
  currentTab.value = tab
  if (tab === 'users') getUserList()
  if (tab === 'goods') getGoodsList()
  if (tab === 'orders') getOrderList()
}

//生命周期钩子
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

.container {
  max-width: 100%;
  margin: 0 auto;
}

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

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: #212121;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.admin-name {
  font-size: 14px;
  color: #666;
}

/* ===== 入驻状态标签样式 ===== */
.role-tag.approved {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}
.role-tag.pending {
  background: #fff7e6;
  color: #faad14;
  border: 1px solid #ffd591;
}
.role-tag.rejected {
  background: #fff1f0;
  color: #ff4d4f;
  border: 1px solid #ffa39e;
}
.role-tag.none {
  background: #f5f5f5;
  color: #8c8c8c;
  border: 1px solid #d9d9d9;
}

/* ===== 通过入驻按钮 ===== */
.btn-approve-apply {
  height: 32px;
  padding: 0 12px;
  background: #fff;
  color: #52c41a;
  border: 1px solid #52c41a;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 8px;
}
.btn-approve-apply:hover {
  background: #52c41a;
  color: #fff;
}

/* ===== 拒绝入驻按钮 ===== */
.btn-reject-apply {
  height: 32px;
  padding: 0 12px;
  background: #fff;
  color: #ff4d4f;
  border: 1px solid #ff4d4f;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 8px;
}
.btn-reject-apply:hover {
  background: #ff4d4f;
  color: #fff;
}



/* ===== 退出按钮 ===== */
.btn-logout {
  height: 36px;
  padding: 0 20px;
  background: #fb7299;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-logout:hover {
  background: #f7507f;
}

/* ===== 标签切换栏 ===== */
.tab-bar {
  background: #fff;
  padding: 0 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  gap: 32px;
  margin-bottom: 16px;
}

.tab-item {
  padding: 14px 0;
  font-size: 15px;
  color: #666;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}
.tab-item:hover {
  color: #fb7299;
}
.tab-item.active {
  color: #fb7299;
  border-bottom-color: #fb7299;
  font-weight: 500;
}

/* ===== 内容面板通用 ===== */
.content-panel {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  min-height: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #212121;
  margin: 0;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #999;
  font-size: 15px;
}

/* ===== 表格通用样式 ===== */
.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 10px;
  text-align: left;
  border-bottom: 1px solid #eee;
  vertical-align: middle;
}

.data-table th {
  background: #fafafa;
  font-size: 13px;
  font-weight: 600;
  color: #666;
  white-space: nowrap;
}

.data-table td {
  font-size: 14px;
  color: #333;
}

.data-table tr:hover {
  background-color: #f9f9f9;
}

/* ===== 商品表格 ===== */
.goods-thumb {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  object-fit: cover;
}

.goods-name {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===== 地址悬浮提示 ===== */
.address-cell {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  position: relative;
  cursor: pointer;
}
.address-cell:hover::after {
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 0;
  background: #262626;
  color: #fff;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  white-space: normal;
  max-width: 280px;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

/* ===== 角色标签 ===== */
.role-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-right: 6px;
}
.role-tag.admin {
  background: #fff2f0;
  color: #ff4d4f;
}
.role-tag.merchant {
  background: #e6f7ff;
  color: #1890ff;
}
.role-tag.user {
  background: #f6ffed;
  color: #52c41a;
}
.role-tag.banned {
  background: #fff2f0;
  color: #ff4d4f;
}

/* ===== 按钮样式 ===== */
.btn-approve {
  height: 32px;
  padding: 0 12px;
  background: #fff;
  color: #52c41a;
  border: 1px solid #52c41a;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 8px;
}
.btn-approve:hover {
  background: #52c41a;
  color: #fff;
}
.btn-reject {
  height: 32px;
  padding: 0 12px;
  background: #fff;
  color: #ff4d4f;
  border: 1px solid #ff4d4f;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 8px;
}
.btn-reject:hover {
  background: #ff4d4f;
  color: #fff;
}
.status-approved {
  display: inline-block;
  padding: 2px 8px;
  margin-right: 8px;
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
  border-radius: 4px;
  font-size: 12px;
}
.status-rejected {
  display: inline-block;
  padding: 2px 8px;
  margin-right: 8px;
  background: #fff1f0;
  color: #ff4d4f;
  border: 1px solid #ffa39e;
  border-radius: 4px;
  font-size: 12px;
}
.status-pending {
  display: inline-block;
  padding: 2px 8px;
  margin-right: 8px;
  background: #fff7e6;
  color: #faad14;
  border: 1px solid #ffd591;
  border-radius: 4px;
  font-size: 12px;
}

/* ===== 商品上下架按钮 ===== */
.btn-status {
  height: 32px;
  padding: 0 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin: 0 8px;
  border: 1px solid #67c23a;
  background: #fff;
  color: #67c23a;
}
.btn-status.btn-off {
  border-color: #e6a23c;
  color: #e6a23c;
}
.btn-status:hover {
  background: #67c23a;
  color: #fff;
}
.btn-status.btn-off:hover {
  background: #e6a23c;
  color: #fff;
}

/* ===== 编辑按钮 ===== */
.btn-edit {
  height: 32px;
  padding: 0 16px;
  background: #fff;
  color: #fb7299;
  border: 1px solid #fb7299;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 8px;
}
.btn-edit:hover:not(:disabled) {
  background: #fb7299;
  color: #fff;
}
.btn-edit:disabled {
  background: #f5f5f5;
  color: #ccc;
  border-color: #ddd;
  cursor: not-allowed;
}

/* ===== 删除按钮 ===== */
.btn-delete {
  height: 32px;
  padding: 0 16px;
  background: #fff;
  color: #ff4d4f;
  border: 1px solid #ff4d4f;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-delete:hover:not(:disabled) {
  background: #ff4d4f;
  color: #fff;
}
.btn-delete:disabled {
  background: #f5f5f5;
  color: #ccc;
  border-color: #ddd;
  cursor: not-allowed;
}

/* ===== 封禁按钮 ===== */
.btn-ban {
  height: 32px;
  padding: 0 16px;
  background: #fff;
  color: #ff9800;
  border: 1px solid #ff9800;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 8px;
}
.btn-ban:hover {
  background: #ff9800;
  color: #fff;
}

/* ===== 解封按钮 ===== */
.btn-ban.btn-unban {
  background: #fff;
  color: #52c41a;
  border-color: #52c41a;
}
.btn-ban.btn-unban:hover {
  background: #52c41a;
  color: #fff;
}

/* ===== 表格行悬停 ===== */
.goods-row,
.user-row {
  cursor: pointer;
  transition: background-color 0.2s;
}
.goods-row:hover,
.user-row:hover {
  background-color: #EFEFF2;
}

/* ===== 缺货文字 ===== */
.out-of-stock {
  color: #C53F3F;
  font-weight: 500;
}

/* ===== 订单筛选下拉框 ===== */
.order-filter {
  display: flex;
  align-items: center;
  gap: 10px;
}
.filter-select {
  height: 32px;
  padding: 0 12px;
  border: 1px solid #c0c4cc;
  border-radius: 4px;
  font-size: 13px;
  color: #262626;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 110px;
}
.filter-select:hover {
  border-color: #86909C;
}
.filter-select:focus {
  outline: none;
  border-color: #1E6BD6;
  box-shadow: 0 0 0 2px rgba(30, 107, 214, 0.1);
}

/* ===== 订单状态标签 ===== */
.order-status-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  min-width: 55px;
  text-align: center;
}
.order-status-tag.pending_pay {
  background: #fff7e6;
  color: #fa8c16;
}
.order-status-tag.pending_ship {
  background: #e6f7ff;
  color: #1890ff;
}
.order-status-tag.pending_receive {
  background: #f6ffed;
  color: #52c41a;
}
.order-status-tag.completed {
  background: #f6ffed;
  color: #52c41a;
}
.order-status-tag.refund {
  background: #fff2f0;
  color: #ff4d4f;
}
.order-status-tag.refunded {
  background: #f5f5f5;
  color: #8c8c8c;
}
.order-status-tag.cancelled {
  background: #f5f5f5;
  color: #8c8c8c;
}

.order-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

/* ===== 表单下拉框通用 ===== */
.status-select {
  height: 36px;
  padding: 0 10px;
  border: 1px solid #c0c4cc;
  border-radius: 4px;
  font-size: 13px;
  color: #262626;
  cursor: pointer;
  transition: all 0.2s;
}
.status-select:hover {
  border-color: #86909C;
}
.status-select:focus {
  outline: none;
  border-color: #1E6BD6;
  box-shadow: 0 0 0 2px rgba(30, 107, 214, 0.1);
}

/* ===== 订单表格列宽 ===== */
.order-table th:nth-child(1),
.order-table td:nth-child(1) {
  min-width: 160px;
  font-weight: 500;
  color: #1E6BD6;
}
.order-table th:nth-child(2),
.order-table td:nth-child(2) {
  min-width: 130px;
}
.order-table th:nth-child(3),
.order-table td:nth-child(3) {
  min-width: 90px;
}
.order-table th:nth-child(4),
.order-table td:nth-child(4) {
  min-width: 110px;
}
.order-table th:nth-child(5),
.order-table td:nth-child(5) {
  min-width: 180px;
}
.order-table th:nth-child(6),
.order-table td:nth-child(6) {
  min-width: 90px;
  font-weight: 500;
  color: #C53F3F;
}
.order-table th:nth-child(7),
.order-table td:nth-child(7) {
  min-width: 90px;
}
.order-table th:nth-child(8),
.order-table td:nth-child(8) {
  min-width: 140px;
}
.order-table th:nth-child(9),
.order-table td:nth-child(9) {
  min-width: 130px;
  text-align: center;
}

/* ===== 弹窗通用样式 ===== */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 400px;
  max-width: 90%;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  animation: modalFadeIn 0.2s ease;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}
.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: #212121;
  font-weight: 600;
}

.close-btn {
  font-size: 20px;
  color: #999;
  cursor: pointer;
  line-height: 1;
  transition: all 0.2s;
}
.close-btn:hover {
  color: #ff4d4f;
}

.modal-body {
  padding: 20px;
  max-height: 65vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  color: #333;
  box-sizing: border-box;
  outline: none;
  transition: all 0.2s;
}
.form-group input:hover,
.form-group textarea:hover,
.form-group select:hover {
  border-color: #fb7299;
}
.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  border-color: #fb7299;
  box-shadow: 0 0 0 2px rgba(251, 114, 153, 0.1);
}

.form-group input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
  color: #999;
}
.disabled-input {
  background: #f5f5f5 !important;
  color: #999;
}

.form-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

/* ===== 头像预览样式 ===== */
.avatar-preview {
  margin-top: 8px;
}
.avatar-preview img {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid #eee;
}

.modal-footer {
  display: flex;
  border-top: 1px solid #eee;
}
.modal-footer button {
  flex: 1;
  padding: 12px;
  border: none;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}
.modal-footer button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== 弹窗取消按钮 ===== */
.cancel-btn {
  background: #f5f5f5;
  color: #666;
}
.cancel-btn:hover {
  background: #eee;
}

/* ===== 弹窗确认按钮 ===== */
.confirm-btn {
  background: #fb7299;
  color: #fff;
}
.confirm-btn:hover:not(:disabled) {
  background: #f7507f;
}

/* ===== 三级地址选择器 ===== */
.area-selects {
  display: flex;
  gap: 10px;
}
.area-selects select {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #c0c4cc;
  border-radius: 4px;
  font-size: 13px;
  color: #262626;
  background: #fff;
  outline: none;
  transition: border-color 0.3s ease;
  cursor: pointer;
}
.area-selects select:focus {
  border-color: #1E6BD6;
}
.area-selects select:disabled {
  background: #E8EAED;
  cursor: not-allowed;
  color: #8c8c8c;
}

/* ===== 各弹窗固定宽度 ===== */
.edit-order-modal {
  width: 500px;
}
.edit-goods-modal {
  width: 550px;
}
.edit-user-modal {
  width: 450px;
}
.user-detail-modal {
  width: 450px;
}

/* ===== 用户详情模块 ===== */
.detail-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 8px 0;
  border-bottom: 1px solid #e5e6eb;
}
.detail-item:last-child {
  border-bottom: none;
}
.detail-item label {
  width: 80px;
  font-weight: 500;
  color: #595959;
  flex-shrink: 0;
}
.detail-item span {
  color: #262626;
  flex: 1;
}
.status-banned {
  color: #C53F3F;
  font-weight: 500;
}
.status-normal {
  color: #449A44;
  font-weight: 500;
}
.detail-avatar {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
}

/* ===== 响应式适配 ===== */
@media (max-width: 1200px) {
  .order-table th:nth-child(5),
  .order-table td:nth-child(5) {
    min-width: 140px;
  }
}

@media (max-width: 768px) {
  .admin-dashboard {
    padding: 70px 8px 20px;
  }
  .container {
    padding: 0;
  }
  .dashboard-header {
    padding: 12px 14px;
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  .header-title {
    font-size: 17px;
  }
  .header-right {
    width: 100%;
    justify-content: space-between;
  }
  .admin-name {
    font-size: 13px;
  }
  .btn-logout {
    height: 32px;
    padding: 0 14px;
    font-size: 13px;
  }
  .tab-bar {
    padding: 0 10px;
    gap: 16px;
    overflow-x: auto;
    flex-wrap: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  .tab-bar::-webkit-scrollbar {
    display: none;
  }
  .tab-item {
    flex-shrink: 0;
    white-space: nowrap;
    padding: 12px 0;
    font-size: 14px;
  }
  .content-panel {
    padding: 12px;
    border-radius: 8px;
  }
  .panel-header {
    flex-wrap: wrap;
    gap: 8px;
  }
  .panel-title {
    font-size: 16px;
  }
  .table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .data-table {
    min-width: 600px;
  }
  .data-table th,
  .data-table td {
    padding: 10px 8px;
    font-size: 12px;
  }
  .order-filter {
    flex-wrap: wrap;
  }
  .filter-select {
    min-width: 90px;
    font-size: 12px;
  }
  .order-actions {
    flex-wrap: wrap;
  }
  .btn-edit, .btn-delete, .btn-ban {
    height: 28px;
    padding: 0 10px;
    font-size: 12px;
    margin-right: 4px;
  }
  .btn-approve-apply, .btn-reject-apply {
    height: 28px;
    padding: 0 10px;
    font-size: 12px;
    margin-right: 4px;
  }
  .btn-status {
    height: 28px;
    padding: 0 10px;
    font-size: 12px;
    margin: 0 4px;
  }
  .modal-content {
    width: 95%;
    max-height: 85vh;
    border-radius: 8px;
  }
  .modal-body {
    max-height: 55vh;
    padding: 16px;
  }
  .edit-order-modal,
  .edit-goods-modal,
  .edit-user-modal,
  .user-detail-modal {
    width: 95%;
  }
  .area-selects {
    flex-direction: column;
    gap: 8px;
  }
  .area-selects select {
    width: 100%;
  }
  .detail-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  .detail-item label {
    width: auto;
  }
  .goods-thumb {
    width: 40px;
    height: 40px;
  }
  .empty-state {
    padding: 40px 0;
    font-size: 14px;
  }
  .role-tag {
    padding: 2px 8px;
    font-size: 11px;
  }
  .order-status-tag {
    padding: 2px 8px;
    font-size: 11px;
  }
}
</style>

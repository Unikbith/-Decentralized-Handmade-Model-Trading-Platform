<template>
  <div class="user-page">
    <div class="container">
      <!--左侧导航栏-->
      <aside class="menu-sidebar">
        <div class="sidebar-header">
          <div class="avatar-wrap">
            <div class="avatar" @click="handleSidebarAvatarClick">
              <img v-if="userInfo.avatar" :src="userInfo.avatar" alt="头像" />
              <span v-else>{{ userInfo.nickname?.charAt(0) || '游' }}</span>
            </div>
            <input
              type="file"
              ref="sidebarAvatarInput"
              accept="image/*"
              style="display: none"
              @change="handleSidebarAvatarUpload"
            />
          </div>
          <h3 class="user-nickname">{{ userInfo.nickname || '游客' }}</h3>
        </div>
        <nav class="sidebar-menu">
          <div
            v-for="item in menuList"
            :key="item.key"
            class="menu-item"
            :class="{ active: currentTab === item.key }"
            @click="currentTab = item.key"
          >
            <span class="menu-text">{{ item.label }}</span>
          </div>
          <div class="menu-item logout" @click="logout">
            <span class="menu-text">退出登录</span>
          </div>
        </nav>
      </aside>

      <!--右侧内容区-->
      <main class="content-area">
        <div v-if="currentTab === 'order'" class="content-panel">
          <h2 class="panel-title">我的订单</h2>
          <div class="order-status-tabs">
            <div 
              v-for="tab in orderTabs" 
              :key="tab.value"
              class="tab-item" 
              :class="{ active: activeStatus === tab.value }"
              @click="activeStatus = tab.value"
            >
              {{ tab.label }}
            </div>
          </div>

          <div class="order-list">
            <div v-if="filteredOrderList.length === 0" class="order-empty">
              <p>暂无订单记录</p>
              <button class="btn-primary" @click="goToHome">去逛逛</button>
            </div>

            <div v-for="order in paginatedOrderList" :key="order.id" class="order-card">
              <div class="order-header">
                <span class="order-no">订单号：{{ order.order_no }}</span>
                <span class="order-status" :class="order.status">
                  {{ getStatusText(order.status) }}
                  <span v-if="order.status === 'refund'" class="status-tip">
                    ({{ getReturnStatusForOrder(order.id) }})
                  </span>
                </span>
                <div class="order-action-menu">
                  <button class="menu-btn" @click="toggleMenu(order.id)">⋮</button>
                  <div class="dropdown-menu" v-if="activeMenuId === order.id">
                    <button
                      v-if="userRole !== 'merchant'"
                      class="dropdown-item"
                      @click="deleteOrder(order.id)"
                    >
                      删除订单
                    </button>

                    <button
                      v-if="userRole === 'merchant' && order.status === 'pending_receive'"
                      class="dropdown-item"
                      @click="remindUserReceive(order.id)"
                    >
                      提醒收货
                    </button>

                    <button
                      v-if="(order.status === 'pending_receive' || order.status === 'completed') && userRole !== 'merchant'"
                      class="dropdown-item"
                      @click="openReturnModal(order.id)"
                    >
                      申请售后
                    </button>
                  </div>
                </div>
              </div>
              
              <div 
                v-if="order.status === 'pending_pay' && orderTimerMap[order.id]" 
                class="order-countdown"
              >
                未支付订单将在 {{ formatCountdown(orderTimerMap[order.id]) }} 后自动取消
              </div>
              
              <div class="order-items">
                <div 
                  v-for="item in order.items" 
                  :key="item.id" 
                  class="order-item"
                  @click="goToGoodsDetail(item.goods_id)"
                >
                  <img :src="item.image" alt="" class="item-img" @error="handleImgError">
                  <div class="item-info">
                    <h4 class="item-name">{{ item.name }}</h4>
                    <p class="item-price">¥{{ (item.price || 0).toFixed(2) }} × {{ item.num }}</p>
                  </div>
                </div>
              </div>
              
              <div class="order-footer">
                <span class="order-time">下单时间：{{ order.created_at }}</span>
                <div class="order-actions">
                  <span class="order-total">合计：¥{{ (order.total_price || 0).toFixed(2) }}</span>
                  
                  <button 
                    v-if="order.status === 'pending_pay'" 
                    class="btn-pay"
                    @click="goToPay(order.order_no)"
                  >
                    去付款
                  </button>
                  
                  <button 
                    v-if="order.status === 'pending_receive' && userRole !== 'merchant'" 
                    class="btn-receive"
                    @click="receiveOrder(order.id)"
                  >
                    确认收货
                  </button>
                    
                  <button 
                    v-if="order.status === 'pending_ship' && userRole === 'merchant'" 
                    class="btn-ship"
                    @click="shipOrder(order.id)"
                  >
                    发货
                  </button>

                  <button
                    v-if="order.status === 'refund' && userRole !== 'merchant'"
                    class="btn-refund-status"
                    @click="viewReturnStatus(order.id)"
                  >
                    查看售后进度
                  </button>

                  <span v-if="order.status === 'refunded'" class="refunded-tag">已退款</span>
                </div>
              </div>
            </div>
          </div>
          <!--订单分页控件-->
          <Pagination 
            v-if="filteredOrderList.length > 0"
            v-model:currentPage="orderCurrentPage" 
            :total="filteredOrderList.length" 
            :pageSize="orderPageSize" 
          />
        </div>

        <div v-if="currentTab === 'collect'" class="content-panel">
          <div class="panel-header">
            <h2 class="panel-title">我的收藏</h2>
          </div>
          
          <div v-if="collectList.length === 0" class="history-empty">
            <p>暂无收藏商品</p>
            <button class="btn-primary" @click="goToHome">去逛逛</button>
          </div>

          <div v-else class="history-list">
            <div 
              v-for="item in paginatedCollectList" 
              :key="item.id" 
              class="history-item"
              @click="goToGoodsDetail(item.goods_id)"
            >
              <div class="goods-img">
                <img :src="item.image" alt="商品图片" />
              </div>
              <div class="goods-info">
                <h3 class="goods-name">{{ item.name }}</h3>
                <p class="goods-price">¥{{ (item.price || 0).toFixed(2) }}</p>
                <p class="browse-time">收藏时间：{{ item.created_at }}</p>
              </div>
              <div class="btn-container">
                <button 
                  class="btn-delete" 
                  @click.stop="deleteCollect(item.id)"
                >
                  取消收藏
                </button>
              </div>
            </div>
          </div>
          <!--收藏分页控件-->
          <Pagination 
            v-if="collectList.length > 0"
            v-model:currentPage="collectCurrentPage" 
            :total="collectList.length" 
            :pageSize="collectPageSize" 
          />
        </div>

        <!--售后申请弹窗-->
        <div v-if="showReturnModal" class="modal-mask" @click.self="showReturnModal = false">
          <div class="modal-content return-modal">
            <div class="modal-header">
              <h3>申请售后</h3>
              <span class="close-btn" @click="showReturnModal = false">&times;</span>
            </div>
            <div class="modal-body">
              <div class="form-item">
                <label>售后类型</label>
                <div class="radio-group">
                  <label class="radio-item" v-for="opt in returnTypeOptions" :key="opt.value">
                    <input type="radio" :value="opt.value" v-model="returnForm.type" />{{ opt.label }}
                  </label>
                </div>
              </div>
              <div class="form-item">
                <label>申请原因</label>
                <textarea v-model="returnForm.reason" class="form-textarea" placeholder="请详细描述售后原因..." maxlength="500"></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button class="cancel-btn" @click="showReturnModal = false">取消</button>
              <button class="confirm-btn" @click="submitReturn">提交申请</button>
            </div>
          </div>
        </div>

        <!--处理售后-->
        <div v-if="currentTab === 'returns'" class="content-panel">
          <div class="panel-header">
            <h2 class="panel-title">处理售后</h2>
          </div>
          <div v-if="merchantReturnList.length === 0" class="order-empty">
            <p>暂无售后申请</p>
          </div>
          <div v-else class="return-list">
            <div v-for="rr in paginatedReturnList" :key="rr.id" class="return-card">
              <div class="return-header">
                <span class="return-no">订单号：{{ rr.order_no }}</span>
                <span class="return-type-tag">{{ getReturnTypeText(rr.type) }}</span>
                <span class="return-status" :class="rr.status">{{ getReturnStatusText(rr.status) }}</span>
              </div>
              <div class="return-body">
                <p><strong>用户：</strong>{{ rr.user_nickname }}</p>
                <p><strong>商品：</strong>{{ rr.goods_name }}</p>
                <p><strong>金额：</strong>&yen;{{ (rr.total_price || 0).toFixed(2) }}</p>
                <p><strong>原因：</strong>{{ rr.reason }}</p>
                <p><strong>时间：</strong>{{ rr.created_at }}</p>
              </div>
              <div v-if="rr.status === 'pending'" class="return-actions">
                <button class="btn-approve" @click="approveReturn(rr.id)">同意售后</button>
                <button class="btn-reject" @click="rejectReturn(rr.id)">拒绝</button>
              </div>
              <div v-if="rr.status === 'approved'" class="return-actions">
                <button class="btn-approve" @click="completeRefund(rr.id)">确认退款完成</button>
              </div>
            </div>
          </div>
          <!-- 售后分页控件 -->
          <Pagination 
            v-if="merchantReturnList.length > 0"
            v-model:currentPage="returnCurrentPage" 
            :total="merchantReturnList.length" 
            :pageSize="returnPageSize" 
          />
        </div>

        <!--我的商品-->
        <div v-if="currentTab === 'goods'" class="content-panel">
          <div class="panel-header">
            <h2 class="panel-title">我的商品</h2>
            <button class="btn-primary" @click="goToPublish">发布新商品</button>
          </div>
          
          <div v-if="myGoodsList.length === 0" class="goods-empty">
            <p>暂无商品</p>
            <button class="btn-primary" @click="goToPublish">去发布</button>
          </div>

          <div v-else class="goods-list">
            <div 
              v-for="item in myGoodsList" 
              :key="item.id" 
              class="goods-item"
              @click="goToEditGoods(item.id)"
            >
              <div class="goods-img">
                <img :src="item.image" alt="商品图片" />
              </div>
              <div class="goods-info">
                <h3 class="goods-name">{{ item.name }}</h3>
                <p class="goods-price">¥{{ (item.price || 0).toFixed(2) }}</p>
                <p class="goods-status">状态：{{ item.status }}</p>
              </div>
              <div class="btn-container">
                <button 
                  class="btn-toggle-status"
                  :class="{ 'btn-off-shelf': item.status !== '下架', 'btn-on-shelf': item.status === '下架' }"
                  @click.stop="toggleGoodsStatus(item)"
                >
                  {{ item.status === '下架' ? '上架' : '下架' }}
                </button>
                <button 
                  class="btn-edit" 
                  @click.stop="goToEditGoods(item.id)"
                >
                  编辑
                </button>
                <button 
                  class="btn-delete-goods" 
                  @click.stop="deleteMyGoods(item.id)"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 个人信息 -->
        <div v-if="currentTab === 'info'" class="content-panel">
          <h2 class="panel-title">个人信息</h2>
          <form class="info-form" @submit.prevent="saveUserInfo">
            <div class="form-item">
              <label>生日</label>
              <el-date-picker
                v-model="formData.birthday"
                type="date"
                placeholder="年/月/日"
                format="YYYY年MM月DD日"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </div>
            <div class="form-item">
              <label>性别</label>
              <div class="radio-group">
                <label class="radio-item"><input type="radio" value="male" v-model="formData.gender" />男</label>
                <label class="radio-item"><input type="radio" value="female" v-model="formData.gender" />女</label>
                <label class="radio-item"><input type="radio" value="secret" v-model="formData.gender" />保密</label>
              </div>
            </div>
            <div class="form-item">
              <label>手机号码</label>
              <input
                type="text"
                v-model="formData.phone"
                class="form-input"
                placeholder="请输入11位手机号"
                maxlength="11"
              />
            </div>
            <div class="form-item">
              <label>收货人</label>
              <input
                type="text"
                v-model="formData.receiverName"
                class="form-input"
                placeholder="请输入默认收货人姓名"
                maxlength="20"
              />
            </div>
            <div class="form-item">
            <label>收货地址</label>
            <div class="address-selector">
              <el-cascader
                v-model="selectedArea"
                :options="regionData"
                placeholder="请选择省/市/区"
                @change="handleAreaChange"
                clearable
                style="width: 100%; margin-bottom: 16px;"
              />
              <input
                v-model="formData.streetAddress"
                type="text"
                class="form-input"
                placeholder="请填写详细地址（如街道、门牌号等）"
                @focus="handleAddressInputFocus"
              />
            </div>
          </div>
            <button type="submit" class="btn-primary">保存信息</button>
          </form>
        </div>

        <!--修改昵称 -->
        <div v-if="currentTab === 'nickname'" class="content-panel">
          <h2 class="panel-title">修改昵称</h2>
          <div class="nickname-form">
            <input type="text" v-model="newNickname" class="form-input" placeholder="请输入新昵称" maxlength="20" />
            <div class="btn-group">
              <button class="btn-primary" @click="saveNickname">保存修改</button>
              <button class="btn-secondary" @click="resetNickname">取消</button>
            </div>
          </div>
        </div>

        <!-- 我的足迹 -->
        <div v-if="currentTab === 'history'" class="content-panel">
          <div class="panel-header">
            <h2 class="panel-title">我的足迹</h2>
            <button 
              v-if="historyList.length > 0" 
              class="btn-clear" 
              @click="clearAllHistory"
            >
              清空全部
            </button>
          </div>
          
          <div v-if="historyList.length === 0" class="history-empty">
            <p>暂无浏览记录</p>
            <button class="btn-primary" @click="goToHome">去逛逛</button>
          </div>

          <div v-else class="history-list">
            <div 
              v-for="item in paginatedHistoryList" 
              :key="item.id" 
              class="history-item"
              @click="goToGoodsDetail(item.goodsId)"
            >
              <div class="goods-img">
                <img :src="item.image" alt="商品图片" />
              </div>
              <div class="goods-info">
                <h3 class="goods-name">{{ item.name }}</h3>
                <p class="goods-price">¥{{ (item.price || 0).toFixed(2) }}</p>
                <p class="browse-time">浏览时间：{{ item.browseTime }}</p>
              </div>
              <div class="btn-container">
                <button 
                  class="btn-delete" 
                  @click.stop="deleteHistory(item.id)"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
          <!-- 足迹分页控件 -->
          <Pagination 
            v-if="historyList.length > 0"
            v-model:currentPage="historyCurrentPage" 
            :total="historyList.length" 
            :pageSize="historyPageSize" 
          />
        </div>

        <!-- 入驻申请 -->
        <div v-if="currentTab === 'apply'" class="content-panel">
          <div class="panel-header">
            <h2 class="panel-title">入驻申请</h2>
          </div>
          
          <div class="apply-container">
            <div v-if="merchantApplyStatus === 'none'" class="apply-status-box">
              <div class="status-icon pending">📝</div>
              <h3>您还未提交入驻申请</h3>
              <p>提交入驻申请后，需要等待管理员审核通过才能发布商品</p>
              <button class="btn-primary btn-apply" @click="submitMerchantApply">
                提交入驻申请
              </button>
            </div>
            
            <div v-if="merchantApplyStatus === 'pending'" class="apply-status-box">
              <div class="status-icon waiting">⏳</div>
              <h3>您的入驻申请正在审核中</h3>
              <p>申请时间：{{ merchantApplyTime || '未知' }}</p>
              <p>请耐心等待管理员审核，审核通过后您将可以发布商品</p>
            </div>
            
            <div v-if="merchantApplyStatus === 'approved'" class="apply-status-box">
              <div class="status-icon success">✅</div>
              <h3>恭喜！您的入驻申请已通过</h3>
              <p>您现在可以正常发布商品了</p>
              <button class="btn-primary" @click="currentTab = 'goods'">
                去发布商品
              </button>
            </div>
            
            <div v-if="merchantApplyStatus === 'rejected'" class="apply-status-box">
              <div class="status-icon error">❌</div>
              <h3>您的入驻申请已被拒绝</h3>
              <p>很抱歉，您的入驻申请未通过审核，无法发布商品</p>
              <p>如有疑问，请联系平台管理员</p>
              <button class="btn-primary btn-apply" @click="submitMerchantApply">
                重新提交申请
              </button>
            </div>
          </div>
        </div>

        <!-- 修改密码 -->
        <div v-if="currentTab === 'password'" class="content-panel">
          <h2 class="panel-title">修改密码</h2>
          <form class="password-form" @submit.prevent="savePassword">
            <div class="form-item">
              <label>原密码</label>
              <input type="password" v-model="passwordData.oldPassword" class="form-input" placeholder="请输入原密码" />
            </div>
            <div class="form-item">
              <label>新密码</label>
              <input type="password" v-model="passwordData.newPassword" class="form-input" placeholder="8-20位" />
            </div>
            <div class="form-item">
              <label>确认新密码</label>
              <input type="password" v-model="passwordData.confirmPassword" class="form-input" placeholder="再次输入新密码" />
            </div>
            <button type="submit" class="btn-primary">确认修改</button>
          </form>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onUnmounted, onActivated } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import request from '@/api/request'
import { regionData, codeToText } from "element-china-area-data"
import { showAlert, showConfirm } from '@/utils/modal'
import Pagination from '@/components/Pagination.vue'

const router = useRouter()
const route = useRoute()

//  商家入驻状态
const merchantApplyStatus = ref('none')
const merchantApplyTime = ref('')

// 从Token解析角色
const getRoleFromToken = () => {
  const token = sessionStorage.getItem('token')
  if (!token) return ''
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.role || ''
  } catch (e) {
    return ''
  }
}

//全局状态
const userRole = ref('')
const currentTab = ref('order')

//根据URL参数切换标签页
const tabMap = {
  'info': 'info',
  'orders': 'order',
  'collects': 'collect',
  'history': 'history'
}

watch(() => route.query.tab, (tab) => {
  if (tab && tabMap[tab]) {
    currentTab.value = tabMap[tab]
  }
}, { immediate: true })

//订单相关数据
const orderList = ref([])
const activeStatus = ref('')
const activeMenuId = ref(null)

//用户信息
const userInfo = ref({})
const newNickname = ref('')
const sidebarAvatarInput = ref(null)
const passwordData = ref({ oldPassword: '', newPassword: '', confirmPassword: '' })

//地址选择器相关
const selectedArea = ref([])
const formData = ref({ 
  birthday: '', 
  gender: 'secret',
  phone: '',            
  receiverName: '',
  province: '',
  city: '',
  district: '',
  streetAddress: '',    
  fullAddress: ''       
})


const myGoodsList = ref([])
const historyList = ref([])
const collectList = ref([])

//分页
const collectCurrentPage = ref(1)
const collectPageSize = 10
const paginatedCollectList = computed(() => {
  const start = (collectCurrentPage.value - 1) * collectPageSize
  return collectList.value.slice(start, start + collectPageSize)
})

const historyCurrentPage = ref(1)
const historyPageSize = 10
const paginatedHistoryList = computed(() => {
  const start = (historyCurrentPage.value - 1) * historyPageSize
  return historyList.value.slice(start, start + historyPageSize)
})

const orderCurrentPage = ref(1)
const orderPageSize = 10
const paginatedOrderList = computed(() => {
  const start = (orderCurrentPage.value - 1) * orderPageSize
  return filteredOrderList.value.slice(start, start + orderPageSize)
})

// 售后相关数据
const showReturnModal = ref(false)
const returnOrderId = ref(null)
const returnForm = ref({ type: 'refund', reason: '' })
const returnTypeOptions = [
  { label: '仅退款', value: 'refund' },
  { label: '退货退款', value: 'return' },
  { label: '换货', value: 'exchange' }
]
const merchantReturnList = ref([])
const userReturnList = ref([])

// 售后分页
const returnCurrentPage = ref(1)
const returnPageSize = 10
const paginatedReturnList = computed(() => {
  const start = (returnCurrentPage.value - 1) * returnPageSize
  return merchantReturnList.value.slice(start, start + returnPageSize)
})

//待付款订单倒计时 
const AUTO_CANCEL_SECONDS = 5
const orderTimerMap = ref({})
const timerInterval = ref(null)

//倒计时格式化方法 
const formatCountdown = (seconds) => {
  if (!seconds || seconds <= 0) return ''
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (minutes > 0 && secs > 0) {
    return `${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分钟`
  } else {
    return `${secs}秒`
  }
}

//倒计时启动与自动取消
const startOrderTimers = () => {
  if (timerInterval.value) clearInterval(timerInterval.value)
  
  timerInterval.value = setInterval(() => {
    let hasUpdate = false
    for (const id of Object.keys(orderTimerMap.value)) {
      if (orderTimerMap.value[id] > 0) {
        orderTimerMap.value[id]--
        hasUpdate = true
      } else {
        autoCancelOrder(id)
        delete orderTimerMap.value[id]
        hasUpdate = true
      }
    }
    if (!hasUpdate) {
      clearInterval(timerInterval.value)
      timerInterval.value = null
    }
  }, 1000)
}

const autoCancelOrder = async (orderId) => {
  try {
    const order = orderList.value.find(o => o.id === orderId)
    if (!order) return
    
    await request.post(`/api/order/cancel/${order.order_no}`)
    await showAlert('订单已超时未支付，已自动取消，商品已返回您的购物车')
    getOrderList()
  } catch (err) {
    console.error('自动取消订单失败', err)
    try {
      await request.delete(`/api/order/delete/${orderId}`)
      getOrderList()
    } catch (deleteErr) {
      console.error('删除订单也失败', deleteErr)
    }
  }
}

const initOrderTimers = () => {
  orderTimerMap.value = {}
  const now = new Date().getTime()
  
  orderList.value.forEach(order => {
    if (order.status === 'pending_pay') {
      const createdAt = new Date(order.created_at.replace(/-/g, '/')).getTime()
      const elapsed = now - createdAt
      const remainingSeconds = Math.max(0, AUTO_CANCEL_SECONDS - Math.floor(elapsed / 1000))
      
      if (remainingSeconds > 0) {
        orderTimerMap.value[order.id] = remainingSeconds
      } else {
        autoCancelOrder(order.id)
      }
    }
  })
  
  startOrderTimers()
}

//左侧菜单列表
const menuList = computed(() => {
  if (userRole.value === 'merchant') {
    return [
      { key: 'order', label: '我的订单' },
      { key: 'returns', label: '处理售后' },
      { key: 'goods', label: '我的商品' },
      { key: 'apply', label: '入驻申请' }, 
    ]
  } else {
    return [
      { key: 'order', label: '我的订单' },
      { key: 'collect', label: '我的收藏' },
      { key: 'info', label: '个人信息' },
      { key: 'nickname', label: '修改昵称' },
      { key: 'history', label: '我的足迹' },
      { key: 'password', label: '修改密码' }
    ]
  }
})

//订单状态标签
const orderTabs = computed(() => {
  if (userRole.value === 'merchant') {
    return [
      { label: '全部', value: '' },
      { label: '待发货', value: 'pending_ship' },
      { label: '待收货', value: 'pending_receive' },
      { label: '已完成', value: 'completed' },
      { label: '退款/售后', value: 'refund' }
    ]
  } else {
    return [
      { label: '全部', value: '' },
      { label: '待付款', value: 'pending_pay' },
      { label: '待收货', value: 'pending_receive' },
      { label: '已完成', value: 'completed' },
      { label: '退款/售后', value: 'refund' }
    ]
  }
})

//筛选后的订单列表
const filteredOrderList = computed(() => {
  let list = [...orderList.value]
  
  if (activeStatus.value) {
    if (activeStatus.value === 'refund') {
      list = list.filter(order => ['refund', 'refunded'].includes(order.status))
    } else {
      list = list.filter(order => order.status === activeStatus.value)
    }
  }
  
  return list
})

//收藏相关方法
const getCollectList = async () => {
  try {
    const res = await request.get('/api/collect/list')
    if (res.data.code === 200) {
      collectList.value = res.data.data
      collectCurrentPage.value = 1
    }
  } catch (err) {
    console.error('获取收藏失败:', err)
    await showAlert('获取收藏失败', '', 'error')
  }
}

const deleteCollect = async (collectId) => {
  if (!(await showConfirm('确定取消收藏该商品吗？'))) return
  try {
    await request.post('/api/collect/delete', { id: collectId })
    collectList.value = collectList.value.filter(item => item.id !== collectId)
    await showAlert('取消收藏成功', '', 'success')
  } catch (err) {
    console.error('取消收藏失败:', err)
    await showAlert('操作失败', '', 'error')
  }
}

//生命周期钩子
onMounted(() => {
  userRole.value = getRoleFromToken()
  currentTab.value = 'order'
  
  if (route.query.tab && menuList.value.some(item => item.key === route.query.tab)) {
    currentTab.value = route.query.tab
  }
  
  getUserInfo()
  document.addEventListener('click', closeAllMenus)
  
  watch(() => route.query.tab, (newTab) => {
    if (newTab && menuList.value.some(item => item.key === newTab)) {
      currentTab.value = newTab
    }
  })
})

onUnmounted(() => {
  document.removeEventListener('click', closeAllMenus)
  if (timerInterval.value) clearInterval(timerInterval.value)
})

onActivated(() => {
  if (currentTab.value === 'order') {
    getOrderList()
    if (userRole.value !== 'merchant') {
      refreshUserReturns()
    }
  }
  if (currentTab.value === 'collect') {
    getCollectList()
  }
})

//通用导航方法
const goToHome = () => router.push('/')
const goToPublish = () => router.push('/publish')
const goToEditGoods = (goodsId) => router.push(`/publish?id=${goodsId}`)
const goToGoodsDetail = (goodsId) => router.push(`/goods/detail/${goodsId}`)

const handleImgError = (e) => {
  e.target.src = '/assets/picture-DPjQRauj.png'
}

const logout = async (force = false) => {
  if (!force && !(await showConfirm('确定退出？'))) return
  sessionStorage.clear()
  await showAlert('退出成功')
  router.push('/login')
}

//用户信息获取与更新
const getUserInfo = async () => {
  const token = sessionStorage.getItem('token')
  if (!token) {
    await showAlert('请先登录！', '', 'error')
    router.push('/login')
    return
  }
  try {
    const res = await request.get('/api/user/info')
    if (res.data.code === 200) {
      userInfo.value = res.data.data
      merchantApplyStatus.value = res.data.data.apply_status || 'none'
      
      let province = '', city = '', district = '', detail = '';
      if (res.data.data.address_struct) {
        const parsed = res.data.data.address_struct;
        province = parsed.province || '';
        city = parsed.city || '';
        district = parsed.district || '';
        detail = parsed.detail || '';
        if (parsed.name) formData.value.receiverName = parsed.name;
        if (parsed.phone) formData.value.phone = parsed.phone;
      } else if (res.data.data.address) {
        try {
          const parsed = JSON.parse(res.data.data.address);
          province = parsed.province || '';
          city = parsed.city || '';
          district = parsed.district || '';
          detail = parsed.detail || '';
          if (parsed.name) formData.value.receiverName = parsed.name;
          if (parsed.phone) formData.value.phone = parsed.phone;
        } catch {
          detail = res.data.data.address;
        }
      }

      formData.value = { 
        ...formData.value,
        birthday: res.data.data.birthday, 
        gender: res.data.data.gender,
        province,
        city,
        district,
        streetAddress: detail,
        fullAddress: res.data.data.address || ''
      };
      
      if (province && city && district) {
        const findCode = (label, list) => {
          for (const item of list) {
            if (item.label === label) return item.value
            if (item.children) {
              const found = findCode(label, item.children)
              if (found) return found
            }
          }
          return null
        }
        const pCode = findCode(province, regionData);
        const cCode = findCode(city, regionData);
        const dCode = findCode(district, regionData);
        if (pCode && cCode && dCode) {
          selectedArea.value = [pCode, cCode, dCode];
        }
      }
      
      newNickname.value = res.data.data.nickname
    } else {
      await showAlert('获取用户信息失败：' + res.data.msg, '', 'error')
      logout(true)
    }
  } catch (err) {
    await showAlert('获取用户信息失败：' + (err.response?.data?.msg || '网络错误'), '', 'error')
    logout(true)
  }
}

//商家入驻相关方法
const getMerchantApplyStatus = async () => {
  if (userRole.value !== 'merchant') return
  
  try {
    const res = await request.get('/api/merchant/apply-status')
    if (res.data.code === 200) {
      merchantApplyStatus.value = res.data.data.apply_status
      merchantApplyTime.value = res.data.data.apply_time || ''
    }
  } catch (err) {
    console.error('获取入驻状态失败:', err)
  }
}

const submitMerchantApply = async () => {
  if (!(await showConfirm('确定提交入驻申请吗？提交后需要等待管理员审核。'))) return
  
  try {
    const res = await request.post('/api/merchant/apply')
    if (res.data.code === 200) {
      await showAlert('入驻申请已提交，请等待管理员审核', '', 'success')
      merchantApplyStatus.value = 'pending'
      getMerchantApplyStatus()
    } else {
      await showAlert(res.data.msg || '提交失败', '', 'error')
    }
  } catch (err) {
    console.error('提交入驻申请失败:', err)
    await showAlert('提交失败，请检查网络连接', '', 'error')
  }
}

//保存用户信息
const saveUserInfo = async () => {
  if (!formData.value.province || !formData.value.city || !formData.value.district) {
    return await showAlert('请选择完整的省市区信息')
  }
  if (!formData.value.streetAddress.trim()) {
    return await showAlert('请填写详细地址')
  }
  if (formData.value.phone && !/^1[3-9]\d{9}$/.test(formData.value.phone.trim())) {
    return await showAlert('请输入正确的11位手机号码')
  }
  
  updateFullAddress()
  
  try {
    const addressStruct = {
      name: formData.value.receiverName.trim(),
      phone: formData.value.phone.trim(),
      province: formData.value.province,
      city: formData.value.city,
      district: formData.value.district,
      detail: formData.value.streetAddress.trim()
    }
    
    await request.post('/api/user/update', {
      birthday: formData.value.birthday,
      gender: formData.value.gender,
      phone: formData.value.phone.trim(),
      receiverName: formData.value.receiverName.trim(),
      address_struct: addressStruct,
      address: formData.value.fullAddress
    })
    await showAlert('保存成功', '', 'success')
    getUserInfo()
  } catch (err) {
    await showAlert(err.response?.data?.msg || '网络错误', '', 'error')
  }
}

//修改昵称
const saveNickname = async () => {
  const nickname = newNickname.value.trim()
  if (!nickname) return await showAlert('昵称不能为空')
  
  if (nickname === userInfo.value.nickname) {
    return await showAlert('新昵称与原昵称相同')
  }

  try {
    await request.post('/api/user/update-nickname', { nickname })
    await showAlert('修改成功', '', 'success')
    getUserInfo() 
    resetNickname() 
  } catch (err) {
    await showAlert(err.response?.data?.msg || '网络错误', '', 'error')
  }
}

const resetNickname = () => {
  newNickname.value = userInfo.value.nickname || ''
}

//售后状态查询
const getReturnStatusForOrder = (orderId) => {
  const rr = userReturnList.value.find(r => r.order_id === orderId)
  if (!rr) return '处理中'
  
  const statusMap = {
    pending: '待商家处理',
    approved: '商家已同意',
    rejected: '已拒绝',
    refunded: '已退款'
  }
  return statusMap[rr.status] || rr.status
}

//头像上传
const handleSidebarAvatarClick = () => {
  sidebarAvatarInput.value.click()
}

const handleSidebarAvatarUpload = async (e) => {
  const file = e.target.files[0]
  sidebarAvatarInput.value.value = ''
  if (!file || !file.type.startsWith('image/') || file.size > 2*1024*1024) {
    return await showAlert('请选择 2MB 以内的图片')
  }
  try {
    const formData = new FormData()
    formData.append('file', file)
    const uploadRes = await request.post('/api/upload/image', formData)
    await request.post('/api/user/update-avatar', { avatar: uploadRes.data.url })
    await showAlert('头像更新成功', '', 'success')
    getUserInfo()
  } catch (err) {
    await showAlert(err.response?.data?.msg || '上传失败', '', 'error')
  }
}

//修改密码
const savePassword = async () => {
  const { oldPassword, newPassword, confirmPassword } = passwordData.value
  if (!oldPassword || !newPassword || newPassword !== confirmPassword) {
    return await showAlert('请完善密码信息，两次密码需一致')
  }
  try {
    await request.post('/api/user/update-password', { oldPassword, newPassword })
    sessionStorage.clear()
    await showAlert('修改成功，请重新登录', '', 'success')
    router.push('/login')
  } catch (err) {
    await showAlert(err.response?.data?.msg || '网络错误', '', 'error')
  }
}

//订单相关方法
const loading = ref(false)

const getOrderList = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/order/list', {
      params: { status: activeStatus.value }
    })
    if (res.data.code === 200) {
      orderList.value = res.data.data.map(order => {
        let fullAddress = order.receiver_address
        try {
          const addressObj = JSON.parse(order.receiver_address)
          fullAddress = `${addressObj.province || ''}${addressObj.city || ''}${addressObj.district || ''}${addressObj.detail || ''}`
        } catch {}
        return { ...order, receiver_address: fullAddress }
      })
      initOrderTimers()
    }
  } catch (err) {
    console.error('获取订单列表失败:', err)
    await showAlert('获取订单列表失败', '', 'error')
  } finally {
    loading.value = false
  }
}

const getStatusText = (status) => {
  const statusMap = {
    'pending_pay': '待付款',
    'pending_ship': '待发货',
    'pending_receive': '待收货',
    'completed': '已完成',
    'refund': '售后处理中',
    'refunded': '已退款',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const toggleMenu = (orderId) => {
  activeMenuId.value = activeMenuId.value === orderId ? null : orderId
}

const closeAllMenus = (e) => {
  if (!e.target?.classList?.contains('menu-btn') && !e.target?.classList?.contains('dropdown-item')) {
    activeMenuId.value = null
  }
}

const goToPay = (orderNo) => {
  router.push(`/confirmPay?order_no=${orderNo}`)
}

const receiveOrder = async (orderId) => {
  if (!(await showConfirm('确定确认收货？'))) return
  try {
    const res = await request.post(`/api/order/receive/${orderId}`)
    if (res.data.code === 200) {
      await showAlert('确认收货成功', '', 'success')
      getOrderList()
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('确认收货失败', '', 'error')
  }
}

const shipOrder = async (orderId) => {
  if (!(await showConfirm('确定要发货吗？'))) return
  try {
    const res = await request.post(`/api/order/ship/${orderId}`)
    if (res.data.code === 200) {
      await showAlert('发货成功，等待用户确认收货', '', 'success')
      getOrderList()
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('发货失败', '', 'error')
  }
}

const deleteOrder = async (orderId) => {
  if (!(await showConfirm('确定要删除这个订单吗？此操作不可恢复'))) return
  try {
    const orderToDelete = orderList.value.find(o => o.id === orderId)
    
    const res = await request.delete(`/api/order/delete/${orderId}`)
    if (res.data.code === 200) {
      if (orderToDelete && (orderToDelete.status === 'pending_pay' || orderToDelete.status === 'cancelled')) {
        await showAlert('删除成功，商品已返回您的购物车', '', 'success')
      } else {
        await showAlert('删除成功', '', 'success')
      }
      getOrderList()
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('删除失败', '', 'error')
  }
}

//售后申请方法
const openReturnModal = (orderId) => {
  activeMenuId.value = null
  returnOrderId.value = orderId
  returnForm.value = { type: 'refund', reason: '' }
  showReturnModal.value = true
}

const submitReturn = async () => {
  if (!returnForm.value.reason.trim()) return await showAlert('请填写申请原因')
  try {
    const res = await request.post('/api/order/return/apply', {
      order_id: returnOrderId.value,
      type: returnForm.value.type,
      reason: returnForm.value.reason
    })
    if (res.data.code === 200) {
      await showAlert('售后申请已提交', '', 'success')
      showReturnModal.value = false
      getOrderList()
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert(err.response?.data?.msg || '提交失败', '', 'error')
  }
}

const viewReturnStatus = async (orderId) => {
  try {
    const res = await request.get('/api/order/return/user')
    if (res.data.code === 200) {
      const rr = res.data.data.find(r => r.order_id === orderId)
      if (rr) {
        let statusText = ''
        let actionText = ''
        
        switch(rr.status) {
          case 'pending':
            statusText = '待商家处理'
            actionText = '商家正在审核您的申请，请耐心等待'
            break
          case 'approved':
            statusText = '商家已同意'
            actionText = rr.type === 'refund' ? '退款已完成' : '请按照商家提供的地址退货，商家收到后将为您退款'
            break
          case 'rejected':
            statusText = '商家已拒绝'
            actionText = '如有疑问，请联系商家协商'
            break
          case 'refunded':
            statusText = '已退款'
            actionText = '退款已完成，请注意查收'
            break
        }
        
        await showAlert(`
售后详情
\n订单号：${rr.order_no}
\n售后类型：${getReturnTypeText(rr.type)}
\n申请时间：${rr.created_at}
\n当前状态：${statusText}
申请原因：${rr.reason}

${actionText}
        `)
      } else {
        await showAlert('未找到该订单的售后记录', '', 'error')
      }
    }
  } catch (err) { 
    await showAlert('查询售后状态失败，请稍后重试', '', 'error') 
  }
}

//售后状态文本转换
const getReturnTypeText = (type) => ({ refund: '仅退款', return: '退货退款', exchange: '换货' }[type] || type)
const getReturnStatusText = (status) => ({
  pending: '待处理',
  approved: '已同意',
  rejected: '已拒绝',
  refunded: '已退款'
}[status] || status)

//商家处理售后方法
const getMerchantReturns = async () => {
  try {
    const res = await request.get('/api/order/return/merchant')
    if (res.data.code === 200) merchantReturnList.value = res.data.data
  } catch (err) { await showAlert('获取售后列表失败', '', 'error') }
}

const approveReturn = async (returnId) => {
  if (!(await showConfirm('确定同意该售后申请？'))) return
  try {
    await request.post(`/api/order/return/approve/${returnId}`)
    await showAlert('已同意，请等待退款', '', 'success')
    getMerchantReturns()
    getOrderList()
  } catch (err) { await showAlert(err.response?.data?.msg || '操作失败', '', 'error') }
}

const rejectReturn = async (returnId) => {
  if (!(await showConfirm('确定拒绝该售后申请？'))) return
  try {
    await request.post(`/api/order/return/reject/${returnId}`)
    await showAlert('已拒绝', '', 'success')
    getMerchantReturns()
    getOrderList()
  } catch (err) { await showAlert(err.response?.data?.msg || '操作失败', '', 'error') }
}

const completeRefund = async (returnId) => {
  if (!(await showConfirm('确认已完成退款？'))) return
  try {
    await request.post(`/api/order/return/refund/${returnId}`)
    await showAlert('退款已完成', '', 'success')
    getMerchantReturns()
    getOrderList()
  } catch (err) { await showAlert(err.response?.data?.msg || '操作失败', '', 'error') }
}

//商家商品管理
const getMyGoods = async () => {
  try {
    const res = await request.get('/api/goods/merchant')
    if (res.data.code === 200) {
      myGoodsList.value = res.data.data
    } else {
      await showAlert('获取商品失败：' + res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('获取商品失败：' + (err.response?.data?.msg || '网络错误'), '', 'error')
  }
}

const toggleGoodsStatus = async (item) => {
  const newStatus = item.status === '下架' ? '现货' : '下架'
  const actionText = newStatus === '下架' ? '下架' : '上架'
  if (!(await showConfirm(`确定${actionText}该商品吗？`))) return
  try {
    const res = await request.post(`/api/goods/update/${item.id}`, { status: newStatus })
    if (res.data.code === 200) {
      await showAlert(`${actionText}成功`, '', 'success')
      getMyGoods()
    } else {
      await showAlert(res.data.msg || `${actionText}失败`, '', 'error')
    }
  } catch (err) {
    await showAlert(err.response?.data?.msg || '操作失败', '', 'error')
  }
}

//删除我的商品
const deleteMyGoods = async (goodsId) => {
  if (!(await showConfirm('确定删除该商品吗？删除后无法恢复！'))) return
  try {
    const res = await request.delete(`/api/goods/delete/${goodsId}`)
    if (res.data.code === 200) {
      await showAlert('删除成功', '', 'success')
      getMyGoods()
    } else {
      await showAlert(res.data.msg || '删除失败', '', 'error')
    }
  } catch (err) {
    await showAlert(err.response?.data?.msg || '删除失败', '', 'error')
  }
}

//浏览足迹方法
const getUserHistory = async () => {
  try {
    const res = await request.get('/api/user/history')
    if (res.data.code === 200) {
      historyList.value = res.data.data
      historyCurrentPage.value = 1
    } else {
      await showAlert('获取足迹失败：' + res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('获取足迹失败：' + (err.response?.data?.msg || '网络错误'), '', 'error')
  }
}

const deleteHistory = async (historyId) => {
  if (!(await showConfirm('确定删除这条浏览记录？'))) return
  try {
    await request.post('/api/user/history/delete', { id: historyId })
    historyList.value = historyList.value.filter(item => item.id !== historyId)
    await showAlert('删除成功', '', 'success')
  } catch (err) {
    await showAlert('删除失败：' + (err.response?.data?.msg || '网络错误'), '', 'error')
  }
}

const clearAllHistory = async () => {
  if (!(await showConfirm('确定清空所有浏览记录？此操作不可恢复'))) return
  try {
    await request.post('/api/user/history/clear')
    historyList.value = []
    await showAlert('清空成功', '', 'success')
  } catch (err) {
    await showAlert('清空失败：' + (err.response?.data?.msg || '网络错误'), '', 'error')
  }
}

const refreshUserReturns = async () => {
  try {
    const res = await request.get('/api/order/return/user')
    if (res.data.code === 200) {
      userReturnList.value = res.data.data
    }
  } catch (err) {
    console.error('刷新售后列表失败:', err)
  }
}

//地址选择器方法
const handleAreaChange = (value) => {
  if (value && value.length === 3) {
    formData.value.province = codeToText[value[0]] || ''
    formData.value.city = codeToText[value[1]] || ''
    formData.value.district = codeToText[value[2]] || ''
    formData.value.streetAddress = ''
  } else {
    formData.value.province = ''
    formData.value.city = ''
    formData.value.district = ''
    formData.value.streetAddress = ''
  }
  updateFullAddress()
}

const handleAddressInputFocus = () => {
  if (formData.value.streetAddress.startsWith(formData.value.province)) {
    formData.value.streetAddress = ''
  }
}

const updateFullAddress = () => {
  const { province, city, district, streetAddress } = formData.value
  formData.value.fullAddress = `${province}${city}${district}${streetAddress}`
}

//监听器：标签页切换加载数据
watch(currentTab, (tab) => {
  if (tab === 'nickname') resetNickname()
  if (tab === 'history') getUserHistory()
  if (tab === 'goods') getMyGoods()
  if (tab === 'collect') getCollectList()
  if (tab === 'apply') getMerchantApplyStatus()
  if (tab === 'password') passwordData.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  if (tab === 'order') {
    activeStatus.value = ''
    getOrderList()
    if (userRole.value !== 'merchant') {
      refreshUserReturns()
    }
  }
  if (tab === 'returns') getMerchantReturns()
}, { immediate: true })

//监听器：订单状态筛选
watch(activeStatus, () => {
  if (currentTab.value === 'order') {
    getOrderList()
    orderCurrentPage.value = 1
  }
})
</script>

<style scoped>
/* ===== 页面布局 ===== */
.user-page {
  min-height: 100vh;
  padding: 80px 20px 40px;
  box-sizing: border-box;
  background: rgb(234, 243, 251);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 24px;
}

/* ===== 左侧侧边栏 ===== */
.menu-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.sidebar-header {
  padding: 30px 20px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
}

.avatar-wrap .avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #fb7299;
  color: #fff;
  font-size: 36px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.2s;
}

.avatar-wrap .avatar:hover {
  transform: scale(1.05);
}

.avatar-wrap .avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-nickname {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.sidebar-menu {
  padding: 16px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 18px 32px;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
  font-size: 15px;
}

.menu-item:hover {
  background: #f5f5f5;
  color: #333;
}

.menu-item.active {
  background: #fff5f8;
  color: #fb7299;
  font-weight: 500;
}

.menu-item.logout {
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
  color: #ff4d4f;
}

.menu-item.logout:hover {
  background: #fff1f0;
}

/* ===== 右侧内容区 ===== */
.content-area {
  flex: 1;
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  min-height: 600px;
}

.content-panel {
  height: 100%;
  background: #fafafa;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-title {
  font-size: 22px;
  font-weight: 600;
  color: #212121;
  margin: 0;
}

.btn-clear {
  background: none;
  border: none;
  color: #999;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.2s;
}

.btn-clear:hover {
  color: #ff4d4f;
}

.order-empty,
.history-empty,
.goods-empty {
  text-align: center;
  padding: 60px 0;
  color: #999;
}

.order-empty p,
.history-empty p,
.goods-empty p {
  margin: 0 0 20px;
  font-size: 16px;
}

/* ===== 订单状态标签 ===== */
.order-status-tabs {
  display: flex;
  gap: 32px;
  margin-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.tab-item {
  padding: 12px 0;
  font-size: 15px;
  color: #666;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-item:hover,
.tab-item.active {
  color: #fb7299;
  border-bottom-color: #fb7299;
}

.apply-hint {
  text-align: center;
  padding: 20px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}
.apply-hint.success {
  color: #52c41a;
}
.apply-hint.error {
  color: #ff4d4f;
}
.apply-modal {
  width: 400px;
}

/* ===== 订单卡片 ===== */
.order-card {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;
  position: relative;
  background: #fff;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  position: relative;
}

.order-no {
  font-size: 14px;
  color: #666;
}

.order-status {
  font-size: 14px;
  font-weight: 500;
  margin-right: 40px;
}

.order-status.pending_pay { color: #faad14; }
.order-status.pending_ship { color: #faad14; }
.order-status.pending_receive { color: #1890ff; }
.order-status.completed { color: #52c41a; }
.order-status.refund { color: #ff4d4f; }
.order-status.refunded { color: #999; text-decoration: line-through; }
.order-status.cancelled { color: #999; text-decoration: line-through; }

.order-countdown {
  padding: 8px 20px;
  background: #fff7e6;
  color: #faad14;
  font-size: 13px;
  border-bottom: 1px dashed #ffe58f;
}

.order-action-menu {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
}

.menu-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.menu-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.dropdown-menu {
  position: absolute;
  right: 0;
  top: 100%;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
  min-width: 120px;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 10px 16px;
  text-align: left;
  background: none;
  border: none;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.dropdown-item:hover {
  background: #f5f5f5;
  color: #ff4d4f;
}

.order-items {
  padding: 16px 20px;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
  cursor: pointer;
}

.order-item .item-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}

.order-item .item-info {
  flex: 1;
}

.order-item .item-name {
  font-size: 14px;
  color: #333;
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.order-item .item-price {
  font-size: 14px;
  color: #666;
  margin: 0;
}

/* ===== 入驻申请页面 ===== */
.apply-container {
  padding: 20px 0;
}

.apply-status-box {
  text-align: center;
  padding: 60px 40px;
  background: #fafafa;
  border-radius: 12px;
  border: 1px dashed #d9d9d9;
}

.status-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.status-icon.pending {
  color: #faad14;
}

.status-icon.waiting {
  color: #1890ff;
}

.status-icon.success {
  color: #52c41a;
}

.status-icon.error {
  color: #ff4d4f;
}

.apply-status-box h3 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px;
}

.apply-status-box p {
  font-size: 14px;
  color: #666;
  margin: 8px 0;
  line-height: 1.6;
}

.btn-apply {
  margin-top: 24px;
  padding: 12px 32px;
  font-size: 16px;
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}

.order-time {
  font-size: 14px;
  color: #999;
}

.order-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.order-total {
  font-size: 16px;
  font-weight: 600;
  color: #ff6b9d;
}

/* ===== 订单操作按钮 ===== */
.btn-pay { background: #fb7299; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; font-size: 14px; cursor: pointer; }
.btn-pay:hover { background: #f56a8f; }
.btn-receive { background: #fb7299; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; font-size: 14px; cursor: pointer; }
.btn-receive:hover { background: #f56a8f; }
.btn-ship { background: #1890ff; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; font-size: 14px; cursor: pointer; }
.btn-ship:hover { background: #096dd9; }
.btn-refund-status { background: #faad14; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; font-size: 14px; cursor: pointer; }
.btn-refund-status:hover { background: #d48806; }
.refunded-tag { font-size: 14px; color: #999; font-weight: 500; }

/* ===== 商品/足迹/收藏列表 ===== */
.goods-list, .history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.goods-item, .history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s;
  min-width: 0;
}

.goods-item:hover, .history-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.goods-img {
  width: 100px;
  height: 100px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
}

.goods-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.goods-info { 
  flex: 1;
  min-width: 0;
}

.goods-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin: 0 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.goods-price {
  font-size: 18px;
  font-weight: 600;
  color: #ff6b9d;
  margin: 0 0 8px;
}

.goods-status { 
  font-size: 14px; 
  color: #999; 
  margin: 0; 
}

.browse-time { 
  font-size: 14px; 
  color: #999; 
  margin: 0; 
}

/* ===== 按钮容器 ===== */
.btn-container {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-edit {
  background: #fb7299;
  border: none;
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

.btn-edit:hover { 
  background: #f7507f; 
}

.btn-delete-goods {
  background: #ff4d4f;
  border: none;
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-delete-goods:hover {
  background: #ff7875;
}

.btn-toggle-status {
  background: #faad14;
  border: none;
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

.btn-toggle-status:hover { 
  opacity: 0.9; 
}

.btn-off-shelf { 
  background: #faad14; 
}

.btn-on-shelf { 
  background: #52c41a; 
}

.btn-delete {
  background: #fff;
  border: 1px solid #d9d9d9;
  color: #666;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
  min-width: 80px;
}

.btn-delete:hover {
  border-color: #ff4d4f;
  color: #ff4d4f;
  background: #fff1f0;
}

/* ===== 表单样式 ===== */
.info-form, .password-form, .nickname-form {
  max-width: 500px;
}
.form-item { margin-bottom: 24px; }
.form-item label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 500;
}
.form-input {
  width: 100%;
  height: 44px;
  padding: 0 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 15px;
  box-sizing: border-box;
}
.form-input:focus {
  outline: none;
  border-color: #fb7299;
}
.form-textarea {
  width: 95%;
  min-height: 100px;
  padding: 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  resize: vertical;
}
.form-textarea:focus {
  outline: none;
  border-color: #fb7299;
}
.radio-group { display: flex; gap: 24px; }
.radio-item { display: flex; align-items: center; gap: 6px; cursor: pointer; }

/* ===== 按钮样式 ===== */
.btn-primary {
  height: 44px;
  padding: 0 24px;
  background: #fb7299;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
}
.btn-primary:hover { background: #f7507f; }

.btn-secondary {
  height: 44px;
  padding: 0 24px;
  background: #fff;
  color: #fb7299;
  border: 1px solid #fb7299;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  margin-left: 12px;
}
.btn-secondary:hover { background: #fff5f8; }

.btn-group { margin-top: 24px; }

/* ===== 售后弹窗 ===== */
.return-modal { width: 440px; }
.return-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.return-card {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
}
.return-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}
.return-no { font-size: 14px; color: #666; }
.return-type-tag { font-size: 13px; color: #fb7299; font-weight: 500; }
.return-status { font-size: 14px; font-weight: 500; }
.return-status.pending { color: #faad14; }
.return-status.approved { color: #1890ff; }
.return-status.rejected { color: #999; }
.return-status.refunded { color: #52c41a; }
.return-body { padding: 16px 20px; }
.return-body p { margin: 6px 0; font-size: 14px; color: #333; }
.return-actions {
  display: flex;
  gap: 12px;
  padding: 12px 20px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}
.btn-approve {
  background: #fb7299;
  color: #fff;
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
}
.btn-approve:hover { background: #f7507f; }
.btn-reject {
  background: #fff;
  color: #666;
  border: 1px solid #d9d9d9;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
}
.btn-reject:hover { border-color: #ff4d4f; color: #ff4d4f; }

/* ===== 弹窗通用样式 ===== */
.modal-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 440px;
  max-width: 90%;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}
.modal-header h3 { margin: 0; font-size: 18px; color: #333; }
.close-btn { font-size: 24px; color: #999; cursor: pointer; }
.modal-body { padding: 24px 20px; }
.modal-footer { display: flex; border-top: 1px solid #f0f0f0; }
.modal-footer button { flex: 1; padding: 14px; border: none; font-size: 16px; cursor: pointer; }
.cancel-btn { background: #f5f5f5; color: #666; }
.confirm-btn { background: #fb7299; color: #fff; }

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .user-page .container {
    flex-direction: column !important;
    padding: 0 8px !important;
  }
  .menu-sidebar {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    flex-direction: row !important;
    overflow-x: auto;
    position: static !important;
    height: auto !important;
    padding: 8px !important;
    gap: 0 !important;
  }
  .sidebar-header {
    display: none !important;
  }
  .sidebar-menu {
    display: flex !important;
    flex-direction: row !important;
    overflow-x: auto;
    gap: 0 !important;
    width: 100%;
  }
  .menu-item {
    white-space: nowrap;
    padding: 8px 12px !important;
    font-size: 13px;
    border-bottom: none !important;
    border-radius: 20px;
    margin-right: 4px;
    flex-shrink: 0;
  }
  .menu-item.active {
    background: #80acee;
    color: white;
  }
  .content-area {
    width: 100% !important;
    padding: 12px 0 !important;
  }
  .order-item {
    flex-direction: column;
    gap: 8px;
  }
  .order-item .item-img {
    width: 80px;
    height: 80px;
  }
  .order-status-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
  }
  .tab-item {
    white-space: nowrap;
    flex-shrink: 0;
  }
  .goods-img {
    width: 60px;
    height: 60px;
  }
  .panel-title {
    font-size: 16px;
  }
  .radio-group { flex-direction: column; gap: 12px; }
  .btn-secondary { margin-left: 0; margin-top: 12px; }
  .history-item, .goods-item { flex-wrap: wrap; }
  .goods-info { width: calc(100% - 116px); }
  .btn-delete, .btn-edit { margin-left: auto; }
}

.status-tip {
  font-size: 12px;
  margin-left: 4px;
  opacity: 0.8;
}

.address-selector {
  width: 100%;
}

:deep(.el-cascader) {
  --el-cascader-height: 44px;
  --el-cascader-border-color: #d9d9d9;
  --el-cascader-border-radius: 8px;
}

:deep(.el-cascader:hover) {
  --el-cascader-border-color: #fb7299;
}

:deep(.el-cascader.is-focus) {
  --el-cascader-border-color: #fb7299;
  --el-cascader-box-shadow: 0 0 0 2px rgba(251, 114, 153, 0.2);
}
</style>

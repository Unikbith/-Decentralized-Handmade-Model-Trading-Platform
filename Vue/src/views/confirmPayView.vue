<template>
  <div class="confirm-pay-page">
    <div class="container">

      <div v-if="loading" class="loading">
        <p>正在加载订单信息...</p>
      </div>

      <div v-else-if="success" class="success">
        <h2>支付成功</h2>
        <p>您的订单已支付完成，商家将尽快发货</p>
        <button class="btn-primary" @click="goToOrders">查看我的订单</button>
      </div>

      <div v-else-if="error" class="error">
        <h2>支付失败</h2>
        <p>{{ errorMsg }}</p>
        <button class="btn-primary" @click="goToOrders">查看我的订单</button>
      </div>

      <div v-else class="pay-form">
        <h2>请扫码支付</h2>
        <p class="order-no">订单号：{{ orderNo }}</p>
        <p class="amount">支付金额：<span>¥{{ totalPrice }}</span></p>
        
        <div class="qrcode-container">
          <div class="qrcode">
            <qrcode-vue :value="qrcodeUrl" :size="200" :level="'H'" />
            <p class="qrcode-tip">请使用微信/支付宝扫码支付</p>
            <p class="countdown">二维码将在 <span>{{ countdown }}</span> 秒后过期</p>
          </div>
        </div>

        <div class="mock-pay">
          <p class="mock-tip">【模拟支付】点击下方按钮模拟支付成功</p>
          <button class="btn-mock-pay" @click="mockPaySuccess" :disabled="paying">
            {{ paying ? '支付中...' : '模拟支付成功' }}
          </button>
        </div>

        <button class="btn-cancel" @click="goToOrders">暂不支付，查看订单</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QrcodeVue from 'qrcode.vue'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const success = ref(false)
const error = ref(false)
const errorMsg = ref('')
const orderNo = ref('')
const totalPrice = ref('0.00')
const paying = ref(false)

const qrcodeUrl = ref('')
const countdown = ref(120)
let countdownTimer = null
let pollTimer = null

// 获取订单信息API
const getOrderInfo = async () => {
  const order_no = route.query.order_no
  if (!order_no) {
    error.value = true
    errorMsg.value = '订单号不存在'
    loading.value = false
    return
  }

  orderNo.value = order_no
  
  try {
    const res = await request.get(`/api/order/public/${order_no}`)
    if (res.data.code === 200) {
      totalPrice.value = res.data.data.total_price
      qrcodeUrl.value = `https://pay.anime-model.com/order/${order_no}?amount=${totalPrice.value}`
      loading.value = false
      startCountdown()
      startPolling()
    } else {
      error.value = true
      errorMsg.value = res.data.msg
      loading.value = false
    }
  } catch (err) {
    error.value = true
    errorMsg.value = '获取订单信息失败'
    loading.value = false
  }
}

// 模拟支付
const mockPaySuccess = async () => {
  paying.value = true
  try {
    const res = await request.post(`/api/order/confirm-public/${orderNo.value}`)
    if (res.data.code === 200) {
      clearTimers()
      success.value = true
      // 记录购买行为
      recordPurchaseBehavior()
    } else {
      error.value = true
      errorMsg.value = res.data.msg || '支付失败'
    }
  } catch (err) {
    error.value = true
    errorMsg.value = '支付请求失败'
  } finally {
    paying.value = false
  }
}

// 记录购买行为
const recordPurchaseBehavior = async () => {
  try {
    // 获取订单中的商品并记录购买行为
    const res = await request.get(`/api/order/detail/${orderNo.value}`)
    if (res.data.code === 200 && res.data.data.items) {
      for (const item of res.data.data.items) {
        await request.post('/api/user/behavior', {
          goods_id: item.goods_id,
          type: 'purchase'
        }).catch(() => {})
      }
    }
  } catch (err) {
    console.error('记录购买行为失败:', err)
  }
}

// 倒计时与轮询方法
const startCountdown = () => {
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      countdown.value = 120
    }
  }, 1000)
}

const startPolling = () => {
  pollTimer = setInterval(async () => {
    try {
      const res = await request.get(`/api/order/public/${orderNo.value}`)
      if (res.data.code === 200) {
        const order = res.data.data
        if (order.status === 'pending_ship' || order.status === 'completed') {
          clearTimers()
          success.value = true
        } else if (order.status === 'cancelled') {
          clearTimers()
          error.value = true
          errorMsg.value = '订单已超时取消，请重新下单'
        }
      }
    } catch (err) {
      console.error('查询支付状态失败', err)
    }
  }, 3000)
}

const clearTimers = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const goToOrders = () => {
  router.push('/profile')
}

// 生命周期钩子
onMounted(() => {
  getOrderInfo()
})

onUnmounted(() => {
  clearTimers()
})
</script>

<style scoped>
/* 页面布局 */
.confirm-pay-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgb(234, 243, 251);
  padding: 20px;
}

.container {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  max-width: 420px;
  width: 100%;
}

.loading, .success, .error, .pay-form {
  text-align: center;
}

/* 支付成功/失败状态*/
.success h2 {
  color: #52c41a;
  margin: 0 0 20px;
  font-size: 24px;
}

.error h2 {
  color: #ff4d4f;
  margin: 0 0 20px;
  font-size: 24px;
}

.pay-form h2 {
  color: #333;
  margin: 0 0 20px;
  font-size: 24px;
}

p {
  color: #666;
  margin: 0 0 15px;
  font-size: 16px;
}

.order-no {
  font-size: 14px;
  color: #999;
}

.amount {
  font-size: 18px;
  margin: 20px 0;
}

.amount span {
  color: #fb7299;
  font-weight: 600;
  font-size: 26px;
}

/* 主按钮 */
.btn-primary {
  height: 44px;
  padding: 0 30px;
  background: #fb7299;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
  margin-top: 10px;
}

.btn-primary:hover {
  background: #f7507f;
}

/* 二维码区域 */
.qrcode-container {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qrcode {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qrcode-tip {
  font-size: 14px;
  color: #666;
  margin-top: 15px;
  margin-bottom: 8px;
}

.countdown {
  font-size: 14px;
  color: #999;
  margin-bottom: 0;
}

.countdown span {
  color: #ff4d4f;
  font-weight: 600;
}

/* 模拟支付区域 */
.mock-pay {
  margin-top: 25px;
  padding-top: 20px;
  border-top: 1px dashed #eee;
}

.mock-tip {
  font-size: 13px;
  color: #999;
  margin-bottom: 12px;
}

.btn-mock-pay {
  height: 44px;
  padding: 0 30px;
  background: #52c41a;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
}

.btn-mock-pay:hover {
  background: #389e0d;
}

.btn-mock-pay:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 取消按钮 */
.btn-cancel {
  height: 40px;
  padding: 0 20px;
  background: #f5f7fa;
  color: #666;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
  margin-top: 15px;
}

.btn-cancel:hover {
  background: #e4e7ed;
  color: #333;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .confirm-pay-page { padding: 12px; }
  .container { padding: 24px 16px; }
  .pay-form h2, .success h2, .error h2 { font-size: 20px; }
  .amount span { font-size: 22px; }
  .btn-primary, .btn-mock-pay, .btn-cancel { font-size: 14px; }
}
</style>

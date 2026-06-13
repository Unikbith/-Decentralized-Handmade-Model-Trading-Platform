<template>
  <div class="cart-page">
    <div class="container">
      <h2 class="page-title">我的购物车</h2>

      <div v-if="loading" class="loading-wrap">
        <p>正在加载购物车...</p>
      </div>

      <div v-else-if="cartList.length === 0" class="empty-cart">
        <p>购物车为空，快去挑选商品吧~</p>
      </div>

      <!--购物车内容区 -->
      <div v-else class="cart-content">
        <!--商品列表-->
        <div class="cart-item" v-for="item in cartList" :key="item.id">
          <img :src="item.image" alt="" class="item-img" @error="handleImgError">
          <div class="item-info">
            <h3 class="item-name">{{ item.name }}</h3>
            <p class="item-price">¥{{ item.price }}</p>
          </div>
          <div class="num-group">
            <button @click="updateNum(item, -1)" :disabled="item.num <= 1">-</button>
            <span>{{ item.num }}</span>
            <button @click="updateNum(item, 1)">+</button>
          </div>
          <button class="del-btn" @click="deleteItem(item.id)">删除</button>
        </div>

        <!--底部结算栏-->
        <div class="cart-footer">
          <div class="total-price">
            合计：<span>¥{{ totalPrice }}</span>
          </div>
          <button
            class="pay-btn"
            @click="goToSettlement"
            :disabled="isSubmitting"
          >
            去结算
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import { showAlert, showConfirm } from '@/utils/modal'

const router = useRouter()

//响应式数据定义
const cartList = ref([])
const loading = ref(false)
const isSubmitting = ref(false)

//获取购物车列表API请求方法
const getCartList = async () => {
  const token = sessionStorage.getItem('token')
  if (!token) {
    await showAlert('请先登录')
    router.push('/login')
    return
  }
  loading.value = true
  try {
    const res = await request.get('/api/cart/list')
    if (res.data.code === 200) cartList.value = res.data.data
  } catch (err) {
    await showAlert('购物车加载失败', '', 'error')
  } finally { loading.value = false }
}

//更新商品数量
const updateNum = async (item, step) => {
  const newNum = item.num + step
  try {
    await request.post('/api/cart/update', { id: item.id, num: newNum })
    item.num = newNum
  } catch (err) {
    await showAlert('修改数量失败', '', 'error')
  }
}

//删除购物车商品
const deleteItem = async (id) => {
  if (!(await showConfirm('确定删除？'))) return
  try {
    await request.delete(`/api/cart/delete/${id}`)
    cartList.value = cartList.value.filter(i => i.id !== id)
  } catch (err) {
    await showAlert('删除失败', '', 'error')
  }
}

//计算总价
const totalPrice = computed(() => {
  return cartList.value.reduce((sum, item) => sum + item.price * item.num, 0).toFixed(2)
})

//图片错误处理
const handleImgError = (e) => {
  e.target.src = '/assets/picture-DPjQRauj.png'
}

//跳转到结算页面
const goToSettlement = async () => {
  if (cartList.value.length === 0) {
    await showAlert('购物车为空，无法结算')
    return
  }

  // 跳转到结算页
  router.push('/orderSettlement')
}

// 生命周期钩子
onMounted(() => { getCartList() })
</script>

<style scoped>
/* ===== 页面布局 ===== */
.cart-page {
  min-height: 100vh;
  padding: 80px 20px 40px;
  box-sizing: border-box;
  background: rgb(234, 243, 251);
}

.container {
  max-width: 1500px;
  margin: 0 auto;
}

/* ===== 页面标题 ===== */
.page-title {
  font-size: 24px;
  font-weight: 600;
  text-align: center;
  color: #212121;
  margin: 0 0 30px;
}

/* ===== 加载&空状态 ===== */
.loading-wrap, .empty-cart {
  background: #fff;
  border-radius: 12px;
  padding: 100px 0;
  text-align: center;
  color: #999;
  font-size: 16px;
}

/* ===== 购物车内容区 ===== */
.cart-content {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}

/* ===== 购物车商品项 ===== */
.cart-item {
  display: flex;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.item-img {
  width: 100px;
  height: 100px;
  object-fit: contain;
  border-radius: 8px;
  background: #f9f9f9;
  margin-right: 20px;
}

.item-info {
  flex: 1;
}

.item-name {
  font-size: 16px;
  color: #333;
  margin: 0 0 8px;
}

.item-price {
  font-size: 20px;
  color: #fb7299;
  font-weight: 600;
  margin: 0;
}

/* ===== 数量控制 ===== */
.num-group {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 30px;
}

.num-group button {
  width: 32px;
  height: 32px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.num-group button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.num-group span {
  min-width: 30px;
  text-align: center;
  font-size: 16px;
}

/* ===== 删除按钮 ===== */
.del-btn {
  color: #ff4d4f;
  background: none;
  border: none;
  font-size: 14px;
  cursor: pointer;
}

.del-btn:hover {
  color: #ff7875;
}

/* ===== 底部结算栏 ===== */
.cart-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #fafafa;
}

.total-price {
  font-size: 18px;
  color: #333;
}

.total-price span {
  font-size: 24px;
  color: #fb7299;
  font-weight: 600;
}

/* ===== 结算按钮 ===== */
.pay-btn {
  background: #fb7299;
  color: #fff;
  border: none;
  padding: 12px 40px;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}

.pay-btn:hover {
  opacity: 0.9;
}

.pay-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .cart-page {
    padding: 10px 0;
  }
  .container {
    padding: 0 12px;
  }
  .cart-item {
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px;
  }
  .item-img {
    width: 80px;
    height: 80px;
  }
  .item-info {
    flex: 1;
    min-width: 0;
  }
  .item-name {
    font-size: 14px;
  }
  .num-group {
    margin-left: 0;
  }
  .del-btn {
    margin-left: auto;
  }
  .cart-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  .pay-btn {
    width: 100%;
  }
}
</style>

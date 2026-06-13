<template>
  <div class="detail-page">

    <div v-if="!loading && goodsInfo.status === '下架'" class="off-shelf-banner">
      <span class="off-shelf-text">该商品已下架，暂时无法购买</span>
      <button class="back-link" @click="router.push('/')">返回首页</button>
    </div>
    <div class="container">

      <div v-if="loading" class="loading-wrap">
        <p>正在加载商品详情...</p>
      </div>

      <!--商品主内容区-->
      <div v-else class="main-content">
        <!--图片展示区-->
        <div class="image-section">
          <div class="main-img-wrap">
            <img :src="currentImg" :alt="goodsInfo.name" class="main-img" @error="handleImgError">
          </div>
          <div class="thumb-list" v-if="goodsInfo.images?.length > 1">
            <button class="arrow-btn prev" @click="prevImg" v-if="showPrevArrow">‹</button>
            <div class="thumb-scroll">
              <div 
                v-for="(img, index) in goodsInfo.images" 
                :key="index"
                class="thumb-item"
                :class="{ active: currentIndex === index }"
                @click="switchImg(index)"
              >
                <img :src="img" :alt="`缩略图${index+1}`" class="thumb-img" @error="handleImgError">
              </div>
            </div>
            <button class="arrow-btn next" @click="nextImg" v-if="showNextArrow">›</button>
          </div>
        </div>

        <!--商品信息区-->
        <div class="info-section">
          <h1 class="goods-title">{{ goodsInfo.name }}</h1>
          <div class="price-wrap">
            <span class="price-symbol">¥</span>
            <span class="price-num">{{ goodsInfo.price }}</span>
          </div>

          <div class="service-row">
            <span class="service-label">服务</span>
            <div class="service-list">
              <span>专业包装</span>
              <span>支持7天无理由</span>
              <span>48h内发货</span>
            </div>
          </div>

          <div class="merchant-row">
            <img 
              :src="merchantAvatar" 
              :alt="goodsInfo.merchant_name" 
              class="merchant-avatar" 
              @error="handleMerchantAvatarError"
            >
            <span class="merchant-name">{{ goodsInfo.merchant_name || '官方店铺' }}</span>
          </div>

          <!--购买操作区-->
          <div class="buy-wrap" v-if="!isMerchant && !isAdmin">
            <div class="stock-info">
              <span>库存：{{ goodsInfo.stock }}件</span>
              <span v-if="goodsInfo.category">分类：{{ goodsInfo.category }}</span>
            </div>
            <div class="btn-group">
              <button 
                class="add-cart-btn" 
                @click="addToCart"
                :disabled="goodsInfo.stock <= 0 || goodsInfo.status === '下架'"
              >
                {{ goodsInfo.status === '下架' ? '已下架' : (goodsInfo.stock <= 0 ? '已售罄' : '加入购物车') }}
              </button>
              <!--收藏按钮-->
              <button 
                class="collect-btn" 
                @click="toggleCollect"
                :disabled="collectLoading || goodsInfo.status === '下架'"
                :class="{ collected: isCollected }"
              >
                {{ collectLoading ? '处理中...' : (isCollected ? '已收藏' : '收藏') }}
              </button>
            </div>
          </div>

          <!--基本信息列表-->
          <div class="base-info-list">
            <div class="info-item" v-if="goodsInfo.ip">
              <span class="info-label">所属IP</span>
              <span class="info-value">{{ goodsInfo.ip }}</span>
            </div>
            <div class="info-item" v-if="goodsInfo.character">
              <span class="info-label">角色名称</span>
              <span class="info-value">{{ goodsInfo.character }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">上架时间</span>
              <span class="info-value">{{ goodsInfo.created_at }}</span>
            </div>
          </div>
        </div>
      </div>

      <!--商品详情底部区-->
      <div v-if="!loading" class="detail-bottom">
        <!--详情表格-->
        <div class="detail-table-card">
          <h3 class="card-title">商品详情</h3>
          <div class="detail-table">
            <div class="table-row">
              <div class="table-cell">
                <span class="cell-label">商品状态</span>
                <span class="cell-value">{{ goodsInfo.status || '暂无' }}</span>
              </div>
              <div class="table-cell">
                <span class="cell-label">品牌</span>
                <span class="cell-value">{{ goodsInfo.brand || '暂无' }}</span>
              </div>
            </div>
            <div class="table-row">
              <div class="table-cell full-width">
                <span class="cell-label">商品简介</span>
                <span class="cell-value">{{ goodsInfo.description || '暂无商品简介' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!--商品展示图-->
        <div class="img-card" v-if="restImages.length > 0">
          <h3 class="card-title">商品展示</h3>
          <div class="img-grid">
            <div 
              v-for="(img, index) in restImages" 
              :key="index"
              class="img-item"
            >
              <img 
                :src="img" 
                :alt="`商品图${index+1}`" 
                class="detail-img"
                @error="handleImgError"
              >
            </div>
          </div>
        </div>

        <!--评论区-->
        <div class="comment-card">
          <h3 class="card-title">用户评论（{{ commentList.length }}）</h3>
          
          <!--评论输入框-->
          <div class="comment-input-wrap" v-if="isLoggedIn && !isAdmin">
            <img class="user-avatar" :src="currentUserAvatar" @error="handleUserAvatarError">
            <div class="input-right">
              <textarea
                v-model="newComment" 
                class="comment-textarea" 
                placeholder="来说点什么吧~"
                maxlength="500"
              ></textarea>
              <div class="input-bottom">
                <span class="word-count">{{ newComment.length }}/500</span>
                <button class="submit-btn" @click="submitComment" :disabled="!newComment.trim() || submitting">
                  {{ submitting ? '发送中...' : '发表评论' }}
                </button>
              </div>
            </div>
          </div>
          
          <!--登录提示-->
          <div class="login-tip" v-else-if="!isLoggedIn">
            <span>请先</span>
            <span class="login-link" @click="goToLogin">登录</span>
            <span>后发表评论</span>
          </div>

          <!--评论列表-->
          <div class="comment-list">
            <div class="comment-item" v-for="comment in commentList" :key="comment.id">
              <img class="avatar" :src="comment.avatar || DEFAULT_PLACEHOLDER" @error="handleCommentAvatarError">
              <div class="comment-right">
                <div class="comment-top">
                  <span class="username">{{ comment.username }}</span>
                  <div class="time-menu-wrapper">
                    <span class="time">{{ comment.time }}</span>
                    <div class="comment-menu" v-if="isMyComment(comment.user_id)">
                      <div class="dots-btn" @click.stop="toggleMenu(comment.id)">⋮</div>
                      <div class="menu-dropdown" v-if="activeMenuId === comment.id">
                        <div class="menu-item" @click="confirmDelete(comment.id)">删除</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="comment-content">{{ comment.content }}</div>
              </div>
            </div>

            <div class="empty-comment" v-if="commentList.length === 0">
              暂无评论，快来抢沙发~
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import request from '@/api/request'
import { showAlert, showConfirm } from '@/utils/modal'

import DEFAULT_PLACEHOLDER from '@/assets/images/picture.png'


const route = useRoute()
const router = useRouter()

//公共API实例
const publicApi = axios.create({
  baseURL: '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

//用户角色
const userRole = computed(() => {
  const token = sessionStorage.getItem('adminToken') || sessionStorage.getItem('token')
  if (!token) return ''
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.role || ''
  } catch (e) {
    return ''
  }
})
const isMerchant = computed(() => userRole.value === 'merchant')
const isAdmin = computed(() => userRole.value === 'admin')

//响应式数据定义
const loading = ref(true)
const currentIndex = ref(0)
const isCollected = ref(false)
const collectLoading = ref(false)

const goodsInfo = ref({
  id: 0,
  name: '',
  price: 0,
  stock: 0,
  images: [],
  description: '',
  category: '',
  status: '',
  brand: '',
  ip: '',
  character: '',
  merchant_name: '',
  merchant_avatar: '',
  created_at: ''
})

const commentList = ref([])
const newComment = ref('')
const submitting = ref(false)
const isLoggedIn = computed(() => !!sessionStorage.getItem('token') || !!sessionStorage.getItem('adminToken'))
const currentUserAvatar = ref(DEFAULT_PLACEHOLDER)
const activeMenuId = ref(null)

//当前用户ID
const currentUserId = computed(() => {
  const token = sessionStorage.getItem('token')
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.id
  } catch (e) {
    return null
  }
})

//图片相关
const currentImg = computed(() => {
  return goodsInfo.value.images?.[currentIndex.value] || DEFAULT_PLACEHOLDER
})

const restImages = computed(() => {
  if (!goodsInfo.value.images || goodsInfo.value.images.length <= 1) return []
  return goodsInfo.value.images.slice(1)
})

const showPrevArrow = computed(() => currentIndex.value > 0)
const showNextArrow = computed(() => currentIndex.value < goodsInfo.value.images?.length - 1)

const merchantAvatar = computed(() => {
  return goodsInfo.value.merchant_avatar || DEFAULT_PLACEHOLDER
})

//获取商品详情API请求方法
const getGoodsDetail = async () => {
  const goodsId = route.params.id
  if (!goodsId) {
    await showAlert('商品参数错误', '', 'error')
    router.back()
    return
  }

  try {
    const res = await publicApi.get(`/api/goods/detail/${goodsId}`)
    if (res.data.code === 200) {
      goodsInfo.value = res.data.data
      getCommentsList()
      checkIsCollected()
      if (isLoggedIn.value && !isAdmin.value) {
        getCurrentUserInfo()
      }
      // 记录用户浏览行为（用于猜你喜欢推荐）
      recordBrowseBehavior(goodsId)
    } else {
      await showAlert(res.data.msg || '商品不存在', '', 'error')
      router.back()
    }
  } catch (err) {
    console.error('获取商品详情失败:', err)
    await showAlert('商品加载失败，请检查后端服务是否启动', '', 'error')
    router.back()
  } finally {
    loading.value = false
  }
}

//记录用户浏览行为
const recordBrowseBehavior = async (goodsId) => {
  const token = sessionStorage.getItem('token')
  if (!token) return // 未登录不记录
  
  try {
    await request.post('/api/user/behavior', {
      goods_id: parseInt(goodsId),
      type: 'view'
    })
  } catch (err) {
    console.error('记录浏览行为失败:', err)
  }
}

//收藏相关方法
const checkIsCollected = async () => {
  if (!isLoggedIn.value) return
  try {
    const res = await request.get('/api/collect/check', {
      params: { goods_id: goodsInfo.value.id }
    })
    if (res.data.code === 200) {
      isCollected.value = res.data.data.is_collected
    }
  } catch (err) {
    console.error('检查收藏状态失败:', err)
  }
}

const toggleCollect = async () => {
  if (!isLoggedIn.value) {
    await showAlert('请先登录')
    router.push('/login')
    return
  }
  collectLoading.value = true
  try {
    if (isCollected.value) {
      await request.post('/api/collect/delete', { goods_id: goodsInfo.value.id })
      isCollected.value = false
      await showAlert('已取消收藏')
    } else {
      await request.post('/api/collect/add', { goods_id: goodsInfo.value.id })
      isCollected.value = true
      await showAlert('收藏成功', '', 'success')
      // 记录收藏行为
      await request.post('/api/user/behavior', { goods_id: goodsInfo.value.id, type: 'collect' }).catch(() => {})
    }
  } catch (err) {
    console.error('收藏操作失败:', err)
    await showAlert('操作失败，请重试', '', 'error')
  } finally {
    collectLoading.value = false
  }
}

//评论相关方法
const getCommentsList = async () => {
  try {
    const res = await publicApi.get(`/api/comments/list/${route.params.id}`)
    if (res.data.code === 200) {
      commentList.value = res.data.data
    }
  } catch (err) {
    console.error('获取评论失败:', err)
  }
}

const getCurrentUserInfo = async () => {
  try {
    const res = await request.get('/api/user/info')
    if (res.data.code === 200 && res.data.data.avatar) {
      currentUserAvatar.value = res.data.data.avatar
    }
  } catch (err) {
    console.error('获取用户信息失败:', err)
  }
}

const submitComment = async () => {
  if (!newComment.value.trim()) return
  submitting.value = true
  try {
    const res = await request.post('/api/comments/add', {
      goods_id: goodsInfo.value.id,
      content: newComment.value.trim()
    })
    if (res.data.code === 200) {
      newComment.value = ''
      getCommentsList()
    } else {
      await showAlert('评论失败：' + res.data.msg, '', 'error')
    }
  } catch (err) {
    console.error('发表评论失败:', err)
    await showAlert('评论失败，请重试', '', 'error')
  } finally {
    submitting.value = false
  }
}

//评论操作方法
const isMyComment = (commentUserId) => {
  return currentUserId.value && String(commentUserId) === String(currentUserId.value)
}

const toggleMenu = (commentId) => {
  activeMenuId.value = activeMenuId.value === commentId ? null : commentId
}

const confirmDelete = async (commentId) => {
  if (!(await showConfirm('确定要删除这条评论吗？'))) {
    activeMenuId.value = null
    return
  }
  try {
    const res = await request.delete(`/api/comments/delete/${commentId}`)
    if (res.data.code === 200) {
      await showAlert('删除成功！', '', 'success')
      getCommentsList()
    } else {
      await showAlert('删除失败：' + res.data.msg, '', 'error')
    }
  } catch (err) {
    console.error('删除评论失败：', err)
    await showAlert('删除失败，请重试', '', 'error')
  } finally {
    activeMenuId.value = null
  }
}

const handleClickOutside = () => {
  activeMenuId.value = null
}

const goToLogin = () => {
  router.push('/login')
}

//图片切换方法
const switchImg = (index) => {
  currentIndex.value = index
}

const prevImg = () => {
  if (currentIndex.value > 0) currentIndex.value--
}
const nextImg = () => {
  if (currentIndex.value < goodsInfo.value.images.length - 1) currentIndex.value++
}

//加入购物车
const addToCart = async () => {
  const token = sessionStorage.getItem('token')
  if (!token) {
    await showAlert('请先登录')
    router.push('/login')
    return
  }

  try {
    const res = await request.post('/api/cart/add', {
      goods_id: goodsInfo.value.id
    })
    
    if (res.data.code === 200) {
      await showAlert(`已将「${goodsInfo.value.name}」加入购物车`, '', 'success')
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    console.error(err)
    await showAlert('加入购物车失败，请重试', '', 'error')
  }
}

//图片错误处理
const handleImgError = (e) => {
  e.target.src = DEFAULT_PLACEHOLDER
}
const handleMerchantAvatarError = (e) => {
  e.target.src = DEFAULT_PLACEHOLDER
}
const handleCommentAvatarError = (e) => {
  e.target.src = DEFAULT_PLACEHOLDER
}
const handleUserAvatarError = (e) => {
  e.target.src = DEFAULT_PLACEHOLDER
}

//生命周期钩子
onMounted(() => {
  getGoodsDetail()
  document.addEventListener('click', handleClickOutside)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>


<style scoped>
/* ===== 页面布局 ===== */
.detail-page {
  min-height: 100vh;
  padding: 80px 20px 40px;
  box-sizing: border-box;
  background: #f4f4f4;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.loading-wrap {
  text-align: center;
  padding: 100px 0;
  color: #999;
  font-size: 16px;
}

/* ===== 商品主内容区 ===== */
.main-content {
  display: flex;
  gap: 40px;
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  margin-bottom: 20px;
}

/* ===== 图片展示区 ===== */
.image-section {
  flex: 1;
  max-width: 560px;
}

.main-img-wrap {
  width: 100%;
  height: 560px;
  border-radius: 8px;
  overflow: hidden;
  background: #f9f9f9;
  margin-bottom: 16px;
}

.main-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.thumb-list {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
}

.thumb-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scroll-behavior: smooth;
  padding: 4px 0;
  width: 100%;
}

.thumb-scroll::-webkit-scrollbar {
  display: none;
}

.thumb-item {
  flex-shrink: 0;
  width: 80px;
  height: 80px;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: border-color 0.2s;
}

.thumb-item.active {
  border-color: #fb7299;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.arrow-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(0,0,0,0.5);
  color: #fff;
  border: none;
  font-size: 16px;
  line-height: 24px;
  text-align: center;
  cursor: pointer;
  z-index: 1;
}

.arrow-btn.prev {
  left: -12px;
}

.arrow-btn.next {
  right: -12px;
}

/* ===== 商品信息区 ===== */
.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.goods-title {
  font-size: 22px;
  font-weight: 600;
  color: #212121;
  margin: 0;
  line-height: 1.4;
}

.price-wrap {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 16px;
  background: #fff5f5;
  border-radius: 8px;
}

.price-symbol {
  font-size: 18px;
  color: #ff4400;
}

.price-num {
  font-size: 36px;
  font-weight: 700;
  color: #ff4400;
}

.service-row {
  display: flex;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.service-label {
  font-size: 14px;
  color: #999;
  flex-shrink: 0;
}

.service-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.service-list span {
  font-size: 14px;
  color: #666;
}

.merchant-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.merchant-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  background: #fb7299;
  flex-shrink: 0;
}

.merchant-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

/* ===== 购买操作区 ===== */
.buy-wrap {
  margin-top: auto;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
}

.stock-info {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #666;
}

.btn-group {
  display: flex;
  gap: 16px;
}

.add-cart-btn {
  flex: 1;
  height: 48px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  color: #fb7299;
  border: 1px solid #fb7299;
}

.add-cart-btn:hover {
  background: #fff5f8;
}

.add-cart-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== 收藏按钮 ===== */
.collect-btn {
  flex: 1;
  height: 48px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  color: #ff9800;
  border: 1px solid #ff9800;
}
.collect-btn.collected {
  background: #ff9800;
  color: #fff;
  border: 1px solid #ff9800;
}
.collect-btn:hover:not(:disabled) {
  opacity: 0.9;
}
.collect-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== 基本信息列表 ===== */
.base-info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 12px;
}

.info-item {
  display: flex;
  gap: 16px;
  font-size: 14px;
}

.info-label {
  color: #999;
  width: 80px;
  flex-shrink: 0;
}

.info-value {
  color: #333;
}

/* ===== 详情底部区 ===== */
.detail-bottom {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px;
}

.img-card {
  padding: 24px 30px;
}

/* ===== 详情表格 ===== */
.detail-table-card {
  padding: 24px 30px;
  border-bottom: 1px solid #eee;
}

.detail-table {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-bottom: 1px solid #e8e8e8;
}

.table-row:last-child {
  border-bottom: none;
}

.table-cell {
  padding: 16px 20px;
  background: #fafafa;
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-cell.full-width {
  grid-column: 1 / -1;
  align-items: flex-start;
}

.cell-label {
  font-size: 14px;
  color: #999;
  flex-shrink: 0;
  width: 70px;
}

.cell-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  line-height: 1.6;
}

/* ===== 商品展示图 ===== */
.img-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
}

.img-item {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s;
}

.img-item:hover {
  transform: translateY(-2px);
}

.detail-img {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  background: #f9f9f9;
}

/* ===== 评论区 ===== */
.comment-card {
  padding: 24px 30px;
  border-top: 1px solid #eee;
}

.comment-input-wrap {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  background: #fb7299;
  flex-shrink: 0;
}

.input-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comment-textarea {
  width: 100%;
  min-height: 80px;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
  resize: vertical;
  transition: border-color 0.2s;
}

.comment-textarea:focus {
  outline: none;
  border-color: #fb7299;
}

.input-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.word-count {
  font-size: 12px;
  color: #999;
}

.submit-btn {
  padding: 8px 24px;
  background: #fb7299;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: #f7507f;
}

.submit-btn:disabled {
  background: #fca5b9;
  cursor: not-allowed;
}

/* ===== 登录提示 ===== */
.login-tip {
  text-align: center;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 24px;
  font-size: 14px;
  color: #666;
}

.login-link {
  color: #fb7299;
  cursor: pointer;
  font-weight: 500;
}

/* ===== 评论列表 ===== */
.comment-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 10px;
}

.comment-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding-bottom: 16px;
  border-bottom: 1px dashed #f0f0f0;
}

.comment-item:last-child {
  border-bottom: none;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  background: #f5f5f5;
  flex-shrink: 0;
}

.comment-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.comment-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.time {
  font-size: 12px;
  color: #999;
}

.comment-content {
  font-size: 14px;
  color: #555;
  line-height: 1.5;
}

/* ===== 评论菜单 ===== */
.time-menu-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}
.dots-btn {
  font-size: 16px;
  color: #999;
  cursor: pointer;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}
.dots-btn:hover {
  background: #f0f0f0;
  color: #333;
}
.comment-menu {
  position: relative;
}
.menu-dropdown {
  position: absolute;
  top: 25px;
  right: 0;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  width: 60px;
  z-index: 99;
  overflow: hidden;
}
.menu-item {
  padding: 6px 12px;
  font-size: 12px;
  color: #ff4444;
  cursor: pointer;
  text-align: center;
}
.menu-item:hover {
  background: #f5f5f5;
}

.empty-comment {
  text-align: center;
  padding: 40px 0;
  color: #999;
  font-size: 14px;
}

/* ===== 下架横幅 ===== */
.off-shelf-banner {
  max-width: 1200px;
  margin: 0 auto 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.off-shelf-text {
  font-size: 15px;
  color: #cf1322;
  font-weight: 500;
}
.back-link {
  background: #fb7299;
  color: #fff;
  border: none;
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
}
.back-link:hover {
  background: #f7507f;
}

/* ===== 响应式适配 ===== */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }
  .image-section {
    max-width: 100%;
  }
  .main-img-wrap {
    height: auto;
    aspect-ratio: 1/1;
  }
  .table-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .detail-page {
    padding: 10px 0;
  }
  .container {
    padding: 0 12px;
  }
  .main-content {
    flex-direction: column !important;
    padding: 16px;
    gap: 16px !important;
  }
  .image-section {
    width: 100% !important;
    max-width: 100% !important;
  }
  .main-img-wrap {
    max-height: 300px;
  }
  .info-section {
    width: 100% !important;
    max-width: 100% !important;
  }
  .goods-title {
    font-size: 18px !important;
  }
  .price-num {
    font-size: 28px !important;
  }
  .service-row, .merchant-row {
    flex-direction: column;
    gap: 8px;
  }
  .btn-group {
    flex-direction: column;
    gap: 10px;
  }
  .btn-group button {
    width: 100%;
  }
  .img-grid {
    flex-direction: column;
  }
  .img-item {
    width: 100%;
    box-sizing: border-box;
  }
  .detail-table-card, .img-card, .comment-card {
    padding: 12px;
  }
  .table-cell {
    padding: 12px 16px;
  }
  .comment-item {
    padding: 10px 0;
  }
  .comment-input-wrap {
    flex-direction: column;
  }
  .comment-input-wrap button {
    width: 100%;
  }
  .user-avatar {
    display: none;
  }
}
</style>

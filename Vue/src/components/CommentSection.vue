<template>
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
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import request from '@/api/request'
import { showAlert, showConfirm } from '@/utils/modal'

import DEFAULT_PLACEHOLDER from '@/assets/images/picture.png'

const props = defineProps({
  goodsId: { type: [Number, String], required: true }
})

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
const isAdmin = computed(() => userRole.value === 'admin')

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

//评论相关方法
const getCommentsList = async () => {
  try {
    const res = await publicApi.get(`/api/comments/list/${props.goodsId}`)
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
      goods_id: props.goodsId,
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

//图片错误处理
const handleCommentAvatarError = (e) => {
  e.target.src = DEFAULT_PLACEHOLDER
}
const handleUserAvatarError = (e) => {
  e.target.src = DEFAULT_PLACEHOLDER
}

//生命周期钩子
onMounted(() => {
  getCommentsList()
  if (isLoggedIn.value && !isAdmin.value) {
    getCurrentUserInfo()
  }
  document.addEventListener('click', handleClickOutside)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.comment-card {
  padding: 24px 30px;
  border-top: 1px solid #eee;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px;
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

@media (max-width: 768px) {
  .comment-card {
    padding: 12px;
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
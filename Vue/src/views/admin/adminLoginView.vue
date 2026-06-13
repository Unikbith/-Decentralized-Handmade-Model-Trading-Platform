<template>
  <div class="admin-login-page">
    <!-- ===== 登录卡片 ===== -->
    <div class="login-box">
      <h1 class="page-title">管理员后台</h1>
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-item">
          <label>管理员账号</label>
          <input type="text" v-model="form.username" class="form-input" placeholder="请输入管理员账号" />
        </div>
        <div class="form-item">
          <label>密码</label>
          <input type="password" v-model="form.password" class="form-input" placeholder="请输入密码" />
        </div>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <div class="back-home" @click="goToHome">返回商城首页</div>
      <!-- ===== 提示消息 ===== -->
      <div v-if="message" class="message" :class="{'error': isError}">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
// ===== 导入依赖 =====
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

// ===== 路由实例 =====
const router = useRouter()

// ===== 响应式数据定义 =====
const loading = ref(false)
const message = ref('')
const isError = ref(false)
const form = ref({ username: '', password: '' })

// ===== 消息提示方法 =====
const showMessage = (msg, error = true) => {
  message.value = msg
  isError.value = error
  setTimeout(() => { message.value = '' }, 3000)
}

// ===== 登录处理方法 =====
const handleLogin = async () => {
  if (!form.value.username.trim() || !form.value.password.trim()) {
    return showMessage('请输入账号和密码', true)
  }
  loading.value = true
  try {
    const res = await request.post('/api/admin/login', form.value)
    if (res.data.code === 200) {
      sessionStorage.setItem('adminToken', res.data.token)
      sessionStorage.setItem('adminNickname', res.data.nickname)
      showMessage('登录成功', false)
      setTimeout(() => { router.push('/admin/dashboard') }, 1000)
    } else {
      showMessage(res.data.msg, true)
    }
  } catch (err) {
    showMessage('服务器连接失败，请检查后端是否启动', true)
  } finally {
    loading.value = false
  }
}

// ===== 导航方法 =====
const goToHome = () => router.push('/')
</script>

<style scoped>
/* ===== 页面布局 ===== */
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

/* ===== 登录卡片 ===== */
.login-box {
  width: 400px;
  background: #fff;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  text-align: center;
  margin: 0 0 40px;
}

/* ===== 表单样式 ===== */
.form-item {
  margin-bottom: 24px;
}

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
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #1890ff;
}

/* ===== 登录按钮 ===== */
.btn-primary {
  width: 100%;
  height: 44px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-primary:disabled {
  background: #91d5ff;
  cursor: not-allowed;
}

/* ===== 返回首页链接 ===== */
.back-home {
  text-align: center;
  margin-top: 20px;
  color: #1890ff;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.2s;
}

.back-home:hover {
  color: #40a9ff;
}

/* ===== 提示消息 ===== */
.message {
  text-align: center;
  padding: 12px;
  border-radius: 8px;
  margin-top: 20px;
  font-size: 14px;
}

.message.error {
  color: #ff4d4f;
  background: #fff1f0;
}

.message:not(.error) {
  color: #52c41a;
  background: #f6ffed;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .admin-login-page {
    padding: 30px 16px;
  }
  .login-box {
    padding: 24px 20px;
    max-width: 100%;
  }
  .page-title {
    font-size: 22px;
    margin-bottom: 30px;
  }
  .form-input {
    height: 44px;
    font-size: 14px;
  }
}
</style>

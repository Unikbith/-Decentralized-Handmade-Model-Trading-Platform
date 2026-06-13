<template>
  <div class="reset-page">
    <!-- ===== 页面标题 ===== -->
    <h1 class="page-title">找回密码</h1>
    <div class="container">
      <div class="reset-card">
        <!-- ===== 表单内容 ===== -->
        <div class="step-content">
          <!-- ===== 账号输入 ===== -->
          <div class="input-group">
            <label class="input-label">账号</label>
            <input
              type="text"
              class="input-field"
              placeholder="请输入您的账号"
              v-model="username"
              @keyup.enter="resetPassword"
            >
          </div>

          <!-- ===== 注册邮箱输入 ===== -->
          <div class="input-group">
            <label class="input-label">注册邮箱</label>
            <input
              type="email"
              class="input-field"
              placeholder="请输入注册时使用的邮箱"
              v-model="email"
              @keyup.enter="resetPassword"
            >
          </div>

          <!-- ===== 验证码输入与发送 ===== -->
          <div class="input-group code-group">
            <label class="input-label">验证码</label>
            <div class="code-input-container">
              <input
                type="text"
                class="input-field code-input"
                placeholder="请输入邮箱验证码"
                v-model="code"
                @keyup.enter="resetPassword"
              >
              <button
                class="btn-code"
                @click="sendCode"
                :disabled="sending || countDown > 0"
              >
                {{ countDown > 0 ? `${countDown}s` : '发送验证码' }}
              </button>
            </div>
          </div>

          <!-- ===== 新密码输入 ===== -->
          <div class="input-group">
            <label class="input-label">新密码</label>
            <input
              type="password"
              class="input-field"
              placeholder="请输入新密码（至少6位）"
              v-model="newPassword"
              @keyup.enter="resetPassword"
            >
          </div>

          <!-- ===== 确认密码输入 ===== -->
          <div class="input-group">
            <label class="input-label">确认密码</label>
            <input
              type="password"
              class="input-field"
              placeholder="请再次输入新密码"
              v-model="confirmPassword"
              @keyup.enter="resetPassword"
            >
          </div>

          <!-- ===== 提交按钮 ===== -->
          <button class="btn-primary" @click="resetPassword" :disabled="resetting">
            {{ resetting ? '重置中...' : '确认修改密码' }}
          </button>
        </div>

        <!-- ===== 返回登录链接 ===== -->
        <div class="back-link">
          <span @click="goToLogin">返回登录</span>
        </div>

        <!-- ===== 提示消息 ===== -->
        <div v-if="message" class="message" :class="{'error': isError}">
          {{ message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// ===== 导入依赖 =====
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

// ===== 路由实例 =====
const router = useRouter()

// ===== 响应式数据定义 =====
const username = ref('')
const email = ref('')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const sending = ref(false)
const resetting = ref(false)
const message = ref('')
const isError = ref(false)
const countDown = ref(0)
let countDownTimer = null

// ===== 提示消息方法 =====
function showMessage(msg, error = true) {
  message.value = msg
  isError.value = error
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

// ===== 发送验证码倒计时 =====
function startCountDown() {
  countDown.value = 60
  countDownTimer = setInterval(() => {
    countDown.value--
    if (countDown.value <= 0) {
      clearInterval(countDownTimer)
    }
  }, 1000)
}

// ===== 发送验证码 =====
const sendCode = async () => {
  if (!username.value.trim()) {
    showMessage('请输入账号')
    return
  }
  if (!email.value.trim() || !email.value.includes('@')) {
    showMessage('请输入有效的邮箱')
    return
  }

  sending.value = true
  try {
    // ✅ 修改为新的二级路径
    const res = await request.post('/api/reset-password-send', {
      username: username.value.trim(),
      email: email.value.trim()
    })
    if (res.data.code === 200) {
      showMessage('验证码已发送到您的邮箱', false)
      startCountDown()
    } else {
      showMessage(res.data.msg || '发送失败')
    }
  } catch (err) {
    // 处理网络错误和后端返回的错误
    if (err.response && err.response.data && err.response.data.msg) {
      showMessage(err.response.data.msg)
    } else {
      showMessage('网络错误，请稍后重试')
    }
  } finally {
    sending.value = false
  }
}

// ===== 重置密码 =====
const resetPassword = async () => {
  if (!username.value.trim()) {
    showMessage('请输入账号')
    return
  }
  if (!email.value.trim() || !email.value.includes('@')) {
    showMessage('请输入有效的邮箱')
    return
  }
  if (!code.value.trim()) {
    showMessage('请输入验证码')
    return
  }
  if (!newPassword.value || newPassword.value.length < 6) {
    showMessage('密码长度不能少于6位')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    showMessage('两次输入的密码不一致')
    return
  }

  resetting.value = true
  try {
    // ✅ 修改为新的二级路径
    const res = await request.post('/api/reset-password-reset', {
      username: username.value.trim(),
      email: email.value.trim(),
      code: code.value.trim(),
      newPassword: newPassword.value
    })
    if (res.data.code === 200) {
      showMessage('密码重置成功，即将跳转到登录页', false)
      setTimeout(() => {
        goToLogin()
      }, 2000)
    } else {
      showMessage(res.data.msg || '重置失败')
    }
  } catch (err) {
    // 处理网络错误和后端返回的错误
    if (err.response && err.response.data && err.response.data.msg) {
      showMessage(err.response.data.msg)
    } else {
      showMessage('网络错误，请稍后重试')
    }
  } finally {
    resetting.value = false
  }
}

// ===== 导航方法 =====
const goToLogin = () => {
  router.push('/login')
}

// ===== 生命周期钩子 =====
// 组件卸载时清除定时器
onUnmounted(() => {
  if (countDownTimer) {
    clearInterval(countDownTimer)
  }
})
</script>

<style scoped>
/* ===== 页面布局 ===== */
.reset-page {
  min-height: 100vh;
  padding: 40px 20px;
  box-sizing: border-box;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* ===== 页面标题 ===== */
.page-title {
  text-align: center;
  color: #333;
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 50px;
}

.container {
  display: flex;
  justify-content: center;
}

/* ===== 重置密码卡片 ===== */
.reset-card {
  background-color: #fff;
  padding: 40px 35px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  width: 100%;
  max-width: 420px;
  box-sizing: border-box;
}

.step-content {
  margin-bottom: 20px;
}

/* ===== 表单输入组 ===== */
.input-group {
  margin-bottom: 20px;
}

.input-label {
  display: block;
  margin-bottom: 8px;
  color: #666;
  font-size: 14px;
  font-weight: 500;
}

.input-field {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 15px;
  color: #333;
  box-sizing: border-box;
  outline: none;
}

.input-field:focus {
  border-color: #82c3ff;
  box-shadow: 0 0 0 3px rgba(130, 195, 255, 0.15);
}

/* ===== 验证码输入框与按钮 ===== */
/* 验证码输入框与按钮水平排列 */
.code-input-container {
  display: flex;
  gap: 12px;
}

.code-input {
  flex: 1;
}

.btn-code {
  width: 120px;
  height: 48px;
  background: #f0f7ff;
  color: #5fb3ff;
  border: 1px solid #82c3ff;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-code:hover:not(:disabled) {
  background: #e6f3ff;
}

.btn-code:disabled {
  background: #f5f5f5;
  color: #999;
  border-color: #e0e0e0;
  cursor: not-allowed;
}

/* ===== 提交按钮 ===== */
.btn-primary {
  width: 100%;
  height: 52px;
  background: linear-gradient(135deg, #82c3ff, #5fb3ff);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #5fb3ff, #4aa8ff);
}

.btn-primary:disabled {
  background: #c3e5ff;
  cursor: not-allowed;
}

/* ===== 返回登录链接 ===== */
.back-link {
  text-align: center;
  margin-top: 20px;
}

.back-link span {
  color: #82c3ff;
  cursor: pointer;
  font-size: 14px;
}

.back-link span:hover {
  text-decoration: underline;
}

/* ===== 提示消息 ===== */
.message {
  text-align: center;
  padding: 8px 0;
  border-radius: 4px;
  font-size: 14px;
  margin-top: 10px;
}

.message.error {
  color: #ff4d4f;
  background-color: #fff2f0;
}

.message:not(.error) {
  color: #52c41a;
  background-color: #f6ffed;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .reset-page {
    padding: 30px 16px;
  }
  .reset-card {
    padding: 24px 20px;
    max-width: 100%;
  }
  .page-title {
    font-size: 22px;
    margin-bottom: 30px;
  }
  .input-field {
    height: 44px;
    font-size: 14px;
  }
  .btn-code {
    width: 100px;
    height: 44px;
    font-size: 13px;
  }
  .btn-primary {
    height: 46px;
    font-size: 15px;
  }
  .input-label {
    font-size: 13px;
  }
}
</style>

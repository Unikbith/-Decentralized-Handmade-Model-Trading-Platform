<template>
  <AuthLayout title="找回密码">
    <el-form ref="formRef" :model="form" :rules="rules" class="auth-form" @submit.prevent>
      <!-- ===== 账号 ===== -->
      <el-form-item prop="username">
        <el-input v-model="form.username" class="auth-field" placeholder="请输入您的账号" @keyup.enter="handleSendCode" />
      </el-form-item>

      <!-- ===== 注册邮箱 + 发送验证码 ===== -->
      <el-form-item prop="email">
        <div class="email-row">
          <el-input v-model="form.email" class="auth-field email-input" placeholder="请输入注册时使用的邮箱" @keyup.enter="handleSendCode" />
          <button
            type="button"
            class="auth-code-outline"
            :disabled="sending || countDown > 0"
            @click="handleSendCode"
          >{{ countDown > 0 ? `${countDown}s` : '发送验证码' }}</button>
        </div>
      </el-form-item>

      <!-- ===== 验证码 ===== -->
      <el-form-item prop="code">
        <el-input v-model="form.code" class="auth-field" placeholder="请输入邮箱验证码" @keyup.enter="resetPassword" />
      </el-form-item>

      <!-- ===== 新密码 ===== -->
      <el-form-item prop="newPassword">
        <el-input v-model="form.newPassword" class="auth-field" type="password" placeholder="请输入新密码（至少6位）" />
      </el-form-item>

      <!-- ===== 确认密码 ===== -->
      <el-form-item prop="confirmPassword">
        <el-input v-model="form.confirmPassword" class="auth-field" type="password" placeholder="请再次输入新密码" @keyup.enter="resetPassword" />
      </el-form-item>

      <!-- ===== 提交按钮 ===== -->
      <el-button class="btn-primary" type="primary" :loading="resetting" @click="resetPassword">
        {{ resetting ? '重置中...' : '确认修改密码' }}
      </el-button>

      <!-- ===== 返回登录链接 ===== -->
      <div class="auth-link">
        <span class="span-bold" @click="goToLogin">返回登录</span>
      </div>
    </el-form>
  </AuthLayout>
</template>

<script setup>
// ===== 导入依赖 =====
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
import AuthLayout from '@/components/AuthLayout.vue'

const router = useRouter()
const formRef = ref()
const sending = ref(false)
const resetting = ref(false)
const countDown = ref(0)
let countDownTimer = null

// ===== 响应式数据 =====
const form = reactive({
  username: '',
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

// ===== 自定义校验：确认密码一致性 =====
function validateConfirm(rule, value, callback) {
  if (!value) {
    callback(new Error('请再次输入新密码'));
  } else if (value !== form.newPassword) {
    callback(new Error('两次输入的密码不一致'));
  } else {
    callback();
  }
}

// ===== 自定义校验：邮箱 =====
function validateEmail(rule, value, callback) {
  if (!value || !value.includes('@')) {
    callback(new Error('请输入有效的邮箱'));
  } else {
    callback();
  }
}

// ===== 表单验证规则 =====
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  email: [{ validator: validateEmail, trigger: 'blur' }],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
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
const handleSendCode = async () => {
  // 校验账号与邮箱，失败时表单会展示行内错误提示
  try {
    await formRef.value.validateField(['username', 'email'])
  } catch (e) {
    return
  }

  sending.value = true
  try {
    const res = await request.post('/api/reset-password-send', {
      username: form.username.trim(),
      email: form.email.trim()
    })
    if (res.data.code === 200) {
      ElMessage.success('验证码已发送到您的邮箱')
      startCountDown()
    } else {
      ElMessage.error(res.data.msg || '发送失败')
    }
  } catch (err) {
    if (err.response && err.response.data && err.response.data.msg) {
      ElMessage.error(err.response.data.msg)
    } else {
      ElMessage.error('网络错误，请稍后重试')
    }
  } finally {
    sending.value = false
  }
}

// ===== 重置密码 =====
const resetPassword = async () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return

    resetting.value = true
    try {
      const res = await request.post('/api/reset-password-reset', {
        username: form.username.trim(),
        email: form.email.trim(),
        code: form.code.trim(),
        newPassword: form.newPassword
      })
      if (res.data.code === 200) {
        ElMessage.success('密码重置成功，即将跳转到登录页')
        setTimeout(() => {
          goToLogin()
        }, 2000)
      } else {
        ElMessage.error(res.data.msg || '重置失败')
      }
    } catch (err) {
      if (err.response && err.response.data && err.response.data.msg) {
        ElMessage.error(err.response.data.msg)
      } else {
        ElMessage.error('网络错误，请稍后重试')
      }
    } finally {
      resetting.value = false
    }
  })
}

// ===== 导航方法 =====
const goToLogin = () => {
  router.push('/login')
}

// ===== 生命周期：卸载时清除定时器 =====
onUnmounted(() => {
  if (countDownTimer) {
    clearInterval(countDownTimer)
  }
})
</script>
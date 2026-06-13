<template>
  <div class="register-page">
    <h1 class="page-title">账号注册</h1>
    <div class="container">
      <div class="register-card">
        <div class="input-group">
          <label class="input-label">用户名</label>
          <input
            type="text"
            class="input-field"
            placeholder="请输入昵称"
            v-model="nickname"
            :class="{ error: nicknameError }"
          >
          <p v-if="nicknameError" class="error-text">{{ nicknameErrorMsg || '请输入账号' }}</p>
        </div>

        <div class="input-group">
          <label class="input-label">账号</label>
          <input
            type="text"
            class="input-field"
            placeholder="请输入账号（字母/数字）"
            v-model="username"
            :class="{ error: usernameError }"
          >
          <p v-if="usernameError" class="error-text">{{ usernameErrorMsg || '请输入账号' }}</p>
        </div>

        <div class="input-group">
          <label class="input-label">密码</label>
          <input
            type="password"
            class="input-field"
            placeholder="请输入密码（至少6位）"
            v-model="password"
            :class="{ error: passwordError }"
          >
          <p v-if="passwordError" class="error-text">{{ passwordErrorMsg || '请输入密码' }}</p>
        </div>

        <div class="input-group">
          <label class="input-label">确认密码</label>
          <input
            type="password"
            class="input-field"
            placeholder="请再次输入密码"
            v-model="confirmPassword"
            :class="{ error: confirmError }"
          >
          <p v-if="confirmError" class="error-text">两次密码不一致</p>
        </div>

        <div class="input-group">
          <label class="input-label">QQ邮箱</label>
          <div class="email-row">
            <input type="email" class="input-field email-input" placeholder="请输入QQ邮箱"
              v-model="email" :class="{ error: emailError }">
            <button class="code-btn" @click="handleSendCode"
              :disabled="codeSending || countdown > 0">
              {{ countdown > 0 ? countdown + 's' : '发送验证码' }}
            </button>
          </div>
          <p v-if="emailError" class="error-text">{{ emailErrorMsg }}</p>
        </div>

        <div class="input-group">
          <label class="input-label">验证码</label>
          <input type="text" class="input-field" placeholder="请输入6位验证码"
            v-model="code" :class="{ error: codeError }" maxlength="6">
          <p v-if="codeError" class="error-text">请输入验证码</p>
        </div>

        <div class="role-buttons">
          <button
            class="role-btn"
            :class="{'active': selectedRole === 'merchant'}"
            @click="selectRole('merchant')"
          >
            我是商家
          </button>
          <button
            class="role-btn"
            :class="{'active': selectedRole === 'user'}"
            @click="selectRole('user')"
          >
            我是用户
          </button>
        </div>
        <p v-if="roleError" class="error-text">请选择角色</p>

        <button
          class="register-btn"
          @click="handleRegister"
          :disabled="loading"
        >
          {{ loading ? '注册中...' : '注册' }}
        </button>

        <div class="login-link">
          已有账号？<span @click="$router.push('/login')">去登录</span>
        </div>

        <div v-if="message" class="message" :class="{'error': isError}">
          {{ message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import request from '@/api/request';
import { showAlert } from '@/utils/modal';

const router = useRouter();

//响应式数据定义
const selectedRole = ref('user');
const nickname = ref('');
const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const email = ref('')
const code = ref('')
const codeSending = ref(false)
const countdown = ref(0)
const emailError = ref(false)
const emailErrorMsg = ref('')
const codeError = ref(false)
const loading = ref(false);
const message = ref('');
const isError = ref(false);

const nicknameError = ref(false);
const nicknameErrorMsg = ref('');
const usernameError = ref(false);
const usernameErrorMsg = ref('');
const passwordError = ref(false);
const passwordErrorMsg = ref('');
const confirmError = ref(false);
const roleError = ref(false);

//角色选择方法
function selectRole(role) {
  selectedRole.value = role;
  roleError.value = false;
}

//提示消息方法
function showMessage(msg, error = true) {
  message.value = msg;
  isError.value = error;
  setTimeout(() => {
    message.value = '';
  }, 3000);
}

//发送验证码
async function handleSendCode() {
  if (!email.value.trim() || !email.value.includes('@qq.com')) {
    emailError.value = true
    emailErrorMsg.value = '请输入正确的QQ邮箱'
    return
  }
  codeSending.value = true
  try {
    const res = await request.post('/api/send_code', { email: email.value })
    if (res.data.code === 200) {
      await showAlert(res.data.msg, '', 'success')
      countdown.value = 60
      const timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) clearInterval(timer)
      }, 1000)
    } else {
      await showAlert(res.data.msg, '', 'error')
    }
  } catch (err) {
    await showAlert('网络错误', '', 'error')
  } finally {
    codeSending.value = false
  }
}

//监听器：密码确认实时校验
watch([password, confirmPassword], () => {
  if (confirmPassword.value && password.value) {
    confirmError.value = password.value !== confirmPassword.value;
  }
});

function validateForm() {
  let isValid = true;

  if (!nickname.value.trim()){
    nicknameError.value = true;
    nicknameErrorMsg.value = '请输入昵称';
    isValid = false;
  } else {
    nicknameError.value = false;
  }

  if (!username.value.trim()) {
    usernameError.value = true;
    usernameErrorMsg.value = '请输入账号';
    isValid = false;
  } else if (!/^[a-zA-Z0-9]{4,16}$/.test(username.value.trim())) {
    usernameError.value = true;
    usernameErrorMsg.value = '账号需为4-16位字母或数字';
    isValid = false;
  } else {
    usernameError.value = false;
  }


  if (!password.value) {
    passwordError.value = true;
    passwordErrorMsg.value = '请输入密码';
    isValid = false;
  } else if (password.value.length < 6) {
    passwordError.value = true;
    passwordErrorMsg.value = '密码至少6位';
    isValid = false;
  } else {
    passwordError.value = false;
  }


  if (confirmPassword.value && password.value !== confirmPassword.value) {
    confirmError.value = true;
    isValid = false;
  } else {
    confirmError.value = false;
  }

  // 验证角色
  if (!selectedRole.value) {
    roleError.value = true;
    isValid = false;
  } else {
    roleError.value = false;
  }
  // 邮箱验证
  if (!email.value.trim() || !email.value.includes('@qq.com')) {
    emailError.value = true
    emailErrorMsg.value = '请输入QQ邮箱'
    isValid = false
  } else {
    emailError.value = false
  }
  // 验证码校验6位数字
  if (!code.value.trim()) {
    codeError.value = true
    isValid = false
  } else if (!/^\d{6}$/.test(code.value.trim())) {
    codeError.value = true
    showMessage('验证码必须是6位数字', true)
    isValid = false
  } else {
    codeError.value = false
  }
  return isValid;
}

// 注册提交
async function handleRegister() {
  if (!validateForm()) {
    showMessage('请完善注册信息', true);
    return;
  }

  loading.value = true;
  message.value = '';

  try {
    const response = await request.post('/api/register', {
      nickname: nickname.value,
      username: username.value.trim(),
      password: password.value,
      role: selectedRole.value,
      email: email.value,
      code: code.value
    });

    if (response.data.code === 200) {
      showMessage('注册成功，请登录！', false);
      setTimeout(() => {
        router.push('/login');
      }, 1500);
    } else {
      showMessage(response.data.msg || '注册失败', true);
    }
  } catch (error) {
    console.error('注册请求失败：', error);
    showMessage('网络错误，请稍后重试', true);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* ===== 页面布局 ===== */
.register-page {
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
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

/* ===== 注册卡片 ===== */
.register-card {
  background-color: #fff;
  padding: 40px 35px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  width: 100%;
  max-width: 420px;
  box-sizing: border-box;
}

/* ===== 表单输入组 ===== */
.input-group {
  margin-bottom: 24px;
  position: relative;
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
  transition: all 0.3s ease;
  outline: none;
}

.input-field:focus {
  border-color: #82c3ff;
  box-shadow: 0 0 0 3px rgba(130, 195, 255, 0.15);
}

.input-field::placeholder {
  color: #bbb;
}

.input-field.error {
  border-color: #ff4d4f;
  box-shadow: 0 0 0 3px rgba(255, 77, 79, 0.1);
}

/* ===== 错误提示 ===== */
.error-text {
  color: #ff4d4f;
  font-size: 12px;
  margin-top: 4px;
  margin-bottom: 0;
  height: 16px;
}

/* ===== 角色按钮 ===== */
.role-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

/* 角色按钮 - 统一浅蓝 */
.role-btn {
  flex: 1;
  height: 44px;
  border: none;
  border-radius: 8px;
  background-color: #f7f8fa;
  color: #666;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}
.role-btn.active {
  background: linear-gradient(135deg, #82c3ff, #5fb3ff);
  color: #fff;
  box-shadow: 0 4px 12px rgba(130, 195, 255, 0.25);
}
.role-btn:not(.active):hover {
  background-color: #e8f3ff;
  color: #82c3ff;
}

/* ===== 注册按钮 ===== */
/* 注册按钮 - 浅蓝渐变 */
.register-btn {
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
  letter-spacing: 0.5px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(130, 195, 255, 0.25);
}
.register-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #5fb3ff, #4aa8ff);
  box-shadow: 0 6px 16px rgba(130, 195, 255, 0.35);
  transform: translateY(-1px);
}
.register-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(130, 195, 255, 0.2);
}
.register-btn:disabled {
  background: #c3e5ff;
  cursor: not-allowed;
  box-shadow: none;
}

/* ===== 登录链接 ===== */
.login-link {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-bottom: 20px;
}
.login-link span {
  color: #82c3ff;
  cursor: pointer;
  margin-left: 4px;
  font-weight: 500;
}
.login-link span:hover {
  text-decoration: underline;
}

/* ===== 提示消息 ===== */
.message {
  text-align: center;
  padding: 8px 0;
  border-radius: 4px;
  font-size: 14px;
}
.message.error {
  color: #ff4d4f;
  background-color: #fff2f0;
}
.message:not(.error) {
  color: #52c41a;
  background-color: #f6ffed;
}

/* ===== 邮箱与验证码行 ===== */
.email-row {
  display: flex;
  gap: 10px;
}
.email-input {
  flex: 1;
}
.code-btn {
  flex-shrink: 0;
  padding: 0 16px;
  height: 48px;
  background: linear-gradient(135deg, #82c3ff, #5fb3ff);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}
.code-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .register-page {
    padding: 30px 16px;
  }
  .register-card {
    padding: 24px 20px;
  }
  .page-title {
    font-size: 22px;
    margin-bottom: 30px;
  }
  .input-field {
    height: 44px;
    font-size: 14px;
  }
  .register-btn {
    height: 46px;
    font-size: 15px;
  }
}
</style>

<template>
  <div class="login-page">
    <!-- ===== 页面标题 ===== -->
    <h1 class="page-title">欢迎来到次元模仓</h1>
    <div class="container">
      <div class="login-card">
        <!-- ===== 账号输入 ===== -->
        <div class="input-group">
          <label class="input-label">账号</label>
          <input
            type="text"
            class="input-field"
            placeholder="请输入账号"
            v-model="username"
            :class="{ error: usernameError }"
          >
          <p v-if="usernameError" class="error-text">请输入账号</p>
        </div>

        <!-- ===== 密码输入 ===== -->
        <div class="input-group">
          <label class="input-label">密码</label>
          <input
            type="password"
            class="input-field"
            placeholder="请输入密码"
            v-model="password"
            :class="{ error: passwordError }"
          >
          <p v-if="passwordError" class="error-text">请输入密码</p>
        </div>

        <!-- ===== 角色选择 ===== -->
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

        <!-- ===== 登录按钮 ===== -->
        <button
          class="login-btn"
          @click="handleLogin"
          :disabled="loading"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <!-- ===== 注册与找回密码链接 ===== -->
        <div class="register-link">
          还没有账号？<span @click="$router.push('/register')">去注册</span>
          <span class="divider">|</span>
          <span @click="$router.push('/reset-password')">忘记密码？</span>
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
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import request from '@/api/request';
import { showAlert } from '@/utils/modal';

// ===== 路由实例 =====
const router = useRouter();

// ===== 响应式数据定义 =====
const selectedRole = ref('user');
const username = ref('');
const password = ref('');
const loading = ref(false);
const message = ref('');
const isError = ref(false);
const usernameError = ref(false);
const passwordError = ref(false);
const roleError = ref(false);

// ===== 角色选择方法 =====
function selectRole(role) {
  selectedRole.value = role;
  roleError.value = false;
}

// ===== 提示消息方法 =====
function showMessage(msg, error = true) {
  message.value = msg;
  isError.value = error;
  setTimeout(() => {
    message.value = '';
  }, 3000);
}

// ===== 表单验证 =====
function validateForm() {
  let isValid = true;
  usernameError.value = !username.value.trim();
  passwordError.value = !password.value.trim();
  roleError.value = !selectedRole.value;

  if (usernameError.value || passwordError.value || roleError.value) {
    isValid = false;
  }
  return isValid;
}

// ===== 登录提交 =====
async function handleLogin() {
  if (!validateForm()) {
    showMessage('请完善登录信息', true);
    return;
  }

  loading.value = true;
  message.value = '';

  try {
    const response = await request.post('/api/login', {
      username: username.value.trim(),
      password: password.value.trim(),
      role: selectedRole.value
    });

    if (response.data.code === 200) {
      showMessage('登录成功！', false);

      sessionStorage.setItem('token', response.data.token);
      sessionStorage.setItem('userRole', response.data.role);
      sessionStorage.setItem('username', response.data.username);
      sessionStorage.setItem('nickname', response.data.nickname);

      router.push('/');
    } else {
      showMessage(response.data.msg || '登录失败', true);
    }
  } catch (error) {
    console.error('登录请求失败：', error);
    // 检查是否是封禁错误（后端返回403状态码）
    if (error.response && error.response.status === 403) {
      const msg = error.response.data?.msg || '您的账号已被封禁，请联系管理员';
      await showAlert(msg, '账号被封禁', 'error');
    } else {
      showMessage('网络错误，请稍后重试', true);
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* ===== 页面布局 ===== */
.login-page {
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

/* ===== 登录卡片 ===== */
.login-card {
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

/* 角色按钮 - 浅蓝主题 */
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

/* ===== 登录按钮 ===== */
/* 登录按钮 - 浅蓝渐变 */
.login-btn {
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
.login-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #5fb3ff, #4aa8ff);
  box-shadow: 0 6px 16px rgba(130, 195, 255, 0.35);
  transform: translateY(-1px);
}
.login-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(130, 195, 255, 0.2);
}
.login-btn:disabled {
  background: #c3e5ff;
  cursor: not-allowed;
  box-shadow: none;
}

/* ===== 注册与找回密码链接 ===== */
.register-link {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-bottom: 20px;
}
.register-link .divider {
  margin: 0 10px;
  color: #ccc;
}
.register-link span {
  color: #333;
  cursor: pointer;
  margin-left: 4px;
  font-weight: 500;
}
.register-link span:hover {
  color: #fb7299;
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

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .login-page {
    padding: 30px 16px;
  }
  .page-title {
    font-size: 22px;
    margin-bottom: 30px;
  }
  .login-card {
    padding: 24px 20px;
  }
  .input-field {
    height: 44px;
    font-size: 14px;
  }
  .login-btn {
    height: 46px;
    font-size: 15px;
  }
}
</style>

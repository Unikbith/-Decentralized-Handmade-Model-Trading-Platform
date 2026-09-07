<template>
  <AuthLayout title="账号注册">
    <el-form ref="formRef" :model="form" :rules="rules" class="auth-form" @submit.prevent>
      <!-- ===== 用户名 ===== -->
      <el-form-item prop="nickname">
        <el-input v-model="form.nickname" class="auth-field" placeholder="请输入昵称" />
      </el-form-item>

      <!-- ===== 账号 ===== -->
      <el-form-item prop="username">
        <el-input v-model="form.username" class="auth-field" placeholder="请输入账号（字母/数字）" />
      </el-form-item>

      <!-- ===== 密码 ===== -->
      <el-form-item prop="password">
        <el-input v-model="form.password" class="auth-field" type="password" placeholder="请输入密码（至少6位）" />
      </el-form-item>

      <!-- ===== 确认密码 ===== -->
      <el-form-item prop="confirmPassword">
        <el-input v-model="form.confirmPassword" class="auth-field" type="password" placeholder="请再次输入密码" />
      </el-form-item>

      <!-- ===== QQ邮箱 + 发送验证码 ===== -->
      <el-form-item prop="email">
        <div class="email-row">
          <el-input v-model="form.email" class="auth-field email-input" placeholder="请输入QQ邮箱" />
          <button
            type="button"
            class="auth-code-btn"
            :disabled="codeSending || countdown > 0"
            @click="handleSendCode"
          >{{ countdown > 0 ? countdown + 's' : '发送验证码' }}</button>
        </div>
      </el-form-item>

      <!-- ===== 验证码 ===== -->
      <el-form-item prop="code">
        <el-input v-model="form.code" class="auth-field" placeholder="请输入6位验证码" maxlength="6" />
      </el-form-item>

      <!-- ===== 角色选择 ===== -->
      <div class="role-buttons">
        <button
          type="button"
          class="role-btn"
          :class="{ active: form.role === 'merchant' }"
          @click="selectRole('merchant')"
        >我是商家</button>
        <button
          type="button"
          class="role-btn"
          :class="{ active: form.role === 'user' }"
          @click="selectRole('user')"
        >我是用户</button>
      </div>

      <!-- ===== 注册按钮 ===== -->
      <el-button class="btn-primary" type="primary" :loading="loading" @click="handleRegister">
        {{ loading ? '注册中...' : '注册' }}
      </el-button>

      <!-- ===== 登录链接 ===== -->
      <div class="auth-link">
        已有账号？<span class="span-bold" @click="$router.push('/login')">去登录</span>
      </div>
    </el-form>
  </AuthLayout>
</template>

<script setup>
// ===== 导入依赖 =====
import { ref, reactive, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import request from '@/api/request';
import { showAlert } from '@/utils/modal';
import AuthLayout from '@/components/AuthLayout.vue';

const router = useRouter();
const formRef = ref();
const loading = ref(false);
const codeSending = ref(false);
const countdown = ref(0);
let countdownTimer = null;

// ===== 响应式数据 =====
const form = reactive({
  role: 'user',
  nickname: '',
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  code: ''
});

// ===== 自定义校验：确认密码一致性 =====
function validateConfirm(rule, value, callback) {
  if (!value) {
    callback(new Error('请再次输入密码'));
  } else if (value !== form.password) {
    callback(new Error('两次密码不一致'));
  } else {
    callback();
  }
}

// ===== 自定义校验：QQ邮箱 =====
function validateEmail(rule, value, callback) {
  if (!value || !value.includes('@qq.com')) {
    callback(new Error('请输入正确的QQ邮箱'));
  } else {
    callback();
  }
}

// ===== 表单验证规则 =====
const rules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9]{4,16}$/, message: '账号需为4-16位字母或数字', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ],
  email: [{ validator: validateEmail, trigger: 'blur' }],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码必须是6位数字', trigger: 'blur' }
  ]
};

// ===== 角色选择 =====
function selectRole(role) {
  form.role = role;
}

// ===== 发送验证码 =====
async function handleSendCode() {
  if (!form.email.trim() || !form.email.includes('@qq.com')) {
    ElMessage.warning('请输入正确的QQ邮箱');
    return;
  }
  codeSending.value = true;
  try {
    const res = await request.post('/api/send_code', { email: form.email });
    if (res.data.code === 200) {
      await showAlert(res.data.msg, '', 'success');
      countdown.value = 60;
      countdownTimer = setInterval(() => {
        countdown.value--;
        if (countdown.value <= 0) clearInterval(countdownTimer);
      }, 1000);
    } else {
      await showAlert(res.data.msg, '', 'error');
    }
  } catch (err) {
    await showAlert('网络错误', '', 'error');
  } finally {
    codeSending.value = false;
  }
}

// ===== 注册提交 =====
async function handleRegister() {
  formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.warning('请完善注册信息');
      return;
    }

    loading.value = true;
    try {
      const response = await request.post('/api/register', {
        nickname: form.nickname,
        username: form.username.trim(),
        password: form.password,
        role: form.role,
        email: form.email,
        code: form.code
      });

      if (response.data.code === 200) {
        ElMessage.success('注册成功，请登录！');
        setTimeout(() => {
          router.push('/login');
        }, 1500);
      } else {
        ElMessage.error(response.data.msg || '注册失败');
      }
    } catch (error) {
      console.error('注册请求失败：', error);
      ElMessage.error('网络错误，请稍后重试');
    } finally {
      loading.value = false;
    }
  });
}

// ===== 生命周期：卸载时清除倒计时 =====
onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer);
});
</script>
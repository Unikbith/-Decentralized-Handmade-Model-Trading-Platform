<template>
  <AuthLayout title="欢迎来到次元模仓">
    <el-form ref="formRef" :model="form" :rules="rules" class="auth-form" @submit.prevent>
      <!-- ===== 账号 ===== -->
      <el-form-item prop="username">
        <el-input v-model="form.username" class="auth-field" placeholder="请输入账号" />
      </el-form-item>

      <!-- ===== 密码 ===== -->
      <el-form-item prop="password">
        <el-input
          v-model="form.password"
          class="auth-field"
          type="password"
          placeholder="请输入密码"
          show-password
          @keyup.enter="handleLogin"
        />
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

      <!-- ===== 登录按钮 ===== -->
      <el-button class="btn-primary" type="primary" :loading="loading" @click="handleLogin">
        {{ loading ? '登录中...' : '登录' }}
      </el-button>

      <!-- ===== 注册与找回密码链接 ===== -->
      <div class="auth-link">
        还没有账号？<span class="span-bold" @click="$router.push('/register')">去注册</span>
        <span class="divider">|</span>
        <span @click="$router.push('/reset-password')">忘记密码？</span>
      </div>
    </el-form>
  </AuthLayout>
</template>

<script setup>
// ===== 导入依赖 =====
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import request from '@/api/request';
import { showAlert } from '@/utils/modal';
import AuthLayout from '@/components/AuthLayout.vue';

const router = useRouter();
const formRef = ref();
const loading = ref(false);

// ===== 响应式数据 =====
const form = reactive({
  role: 'user',
  username: '',
  password: ''
});

// ===== 表单验证规则 =====
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
};

// ===== 角色选择 =====
function selectRole(role) {
  form.role = role;
}

// ===== 登录提交 =====
async function handleLogin() {
  formRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      const response = await request.post('/api/login', {
        username: form.username.trim(),
        password: form.password.trim(),
        role: form.role
      });

      if (response.data.code === 200) {
        ElMessage.success('登录成功！');

        sessionStorage.setItem('token', response.data.token);
        sessionStorage.setItem('userRole', response.data.role);
        sessionStorage.setItem('username', response.data.username);
        sessionStorage.setItem('nickname', response.data.nickname);

        router.push('/');
      } else {
        ElMessage.error(response.data.msg || '登录失败');
      }
    } catch (error) {
      console.error('登录请求失败：', error);
      // 检查是否是封禁错误（后端返回403状态码）
      if (error.response && error.response.status === 403) {
        const msg = error.response.data?.msg || '您的账号已被封禁，请联系管理员';
        await showAlert(msg, '账号被封禁', 'error');
      } else {
        ElMessage.error('网络错误，请稍后重试');
      }
    } finally {
      loading.value = false;
    }
  });
}
</script>
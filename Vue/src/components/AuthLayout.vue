<template>
  <div class="auth-page">
    <h1 class="page-title">{{ title }}</h1>
    <div class="container">
      <div class="auth-card">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true }
})
</script>

<style scoped>
/* ===== 页面布局 ===== */
.auth-page {
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
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

/* ===== 认证卡片 ===== */
.auth-card {
  background-color: #fff;
  padding: 40px 35px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  width: 100%;
  max-width: 420px;
  box-sizing: border-box;
}

/* ================= 认证页共用样式（仅认证页使用，全局化避免三页重复） ================= */

/* ===== Element Plus 输入框 · 统一为原 style ===== */
:global(.auth-field) {
  width: 100%;
}
:global(.auth-field .el-input__wrapper) {
  height: 48px;
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e0e0e0 inset;
  padding: 0 16px;
  transition: all 0.3s ease;
}
:global(.auth-field .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #82c3ff inset, 0 0 0 3px rgba(130, 195, 255, 0.15);
}
:global(.auth-field .el-input__inner) {
  font-size: 15px;
  color: #333;
  height: 46px;
}
:global(.auth-field .el-input__inner::placeholder) {
  color: #bbb;
}

/* ===== 主提交按钮 · 浅蓝渐变 ===== */
:global(.auth-form .btn-primary.el-button) {
  width: 100%;
  height: 52px;
  margin: 4px 0 16px;
  background: linear-gradient(135deg, #82c3ff, #5fb3ff);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(130, 195, 255, 0.25);
  transition: all 0.3s ease;
}
:global(.auth-form .btn-primary.el-button:not(.is-disabled):hover) {
  background: linear-gradient(135deg, #5fb3ff, #4aa8ff);
  box-shadow: 0 6px 16px rgba(130, 195, 255, 0.35);
  transform: translateY(-1px);
}
:global(.auth-form .btn-primary.el-button.is-disabled) {
  background: #c3e5ff;
  box-shadow: none;
}

/* ===== 发送验证码按钮 · 渐变款（注册页） ===== */
:global(.auth-code-btn) {
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
  transition: all 0.3s ease;
}
:global(.auth-code-btn:disabled) {
  background: #ccc;
  cursor: not-allowed;
}

/* ===== 发送验证码按钮 · 描边款（找回密码页） ===== */
:global(.auth-code-outline) {
  flex-shrink: 0;
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
:global(.auth-code-outline:hover:not(:disabled)) {
  background: #e6f3ff;
}
:global(.auth-code-outline:disabled) {
  background: #f5f5f5;
  color: #999;
  border-color: #e0e0e0;
  cursor: not-allowed;
}

/* ===== 角色按钮 ===== */
:global(.role-buttons) {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
:global(.role-btn) {
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
:global(.role-btn.active) {
  background: linear-gradient(135deg, #82c3ff, #5fb3ff);
  color: #fff;
  box-shadow: 0 4px 12px rgba(130, 195, 255, 0.25);
}
:global(.role-btn:not(.active):hover) {
  background-color: #e8f3ff;
  color: #82c3ff;
}

/* ===== 底部跳转链接 ===== */
:global(.auth-link) {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 4px;
}
:global(.auth-link span) {
  cursor: pointer;
  margin-left: 4px;
  font-weight: 500;
}
:global(.auth-link .span-bold) {
  color: #82c3ff;
}
:global(.auth-link span:hover) {
  text-decoration: underline;
}
:global(.auth-link .divider) {
  margin: 0 10px;
  color: #ccc;
  cursor: default;
}

/* ===== 邮箱与验证码行 ===== */
:global(.email-row) {
  display: flex;
  gap: 10px;
}
:global(.email-row .auth-field) {
  flex: 1;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .auth-page {
    padding: 30px 16px;
  }
  .page-title {
    font-size: 22px;
    margin-bottom: 30px;
  }
  .auth-card {
    padding: 24px 20px;
    max-width: 100%;
  }
  :global(.auth-form .btn-primary.el-button) {
    height: 46px;
    font-size: 15px;
  }
  :global(.auth-code-outline) {
    width: 100px;
    height: 44px;
    font-size: 13px;
  }
  :global(.auth-code-btn) {
    height: 44px;
  }
  :global(.auth-field .el-input__wrapper) {
    height: 44px;
  }
  :global(.auth-field .el-input__inner) {
    height: 42px;
    font-size: 14px;
  }
}
</style>
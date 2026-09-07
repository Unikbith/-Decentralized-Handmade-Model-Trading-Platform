<template>
  <el-dialog
    v-model="visibleDialog"
    title="编辑用户信息"
    width="460px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form ref="formRef" :model="form" label-width="90px" class="admin-dialog-form">
      <el-form-item label="用户ID">
        <el-input :model-value="form.id" disabled />
      </el-form-item>
      <el-form-item label="用户账号">
        <el-input :model-value="form.username" disabled />
      </el-form-item>
      <el-form-item label="用户昵称" prop="nickname">
        <el-input v-model="form.nickname" placeholder="请输入用户昵称" />
      </el-form-item>
      <el-form-item label="用户角色">
        <el-select v-model="form.role" class="full-select">
          <el-option label="普通用户" value="user" />
          <el-option label="商家" value="merchant" />
        </el-select>
      </el-form-item>
      <el-form-item label="头像URL">
        <el-input v-model="form.avatar" placeholder="请输入头像链接" />
        <div v-if="form.avatar" class="avatar-preview">
          <img :src="form.avatar" alt="头像预览" />
        </div>
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="form.phone" placeholder="请输入手机号" maxlength="11" />
      </el-form-item>
      <el-form-item label="收货地址">
        <el-input v-model="form.address" type="textarea" :rows="3" placeholder="请输入收货地址" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" class="pink-btn" :loading="saving" @click="handleSave">
        {{ saving ? '保存中...' : '保存修改' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const props = defineProps({
  visible: Boolean,
  user: { type: Object, default: null }
})
const emit = defineEmits(['update:visible', 'saved'])

const visibleDialog = computed({
  get: () => props.visible,
  set: v => emit('update:visible', v)
})

const formRef = ref()
const saving = ref(false)

const form = reactive({
  id: null,
  username: '',
  nickname: '',
  role: 'user',
  avatar: '',
  phone: '',
  address: ''
})

watch(
  () => props.visible,
  (v) => {
    if (!v || !props.user) return
    const u = props.user
    form.id = u.id
    form.username = u.username || ''
    form.nickname = u.nickname || ''
    form.role = u.role || 'user'
    form.avatar = u.avatar || ''
    form.phone = u.phone || ''
    form.address = u.address || ''
  }
)

const resetForm = () => {
  formRef.value?.clearValidate()
  saving.value = false
}

const handleClose = () => { visibleDialog.value = false }

const handleSave = async () => {
  if (!form.nickname.trim()) return ElMessage.error('请输入用户昵称')
  if (!['user', 'merchant', 'admin'].includes(form.role)) return ElMessage.error('请选择有效用户角色')
  if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone.trim())) return ElMessage.error('请输入正确的11位手机号码')

  saving.value = true
  try {
    const res = await request.post(`/api/admin/user/update/${form.id}`, {
      nickname: form.nickname.trim(),
      role: form.role,
      avatar: form.avatar.trim(),
      phone: form.phone.trim(),
      address: form.address.trim()
    })
    if (res.data.code === 200) {
      ElMessage.success('用户信息修改成功')
      visibleDialog.value = false
      emit('saved', form.id)
    } else {
      ElMessage.error(res.data.msg || '修改失败')
    }
  } catch (err) {
    console.error('保存用户失败', err)
    ElMessage.error('修改用户信息失败，请检查后端接口')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.full-select { width: 100%; }
.avatar-preview { margin-top: 8px; }
.avatar-preview img {
  width: 60px; height: 60px; border-radius: 8px; object-fit: cover; border: 1px solid #eee;
}
.pink-btn { background: #fb7299; border-color: #fb7299; }
.pink-btn:hover { background: #f7507f; border-color: #f7507f; }
</style>
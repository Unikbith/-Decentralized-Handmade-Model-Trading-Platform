<template>
  <el-dialog v-model="visibleDialog" title="用户详情" width="460px" :close-on-click-modal="false" @closed="resetDetail">
    <div v-if="detail.id" class="detail-list">
      <div class="detail-item">
        <label>用户ID：</label>
        <span>{{ detail.id }}</span>
      </div>
      <div class="detail-item">
        <label>账号：</label>
        <span>{{ detail.username }}</span>
      </div>
      <div class="detail-item">
        <label>昵称：</label>
        <span>{{ detail.nickname }}</span>
      </div>
      <div class="detail-item">
        <label>角色：</label>
        <span>{{ detail.role === 'merchant' ? '商家' : '普通用户' }}</span>
      </div>
      <div class="detail-item">
        <label>封禁状态：</label>
        <span :class="detail.is_banned === 1 ? 'status-banned' : 'status-normal'">
          {{ detail.is_banned === 1 ? '已封禁' : '正常' }}
        </span>
      </div>
      <div class="detail-item">
        <label>头像：</label>
        <img v-if="detail.avatar" :src="detail.avatar" class="detail-avatar" alt="头像" />
        <span v-else>未设置</span>
      </div>
      <div class="detail-item">
        <label>手机号：</label>
        <span>{{ detail.phone || '未设置' }}</span>
      </div>
      <div class="detail-item">
        <label>收货地址：</label>
        <span>{{ detail.address || '未设置' }}</span>
      </div>
    </div>

    <template #footer>
      <el-button type="primary" class="pink-btn" @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const props = defineProps({
  visible: Boolean,
  userId: { type: [Number, String], default: null }
})
const emit = defineEmits(['update:visible'])

const visibleDialog = computed({
  get: () => props.visible,
  set: v => emit('update:visible', v)
})

const detail = reactive({
  id: null,
  username: '',
  nickname: '',
  role: '',
  is_banned: 0,
  avatar: '',
  phone: '',
  address: ''
})

watch(
  () => props.visible,
  (v) => {
    if (v && props.userId) {
      fetchDetail(props.userId)
    }
  }
)

const fetchDetail = async (userId) => {
  try {
    const res = await request.get(`/api/admin/user/detail/${userId}`)
    if (res.data.code === 200) {
      const user = res.data.data
      detail.id = user.id
      detail.username = user.username || ''
      detail.nickname = user.nickname || ''
      detail.role = user.role || 'user'
      detail.is_banned = user.is_banned || 0
      detail.avatar = user.info?.avatar || ''
      detail.phone = user.info?.phone || ''
      detail.address = user.info?.address || ''
    } else {
      ElMessage.error(res.data.msg || '获取用户详情失败')
    }
  } catch (err) {
    ElMessage.error('获取用户详情失败，请检查接口')
  }
}

const resetDetail = () => {
  detail.id = null
}

const handleClose = () => { visibleDialog.value = false }

defineExpose({ refresh: fetchDetail })
</script>

<style scoped>
.detail-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #e5e6eb;
}
.detail-item:last-child { border-bottom: none; }
.detail-item label {
  width: 80px; flex-shrink: 0; font-weight: 500; color: #595959;
}
.detail-item span { color: #262626; flex: 1; }
.status-banned { color: #C53F3F; font-weight: 500; }
.status-normal { color: #449A44; font-weight: 500; }
.detail-avatar { width: 60px; height: 60px; border-radius: 8px; object-fit: cover; }
.pink-btn { background: #fb7299; border-color: #fb7299; }
.pink-btn:hover { background: #f7507f; border-color: #f7507f; }
</style>
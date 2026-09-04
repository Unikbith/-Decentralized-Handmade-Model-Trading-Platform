<template>
  <el-dialog
    v-model="visibleDialog"
    title="编辑订单信息"
    width="520px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form ref="formRef" :model="form" label-width="90px" class="admin-dialog-form">
      <el-form-item label="订单号">
        <el-input :model-value="order?.order_no" disabled />
      </el-form-item>
      <el-form-item label="收货人姓名" prop="receiver_name">
        <el-input v-model="form.receiver_name" placeholder="请输入收货人姓名" />
      </el-form-item>
      <el-form-item label="联系电话" prop="receiver_phone">
        <el-input v-model="form.receiver_phone" placeholder="请输入联系电话" maxlength="11" />
      </el-form-item>
      <el-form-item label="收货地区">
        <div class="area-selects">
          <el-select v-model="province" placeholder="请选择省" @change="onProvinceChange">
            <el-option v-for="p in provinces" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
          <el-select v-model="city" placeholder="请选择市" :disabled="!province" @change="onCityChange">
            <el-option v-for="c in cities" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
          <el-select v-model="district" placeholder="请选择区" :disabled="!city">
            <el-option v-for="d in districts" :key="d.value" :label="d.label" :value="d.value" />
          </el-select>
        </div>
      </el-form-item>
      <el-form-item label="详细地址" prop="receiver_detail">
        <el-input v-model="form.receiver_detail" type="textarea" :rows="3" placeholder="请输入详细地址" />
      </el-form-item>
      <el-form-item label="订单总金额" prop="total_price">
        <el-input v-model="form.total_price" type="number" placeholder="请输入订单总金额" min="0" step="0.01" />
      </el-form-item>
      <el-form-item label="订单状态">
        <el-select v-model="form.status" class="full-select">
          <el-option v-for="(label, val) in statusMap" :key="val" :label="label" :value="val" />
        </el-select>
        <p class="form-tip">修改订单状态会同步更新用户端显示</p>
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
import { regionData } from 'element-china-area-data'
import request from '@/api/request'

const props = defineProps({
  visible: Boolean,
  order: { type: Object, default: null }
})
const emit = defineEmits(['update:visible', 'saved'])

const visibleDialog = computed({
  get: () => props.visible,
  set: v => emit('update:visible', v)
})

const formRef = ref()
const saving = ref(false)

const form = reactive({
  receiver_name: '',
  receiver_phone: '',
  receiver_detail: '',
  total_price: 0,
  status: ''
})

const province = ref('')
const city = ref('')
const district = ref('')

const statusMap = {
  pending_pay: '待付款',
  pending_ship: '待发货',
  pending_receive: '待收货',
  completed: '已完成',
  refund: '退款/售后',
  refunded: '已退款'
}

const provinces = computed(() => regionData.map(i => ({ value: i.value, label: i.label })))
const cities = computed(() => {
  const p = regionData.find(x => x.value === province.value)
  return (p?.children || []).map(c => ({ value: c.value, label: c.label }))
})
const districts = computed(() => {
  const p = regionData.find(x => x.value === province.value)
  const c = p?.children?.find(x => x.value === city.value)
  return (c?.children || []).map(d => ({ value: d.value, label: d.label }))
})

const findValueByLabel = (data, label) => {
  if (!label) return ''
  for (const item of data) {
    if (item.label === label) return item.value
    if (item.children?.length) {
      const r = findValueByLabel(item.children, label)
      if (r) return r
    }
  }
  return ''
}

const onProvinceChange = () => { city.value = ''; district.value = '' }
const onCityChange = () => { district.value = '' }

// 打开时回填表单（含地址三级联动还原）
watch(
  () => props.visible,
  (v) => {
    if (!v || !props.order) return
    const o = props.order
    form.receiver_name = o.receiver_name || ''
    form.receiver_phone = o.receiver_phone || ''
    form.total_price = parseFloat(o.total_price) || 0
    form.status = statusMap[o.status] ? o.status : 'pending_pay'

    let pLabel = '', cLabel = '', dLabel = '', detail = ''
    try {
      const addr = JSON.parse(o.receiver_address)
      pLabel = addr.province || ''
      cLabel = addr.city || ''
      dLabel = addr.district || ''
      detail = addr.detail || ''
    } catch (e) {
      detail = o.receiver_address || ''
    }
    form.receiver_detail = detail

    province.value = findValueByLabel(regionData, pLabel)
    city.value = province.value ? findValueByLabel(regionData.find(p => p.value === province.value)?.children || [], cLabel) : ''
    district.value = city.value
      ? findValueByLabel(regionData.find(p => p.value === province.value)?.children?.find(c => c.value === city.value)?.children || [], dLabel)
      : ''
  }
)

const resetForm = () => {
  formRef.value?.clearValidate()
  saving.value = false
}

const handleClose = () => { visibleDialog.value = false }

const handleSave = async () => {
  if (!form.receiver_name.trim()) return ElMessage.error('请输入收货人姓名')
  if (!/^1[3-9]\d{9}$/.test(form.receiver_phone.trim())) return ElMessage.error('请输入正确的11位手机号码')

  const pLabel = provinces.value.find(p => p.value === province.value)?.label || ''
  const cLabel = cities.value.find(c => c.value === city.value)?.label || ''
  const dLabel = districts.value.find(d => d.value === district.value)?.label || ''
  if (!pLabel || !cLabel || !dLabel) return ElMessage.error('请选择完整的省市区')
  if (!form.receiver_detail.trim()) return ElMessage.error('请输入详细地址')
  if (parseFloat(form.total_price) < 0) return ElMessage.error('订单总金额不能为负数')

  const addressJson = JSON.stringify({
    province: pLabel, city: cLabel, district: dLabel, detail: form.receiver_detail.trim()
  })

  saving.value = true
  try {
    const res = await request.post(`/api/admin/order/update/${props.order.id}`, {
      receiver_name: form.receiver_name.trim(),
      receiver_phone: form.receiver_phone.trim(),
      receiver_address: addressJson,
      total_price: parseFloat(parseFloat(form.total_price).toFixed(2)),
      status: form.status
    })
    if (res.data.code === 200) {
      ElMessage.success('订单信息修改成功')
      visibleDialog.value = false
      emit('saved')
    } else {
      ElMessage.error(res.data.msg || '修改失败')
    }
  } catch (err) {
    console.error('保存订单失败', err)
    ElMessage.error('修改订单信息失败，请稍后重试')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.full-select { width: 100%; }
.area-selects { display: flex; gap: 8px; width: 100%; }
.area-selects :deep(.el-select) { flex: 1; }
.form-tip { margin-top: 6px; font-size: 12px; color: #999; line-height: 1.5; }
.pink-btn { background: #fb7299; border-color: #fb7299; }
.pink-btn:hover { background: #f7507f; border-color: #f7507f; }
</style>
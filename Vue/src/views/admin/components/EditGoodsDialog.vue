<template>
  <el-dialog
    v-model="visibleDialog"
    title="编辑商品信息"
    width="520px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <el-form ref="formRef" :model="form" label-width="90px" class="admin-dialog-form">
      <el-form-item label="商品ID">
        <el-input :model-value="goods?.id" disabled />
      </el-form-item>
      <el-form-item label="商品名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入商品名称" />
      </el-form-item>
      <el-form-item label="商品价格" prop="price">
        <el-input v-model="form.price" type="number" placeholder="请输入商品价格" min="0" step="0.01" />
      </el-form-item>
      <el-form-item label="商品库存" prop="stock">
        <el-input v-model="form.stock" type="number" placeholder="请输入商品库存" min="0" @input="handleStockChange" />
      </el-form-item>
      <el-form-item label="商品分类">
        <el-select v-model="form.category" class="full-select">
          <el-option label="未分类" value="" />
          <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
        </el-select>
      </el-form-item>
      <el-form-item label="商品状态">
        <el-select v-model="form.status" class="full-select">
          <el-option v-if="form.stock === 0" label="缺货" value="缺货" />
          <template v-else>
            <el-option label="现货" value="现货" />
            <el-option label="预售" value="预售" />
            <el-option label="下架" value="下架" />
          </template>
        </el-select>
        <p v-if="form.stock === 0" class="form-tip">库存为0时，商品状态自动为"缺货"</p>
      </el-form-item>
      <el-form-item label="商品品牌">
        <el-input v-model="form.brand" placeholder="请输入商品品牌" />
      </el-form-item>
      <el-form-item label="IP名称">
        <el-input v-model="form.ip" placeholder="请输入IP名称" />
      </el-form-item>
      <el-form-item label="角色名称">
        <el-input v-model="form.character" placeholder="请输入角色名称" />
      </el-form-item>
      <el-form-item label="商品描述">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入商品描述" />
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
  goods: { type: Object, default: null }
})
const emit = defineEmits(['update:visible', 'saved'])

const visibleDialog = computed({
  get: () => props.visible,
  set: v => emit('update:visible', v)
})

const formRef = ref()
const saving = ref(false)

const form = reactive({
  name: '',
  price: 0,
  stock: 0,
  category: '',
  status: '',
  brand: '',
  ip: '',
  character: '',
  description: ''
})

const categories = ['景品', 'Q版手办', '可动手办', '盒蛋', '雕像', '拼装模型', '原创/同人作品', 'GK白模/手办']

watch(
  () => props.visible,
  (v) => {
    if (!v || !props.goods) return
    const g = props.goods
    form.name = g.name || ''
    form.price = g.price
    form.stock = g.stock || 0
    form.category = g.category || ''
    form.status = (g.stock || 0) === 0 ? '缺货' : (g.status || '现货')
    form.brand = g.brand || ''
    form.ip = g.ip || ''
    form.character = g.charactername || ''
    form.description = g.description || ''
  }
)

const resetForm = () => {
  formRef.value?.clearValidate()
  saving.value = false
}

const handleStockChange = () => {
  const oldStock = form.stock
  const newStock = parseInt(form.stock) || 0
  form.stock = newStock
  if (newStock === 0) {
    form.status = '缺货'
  } else if (oldStock === 0 && newStock > 0 && form.status === '缺货') {
    form.status = '现货'
  }
}

const handleClose = () => { visibleDialog.value = false }

const handleSave = async () => {
  if (!form.name.trim()) return ElMessage.error('请输入商品名称')
  if (parseFloat(form.price) < 0) return ElMessage.error('商品价格不能为负数')
  if (form.stock < 0) return ElMessage.error('商品库存不能为负数')

  const finalStatus = form.stock === 0 ? '缺货' : form.status

  saving.value = true
  try {
    const res = await request.post(`/api/admin/goods/update/${props.goods.id}`, {
      name: form.name.trim(),
      price: parseFloat(form.price),
      stock: parseInt(form.stock),
      category: form.category.trim(),
      status: finalStatus,
      brand: form.brand.trim(),
      ip: form.ip.trim(),
      character: form.character.trim(),
      description: form.description.trim()
    })
    if (res.data.code === 200) {
      ElMessage.success('商品信息修改成功')
      visibleDialog.value = false
      emit('saved')
    } else {
      ElMessage.error(res.data.msg || '修改失败')
    }
  } catch (err) {
    ElMessage.error('修改商品信息失败，请稍后重试')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.full-select { width: 100%; }
.form-tip { margin-top: 6px; font-size: 12px; color: #999; line-height: 1.5; }
.pink-btn { background: #fb7299; border-color: #fb7299; }
.pink-btn:hover { background: #f7507f; border-color: #f7507f; }
</style>
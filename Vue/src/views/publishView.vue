<template>
  <div class="publish-page">
    <div class="container">
      <h1 class="page-title">{{ editingGoodsId ? '编辑商品' : '商品上架' }}</h1>
      <div class="publish-form">
        <el-form ref="formRef" :model="form" :rules="rules" class="goods-form" label-position="top" @submit.prevent>
          <!--商品图片上传-->
          <el-form-item label="商品图片">
            <el-upload
              v-model:file-list="imageList"
              list-type="picture-card"
              accept="image/*"
              :limit="10"
              :http-request="onUploadRequest"
              :before-upload="beforeUpload"
              :on-exceed="handleExceed"
            >
              <div class="upload-trigger">
                <span class="plus">+</span>
                <span>上传图片</span>
              </div>
            </el-upload>
            <div class="tips">最多上传10张图片，第一张为主图</div>
          </el-form-item>

          <!--基础信息表单-->
          <div class="form-row">
            <el-form-item class="half" label="商品名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入商品名称" />
            </el-form-item>
            <el-form-item class="half" label="价格（元）" prop="price">
              <el-input v-model="form.price" placeholder="请输入价格" min="0.01" step="0.01" />
            </el-form-item>
          </div>

          <div class="form-row">
            <el-form-item class="half" label="库存" prop="stock">
              <el-input v-model="form.stock" placeholder="请输入库存" min="1" step="1" />
            </el-form-item>
            <el-form-item class="half" label="所属IP">
              <el-input v-model="form.ip" placeholder="请输入所属IP/作品" />
            </el-form-item>
          </div>

          <div class="form-row">
            <el-form-item class="half" label="角色">
              <el-input v-model="form.character" placeholder="请输入角色名称" />
            </el-form-item>
            <el-form-item class="half" label="商品状态" prop="status">
              <el-select v-model="form.status" placeholder="请选择商品状态" class="full-select">
                <el-option label="现货" value="现货" />
                <el-option label="预售" value="预售" />
              </el-select>
            </el-form-item>
          </div>

          <div class="form-row">
            <el-form-item class="half" label="分类" prop="category">
              <el-select v-model="form.category" placeholder="请选择商品分类" class="full-select" @change="handleCategoryChange">
                <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
            <el-form-item class="half" label="品牌">
              <el-input v-model="form.brand" placeholder="请输入品牌/厂商" />
            </el-form-item>
          </div>

          <!--自定义分类输入框-->
          <div class="form-row" v-if="form.category === '其他'">
            <el-form-item class="half" label="自定义分类" prop="customCategory">
              <el-input v-model="form.customCategory" placeholder="请输入自定义分类名称" />
            </el-form-item>
          </div>

          <el-form-item label="商品简介">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              placeholder="请输入商品简介，用于列表展示"
              resize="vertical"
            />
          </el-form-item>

          <!--提交按钮-->
          <div class="submit-area">
            <el-button class="goods-submit" :loading="loading" @click="handleSubmit">
              {{ loading ? '提交中...' : (editingGoodsId ? '保存修改' : '发布商品') }}
            </el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
// ===== 导入依赖 =====
import { ref, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import request from '@/api/request';

const router = useRouter();
const route = useRoute();
const formRef = ref();

// ===== 响应式数据定义 =====
const loading = ref(false);
const editingGoodsId = ref(null);
const merchantApplyStatus = ref('none');
const imageList = ref([]);
const presetCategories = ['景品', 'Q版手办', '可动手办', '盒蛋', '雕像', '拼装模型', '原创/同人作品', 'GK白模/手办'];
const categories = [...presetCategories, '其他'];

const form = reactive({
  name: '',
  price: '',
  stock: 1,
  ip: '',
  character: '',
  status: '',
  category: '',
  customCategory: '',
  brand: '',
  description: '',
});

// ===== 自定义校验：上传至少一张图片 =====
function validateImages(rule, value, callback) {
  if (imageList.value.length === 0) {
    callback(new Error('请至少上传一张商品图片'));
  } else {
    callback();
  }
}

// ===== 表单验证规则 =====
const rules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入正确的价格', trigger: 'blur' }],
  status: [{ required: true, message: '请选择商品状态', trigger: 'change' }],
  category: [{ required: true, message: '请选择商品分类', trigger: 'change' }],
  customCategory: [
    {
      validator: (rule, value, callback) => {
        if (form.category === '其他' && !value?.trim()) {
          callback(new Error('请输入自定义分类名称'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
  images: [{ validator: validateImages, trigger: 'change' }]
};

// ===== 图片上传触发 =====
const handleExceed = (files, fileList) => {
  ElMessage.warning('最多只能上传10张图片');
};

// ===== 上传前校验：单张大小 =====
const beforeUpload = (file) => {
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning(`图片 ${file.name} 超过5MB，已跳过`);
    return false;
  }
  return true;
};

// ===== 自定义上传请求（保持原有上传逻辑） =====
const onUploadRequest = async (options) => {
  const token = sessionStorage.getItem('token');
  if (!token) {
    ElMessage.error('请先登录！');
    options.onError(new Error('未登录'));
    router.push('/login');
    return;
  }

  const formData = new FormData();
  formData.append('file', options.file);

  try {
    const response = await request.post('/api/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    if (response.data.code === 200) {
      // 回填 URL 以便预览图正常展示
      options.file.url = response.data.url;
      options.file.status = 'success';
      options.onSuccess(response.data);
    } else {
      options.onError(new Error(response.data.msg || '上传失败'));
    }
  } catch (error) {
    options.onError(new Error(error.response?.data?.msg || '网络异常，上传失败'));
  }
};

// ===== 分类切换处理 =====
const handleCategoryChange = () => {
  if (form.category !== '其他') {
    form.customCategory = '';
  }
};

// ===== 从Token解析角色 =====
const getRoleFromToken = () => {
  const token = sessionStorage.getItem('token');
  if (!token) return '';
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.role || '';
  } catch (e) {
    return '';
  }
};

// ===== 获取商家入驻状态 =====
const getMerchantApplyStatus = async () => {
  if (getRoleFromToken() !== 'merchant') return;
  try {
    const res = await request.get('/api/merchant/apply-status');
    if (res.data.code === 200) {
      merchantApplyStatus.value = res.data.data.apply_status;
    }
  } catch (err) {
    console.error('获取入驻状态失败:', err);
  }
};

// ===== 生命周期钩子 =====
onMounted(() => {
  const goodsId = route.query.id;
  if (goodsId) {
    editingGoodsId.value = goodsId;
    getGoodsDetail(goodsId);
  }
  getMerchantApplyStatus();
});

// ===== API请求方法：获取商品详情用于编辑 =====
const getGoodsDetail = async (id) => {
  try {
    const res = await request.get(`/api/goods/detail/${id}`);
    if (res.data.code === 200) {
      const data = res.data.data;
      const isPresetCategory = presetCategories.includes(data.category);

      Object.assign(form, {
        name: data.name,
        price: data.price,
        stock: data.stock,
        ip: data.ip,
        character: data.character,
        status: data.status,
        category: isPresetCategory ? data.category : '其他',
        customCategory: isPresetCategory ? '' : data.category,
        brand: data.brand,
        description: data.description,
      });
      imageList.value = data.images.map(url => ({ name: url, url }));
    } else {
      ElMessage.error(res.data.msg || '获取商品详情失败');
    }
  } catch (error) {
    ElMessage.error('网络错误，获取商品详情失败');
  }
};

// ===== 清空表单（发布成功后重置） =====
function resetForm() {
  Object.assign(form, {
    name: '', price: '', stock: 1, ip: '', character: '',
    status: '', category: '', customCategory: '', brand: '', description: '',
  });
  imageList.value = [];
  editingGoodsId.value = null;
}

// ===== 表单提交（支持新增和更新） =====
const handleSubmit = async () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return;

    const token = sessionStorage.getItem('token');
    if (!token) {
      ElMessage.error('请先登录！');
      router.push('/login');
      return;
    }

    // 商家入驻状态校验
    if (getRoleFromToken() === 'merchant' && !editingGoodsId.value) {
      if (merchantApplyStatus.value === 'none') {
        ElMessage.warning('请先提交入驻申请，等待管理员审核通过后再发布商品');
        return;
      } else if (merchantApplyStatus.value === 'pending') {
        ElMessage.warning('您的入驻申请正在审核中，请等待管理员审核通过');
        return;
      } else if (merchantApplyStatus.value === 'rejected') {
        ElMessage.warning('您的入驻申请已被拒绝，无法发布商品，如有疑问请联系管理员');
        return;
      }
    }

    loading.value = true;

    try {
      const actualCategory = form.category === '其他' ? form.customCategory.trim() : form.category;
      const payload = {
        name: form.name,
        price: form.price,
        stock: form.stock,
        ip: form.ip,
        character: form.character,
        status: form.status,
        category: actualCategory,
        brand: form.brand,
        description: form.description,
        images: imageList.value.map(f => f.url)
      };

      const url = editingGoodsId.value
        ? `/api/goods/update/${editingGoodsId.value}`
        : '/api/goods/publish';

      const response = await request.post(url, payload);

      if (response.data.code === 200) {
        ElMessage.success(editingGoodsId.value ? '商品更新成功！' : '商品上架成功！');
        resetForm();
        setTimeout(() => {
          router.push('/profile');
        }, 1500);
      } else {
        ElMessage.error(response.data.msg || '操作失败');
      }
    } catch (error) {
      console.error('操作失败:', error);
      ElMessage.error('网络错误，请稍后重试');
    } finally {
      loading.value = false;
    }
  });
};
</script>

<style scoped>
/* ===== 页面布局 ===== */
.publish-page {
  min-height: 100vh;
  padding: 80px 20px 40px;
  box-sizing: border-box;
  background: #f5f5f5;
}

.container {
  max-width: 720px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #0a0a0a;
  text-align: center;
  margin-bottom: 40px;
  letter-spacing: -0.5px;
}

/* ===== 表单容器 ===== */
.publish-form {
  background: #fafafa;
  padding: 32px;
  border-radius: 16px;
  border: 1px solid #e5e5e5;
}

.form-row {
  display: flex;
  gap: 20px;
}

.form-row .half {
  flex: 1;
}

/* ===== Element Plus 表单元素 · 统一为原 style ===== */
.goods-form :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: #0a0a0a;
  letter-spacing: 0.3px;
  padding-bottom: 8px;
}
.goods-form :deep(.el-form-item.is-required .el-form-item__label::before) {
  color: #ff6b9d;
}
.goods-form :deep(.el-input__wrapper),
.goods-form :deep(.el-textarea__inner) {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e5e5e5 inset;
  transition: box-shadow 0.2s ease;
}
.goods-form :deep(.el-input__wrapper:hover),
.goods-form :deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px #ccc inset;
}
.goods-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #ff6b9d inset, 0 0 0 3px rgba(255, 107, 157, 0.15);
}
.goods-form :deep(.el-input__inner) {
  font-size: 14px;
  color: #0a0a0a;
}
.goods-form .full-select {
  width: 100%;
}
.goods-form :deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e5e5e5 inset;
}
.goods-form :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px #ff6b9d inset, 0 0 0 3px rgba(255, 107, 157, 0.15);
}
.goods-form :deep(.el-textarea__inner) {
  font-family: inherit;
  resize: vertical;
}

/* ===== 图片上传区域 ===== */
.tips {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.6;
  width: 100%;
}
.upload-trigger {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #666;
  font-size: 11px;
  transition: color 0.2s ease;
}
.upload-trigger .plus {
  font-size: 24px;
  line-height: 1;
  margin-bottom: 4px;
  font-weight: 300;
}
.goods-form :deep(.el-upload--picture-card),
.goods-form :deep(.el-upload-list--picture-card .el-upload-list__item) {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  border: 1px dashed #ccc;
  background: #fff;
}
.goods-form :deep(.el-upload--picture-card:hover) {
  border-color: #ff6b9d;
}
.goods-form :deep(.el-upload--picture-card:hover .upload-trigger) {
  color: #ff6b9d;
}
.goods-form :deep(.el-upload-list--picture-card .el-upload-list__item) {
  border: 1px solid #e5e5e5;
}
.goods-form :deep(.el-upload-list--picture-card .el-upload-list__item-delete:hover) {
  background: rgba(255, 107, 157, 0.9);
}

/* ===== 提交按钮 ===== */
.submit-area {
  margin-top: 8px;
  text-align: center;
}
.goods-submit.el-button {
  width: 100%;
  max-width: 200px;
  height: 44px;
  background: linear-gradient(135deg, #ff6b9d 0%, #ff8a80 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
  transition: all 0.2s ease;
}
.goods-submit.el-button:not(.is-disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(255, 107, 157, 0.4);
}
.goods-submit.el-button.is-loading {
  opacity: 0.6;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .publish-page {
    padding: 70px 16px 24px;
  }
  .publish-form {
    padding: 24px 20px;
  }
  .form-row {
    flex-direction: column;
    gap: 0;
  }
  .goods-submit.el-button {
    max-width: 100%;
  }
  .page-title {
    font-size: 20px;
    margin-bottom: 24px;
  }
}
</style>
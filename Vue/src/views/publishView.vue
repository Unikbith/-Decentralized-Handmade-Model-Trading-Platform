<template>
  <div class="publish-page">
    <div class="container">
      <h1 class="page-title">{{ editingGoodsId ? '编辑商品' : '商品上架' }}</h1>
      <div class="publish-form">
        <!--商品图片上传-->
        <div class="form-group">
          <label class="form-label">商品图片</label>
          <div class="image-upload-area">
            <div class="image-preview-list">
              <div class="image-item" v-for="(url, index) in imageList" :key="index">
                <img :src="url" alt="商品图" class="preview-img">
                <button class="delete-btn" @click="deleteImage(index)">×</button>
              </div>
              <div class="upload-box" v-if="imageList.length < 10">
                <input type="file" id="file-upload" accept="image/*" @change="handleImageUpload" hidden multiple>
                <label for="file-upload" class="upload-label">
                  <span class="plus">+</span>
                  <span>上传图片</span>
                </label>
              </div>
            </div>
            <p class="tips">最多上传10张图片，第一张为主图</p>
          </div>
        </div>

        <!--基础信息表单-->
        <div class="form-row">
          <div class="form-group half">
            <label class="form-label">商品名称 <span class="required">*</span></label>
            <input type="text" class="form-input" v-model="form.name" placeholder="请输入商品名称">
          </div>
          <div class="form-group half">
            <label class="form-label">价格（元） <span class="required">*</span></label>
            <input type="number" class="form-input" v-model="form.price" placeholder="请输入价格" min="0.01" step="0.01">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group half">
            <label class="form-label">库存 <span class="required">*</span></label>
            <input type="number" class="form-input" v-model="form.stock" placeholder="请输入库存" min="1" step="1">
          </div>
          <div class="form-group half">
            <label class="form-label">所属IP</label>
            <input type="text" class="form-input" v-model="form.ip" placeholder="请输入所属IP/作品">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group half">
            <label class="form-label">角色</label>
            <input type="text" class="form-input" v-model="form.character" placeholder="请输入角色名称">
          </div>
          <div class="form-group half">
            <label class="form-label">商品状态 <span class="required">*</span></label>
            <select class="form-input" v-model="form.status">
              <option value="" disabled>请选择商品状态</option>
              <option value="现货">现货</option>
              <option value="预售">预售</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group half">
            <label class="form-label">分类 <span class="required">*</span></label>
            <select class="form-input" v-model="form.category" @change="handleCategoryChange">
              <option value="" disabled>请选择商品分类</option>
              <option value="景品">景品</option>
              <option value="Q版手办">Q版手办</option>
              <option value="可动手办">可动手办</option>
              <option value="盒蛋">盒蛋</option>
              <option value="雕像">雕像</option>
              <option value="拼装模型">拼装模型</option>
              <option value="原创/同人作品">原创/同人作品</option>
              <option value="GK白模/手办">GK白模/手办</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="form-group half">
            <label class="form-label">品牌</label>
            <input type="text" class="form-input" v-model="form.brand" placeholder="请输入品牌/厂商">
          </div>
        </div>

        <!--自定义分类输入框-->
        <div class="form-row" v-if="form.category === '其他'">
          <div class="form-group half">
            <label class="form-label">自定义分类 <span class="required">*</span></label>
            <input type="text" class="form-input" v-model="form.customCategory" placeholder="请输入自定义分类名称">
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">商品简介</label>
          <textarea class="form-textarea" v-model="form.description" placeholder="请输入商品简介，用于列表展示" rows="3"></textarea>
        </div>

        <!--提交按钮-->
        <div class="submit-area">
          <button class="submit-btn" @click="handleSubmit" :disabled="loading">
            {{ loading ? '提交中...' : (editingGoodsId ? '保存修改' : '发布商品') }}
          </button>
        </div>

        <!--提示信息-->
        <div v-if="message" class="message" :class="{'error': isError}">
          {{ message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import request from '@/api/request';

const router = useRouter();
const route = useRoute();

//响应式数据定义
const loading = ref(false);
const message = ref('');
const isError = ref(false);
const editingGoodsId = ref(null);
const merchantApplyStatus = ref('none');

const imageList = ref([]);

const form = ref({
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

//分类切换处理
const handleCategoryChange = () => {
  if (form.value.category !== '其他') {
    form.value.customCategory = '';
  }
};

//从Token解析角色
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

//获取商家入驻状态
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

//生命周期钩子
onMounted(() => {
  const goodsId = route.query.id;
  if (goodsId) {
    editingGoodsId.value = goodsId;
    getGoodsDetail(goodsId);
  }
  getMerchantApplyStatus();
});

//API请求方法：获取商品详情用于编辑
const getGoodsDetail = async (id) => {
  try {
    const res = await request.get(`/api/goods/detail/${id}`);
    if (res.data.code === 200) {
      const data = res.data.data;
      const presetCategories = ['景品', 'Q版手办', '可动手办', '盒蛋', '雕像', '拼装模型', '原创/同人作品', 'GK白模/手办'];
      const isPresetCategory = presetCategories.includes(data.category);
      
      form.value = {
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
      };
      imageList.value = data.images;
    } else {
      showMessage(res.data.msg || '获取商品详情失败', true);
    }
  } catch (error) {
    showMessage('网络错误，获取商品详情失败', true);
  }
};

//图片上传方法
const handleImageUpload = async (e) => {
  const files = e.target.files;
  if (!files || files.length === 0) return;

  const token = sessionStorage.getItem('token');
  if (!token) {
    showMessage('请先登录！', true);
    router.push('/login');
    return;
  }

  loading.value = true;
  let successCount = 0;
  let failCount = 0;

  for (const file of files) {
    if (file.size > 5 * 1024 * 1024) {
      showMessage(`图片 ${file.name} 超过5MB，已跳过`, true);
      failCount++;
      continue;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await request.post('/api/upload/image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.code === 200) {
        imageList.value.push(response.data.url);
        successCount++;
      } else {
        failCount++;
        console.error('单张图片上传失败：', response.data.msg);
      }
    } catch (error) {
      failCount++;
      const errMsg = error.response?.data?.msg || '网络异常，上传失败';
      console.error('文件上传异常：', errMsg);
    }
  }

  e.target.value = '';
  loading.value = false;

  if (successCount > 0 && failCount === 0) {
    showMessage(`成功上传 ${successCount} 张图片`, false);
  } else if (successCount > 0 && failCount > 0) {
    showMessage(`成功${successCount}张，失败${failCount}张`, true);
  } else {
    showMessage('所有图片上传失败', true);
  }
};

//删除图片
const deleteImage = (index) => {
  imageList.value.splice(index, 1);
};

//提示信息方法
const showMessage = (msg, error = true) => {
  message.value = msg;
  isError.value = error;
  setTimeout(() => {
    message.value = '';
  }, 3000);
};

// 表单提交（支持新增和更新）
const handleSubmit = async () => {
  if (!form.value.name.trim()) {
    showMessage('请输入商品名称', true);
    return;
  }
  if (!form.value.price || form.value.price <= 0) {
    showMessage('请输入正确的价格', true);
    return;
  }
  if (!form.value.status) {
    showMessage('请选择商品状态', true);
    return;
  }
  if (!form.value.category) {
    showMessage('请选择商品分类', true);
    return;
  }
  if (form.value.category === '其他' && !form.value.customCategory.trim()) {
    showMessage('请输入自定义分类名称', true);
    return;
  }
  if (imageList.value.length === 0) {
    showMessage('请至少上传一张商品图片', true);
    return;
  }

  const token = sessionStorage.getItem('token');
  if (!token) {
    showMessage('请先登录！', true);
    router.push('/login');
    return;
  }

  //商家入驻状态校验
  if (getRoleFromToken() === 'merchant' && !editingGoodsId.value) {
    if (merchantApplyStatus.value === 'none') {
      showMessage('请先提交入驻申请，等待管理员审核通过后再发布商品', true);
      return;
    } else if (merchantApplyStatus.value === 'pending') {
      showMessage('您的入驻申请正在审核中，请等待管理员审核通过', true);
      return;
    } else if (merchantApplyStatus.value === 'rejected') {
      showMessage('您的入驻申请已被拒绝，无法发布商品，如有疑问请联系管理员', true);
      return;
    }
  }

  loading.value = true;
  message.value = '';

  try {
    let url = '/api/goods/publish';
    const actualCategory = form.value.category === '其他' ? form.value.customCategory.trim() : form.value.category;
    const data = { 
      ...form.value, 
      category: actualCategory,
      images: imageList.value 
    };
    delete data.customCategory;

    if (editingGoodsId.value) {
      url = `/api/goods/update/${editingGoodsId.value}`;
    }

    const response = await request.post(url, data);

    if (response.data.code === 200) {
      showMessage(editingGoodsId.value ? '商品更新成功！' : '商品上架成功！', false);
      form.value = {
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
      };
      imageList.value = [];
      editingGoodsId.value = null;
      setTimeout(() => {
        router.push('/profile');
      }, 1500);
    } else {
      showMessage(response.data.msg || '操作失败', true);
    }
  } catch (error) {
    console.error('操作失败:', error);
    showMessage('网络错误，请稍后重试', true);
  } finally {
    loading.value = false;
  }
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

.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: flex;
  gap: 20px;
}

.form-row .half {
  flex: 1;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #0a0a0a;
  margin-bottom: 8px;
  letter-spacing: 0.3px;
}

.required {
  color: #ff6b9d;
}

/* ===== 表单输入框 ===== */
.form-input,
.form-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  font-size: 14px;
  color: #0a0a0a;
  outline: none;
  transition: border-color 0.2s ease;
  background: #fff;
}

.form-input:hover,
.form-textarea:hover {
  border-color: #ccc;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #ff6b9d;
}

select.form-input {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8' fill='none'%3E%3Cpath d='M1 1L6 6L11 1' stroke='%23666' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  background-size: 12px 8px;
  padding-right: 40px;
  cursor: pointer;
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
  min-height: 100px;
}

/* ===== 图片上传区域 ===== */
.image-upload-area {
  width: 100%;
}

.image-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.image-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e5e5;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(255, 107, 157, 0.9);
  color: white;
  border: none;
  font-size: 14px;
  line-height: 20px;
  text-align: center;
  cursor: pointer;
  transition: background 0.2s ease;
}

.delete-btn:hover {
  background: #ff6b9d;
}

.upload-box {
  width: 100px;
  height: 100px;
  border: 1px dashed #ccc;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s ease;
  background: #fff;
}

.upload-box:hover {
  border-color: #ff6b9d;
}

.upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  cursor: pointer;
  color: #666;
  font-size: 11px;
  transition: color 0.2s ease;
}

.upload-box:hover .upload-label {
  color: #ff6b9d;
}

.upload-label .plus {
  font-size: 24px;
  line-height: 1;
  margin-bottom: 4px;
  font-weight: 300;
}

.tips {
  font-size: 12px;
  color: #999;
  margin-top: 10px;
}

/* ===== 提交按钮 ===== */
.submit-area {
  margin-top: 32px;
  text-align: center;
}

.submit-btn {
  width: 100%;
  max-width: 200px;
  height: 44px;
  background: linear-gradient(135deg, #ff6b9d 0%, #ff8a80 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(255, 107, 157, 0.4);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== 提示信息 ===== */
.message {
  text-align: center;
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 20px;
  font-size: 13px;
  font-weight: 500;
}

.message.error {
  color: #ff6b9d;
  background: #fff5f8;
  border: 1px solid #ffe0eb;
}

.message:not(.error) {
  color: #52c41a;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
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

  .submit-btn {
    max-width: 100%;
  }

  .form-group {
    margin-bottom: 16px;
  }

  .image-preview-list {
    gap: 8px;
  }

  .image-item, .upload-box {
    width: 80px;
    height: 80px;
  }

  .page-title {
    font-size: 20px;
    margin-bottom: 24px;
  }
}
</style>

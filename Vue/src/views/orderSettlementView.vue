<template>
  <div class="settlement-page">
    <div class="container">
      <h2 class="page-title">确认订单</h2>

      <div v-if="loading" class="loading-wrap">
        <p>正在加载订单信息...</p>
      </div>

      <div v-else>
        <!--收货地址-->
        <div class="section address-section">
          <h3 class="section-title">收货地址</h3>
          <div class="address-card" v-if="hasAddress">
            <div class="address-info">
              <span class="name">{{ addressData.name }}</span>
              <span class="phone">{{ addressData.phone }}</span>
              <p class="detail">{{ addressData.fullAddress }}</p>
            </div>
            <button class="edit-address-btn" @click="openAddressEditor">编辑地址</button>
          </div>
          <div v-else class="empty-address">
            <p>您还没有添加收货地址</p>
            <button class="add-address-btn" @click="openAddressEditor">+ 添加新地址</button>
          </div>
        </div>

        <!--商品信息-->
        <div class="section goods-section">
          <h3 class="section-title">商品信息</h3>
          <div class="goods-list">
            <div class="goods-item" v-for="item in orderGoods" :key="item.id">
              <img :src="item.image" alt="" class="goods-img" @error="handleImgError"/>
              <div class="goods-info">
                <h4 class="goods-name">{{ item.name }}</h4>
                <p class="goods-price">¥{{ item.price }}</p>
              </div>
              <div class="goods-num">x{{ item.num }}</div>
              <div class="goods-total">¥{{ (item.price * item.num).toFixed(2) }}</div>
            </div>
          </div>
        </div>

        <!--价格计算-->
        <div class="section price-section">
          <div class="price-row"><span>商品总价</span><span>¥{{ totalPrice }}</span></div>
          <div class="price-row"><span>运费</span><span>¥{{ shippingFee.toFixed(2) }}</span></div>
          <div class="price-row total-row">
            <span>实付金额</span><span class="total-amount">¥{{ finalPrice }}</span>
          </div>
        </div>

        <!--提交订单区-->
        <div class="submit-section">
          <button class="submit-btn" @click="submitOrder" :disabled="isSubmitting || !hasAddress || orderGoods.length === 0">
            {{ isSubmitting ? '正在创建订单...' : '确认支付' }}
          </button>
        </div>
      </div>
    </div>

    <!--地址编辑弹窗-->
    <div v-if="showAddressModal" class="modal-mask" @click.self="closeAddressModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ hasAddress ? '编辑收货地址' : '添加收货地址' }}</h3>
          <span class="close-btn" @click="closeAddressModal">×</span>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>收货人</label>
            <input type="text" v-model="addressForm.name" placeholder="请输入收货人姓名"/>
          </div>
          <div class="form-group">
            <label>手机号码</label>
            <input type="text" v-model="addressForm.phone" placeholder="请输入手机号码" maxlength="11"/>
          </div>
          <div class="form-group">
            <label>所在地区</label>
            <div class="area-selects">
              <select v-model="selectedProvince" @change="onProvinceChange">
                <option value="">请选择省</option>
                <option v-for="p in provinces" :key="p.value" :value="p.value">{{ p.label }}</option>
              </select>
              <select v-model="selectedCity" @change="onCityChange" :disabled="!selectedProvince">
                <option value="">请选择市</option>
                <option v-for="c in cities" :key="c.value" :value="c.value">{{ c.label }}</option>
              </select>
              <select v-model="selectedDistrict" :disabled="!selectedCity">
                <option value="">请选择区</option>
                <option v-for="d in districts" :key="d.value" :value="d.value">{{ d.label }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>详细地址</label>
            <textarea v-model="addressForm.detail" placeholder="请输入详细地址" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeAddressModal">取消</button>
          <button class="confirm-btn" @click="saveAddress">保存</button>
        </div>
      </div>
    </div>

    <!--支付弹窗-->
    <div v-if="showPayModal" class="modal-mask" @click.self="closePayModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>扫码支付</h3>
          <span class="close-btn" @click="closePayModal">×</span>
        </div>
        <div class="modal-body">
          <p class="pay-tip">请使用手机扫描下方二维码完成支付</p>
          <p class="pay-amount">支付金额：<span>¥{{ finalPrice }}</span></p>
          <p class="order-no">订单号：{{ currentOrderNo }}</p>
          <div class="qrcode"><canvas id="qrcodeImg" style="width: 200px; height: 200px;"></canvas></div>
          <p class="scan-tip">扫码后在手机上点击确认支付</p>
          <p class="tip">订单将在1分钟后自动取消，请尽快完成支付</p>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closePayModal">取消</button>
          <button class="confirm-btn" @click="simulatePay" :disabled="isPaying">
            {{ isPaying ? '正在处理支付...' : '模拟支付成功' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, nextTick, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import request from '@/api/request';
import { regionData } from "element-china-area-data";
import QRCode from 'qrcode'
import DEFAULT_PLACEHOLDER from '@/assets/images/picture.png'
import { showAlert } from '@/utils/modal'

const router = useRouter();
const route = useRoute();

//响应式数据定义
const loading = ref(false);
const isSubmitting = ref(false);
const isPaying = ref(false);


const isBuyNow = ref(false);
const buyNowGoods = ref(null);

//地址数据
const addressData = reactive({ name: "", phone: "", fullAddress: "" });
const showAddressModal = ref(false);
const addressForm = reactive({ name: "", phone: "", province: "", city: "", district: "", detail: "" });
const selectedProvince = ref("");
const selectedCity = ref("");
const selectedDistrict = ref("");

//支付相关
const showPayModal = ref(false)
const currentOrderNo = ref('')

//省市区级联数据
const provinces = computed(() => regionData.map(item => ({ value: item.value, label: item.label })));
const cities = computed(() => {
  if (!selectedProvince.value) return [];
  const p = regionData.find(i => i.value === selectedProvince.value);
  return p?.children?.map(i => ({ value: i.value, label: i.label })) || [];
});
const districts = computed(() => {
  if (!selectedCity.value) return [];
  const p = regionData.find(i => i.value === selectedProvince.value);
  const c = p?.children?.find(i => i.value === selectedCity.value);
  return c?.children?.map(i => ({ value: i.value, label: i.label })) || [];
});

//商品与价格数据
const orderGoods = ref([]);
const shippingFee = ref(0);

const totalPrice = computed(() => orderGoods.value.reduce((s, i) => s + i.price * i.num, 0).toFixed(2));
const finalPrice = computed(() => (parseFloat(totalPrice.value) + shippingFee.value).toFixed(2));
const hasAddress = computed(() => !!(addressData.fullAddress && addressData.name && addressData.phone));

//加载商品API请求方法
const getSettlementGoods = async () => {
  loading.value = true;
  try {
    if (route.query.goods) {
      isBuyNow.value = true;
      buyNowGoods.value = JSON.parse(route.query.goods);
      orderGoods.value = [buyNowGoods.value];
      return;
    }
    const res = await request.get("/api/cart/list");
    if (res.data.code === 200) orderGoods.value = res.data.data;
  } catch (err) {
    console.error("加载失败:", err);
  } finally {
    loading.value = false;
  }
};

//提交订单
const submitOrder = async () => {
  if (!hasAddress.value) {
    await showAlert('请先添加收货地址')
    return
  }
  if (orderGoods.value.length === 0) {
    await showAlert('请选择商品')
    return
  }

  isSubmitting.value = true;
  try {
    const addr = {
      name: addressData.name,
      phone: addressData.phone,
      address: JSON.stringify(addressData)
    };

    let res;
    if (isBuyNow.value) {
      res = await request.post("/api/order/create-direct", {
        ...addr,
        goods_id: buyNowGoods.value.id,
        num: buyNowGoods.value.num
      });
    } else {
      res = await request.post("/api/order/create", addr);
    }

    if (res.data.code === 200) {
      currentOrderNo.value = res.data.order_no;
      showPayModal.value = true;
      nextTick(generateQrcode);
    } else {
      handleOrderCreateError(res.data.code, res.data.msg);
    }
  } catch (err) {
    handleOrderCreateNetworkError(err);
  } finally {
    isSubmitting.value = false;
  }
};

//地址相关逻辑
const onProvinceChange = () => { 
  selectedCity.value = ""; 
  selectedDistrict.value = ""; 
  addressForm.province = provinces.value.find(i=>i.value===selectedProvince.value)?.label||"";
};

const onCityChange = () => { 
  selectedDistrict.value = ""; 
  addressForm.city = cities.value.find(i=>i.value===selectedCity.value)?.label||"";
};

watch(selectedDistrict, (newVal) => {
  if (newVal) {
    addressForm.district = districts.value.find(i=>i.value===newVal)?.label||"";
  }
});

//获取用户信息
const getUserInfo = async () => {
  try {
    const res = await request.get("/api/user/info");
    if (res.data.code === 200) {
      const info = res.data.data;
      if(info.address_struct) {
        Object.assign(addressData, info.address_struct);
        if (info.address_struct.province) {
          const province = regionData.find(p => p.label === info.address_struct.province);
          if (province) {
            selectedProvince.value = province.value;
            addressForm.province = province.label;
            
            if (info.address_struct.city) {
              const city = province.children.find(c => c.label === info.address_struct.city);
              if (city) {
                selectedCity.value = city.value;
                addressForm.city = city.label;
                
                if (info.address_struct.district) {
                  const district = city.children.find(d => d.label === info.address_struct.district);
                  if (district) {
                    selectedDistrict.value = district.value;
                    addressForm.district = district.label;
                  }
                }
              }
            }
          }
        }
        addressForm.name = addressData.name;
        addressForm.phone = addressData.phone;
        addressForm.detail = info.address_struct.detail || "";
      }
      updateFullAddress();
    }
  } catch (e) {
    console.error("获取用户信息失败:", e);
  }
};

const updateFullAddress = () => {
  addressData.fullAddress = `${addressData.province||''}${addressData.city||''}${addressData.district||''}${addressData.detail||''}`;
};

//地址编辑弹窗操作
const openAddressEditor = () => {
  addressForm.name = addressData.name;
  addressForm.phone = addressData.phone;
  addressForm.detail = addressData.detail || "";
  showAddressModal.value = true;
};

//保存地址
const saveAddress = async () => {
  if (!addressForm.name.trim()) {
    await showAlert('请输入收货人姓名');
    return;
  }
  if (!addressForm.phone.trim() || !/^1[3-9]\d{9}$/.test(addressForm.phone)) {
    await showAlert('请输入正确的手机号码');
    return;
  }
  if (!selectedProvince.value || !selectedCity.value || !selectedDistrict.value) {
    await showAlert('请选择完整的省市区');
    return;
  }
  if (!addressForm.detail.trim()) {
    await showAlert('请输入详细地址');
    return;
  }

  try {
    const addressStruct = {
      name: addressForm.name,
      phone: addressForm.phone,
      province: addressForm.province,
      city: addressForm.city,
      district: addressForm.district,
      detail: addressForm.detail
    };

    const res = await request.post("/api/user/update", {
      name: addressForm.name,
      phone: addressForm.phone,
      address_struct: addressStruct
    });

    if (res.data.code === 200) {
      Object.assign(addressData, addressStruct);
      updateFullAddress();
      closeAddressModal();
      await showAlert('地址保存成功');
    } else {
      await showAlert(res.data.msg || '保存失败，请重试');
    }
  } catch (err) {
    console.error("保存地址失败:", err);
    await showAlert('网络错误，保存失败');
  }
};

const closeAddressModal = () => { 
  showAddressModal.value = false; 
};

//支付相关逻辑
const closePayModal = () => { 
  showPayModal.value = false; 
  router.push('/profile');
};

const generateQrcode = async () => {
  try {
    const qrcodeUrl = `/api/order/public/${currentOrderNo.value}`;
    await QRCode.toCanvas(document.getElementById('qrcodeImg'), qrcodeUrl, {
      width: 200,
      height: 200,
      margin: 1
    });
  } catch (err) {
    console.error("生成二维码失败:", err);
  }
};

const simulatePay = async () => {
  isPaying.value = true;
  try {
    const res = await request.post(`/api/order/confirm/${currentOrderNo.value}`);
    if (res.data.code === 200) {
      closePayModal();
      await showAlert('支付成功！');
    } else {
      await showAlert(res.data.msg || '支付失败，请重试');
    }
  } catch (err) {
    console.error("模拟支付失败:", err);
    await showAlert('网络错误，支付失败');
  } finally {
    isPaying.value = false;
  }
};

//工具函数
const handleImgError = (e) => { 
  e.target.src = DEFAULT_PLACEHOLDER; 
};

const handleOrderCreateError = (code, msg) => {
  showAlert(msg || '创建订单失败，请重试');
};

const handleOrderCreateNetworkError = (err) => {
  console.error("创建订单网络错误:", err);
  showAlert('网络错误，请检查网络连接');
};

const handlePayError = (code, msg) => {
  showAlert(msg || '支付失败，请重试');
};

const handlePayNetworkError = (err) => {
  console.error("支付网络错误:", err);
  showAlert('网络错误，请检查网络连接');
};

//生命周期钩子
onMounted(() => {
  getSettlementGoods();
  getUserInfo();
});
</script>

<style scoped>
/* ===== 页面布局 ===== */
.settlement-page {
  min-height: 100vh;
  padding: 80px 20px 40px;
  box-sizing: border-box;
  background: rgb(234, 243, 251);
}

.container {
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  text-align: center;
  color: #212121;
  margin: 0 0 30px;
}

.loading-wrap {
  background: #fff;
  border-radius: 12px;
  padding: 100px 0;
  text-align: center;
  color: #999;
  font-size: 16px;
}

/* ===== 内容区块 ===== */
.section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

/* ===== 收货地址 ===== */
.address-card {
  display: flex;
  align-items: center;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
}

.address-info {
  flex: 1;
}

.name {
  font-weight: 600;
  color: #333;
  margin-right: 15px;
}

.phone {
  color: #666;
}

.detail {
  margin: 5px 0 0;
  color: #666;
  font-size: 14px;
}

.edit-address-btn {
  background: none;
  border: 1px solid #fb7299;
  color: #fb7299;
  padding: 6px 15px;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.3s;
}

.edit-address-btn:hover {
  background: #fff0f5;
}

.empty-address {
  text-align: center;
  padding: 30px 0;
  color: #999;
}

.add-address-btn {
  width: 100%;
  height: 44px;
  border: 1px dashed #fb7299;
  background: #fff0f5;
  color: #fb7299;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  margin-top: 10px;
  transition: all 0.3s ease;
}

.add-address-btn:hover {
  background: #ffe6ed;
}

/* ===== 地区选择器 ===== */
.area-selects {
  display: flex;
  gap: 10px;
}

.area-selects select {
  flex: 1;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
  outline: none;
  transition: border-color 0.3s ease;
  cursor: pointer;
}

.area-selects select:focus {
  border-color: #fb7299;
}

.area-selects select:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

/* ===== 商品列表 ===== */
.goods-item {
  display: flex;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.goods-item:last-child {
  border-bottom: none;
}

.goods-img {
  width: 80px;
  height: 80px;
  object-fit: contain;
  border-radius: 8px;
  background: #f9f9f9;
  margin-right: 15px;
}

.goods-info {
  flex: 1;
}

.goods-name {
  font-size: 16px;
  color: #333;
  margin: 0 0 5px;
}

.goods-price {
  color: #fb7299;
  font-weight: 600;
  margin: 0;
}

.goods-num {
  color: #999;
  margin: 0 20px;
}

.goods-total {
  color: #333;
  font-weight: 600;
}

/* ===== 价格汇总 ===== */
.price-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  color: #666;
}

.total-row {
  border-top: 1px solid #f0f0f0;
  padding-top: 15px;
  margin-top: 5px;
  font-size: 18px;
  color: #333;
}

.total-amount {
  color: #fb7299;
  font-weight: 600;
  font-size: 22px;
}

/* ===== 提交按钮 ===== */
.submit-section {
  text-align: right;
}

.submit-btn {
  background: #fb7299;
  color: #fff;
  border: none;
  padding: 15px 50px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== 弹窗样式 ===== */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 420px;
  max-width: 90%;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-btn {
  font-size: 24px;
  color: #999;
  cursor: pointer;
  line-height: 1;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #666;
  font-size: 14px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.3s ease;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: #fb7299;
}

.modal-footer {
  display: flex;
  border-top: 1px solid #f0f0f0;
}

.modal-footer button {
  flex: 1;
  padding: 15px;
  border: none;
  font-size: 16px;
  cursor: pointer;
}

.cancel-btn {
  background: #f5f5f5;
  color: #666;
}

.confirm-btn {
  background: #fb7299;
  color: #fff;
}

/* ===== 支付弹窗内容 ===== */
.pay-tip {
  font-size: 16px;
  color: #333;
  margin: 0 0 10px;
  text-align: center;
}

.pay-amount {
  font-size: 18px;
  color: #666;
  margin: 0 0 10px;
  text-align: center;
}

.pay-amount span {
  color: #fb7299;
  font-weight: 600;
  font-size: 22px;
}

.order-no {
  font-size: 14px;
  color: #999;
  margin: 0 0 20px;
  text-align: center;
}

.qrcode {
  display: block;
  margin: 0 auto 20px;
  border: 1px solid #eee;
  padding: 10px;
  border-radius: 8px;
  width: fit-content;
}

.scan-tip {
  font-size: 14px;
  color: #999;
  margin: 0 0 10px;
  text-align: center;
}

.tip {
  font-size: 12px;
  color: #666;
  margin: 0;
  text-align: center;
}

/* ===== 响应式适配 ===== */
@media (max-width: 768px) {
  .settlement-page { padding: 70px 12px 24px; }
  .page-title { font-size: 20px; margin-bottom: 20px; }
  .section { padding: 16px; margin-bottom: 12px; }
  .section-title { font-size: 16px; margin-bottom: 12px; }
  .address-card { flex-direction: column; align-items: flex-start; padding: 12px; }
  .edit-address-btn { margin-top: 10px; align-self: flex-end; }
  .goods-item { flex-wrap: wrap; }
  .goods-img { width: 60px; height: 60px; margin-right: 10px; }
  .goods-name { font-size: 14px; }
  .goods-num { margin: 0 10px; }
  .submit-section { text-align: center; }
  .submit-btn { width: 100%; padding: 14px 0; }
  .area-selects { flex-direction: column; gap: 8px; }
  .modal-content { width: 95%; }
  .modal-body { padding: 16px; }
}
</style>

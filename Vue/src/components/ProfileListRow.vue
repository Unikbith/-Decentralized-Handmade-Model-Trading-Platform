<template>
  <div class="profile-list-row" @click="$emit('click')">
    <div class="goods-img">
      <img :src="image" alt="商品图片" @error="handleImgError">
    </div>
    <div class="goods-info">
      <h3 class="goods-name">{{ name }}</h3>
      <p class="goods-price">¥{{ price }}</p>
      <p class="goods-meta" v-if="meta">{{ meta }}</p>
    </div>
    <div class="btn-container">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  image: { type: String, default: '' },
  name: { type: String, default: '' },
  price: { type: [String, Number], default: '0.00' },
  meta: { type: String, default: '' }
})

defineEmits(['click'])

const handleImgError = (e) => {
  e.target.src = '/assets/picture-DPjQRauj.png'
}
</script>

<style scoped>
.profile-list-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s;
  min-width: 0;
}

.profile-list-row:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.goods-img {
  width: 100px;
  height: 100px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
}

.goods-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.goods-info {
  flex: 1;
  min-width: 0;
}

.goods-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin: 0 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.goods-price {
  font-size: 18px;
  font-weight: 600;
  color: #ff6b9d;
  margin: 0 0 8px;
}

.goods-meta {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.btn-container {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .profile-list-row {
    flex-wrap: wrap;
  }
  .goods-img {
    width: 60px;
    height: 60px;
  }
  .btn-container {
    margin-left: auto;
  }
}
</style>
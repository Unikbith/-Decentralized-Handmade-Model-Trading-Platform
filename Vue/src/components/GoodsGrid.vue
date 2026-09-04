<template>
  <div class="goods-grid">
    <slot />
  </div>
</template>

<style scoped>
.goods-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

@media (max-width: 1200px) {
  .goods-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .goods-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
}

@media (max-width: 480px) {
  .goods-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}
</style>
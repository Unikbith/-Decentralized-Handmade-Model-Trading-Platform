<template>
  <GoodsFilterPage mode="status" :status-tabs="statusTabs" header-type="line" show-pagination />
</template>

<script setup>
import GoodsFilterPage from '@/components/GoodsFilterPage.vue'

const statusTabs = [
  { label: '预购', value: 'preorder' },
  { label: '现货', value: 'stock' }
]
</script>
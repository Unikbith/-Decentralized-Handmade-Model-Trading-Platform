<template>
  <div class="stat-card" :class="colorClass">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value" :class="{ 'error-text': danger }">{{ value }}<span v-if="unit" class="stat-unit">{{ unit }}</span></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  value: { type: [String, Number], default: '' },
  unit: { type: String, default: '' },
  color: { type: String, default: 'blue' },
  danger: { type: Boolean, default: false }
})

const colorClass = computed(() => `card-${props.color}`)
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 18px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-left: 4px solid #ddd;
}

.card-blue { border-left-color: #80acee; }
.card-green { border-left-color: #52c41a; }
.card-red { border-left-color: #ff4d4f; }
.card-purple { border-left-color: #9b59b6; }
.card-orange { border-left-color: #e67e22; }
.card-cyan { border-left-color: #1abc9c; }

.stat-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
}

.stat-unit {
  font-size: 13px;
  font-weight: 400;
  color: #999;
  margin-left: 2px;
}

.error-text {
  color: #ff4d4f;
}

@media (max-width: 768px) {
  .stat-card { padding: 12px; }
  .stat-value { font-size: 18px; }
}

@media (max-width: 480px) {
  .stat-value { font-size: 16px; }
}
</style>
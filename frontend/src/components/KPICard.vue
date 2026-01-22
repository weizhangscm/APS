<template>
  <div class="kpi-card" :class="colorClass">
    <div class="kpi-header">
      <div class="kpi-icon">
        <el-icon :size="24">
          <component :is="icon" />
        </el-icon>
      </div>
    </div>
    <div class="kpi-body">
      <div class="kpi-title">{{ title }}</div>
      <div class="kpi-value" :class="valueColorClass">
        {{ formattedValue }}<span class="kpi-unit">{{ unit }}</span>
      </div>
      <div class="kpi-trend" v-if="trend !== null">
        <el-icon v-if="trend > 0" class="trend-up"><Top /></el-icon>
        <el-icon v-else-if="trend < 0" class="trend-down"><Bottom /></el-icon>
        <span :class="trend >= 0 ? 'trend-up' : 'trend-down'">
          {{ trend > 0 ? '+' : '' }}{{ trend }}%
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    required: true
  },
  unit: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: 'DataAnalysis'
  },
  color: {
    type: String,
    default: 'primary'
  },
  trend: {
    type: Number,
    default: null
  },
  decimals: {
    type: Number,
    default: 0
  }
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toFixed(props.decimals)
  }
  return props.value
})

const colorClass = computed(() => `kpi-${props.color}`)
const valueColorClass = computed(() => props.color)
</script>

<style lang="scss" scoped>
// Material 3 Color Tokens
$m3-primary: #1a73e8;
$m3-primary-container: #d3e3fd;
$m3-on-primary-container: #041e49;
$m3-tertiary: #1e8e3e;
$m3-error: #d93025;
$m3-warning: #f9ab00;
$m3-surface: #ffffff;
$m3-on-surface: #1f1f1f;
$m3-on-surface-variant: #444746;

$m3-shape-lg: 16px;
$m3-shape-xl: 28px;
$m3-elevation-1: 0 1px 2px rgba(0, 0, 0, 0.3), 0 1px 3px 1px rgba(0, 0, 0, 0.15);
$m3-elevation-2: 0 1px 2px rgba(0, 0, 0, 0.3), 0 2px 6px 2px rgba(0, 0, 0, 0.15);

.kpi-card {
  background: $m3-surface;
  border-radius: $m3-shape-lg;
  padding: 24px;
  box-shadow: $m3-elevation-1;
  transition: box-shadow 0.2s ease, transform 0.15s ease;
  
  &:hover {
    box-shadow: $m3-elevation-2;
    transform: translateY(-2px);
  }
  
  &.kpi-primary .kpi-icon {
    background: $m3-primary-container;
    color: $m3-on-primary-container;
  }
  
  &.kpi-success .kpi-icon {
    background: rgba($m3-tertiary, 0.12);
    color: $m3-tertiary;
  }
  
  &.kpi-warning .kpi-icon {
    background: rgba($m3-warning, 0.15);
    color: darken($m3-warning, 15%);
  }
  
  &.kpi-danger .kpi-icon {
    background: rgba($m3-error, 0.12);
    color: $m3-error;
  }
}

.kpi-header {
  margin-bottom: 16px;
}

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: $m3-shape-lg;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-title {
  font-size: 14px;
  color: $m3-on-surface-variant;
  font-weight: 500;
  margin-bottom: 8px;
  letter-spacing: 0.25px;
}

.kpi-body {
  display: flex;
  flex-direction: column;
}

.kpi-value {
  font-size: 36px;
  font-weight: 400;
  color: $m3-on-surface;
  line-height: 1.2;
  
  &.primary { color: $m3-primary; }
  &.success { color: $m3-tertiary; }
  &.warning { color: darken($m3-warning, 10%); }
  &.danger { color: $m3-error; }
}

.kpi-unit {
  font-size: 14px;
  font-weight: 400;
  color: $m3-on-surface-variant;
  margin-left: 4px;
}

.kpi-trend {
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  
  .trend-up {
    color: $m3-tertiary;
  }
  
  .trend-down {
    color: $m3-error;
  }
}
</style>

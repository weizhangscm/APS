<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>
        <el-icon><TrendCharts /></el-icon>
        {{ t('dashboard.title') }}
      </h1>
    </div>

    <!-- 交期区间与刷新按钮同一行 -->
    <el-row :gutter="16" class="toolbar-row">
      <el-col :span="6">
        <div class="date-range-bar">
          <span class="date-range-label">{{ t('dashboard.dateRange') }}</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            :range-separator="t('common.to')"
            :start-placeholder="t('common.startDate')"
            :end-placeholder="t('common.endDate')"
            value-format="YYYY-MM-DD"
            :shortcuts="dateShortcuts"
            class="date-range-picker"
            @change="onDateRangeChange"
          />
        </div>
      </el-col>
      <el-col :span="18" class="toolbar-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          {{ t('dashboard.refreshView') }}
        </el-button>
      </el-col>
    </el-row>

    <!-- KPI Cards -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :span="6">
        <KPICard 
          :title="t('dashboard.totalOrders')"
          :value="kpiData?.order_kpi?.total_orders || 0"
          :unit="t('dashboard.unitPcs')"
          icon="Document"
          color="primary"
        />
      </el-col>
      <el-col :span="6">
        <KPICard 
          :title="t('dashboard.scheduledOrders')"
          :value="kpiData?.order_kpi?.scheduled_orders || 0"
          :unit="t('dashboard.unitPcs')"
          icon="Finished"
          color="success"
        />
      </el-col>
      <el-col :span="6">
        <KPICard 
          :title="t('dashboard.onTimeRate')"
          :value="kpiData?.order_kpi?.on_time_rate || 0"
          unit="%"
          icon="Timer"
          :color="getOnTimeRateColor(kpiData?.order_kpi?.on_time_rate)"
          :decimals="1"
        />
      </el-col>
      <el-col :span="6">
        <KPICard 
          :title="t('dashboard.averageLeadTime')"
          :value="kpiData?.avg_lead_time_hours || 0"
          :unit="t('dashboard.unitHours')"
          icon="Clock"
          color="primary"
          :decimals="1"
        />
      </el-col>
    </el-row>
    
    <!-- Charts Row -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.resourceUtilization') }}</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart :option="utilizationChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.dailyCapacityLoad') }}</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart :option="capacityChartOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Resource Table -->
    <el-card style="margin-top: 16px;">
      <template #header>
        <div class="card-header">
          <span>{{ t('dashboard.resourceUtilizationDetails') }}</span>
        </div>
      </template>
      <el-table :data="kpiData?.resource_utilization || []" stripe>
        <el-table-column prop="resource_name" :label="t('dashboard.resourceName')" />
        <el-table-column prop="work_center_name" :label="t('dashboard.workCenter')" />
        <el-table-column prop="total_capacity_hours" :label="t('dashboard.totalCapacity')" width="120">
          <template #default="{ row }">
            {{ row.total_capacity_hours.toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column prop="scheduled_hours" :label="t('dashboard.scheduled')" width="120">
          <template #default="{ row }">
            {{ row.scheduled_hours.toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column prop="utilization_percent" :label="t('dashboard.utilization')" width="220">
          <template #default="{ row }">
            <div class="utilization-cell">
              <el-progress 
                :percentage="Math.min(row.utilization_percent, 100)"
                :color="getUtilizationColor(row.utilization_percent)"
                :stroke-width="8"
              />
              <span class="utilization-text">{{ row.utilization_percent.toFixed(1) }}%</span>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18nStore } from '@/stores/i18n'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { 
  TitleComponent, 
  TooltipComponent, 
  GridComponent,
  LegendComponent 
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useSchedulingStore } from '@/stores/scheduling'
import KPICard from '@/components/KPICard.vue'

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
])

// Material 3 Colors
const m3Primary = '#1a73e8'
const m3Tertiary = '#1e8e3e'
const m3Warning = '#f9ab00'
const m3Error = '#d93025'
const m3OnSurface = '#1f1f1f'
const m3OnSurfaceVariant = '#444746'
const m3OutlineVariant = '#c4c7c5'
const m3SurfaceContainerHigh = '#e3e5e8'

const schedulingStore = useSchedulingStore()

const loading = ref(false)
const kpiData = computed(() => schedulingStore.kpiData)

// 交期区间：默认为下周一到周日
function getDefaultDateRange() {
  const today = new Date()
  const day = today.getDay() // 0 周日, 1 周一, ..., 6 周六
  const daysUntilNextMonday = day === 0 ? 1 : (8 - day)
  const nextMonday = new Date(today)
  nextMonday.setDate(today.getDate() + daysUntilNextMonday)
  const nextSunday = new Date(nextMonday)
  nextSunday.setDate(nextMonday.getDate() + 6)
  const fmt = (d) => d.toISOString().slice(0, 10)
  return [fmt(nextMonday), fmt(nextSunday)]
}
const dateRange = ref(getDefaultDateRange())

const dateShortcuts = computed(() => [
  { text: t('dashboard.shortcuts.thisWeek'), value: () => {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - start.getDay() + 1)
    return [start, end]
  }},
  { text: t('dashboard.shortcuts.thisMonth'), value: () => {
    const end = new Date()
    const start = new Date(end.getFullYear(), end.getMonth(), 1)
    return [start, end]
  }},
  { text: t('dashboard.shortcuts.next7Days'), value: () => {
    const start = new Date()
    const end = new Date()
    end.setDate(end.getDate() + 7)
    return [start, end]
  }},
  { text: t('dashboard.shortcuts.next30Days'), value: () => {
    const start = new Date()
    const end = new Date()
    end.setDate(end.getDate() + 30)
    return [start, end]
  }}
])

function onDateRangeChange() {
  refreshData()
}

const refreshData = async () => {
  loading.value = true
  try {
    const [start, end] = dateRange.value || []
    await schedulingStore.fetchKPIData({
      ...(start && { dueDateStart: start }),
      ...(end && { dueDateEnd: end })
    })
  } finally {
    loading.value = false
  }
}

const getOnTimeRateColor = (rate) => {
  if (rate >= 90) return 'success'
  if (rate >= 70) return 'warning'
  return 'danger'
}

const getUtilizationColor = (percent) => {
  if (percent >= 90) return m3Error
  if (percent >= 70) return m3Warning
  return m3Tertiary
}

// Resource Utilization Chart - M3 style
const utilizationChartOption = computed(() => {
  const data = kpiData.value?.resource_utilization || []
  
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: m3OnSurface,
      borderColor: 'transparent',
      textStyle: { color: '#fff', fontSize: 14 },
      borderRadius: 8,
      padding: [12, 16]
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.resource_name),
      axisLabel: {
        color: m3OnSurfaceVariant,
        fontSize: 12,
        interval: 0,
        rotate: 30
      },
      axisLine: { lineStyle: { color: m3OutlineVariant } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { 
        color: m3OnSurfaceVariant,
        formatter: '{value}%',
        fontSize: 12
      },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: m3SurfaceContainerHigh, type: 'dashed' } }
    },
    series: [{
      name: t('dashboard.utilization').replace('(%)', '').trim(),
      type: 'bar',
      data: data.map(d => ({
        value: d.utilization_percent,
        itemStyle: {
          color: getUtilizationColor(d.utilization_percent),
          borderRadius: [8, 8, 0, 0]
        }
      })),
      barWidth: '40%'
    }]
  }
})

// Capacity Load Chart - M3 style
const capacityChartOption = computed(() => {
  const data = kpiData.value?.capacity_load_by_day || {}
  const dates = Object.keys(data).sort()
  
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: m3OnSurface,
      borderColor: 'transparent',
      textStyle: { color: '#fff', fontSize: 14 },
      borderRadius: 8,
      padding: [12, 16]
    },
    legend: {
      data: [t('dashboard.usedCapacity'), t('dashboard.totalCapacityLegend')],
      textStyle: { color: m3OnSurfaceVariant, fontSize: 12 },
      icon: 'roundRect',
      itemWidth: 16,
      itemHeight: 8,
      itemGap: 24
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '48px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates.map(d => d.slice(5)),
      axisLabel: { color: m3OnSurfaceVariant, fontSize: 12 },
      axisLine: { lineStyle: { color: m3OutlineVariant } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLabel: { 
        color: m3OnSurfaceVariant,
        formatter: '{value}h',
        fontSize: 12
      },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: m3SurfaceContainerHigh, type: 'dashed' } }
    },
    series: [
      {
        name: t('dashboard.usedCapacity'),
        type: 'bar',
        data: dates.map(d => data[d]?.used_capacity || 0),
        itemStyle: { 
          color: m3Primary,
          borderRadius: [8, 8, 0, 0]
        },
        barWidth: '35%'
      },
      {
        name: t('dashboard.totalCapacityLegend'),
        type: 'line',
        data: dates.map(d => data[d]?.total_capacity || 0),
        itemStyle: { color: m3OnSurfaceVariant },
        lineStyle: { type: 'dashed', width: 2 },
        symbol: 'circle',
        symbolSize: 8
      }
    ]
  }
})

onMounted(() => {
  refreshData()
})
</script>

<style lang="scss" scoped>
$m3-on-surface: #1f1f1f;
$m3-on-surface-variant: #444746;

.dashboard {
  min-height: calc(100vh - 100px);
}

.toolbar-row {
  margin-bottom: 16px;
  align-items: center;

  .toolbar-actions {
    display: flex;
    justify-content: flex-end;
    align-items: center;
  }
}

.date-range-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;

  .date-range-label {
    font-size: 14px;
    color: $m3-on-surface-variant;
    white-space: nowrap;
  }

  .date-range-picker {
    flex: 1;
    min-width: 0;
  }
}

.kpi-row {
  margin-bottom: 16px;
}

.card-header {
  font-size: 16px;
  font-weight: 500;
  color: $m3-on-surface;
}

.chart-container {
  height: 300px;
}

.utilization-cell {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .el-progress {
    flex: 1;
  }
  
  .utilization-text {
    min-width: 55px;
    text-align: right;
    color: $m3-on-surface-variant;
    font-weight: 500;
  }
}
</style>

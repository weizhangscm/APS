<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>
        <el-icon><TrendCharts /></el-icon>
        KPI仪表板
      </h1>
      <el-button @click="refreshData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>
    
    <!-- KPI Cards -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :span="6">
        <KPICard 
          title="总订单数"
          :value="kpiData?.order_kpi?.total_orders || 0"
          unit="个"
          icon="Document"
          color="primary"
        />
      </el-col>
      <el-col :span="6">
        <KPICard 
          title="已排程订单"
          :value="kpiData?.order_kpi?.scheduled_orders || 0"
          unit="个"
          icon="Finished"
          color="success"
        />
      </el-col>
      <el-col :span="6">
        <KPICard 
          title="订单准时率"
          :value="kpiData?.order_kpi?.on_time_rate || 0"
          unit="%"
          icon="Timer"
          :color="getOnTimeRateColor(kpiData?.order_kpi?.on_time_rate)"
          :decimals="1"
        />
      </el-col>
      <el-col :span="6">
        <KPICard 
          title="平均提前期"
          :value="kpiData?.avg_lead_time_hours || 0"
          unit="小时"
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
              <span>资源利用率</span>
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
              <span>每日产能负荷</span>
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
          <span>资源利用详情</span>
        </div>
      </template>
      <el-table :data="kpiData?.resource_utilization || []" stripe>
        <el-table-column prop="resource_name" label="资源名称" />
        <el-table-column prop="work_center_name" label="工作中心" />
        <el-table-column prop="total_capacity_hours" label="总产能(小时)" width="120">
          <template #default="{ row }">
            {{ row.total_capacity_hours.toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column prop="scheduled_hours" label="已排程(小时)" width="120">
          <template #default="{ row }">
            {{ row.scheduled_hours.toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column prop="utilization_percent" label="利用率" width="220">
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

const refreshData = async () => {
  loading.value = true
  try {
    await schedulingStore.fetchKPIData()
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
      axisLabel: { color: m3OnSurfaceVariant, fontSize: 12 },
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
      name: '利用率',
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
      data: ['已用产能', '总产能'],
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
        name: '已用产能',
        type: 'bar',
        data: dates.map(d => data[d]?.used_capacity || 0),
        itemStyle: { 
          color: m3Primary,
          borderRadius: [8, 8, 0, 0]
        },
        barWidth: '35%'
      },
      {
        name: '总产能',
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

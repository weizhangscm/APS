<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>
        <el-icon><TrendCharts /></el-icon>
        {{ t('dashboard.title') }}
      </h1>
    </div>

    <!-- 日期区间、位置与刷新按钮同一行 -->
    <el-row :gutter="16" class="toolbar-row">
      <el-col :xs="24" :md="18">
        <div class="filters-inline">
          <div class="date-range-bar">
            <span class="date-range-label">
              {{ t('dashboard.dateRange') }}<span class="required-mark">*</span>
            </span>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              :format="datePickerDisplayFormat"
              :range-separator="t('common.to')"
              :start-placeholder="t('common.startDate')"
              :end-placeholder="t('common.endDate')"
              value-format="YYYY-MM-DD"
              :shortcuts="dateShortcuts"
              class="date-range-picker"
              @change="onDateRangeChange"
            />
          </div>
          <div class="location-bar">
            <span class="date-range-label">
              {{ t('dashboard.location') }}<span class="required-mark">*</span>
            </span>
            <el-select
              v-model="kpiLocationCodes"
              multiple
              collapse-tags
              collapse-tags-tooltip
              filterable
              :placeholder="t('dashboard.selectLocations')"
              class="location-select"
              @change="onKpiLocationChange"
            >
              <template #header>
                <div class="select-header-options">
                  <el-checkbox
                    v-model="allKpiLocationsSelected"
                    :indeterminate="kpiLocationsIndeterminate"
                    @change="handleSelectAllKpiLocations"
                  >
                    {{ t('dashboard.selectLocations') }}
                  </el-checkbox>
                </div>
              </template>
              <el-option
                v-for="loc in locationOptions"
                :key="loc.code"
                :label="locationOptionLabel(loc)"
                :value="loc.code"
              />
            </el-select>
          </div>
          <div class="resource-bar">
            <span class="date-range-label">
              {{ t('dashboard.resourceName') }}<span class="required-mark">*</span>
            </span>
            <el-select
              v-model="kpiResourceIds"
              multiple
              collapse-tags
              collapse-tags-tooltip
              filterable
              :clearable="false"
              :placeholder="resourceSelectPlaceholder"
              class="resource-select"
              @change="refreshData"
            >
              <template #header>
                <div class="select-header-options">
                  <el-checkbox
                    v-model="allKpiResourcesSelected"
                    :indeterminate="kpiResourcesIndeterminate"
                    @change="handleSelectAllKpiResources"
                  >
                    {{ t('dashboard.selectResources') }}
                  </el-checkbox>
                </div>
              </template>
              <el-option
                v-for="r in resourcesForKpiSelect"
                :key="r.id"
                :label="r.name"
                :value="r.id"
              />
            </el-select>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="6" class="toolbar-actions">
        <el-button @click="handleRefreshClick" :loading="loading">
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
          :value="scheduledOrders"
          :unit="t('dashboard.unitPcs')"
          icon="Finished"
          color="success"
        />
      </el-col>
      <el-col :span="6">
        <KPICard 
          :title="t('dashboard.onTimeRate')"
          :value="safeOnTimeRate"
          unit="%"
          icon="Timer"
          :color="getOnTimeRateColor(onTimeRateForColor)"
          :decimals="1"
        />
      </el-col>
      <el-col :span="6">
        <KPICard 
          :title="t('dashboard.averageLeadTime')"
          :value="safeAvgLeadTimeHours"
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
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
import { masterDataApi } from '@/api'
import KPICard from '@/components/KPICard.vue'
import { elementDatePickerDisplayFormat } from '@/utils/displayDateTime'

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)
const datePickerDisplayFormat = computed(() => elementDatePickerDisplayFormat())

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

// --- KPI values (avoid misleading values when scheduled=0) ---
const scheduledOrders = computed(() => kpiData.value?.order_kpi?.scheduled_orders ?? 0)

const onTimeRateValue = computed(() => {
  const rate = kpiData.value?.order_kpi?.on_time_rate
  if (scheduledOrders.value <= 0) return null
  return typeof rate === 'number' && Number.isFinite(rate) ? rate : null
})
const safeOnTimeRate = computed(() => onTimeRateValue.value ?? '--')
const onTimeRateForColor = computed(() =>
  typeof onTimeRateValue.value === 'number' ? onTimeRateValue.value : 0
)

const avgLeadTimeValue = computed(() => {
  const v = kpiData.value?.avg_lead_time_hours
  if (scheduledOrders.value <= 0) return null
  return typeof v === 'number' && Number.isFinite(v) ? v : null
})
const safeAvgLeadTimeHours = computed(() => avgLeadTimeValue.value ?? '--')

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

const locationOptions = ref([])
const kpiLocationCodes = ref([])
const resourceOptions = ref([])
const kpiResourceIds = ref([])

const normLocationCode = (v) => (v != null && String(v).trim() ? String(v).trim() : '')

const kpiLocationCodesNorm = computed(() =>
  [...new Set(kpiLocationCodes.value.map(normLocationCode).filter(Boolean))]
)

/** 必选位置：仅列出所选 location 下的资源（未维护 location 的条目不匹配） */
const resourcesForKpiSelect = computed(() => {
  const codes = kpiLocationCodesNorm.value
  const all = resourceOptions.value
  if (codes.length === 0) return []
  const set = new Set(codes)
  return all.filter((r) => set.has(normLocationCode(r.location)))
})

const resourceSelectPlaceholder = computed(() => {
  if (kpiLocationCodesNorm.value.length > 0 && resourcesForKpiSelect.value.length === 0) {
    return t('dashboard.noResourcesAtLocation')
  }
  return t('dashboard.selectResources')
})

const allKpiLocationsSelected = computed(() => {
  const options = locationOptions.value
  if (options.length === 0) return false
  const selected = new Set(kpiLocationCodes.value)
  return selected.size === options.length && options.every((loc) => selected.has(loc.code))
})

const kpiLocationsIndeterminate = computed(() => {
  const options = locationOptions.value
  const selected = new Set(kpiLocationCodes.value)
  const n = options.filter((loc) => selected.has(loc.code)).length
  return n > 0 && n < options.length
})

const handleSelectAllKpiLocations = (val) => {
  if (val) {
    kpiLocationCodes.value = locationOptions.value.map((loc) => loc.code)
  } else {
    kpiLocationCodes.value = []
  }
  onKpiLocationChange()
}

const allKpiResourcesSelected = computed(() => {
  const options = resourcesForKpiSelect.value
  return (
    options.length > 0 &&
    kpiResourceIds.value.length === options.length &&
    options.every((r) => kpiResourceIds.value.includes(r.id))
  )
})

const kpiResourcesIndeterminate = computed(() => {
  const options = resourcesForKpiSelect.value
  const selectedInOptions = options.filter((r) => kpiResourceIds.value.includes(r.id)).length
  return selectedInOptions > 0 && selectedInOptions < options.length
})

const handleSelectAllKpiResources = (val) => {
  if (val) {
    kpiResourceIds.value = resourcesForKpiSelect.value.map((r) => r.id)
  } else {
    const filteredIds = new Set(resourcesForKpiSelect.value.map((r) => r.id))
    kpiResourceIds.value = kpiResourceIds.value.filter((id) => !filteredIds.has(id))
  }
  refreshData()
}

const locationOptionLabel = (loc) => {
  if (!loc) return ''
  const d = (loc.description || '').trim()
  return d ? `${loc.code} · ${d}` : loc.code
}

const loadLocationOptions = async () => {
  try {
    locationOptions.value = (await masterDataApi.getLocations()) || []
  } catch (e) {
    console.error('Failed to load locations:', e)
    locationOptions.value = []
  }
}

const loadResourceOptions = async () => {
  try {
    const pageSize = 2000
    let skip = 0
    const all = []
    const seen = new Set()
    for (let guard = 0; guard < 50; guard += 1) {
      const batch = await masterDataApi.getResources({ limit: pageSize, skip })
      if (!Array.isArray(batch) || batch.length === 0) break
      for (const r of batch) {
        if (r && r.id != null && !seen.has(r.id)) {
          seen.add(r.id)
          all.push(r)
        }
      }
      if (batch.length < pageSize) break
      skip += pageSize
    }
    resourceOptions.value = all
  } catch (e) {
    console.error('Failed to load resources:', e)
    resourceOptions.value = []
  }
}

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

async function onKpiLocationChange() {
  await nextTick()
  const allowed = new Set(resourcesForKpiSelect.value.map((r) => r.id))
  kpiResourceIds.value = kpiResourceIds.value.filter((id) => allowed.has(id))
  refreshData()
}

function getKpiFilterValidationError() {
  const [start, end] = dateRange.value || []
  if (!start || !end) return t('dashboard.selectDateRangeRequired')
  if (kpiLocationCodesNorm.value.length === 0) return t('dashboard.selectLocationRequired')
  if (kpiResourceIds.value.length === 0) return t('dashboard.selectResourcesRequired')
  return null
}

const refreshData = async (options = {}) => {
  const { showValidationWarning = false } = options
  const err = getKpiFilterValidationError()
  if (err) {
    schedulingStore.$patch({ kpiData: null })
    if (showValidationWarning) ElMessage.warning(err)
    return
  }

  loading.value = true
  try {
    const [start, end] = dateRange.value || []
    const locCodes = kpiLocationCodesNorm.value
    await schedulingStore.fetchKPIData({
      // 保持订单KPI/平均提前期的原有口径：仍按交期区间过滤（不改功能）
      ...(start && { dueDateStart: start }),
      ...(end && { dueDateEnd: end }),
      // 资源利用率/每日产能负荷/资源利用详情：按“日期区间”（排程时间窗口）过滤
      ...(start && { scheduleDateStart: start }),
      ...(end && { scheduleDateEnd: end }),
      productLocations: locCodes,
      resourceLocations: locCodes,
      resourceIds: kpiResourceIds.value
    })
  } finally {
    loading.value = false
  }
}

async function handleRefreshClick() {
  await refreshData({ showValidationWarning: true })
  if (!getKpiFilterValidationError()) {
    ElMessage.success(t('messages.dataRefreshed'))
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

onMounted(async () => {
  await Promise.all([loadLocationOptions(), loadResourceOptions()])

  if (kpiLocationCodesNorm.value.length === 0 && locationOptions.value.length > 0) {
    kpiLocationCodes.value = locationOptions.value.map((loc) => loc.code)
  }
  await nextTick()
  if (kpiResourceIds.value.length === 0 && resourcesForKpiSelect.value.length > 0) {
    kpiResourceIds.value = resourcesForKpiSelect.value.map((r) => r.id)
  }

  await refreshData()
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
    margin-top: 0;
  }
}

.filters-inline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  min-width: 0;

  /* 与日期区间、位置、资源共用：防止窄列下中文标签被压成一字一行（看似竖排） */
  .date-range-label {
    font-size: 14px;
    color: $m3-on-surface-variant;
    white-space: nowrap;
    flex-shrink: 0;

    .required-mark {
      color: #f56c6c;
      margin-left: 2px;
    }
  }
}

.location-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;

  .location-select {
    width: 200px;
  }
}

.resource-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;

  .resource-select {
    width: min(260px, 100%);
    min-width: 200px;
  }
}

.date-range-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;

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

.select-header-options {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 4px 0;
}
</style>

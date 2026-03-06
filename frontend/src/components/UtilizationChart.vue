<template>
  <div class="utilization-chart">
    <!-- 表头行 -->
    <div class="header-row">
      <!-- 左侧表头 -->
      <div class="left-header">
        <div class="header-cell col-name">{{ t('gantt.resourceName') }}</div>
        <div class="header-cell col-capacity">{{ t('gantt.capacityHeader') }}</div>
      </div>
      <!-- 右侧时间轴表头 -->
      <div class="right-header" ref="timeAxisRef">
        <div class="time-axis">
          <div 
            v-for="day in timeAxis" 
            :key="day.date" 
            class="time-slot"
            :style="{ width: `${dayWidth}px` }"
          >
            <div class="day-label">{{ day.date }}</div>
            <div class="hour-labels">
              <span v-for="hour in hourLabels" :key="hour">{{ hour }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 内容行 -->
    <div class="content-row">
      <!-- 左侧内容（可纵向滚动） -->
      <div class="left-content" ref="leftContentRef" @scroll="handleLeftScroll">
        <div 
          v-for="resource in chartData" 
          :key="resource.resource_id"
          class="left-row"
        >
          <div class="cell col-name">{{ resource.resource_name }}</div>
          <div class="cell col-capacity">
            <div class="capacity-scale">
              <span>27</span>
              <span>18</span>
              <span>9</span>
              <span>0</span>
            </div>
          </div>
        </div>
        <div v-if="chartData.length === 0" class="empty-row">
          {{ t('gantt.noData') }}
        </div>
      </div>
      
      <!-- 右侧图表（可双向滚动） -->
      <div class="right-content" ref="rightContentRef" @scroll="handleRightScroll">
        <div class="chart-rows">
          <div 
            v-for="resource in chartData" 
            :key="resource.resource_id" 
            class="chart-row"
            :style="{ backgroundSize: `${dayWidth}px 100%` }"
          >
            <!-- 当前时间线 -->
            <div class="current-time-line" :style="{ left: currentTimePosition + 'px' }"></div>
            
            <!-- 利用率柱状图 -->
            <div class="utilization-bars">
              <div 
                v-for="(slot, index) in resource.time_slots" 
                :key="index"
                class="bar-container"
                :style="{ left: getSlotPosition(slot.start) + 'px', width: getSlotWidth(slot.start, slot.end) + 'px' }"
                :title="`利用率: ${(slot.utilization * 100).toFixed(1)}%`"
              >
                <div 
                  class="bar"
                  :class="{ 
                    'overload': slot.utilization > 1, 
                    'normal': slot.utilization > 0 && slot.utilization <= 1,
                    'empty': slot.utilization === 0 
                  }"
                  :style="{ height: slot.utilization > 0 ? Math.min(slot.utilization * 100, 100) + '%' : '2px' }"
                >
                  <div 
                    v-if="slot.utilization > 1"
                    class="overload-indicator"
                    :style="{ height: ((slot.utilization - 1) * 100) + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18nStore } from '@/stores/i18n'

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  dateRange: {
    type: Array,
    default: () => []
  },
  zoomLevel: {
    type: Number,
    default: 1 // 0=小时, 1=4小时, 2=天, 3=周, 4=月
  }
})

const timeAxisRef = ref(null)
const leftContentRef = ref(null)
const rightContentRef = ref(null)

let isScrolling = false

// 左侧内容纵向滚动时，同步右侧内容
const handleLeftScroll = () => {
  if (isScrolling) return
  isScrolling = true
  if (leftContentRef.value && rightContentRef.value) {
    rightContentRef.value.scrollTop = leftContentRef.value.scrollTop
  }
  setTimeout(() => { isScrolling = false }, 10)
}

// 右侧内容滚动时，同步时间轴横向滚动和左侧内容纵向滚动
const handleRightScroll = () => {
  if (isScrolling) return
  isScrolling = true
  if (rightContentRef.value) {
    // 同步时间轴横向滚动
    if (timeAxisRef.value) {
      timeAxisRef.value.scrollLeft = rightContentRef.value.scrollLeft
    }
    // 同步左侧内容纵向滚动
    if (leftContentRef.value) {
      leftContentRef.value.scrollTop = rightContentRef.value.scrollTop
    }
  }
  setTimeout(() => { isScrolling = false }, 10)
}

// 根据缩放级别计算每天的宽度
const dayWidth = computed(() => {
  const widthMap = {
    0: 480,  // 小时视图 - 每天480px (每小时20px)
    1: 240,  // 4小时视图 - 每天240px (每4小时40px)
    2: 120,  // 天视图 - 每天120px
    3: 40,   // 周视图 - 每天40px
    4: 20    // 月视图 - 每天20px
  }
  return widthMap[props.zoomLevel] || 240
})

// 根据缩放级别生成小时标签
const hourLabels = computed(() => {
  switch (props.zoomLevel) {
    case 0: // 小时视图 - 显示每小时
      return ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
    case 1: // 4小时视图 - 显示每4小时
      return ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
    case 2: // 天视图 - 显示每8小时
      return ['00:00', '08:00', '16:00']
    case 3: // 周视图 - 只显示日期
      return ['00:00', '12:00']
    case 4: // 月视图 - 只显示日期
      return ['00:00']
    default:
      return ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
  }
})

// 生成时间轴
const timeAxis = computed(() => {
  if (!props.dateRange || props.dateRange.length < 2) return []
  
  const [startStr, endStr] = props.dateRange
  const start = new Date(startStr)
  const end = new Date(endStr)
  const days = []
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  
  const current = new Date(start)
  while (current <= end) {
    days.push({
      date: `${current.getFullYear()}.${String(current.getMonth() + 1).padStart(2, '0')}.${String(current.getDate()).padStart(2, '0')}`,
      weekday: weekdays[current.getDay()],
      timestamp: current.getTime()
    })
    current.setDate(current.getDate() + 1)
  }
  
  return days
})

// 图表数据 - 直接使用传入的数据
const chartData = computed(() => {
  return props.data || []
})

// 计算当前时间线位置
const currentTimePosition = computed(() => {
  if (timeAxis.value.length === 0) return 0
  
  const now = new Date()
  // 将 dateRange[0] 解析为本地时间的 00:00:00
  const startDate = props.dateRange[0]
  const start = new Date(startDate + ' 00:00:00')
  const diffMs = now - start
  const diffDays = diffMs / (1000 * 60 * 60 * 24)
  
  return diffDays * dayWidth.value
})

// 计算时间槽位置
const getSlotPosition = (startStr) => {
  if (!props.dateRange || props.dateRange.length < 2) return 0
  
  // 将 dateRange[0] 解析为本地时间的 00:00:00
  const startDate = props.dateRange[0]
  const start = new Date(startDate + ' 00:00:00')
  
  // 将时间槽开始时间解析为本地时间
  const slotStart = new Date(startStr.replace(' ', 'T'))
  
  const diffMs = slotStart - start
  const diffDays = diffMs / (1000 * 60 * 60 * 24)
  
  return diffDays * dayWidth.value
}

// 计算时间槽宽度
const getSlotWidth = (startStr, endStr) => {
  const start = new Date(startStr.replace(' ', 'T'))
  const end = new Date(endStr.replace(' ', 'T'))
  const diffMs = end - start
  const diffDays = diffMs / (1000 * 60 * 60 * 24)
  
  return Math.max(diffDays * dayWidth.value, 2)
}

// 监听数据变化
watch(() => props.data, () => {
  // 数据变化时重新渲染
}, { deep: true })

onMounted(() => {
  // 初始化
})
</script>

<style lang="scss" scoped>
.utilization-chart {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

// ===== 表头行 =====
.header-row {
  display: flex;
  flex-shrink: 0;
  border-bottom: 1px solid #e4e7ed;
}

.left-header {
  display: flex;
  width: 460px;
  min-width: 460px;
  flex-shrink: 0;
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  
  .header-cell {
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 500;
    color: #606266;
    display: flex;
    align-items: center;
  }
  
  .col-name {
    width: 380px;
    min-width: 380px;
  }
  
  .col-capacity {
    width: 80px;
    min-width: 80px;
    justify-content: center;
  }
}

.right-header {
  flex: 1;
  overflow-x: hidden;
  overflow-y: hidden;
  background: #f5f7fa;
}

.time-axis {
  display: flex;
}

.time-slot {
  flex-shrink: 0;
  border-right: 1px solid #ebeef5;
  
  .day-label {
    padding: 4px 8px;
    font-size: 12px;
    color: #606266;
    text-align: center;
    border-bottom: 1px solid #ebeef5;
  }
  
  .hour-labels {
    display: flex;
    justify-content: space-between;
    padding: 2px 4px;
    font-size: 11px;
    color: #909399;
  }
}

// ===== 内容行 =====
.content-row {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-content {
  width: 460px;
  min-width: 460px;
  flex-shrink: 0;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 1px solid #e4e7ed;
  
  // 隐藏滚动条但保持功能
  scrollbar-width: none;
  -ms-overflow-style: none;
  &::-webkit-scrollbar {
    display: none;
  }
}

.left-row {
  display: flex;
  height: 80px;
  border-bottom: 1px solid #ebeef5;
  
  &:hover {
    background: #f5f7fa;
  }
  
  .cell {
    padding: 8px 12px;
    font-size: 13px;
    color: #303133;
    display: flex;
    align-items: center;
  }
  
  .col-name {
    width: 380px;
    min-width: 380px;
  }
  
  .col-capacity {
    width: 80px;
    min-width: 80px;
    justify-content: center;
  }
}

.capacity-scale {
  display: flex;
  flex-direction: column;
  font-size: 11px;
  color: #909399;
  line-height: 1.4;
  text-align: center;
}

.empty-row {
  text-align: center;
  color: #909399;
  padding: 24px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.right-content {
  flex: 1;
  overflow: auto;
}

.chart-rows {
  position: relative;
}

.chart-row {
  height: 80px;
  position: relative;
  border-bottom: 1px solid #ebeef5;
  background: linear-gradient(
    to right,
    #f9fafb 0%,
    #f9fafb 33.33%,
    #fff 33.33%,
    #fff 66.66%,
    #f9fafb 66.66%,
    #f9fafb 100%
  );
}

.current-time-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(229, 57, 53, 0.4);
  z-index: 2;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -3px;
    width: 6px;
    height: 6px;
    background: rgba(229, 57, 53, 0.5);
    border-radius: 50%;
  }
}

.utilization-bars {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.bar-container {
  position: absolute;
  bottom: 0;
  height: 100%;
  display: flex;
  align-items: flex-end;
}

.bar {
  width: 100%;
  border-radius: 2px 2px 0 0;
  position: relative;
  min-height: 4px;
  transition: opacity 0.2s;
  
  // 正常状态 - 绿色
  &.normal {
    background: linear-gradient(to top, #95de64, #52c41a);
  }
  
  // 超载状态 - 红色
  &.overload {
    background: linear-gradient(to top, #ff7875, #f5222d);
  }
  
  // 空闲状态 - 灰色
  &.empty {
    background: #e4e7ed;
    min-height: 2px;
  }
  
  &:hover {
    opacity: 0.8;
  }
}

.overload-indicator {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background: rgba(245, 34, 45, 0.6);
  border-radius: 2px 2px 0 0;
}
</style>

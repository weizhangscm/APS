<template>
  <div class="simple-gantt-table">
    <!-- 左侧固定区域 -->
    <div class="left-panel">
      <!-- 左侧表头 -->
      <div class="left-header">
        <table>
          <thead>
            <tr>
              <th class="col-name">{{ t('gantt.resourceName') }}</th>
              <th class="col-start">{{ t('gantt.startTime') }}</th>
              <th class="col-duration">{{ t('gantt.durationH') }}</th>
            </tr>
          </thead>
        </table>
      </div>
      <!-- 左侧表格内容 -->
      <div class="left-content" ref="leftContentRef" @scroll="handleLeftScroll">
        <table>
          <tbody>
            <template v-for="item in flattenedData" :key="item.id">
              <tr :class="{ 'group-row': item.isGroup, 'task-row': !item.isGroup }">
                <td class="col-name">
                  <span 
                    class="task-text" 
                    :style="{ paddingLeft: (item.level * 20) + 'px' }"
                  >
                    <span v-if="item.isGroup" class="expand-icon" @click="toggleExpand(item)">
                      <el-icon><component :is="item.expanded ? 'Minus' : 'Plus'" /></el-icon>
                    </span>
                    <el-icon v-if="item.isGroup" class="group-icon"><Folder /></el-icon>
                    <el-icon v-else class="task-icon"><Document /></el-icon>
                    {{ item.displayName }}
                  </span>
                </td>
                <td class="col-start">{{ formatDate(item.displayStartDate || item.start_date) }}</td>
                <td class="col-duration">{{ item.durationDisplay }}</td>
              </tr>
            </template>
            <tr v-if="flattenedData.length === 0">
              <td colspan="3" class="empty-row">{{ t('gantt.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 右侧甘特图区域 -->
    <div class="right-panel">
      <!-- 右侧时间轴 -->
      <div class="right-header" ref="timeAxisRef">
        <div class="time-axis">
          <div 
            v-for="day in timeAxis" 
            :key="day.timestamp" 
            class="time-slot"
            :class="{ 'is-hour-view': props.zoomLevel === 0 }"
            :style="{ width: dayWidth + 'px' }"
          >
            <div class="day-label">{{ formatDisplayDate(day.date) }}</div>
            <div class="hour-labels">
              <span v-for="hour in hourTicks" :key="hour">{{ formatDisplayHourOfDay(hour) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧甘特条区域 -->
      <div class="right-content" ref="rightContentRef" @scroll="handleRightScroll">
        <div class="gantt-rows" :style="{ width: totalWidth + 'px' }">
          <div 
            v-for="item in flattenedData" 
            :key="item.id" 
            class="gantt-row"
            :class="{ 'group-row': item.isGroup }"
          >
            <!-- 当前时间线 -->
            <div 
              v-if="currentTimePosition >= 0" 
              class="current-time-line" 
              :style="{ left: currentTimePosition + 'px' }"
            ></div>
            
            <!-- 资源行：多段条形图 -->
            <template v-if="item.isGroup && item.timeRanges && item.timeRanges.length > 0">
              <div 
                v-for="(range, rangeIndex) in item.timeRanges"
                :key="`${item.id}-range-${rangeIndex}`"
                class="task-bar project-bar"
                :style="getTaskStyleFromRange(range)"
                :title="`${item.text}\n开始: ${formatDateTime(range.start_date)}\n结束: ${formatDateTime(range.end_date)}`"
              >
              </div>
            </template>
            
            <!-- 子任务条：单个条形图（可拖拽） -->
            <div 
              v-else-if="!item.isGroup && item.start_date && item.end_date"
              class="task-bar"
              :class="[getTaskClass(item), { 'is-draggable': canDrag(item), 'is-dragging': draggingItem?.id === item.id }]"
              :style="getTaskBarStyle(item)"
              :title="`${item.text}\n开始: ${formatDateTime(item.start_date)}\n结束: ${formatDateTime(item.end_date)}`"
              @pointerdown.prevent="canDrag(item) && onTaskBarPointerDown($event, item)"
            >
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { Folder, Document, Plus, Minus } from '@element-plus/icons-vue'
import { useI18nStore } from '@/stores/i18n'
import {
  formatDisplayDate,
  formatDisplayDateTime,
  formatDisplayHourOfDay
} from '@/utils/displayDateTime'

const emit = defineEmits(['task-dragged'])

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const props = defineProps({
  tasks: {
    type: Object,
    default: () => ({ data: [], links: [] })
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

const ganttArea = ref(null)
const timeAxisRef = ref(null)
const leftContentRef = ref(null)
const rightContentRef = ref(null)

// 与 .gantt-row / 左侧表格 tr 高度一致
const GANTT_ROW_HEIGHT = 44

// 拖拽状态：当前拖拽的工序项、预览位置（px）
const draggingItem = ref(null)
const dragPreviewLeft = ref(null)

let isScrolling = false
let dragShiftKey = false

// 是否允许拖拽：子任务、有 operation_id、非生产订单、非切换准备条
function canDrag(item) {
  if (!item || item.isGroup) return false
  if (!item.operation_id) return false
  if (item.order_type === 'production' || (item.text && item.text.startsWith('[生产]'))) return false
  if (item.task_type === 'changeover' || item.status === 'changeover') return false
  // 运行时间缺失的工序视为主数据不完整，禁止拖拽（避免后端报错）
  if (item.work_hours == null || item.work_hours < 0) return false
  return true
}

// 将时间取整到 15 分钟
function roundTo15Min(date) {
  const ms = date.getTime()
  const rounded = Math.round(ms / (15 * 60 * 1000)) * (15 * 60 * 1000)
  return new Date(rounded)
}

// 将像素偏移（相对时间轴起点）转为日期
function pixelOffsetToDate(pixelOffset) {
  if (timeAxis.value.length === 0) return null
  const firstDay = timeAxis.value[0].date
  const days = pixelOffset / dayWidth.value
  const ms = firstDay.getTime() + days * 24 * 60 * 60 * 1000
  return new Date(ms)
}

// 任务条样式：拖拽中时使用预览 left
function getTaskBarStyle(item) {
  const base = getTaskStyle(item)
  if (base.display === 'none') return base
  if (draggingItem.value?.id === item.id && dragPreviewLeft.value != null) {
    return { ...base, left: `${dragPreviewLeft.value}px`, transition: 'none' }
  }
  return base
}

/** 根据指针 Y 命中哪一行，解析目标资源 ID（资源视图跨行拖拽） */
function resolveTargetResourceIdFromY(clientY) {
  const el = rightContentRef.value
  if (!el) return null
  const rect = el.getBoundingClientRect()
  const y = clientY - rect.top + el.scrollTop
  let idx = Math.floor(y / GANTT_ROW_HEIGHT)
  const rows = flattenedData.value
  if (!rows.length) return null
  idx = Math.max(0, Math.min(idx, rows.length - 1))
  const row = rows[idx]
  if (!row) return null
  if (row.isGroup) {
    return row.resource_id != null ? row.resource_id : null
  }
  return row.resource_id != null ? row.resource_id : null
}

function onTaskBarPointerDown(e, item) {
  if (e.button !== 0 || !canDrag(item) || !rightContentRef.value || timeAxis.value.length === 0) return
  dragShiftKey = !!e.shiftKey
  const startLeft = timeAxis.value[0].date
    ? (new Date(item.start_date) - timeAxis.value[0].date) / (24 * 60 * 60 * 1000) * dayWidth.value
    : 0

  draggingItem.value = item
  dragPreviewLeft.value = startLeft

  const onMove = (e2) => {
    if (!draggingItem.value || !rightContentRef.value) return
    const r = rightContentRef.value.getBoundingClientRect()
    let offset = e2.clientX - r.left + rightContentRef.value.scrollLeft
    const barWidth = Math.max(((new Date(item.end_date) - new Date(item.start_date)) / (24 * 60 * 60 * 1000)) * dayWidth.value, 6)
    offset = Math.max(0, Math.min(offset, totalWidth.value - barWidth))
    dragPreviewLeft.value = offset
  }

  const onUp = (e2) => {
    if (!draggingItem.value) return
    const itemToEmit = draggingItem.value
    const leftPx = dragPreviewLeft.value != null ? dragPreviewLeft.value : 0
    draggingItem.value = null
    dragPreviewLeft.value = null
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp, true)

    const newStart = pixelOffsetToDate(leftPx)
    if (!newStart) return
    const roundedStart = roundTo15Min(newStart)
    const [rangeStart, rangeEnd] = props.dateRange || []
    let clampedStart = roundedStart
    if (rangeStart && rangeEnd) {
      const start = new Date(rangeStart)
      const end = new Date(rangeEnd)
      end.setHours(23, 59, 59, 999)
      if (clampedStart < start) clampedStart = start
      if (clampedStart > end) clampedStart = end
    }

    const targetRes = resolveTargetResourceIdFromY(e2.clientY)
    const origRes = itemToEmit.resource_id
    let newResourceId = null
    if (targetRes != null && origRes != null && targetRes !== origRes) {
      newResourceId = targetRes
    }

    emit('task-dragged', {
      operationId: itemToEmit.operation_id,
      newStart: clampedStart,
      resourceId: newResourceId,
      originalStart: new Date(itemToEmit.start_date),
      moveWholeOrder: dragShiftKey
    })
    dragShiftKey = false
  }

  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp, true)
}

// 左侧表格纵向滚动时，同步右侧甘特条区域
const handleLeftScroll = () => {
  if (isScrolling) return
  isScrolling = true
  if (leftContentRef.value && rightContentRef.value) {
    rightContentRef.value.scrollTop = leftContentRef.value.scrollTop
  }
  setTimeout(() => { isScrolling = false }, 10)
}

// 右侧甘特条区域滚动时，同步时间轴横向滚动和左侧表格纵向滚动
const handleRightScroll = () => {
  if (isScrolling) return
  isScrolling = true
  if (rightContentRef.value) {
    // 同步时间轴横向滚动
    if (timeAxisRef.value) {
      timeAxisRef.value.scrollLeft = rightContentRef.value.scrollLeft
    }
    // 同步左侧表格纵向滚动
    if (leftContentRef.value) {
      leftContentRef.value.scrollTop = rightContentRef.value.scrollTop
    }
  }
  setTimeout(() => { isScrolling = false }, 10)
}

// 根据缩放级别计算每天的宽度
const dayWidth = computed(() => {
  const widthMap = {
    0: 480,  // 小时视图
    1: 240,  // 4小时视图
    2: 120,  // 天视图
    3: 40,   // 周视图
    4: 20    // 月视图
  }
  return widthMap[props.zoomLevel] || 240
})

// 根据缩放级别生成时间轴小时刻度：小时视图显示每小时，其余显示每4小时等
const hourTicks = computed(() => {
  if (props.zoomLevel === 0) {
    return Array.from({ length: 24 }, (_, i) => i)
  }
  return [0, 4, 8, 12, 16, 20]
})

// 存储展开状态
const expandedItems = reactive({})

// 切换展开/收起
const toggleExpand = (item) => {
  expandedItems[item.id] = !expandedItems[item.id]
}

// 按资源分组的数据结构
const groupedByResource = computed(() => {
  const data = props.tasks?.data || []
  if (data.length === 0) return []
  
  // 首先建立ID到数据的映射
  const itemMap = {}
  data.forEach(item => {
    itemMap[item.id] = item
  })
  
  // 找出所有顶级项（资源）
  const topLevelItems = data.filter(d => d.parent === 0 || d.parent === null || d.parent === undefined)
  
  // 按资源分组
  const resourceList = []
  
  topLevelItems.forEach(resource => {
    // 资源名称就是顶级项的 text
    const resourceName = resource.text || `资源 ${resource.id}`
    
    // 找出该资源下的所有子任务（只在当前传入的数据中查找，确保是过滤后的数据）
    const children = data.filter(d => d.parent === resource.id)
    
    // 计算合并后的时间段（用于资源行显示多段条形图）
    const mergedTimeRanges = calculateMergedTimeRanges(children)
    
    const rid =
      resource.resource_id != null
        ? resource.resource_id
        : typeof resource.id === 'string' && resource.id.startsWith('resource_')
          ? parseInt(resource.id.replace(/^resource_/, ''), 10)
          : typeof resource.id === 'number'
            ? resource.id
            : null
    resourceList.push({
      id: resource.id,
      resource_id: Number.isFinite(rid) ? rid : resource.resource_id ?? null,
      resourceName: resourceName,
      description: resource.description || '',
      children: children.map(child => ({
        ...child,
        // 子任务的文本就是原始 text，包含订单号和工序名称
        displayText: child.text
      })),
      // 资源行使用多段时间范围
      timeRanges: mergedTimeRanges,
      expanded: expandedItems[resource.id] === true // 默认收起
    })
  })
  
  return resourceList
})

// 计算资源的实际占用时间范围（根据子任务的时间）
const calculateResourceTimeRange = (children) => {
  if (!children || children.length === 0) {
    return { start_date: null, end_date: null }
  }
  
  let minStart = null
  let maxEnd = null
  
  children.forEach(child => {
    if (child.start_date) {
      const start = new Date(child.start_date)
      if (!minStart || start < minStart) {
        minStart = start
      }
    }
    if (child.end_date) {
      const end = new Date(child.end_date)
      if (!maxEnd || end > maxEnd) {
        maxEnd = end
      }
    }
  })
  
  return {
    start_date: minStart ? minStart.toISOString() : null,
    end_date: maxEnd ? maxEnd.toISOString() : null
  }
}

// 计算合并后的时间段（将重叠或相邻的时间段合并）
const calculateMergedTimeRanges = (children) => {
  if (!children || children.length === 0) {
    return []
  }
  
  // 收集所有有效的时间段
  const ranges = children
    .filter(child => child.start_date && child.end_date)
    .map(child => ({
      start: new Date(child.start_date).getTime(),
      end: new Date(child.end_date).getTime()
    }))
    .sort((a, b) => a.start - b.start)
  
  if (ranges.length === 0) return []
  
  // 合并重叠或相邻的时间段（相邻定义为间隔小于1小时）
  const merged = []
  let current = { ...ranges[0] }
  const GAP_THRESHOLD = 1 * 60 * 60 * 1000 // 1小时间隔阈值
  
  for (let i = 1; i < ranges.length; i++) {
    const next = ranges[i]
    // 如果当前段的结束时间 + 阈值 >= 下一段的开始时间，则合并
    if (current.end + GAP_THRESHOLD >= next.start) {
      // 合并：扩展当前段的结束时间
      current.end = Math.max(current.end, next.end)
    } else {
      // 不重叠，保存当前段，开始新段
      merged.push(current)
      current = { ...next }
    }
  }
  merged.push(current)
  
  // 转换回日期字符串
  return merged.map(range => ({
    start_date: new Date(range.start).toISOString(),
    end_date: new Date(range.end).toISOString()
  }))
}

// 扁平化数据用于显示
const flattenedData = computed(() => {
  const result = []
  
  groupedByResource.value.forEach(resource => {
    // 添加资源行（第一级）- 显示资源名称
    const isExpanded = expandedItems[resource.id] === true // 默认收起
    
    // 计算子任务的时间范围（仅用于显示开始时间列）
    const timeRange = calculateResourceTimeRange(resource.children)
    
    // 资源行使用多段时间范围显示
    result.push({
      id: resource.id,
      resource_id: resource.resource_id,
      displayName: resource.resourceName,
      // 资源行使用多段时间范围
      timeRanges: resource.timeRanges,
      // 用于在左侧表格"开始时间"列显示
      displayStartDate: timeRange.start_date,
      level: 0,
      isGroup: true,
      expanded: isExpanded,
      durationDisplay: calculateTotalDuration(resource.children),
      text: resource.resourceName
    })
    
    // 如果展开，添加子任务（第二级 - 订单+工序名称）
    if (isExpanded && resource.children.length > 0) {
      resource.children.forEach(task => {
        result.push({
          ...task,
          // 直接使用原始文本（已包含订单号和工序名称，如 "PLN20260017 - 10 精密加工"）
          displayName: task.displayText || task.text,
          level: 1,
          isGroup: false,
          expanded: false,
          durationDisplay: calculateDuration(task),
          text: task.text
        })
      })
    }
  })
  
  return result
})

// 计算总时长：优先用作业时间 work_hours（与排程前一致，避免排程后因日历跨度显示成更大值）
const calculateTotalDuration = (children) => {
  if (!children || children.length === 0) return '-'
  let totalHours = 0
  children.forEach(child => {
    if (child.work_hours != null && child.work_hours >= 0) {
      totalHours += child.work_hours
    } else if (child.start_date && child.end_date) {
      const start = new Date(child.start_date)
      const end = new Date(child.end_date)
      totalHours += (end - start) / (1000 * 60 * 60)
    }
  })
  return totalHours > 0 ? totalHours.toFixed(1) : '-'
}

// 计算单个任务时长：优先用 work_hours（作业时间），否则用日历跨度
const calculateDuration = (item) => {
  if (item.work_hours != null && item.work_hours >= 0) return Number(item.work_hours).toFixed(1)
  if (!item.start_date || !item.end_date) return '-'
  const start = new Date(item.start_date)
  const end = new Date(item.end_date)
  const hours = (end - start) / (1000 * 60 * 60)
  return hours.toFixed(1)
}

// 生成时间轴
const timeAxis = computed(() => {
  if (!props.dateRange || props.dateRange.length < 2) {
    // 从任务数据推断时间范围
    const data = flattenedData.value
    if (data.length === 0) return []
    
    let minDate = null
    let maxDate = null
    
    data.forEach(item => {
      if (item.start_date) {
        const start = new Date(item.start_date)
        if (!minDate || start < minDate) minDate = start
      }
      if (item.end_date) {
        const end = new Date(item.end_date)
        if (!maxDate || end > maxDate) maxDate = end
      }
    })
    
    if (!minDate || !maxDate) return []
    
    // 扩展范围
    minDate.setDate(minDate.getDate() - 1)
    maxDate.setDate(maxDate.getDate() + 1)
    
    return generateTimeAxis(minDate, maxDate)
  }
  
  const [startStr, endStr] = props.dateRange
  const startDate = new Date(startStr)
  const endDate = new Date(endStr)
  // 确保结束日期包含当天的最后时刻
  endDate.setHours(23, 59, 59, 999)
  return generateTimeAxis(startDate, endDate)
})

const generateTimeAxis = (start, end) => {
  const days = []
  const current = new Date(start)
  current.setHours(0, 0, 0, 0)
  
  while (current <= end) {
    days.push({
      date: new Date(current),
      timestamp: current.getTime()
    })
    current.setDate(current.getDate() + 1)
  }
  
  return days
}

// 计算甘特图总宽度
const totalWidth = computed(() => {
  return timeAxis.value.length * dayWidth.value
})

// 计算当前时间线位置
const currentTimePosition = computed(() => {
  if (timeAxis.value.length === 0) return -1
  
  const now = new Date()
  const firstDay = timeAxis.value[0].date
  const diffMs = now - firstDay
  const diffDays = diffMs / (1000 * 60 * 60 * 24)
  
  if (diffDays < 0 || diffDays > timeAxis.value.length) return -1
  
  return diffDays * dayWidth.value
})

// 计算任务条位置和宽度
const getTaskStyle = (item) => {
  if (!item.start_date || !item.end_date || timeAxis.value.length === 0) {
    return { display: 'none' }
  }
  
  const firstDay = timeAxis.value[0].date
  const taskStart = new Date(item.start_date)
  const taskEnd = new Date(item.end_date)
  
  const startDiffMs = taskStart - firstDay
  const startDiffDays = startDiffMs / (1000 * 60 * 60 * 24)
  
  const durationMs = taskEnd - taskStart
  const durationDays = durationMs / (1000 * 60 * 60 * 24)
  
  let left = startDiffDays * dayWidth.value
  // 最小 6px，避免短工序（如 0.8h）被强制成 20px 后视觉上像 2 小时
  let width = Math.max(durationDays * dayWidth.value, 6)
  
  // 处理任务开始时间早于显示区间的情况
  if (left < 0) {
    // 调整宽度，减去超出的部分
    width = width + left
    left = 0
    // 如果宽度变成负数或太小，隐藏该条
    if (width < 5) {
      return { display: 'none' }
    }
  }
  
  return {
    left: `${left}px`,
    width: `${width}px`
  }
}

// 计算时间范围的条形图样式（用于资源行的多段显示）
const getTaskStyleFromRange = (range) => {
  if (!range.start_date || !range.end_date || timeAxis.value.length === 0) {
    return { display: 'none' }
  }
  
  const firstDay = timeAxis.value[0].date
  const taskStart = new Date(range.start_date)
  const taskEnd = new Date(range.end_date)
  
  const startDiffMs = taskStart - firstDay
  const startDiffDays = startDiffMs / (1000 * 60 * 60 * 24)
  
  const durationMs = taskEnd - taskStart
  const durationDays = durationMs / (1000 * 60 * 60 * 24)
  
  let left = startDiffDays * dayWidth.value
  let width = Math.max(durationDays * dayWidth.value, 6)
  
  // 处理任务开始时间早于显示区间的情况
  if (left < 0) {
    // 调整宽度，减去超出的部分
    width = width + left
    left = 0
    // 如果宽度变成负数或太小，隐藏该条
    if (width < 5) {
      return { display: 'none' }
    }
  }
  
  return {
    left: `${left}px`,
    width: `${width}px`
  }
}

// 获取任务类名
const getTaskClass = (item) => {
  const classes = []
  
  if (item.isGroup) {
    classes.push('project-bar')
  }
  
  if (item.order_type === 'production' || (item.text && item.text.startsWith('[生产]'))) {
    classes.push('production-bar')
  } else {
    classes.push('planned-bar')
  }
  
  if (item.task_type === 'changeover' || item.status === 'changeover') {
    classes.push('changeover-bar')
  }
  
  // 仅对已保存到数据库的已排程工序显示红色边框（未保存的启发式结果不显示红框）
  if (item.order_status === 'scheduled' && item.status !== 'pending' && !item.is_preview) {
    classes.push('scheduled-order')
  }
  
  return classes
}

const formatDate = (dateStr) => (dateStr ? formatDisplayDate(dateStr) : '-')
const formatDateTime = (dateStr) => (dateStr ? formatDisplayDateTime(dateStr) : '-')
</script>

<style lang="scss" scoped>
.simple-gantt-table {
  width: 100%;
  height: 100%;
  display: flex;
  overflow: hidden;
}

// ========== 左侧固定区域 ==========
.left-panel {
  width: 460px;
  min-width: 460px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e4e7ed;
  background: #fff;
  z-index: 5;
}

.left-header {
  flex-shrink: 0;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
  
  table {
    width: 100%;
    border-collapse: collapse;
  }
  
  th {
    padding: 8px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    color: #606266;
    white-space: nowrap;
    background: #f5f7fa;
    height: 52px; // 与时间轴高度一致
  }
  
  .col-name {
    width: 280px;
    min-width: 280px;
  }
  
  .col-start {
    width: 100px;
    min-width: 100px;
    text-align: center;
  }
  
  .col-duration {
    width: 80px;
    min-width: 80px;
    text-align: center;
  }
}

.left-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  
  table {
    width: 100%;
    border-collapse: collapse;
  }
  
  td {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid #ebeef5;
    font-size: 13px;
    white-space: nowrap;
    color: #303133;
  }
  
  .col-name {
    width: 280px;
    min-width: 280px;
  }
  
  .col-start {
    width: 100px;
    min-width: 100px;
    text-align: center;
  }
  
  .col-duration {
    width: 80px;
    min-width: 80px;
    text-align: center;
  }
  
  .task-text {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  
  .expand-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    cursor: pointer;
    color: #606266;
    border: 1px solid #dcdfe6;
    border-radius: 2px;
    margin-right: 4px;
    
    &:hover {
      color: #409eff;
      border-color: #409eff;
    }
    
    .el-icon {
      font-size: 12px;
    }
  }
  
  .group-icon {
    color: #409eff;
  }
  
  .task-icon {
    color: #67c23a;
  }
  
  .group-row {
    background: #f8fafd;
    font-weight: 500;
  }
  
  .task-row {
    background: #fff;
  }
  
  .empty-row {
    text-align: center;
    color: #909399;
    padding: 24px;
  }
  
  tr {
    height: 44px;
    
    &:hover {
      background: #f5f7fa;
    }
  }
}

// ========== 右侧甘特图区域 ==========
.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.right-header {
  flex-shrink: 0;
  overflow: hidden;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
}

.time-axis {
  display: flex;
  background: #f5f7fa;
}

.right-content {
  flex: 1;
  overflow: auto; // 横向和纵向都可滚动
  min-height: 0;
}

.gantt-rows {
  position: relative;
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
    font-weight: 500;
  }
  
  .hour-labels {
    display: flex;
    justify-content: space-between;
    padding: 2px 4px;
    font-size: 10px;
    color: #909399;
    span {
      flex-shrink: 0;
    }
  }
  &.is-hour-view .hour-labels {
    justify-content: space-between;
    padding: 1px 2px;
    font-size: 9px;
    span {
      flex: 1 1 0;
      min-width: 0;
      text-align: center;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

.gantt-rows {
  position: relative;
}

.gantt-row {
  height: 44px;
  position: relative;
  border-bottom: 1px solid #ebeef5;
  
  &.group-row {
    background: #f8fafd;
  }
  
  &:hover {
    background: #f5f7fa;
  }
}

.current-time-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(229, 57, 53, 0.4);  // 降低透明度，使用更细的线条
  z-index: 2;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -3px;
    width: 6px;
    height: 6px;
    background: rgba(229, 57, 53, 0.5);  // 降低圆点透明度
    border-radius: 50%;
  }
}

.task-bar {
  position: absolute;
  top: 8px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.2s;

  &.is-draggable {
    cursor: grab;
    touch-action: none;
  }

  &.is-dragging {
    cursor: grabbing;
    user-select: none;
    z-index: 10;
  }
  
  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  }
  
  .task-label {
    font-size: 12px;
    color: #fff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.planned-bar {
  background: linear-gradient(135deg, #1a73e8 0%, #4285f4 100%);
}

.production-bar {
  background: linear-gradient(135deg, #6B7280 0%, #9CA3AF 100%);
}

.project-bar {
  background: linear-gradient(135deg, #4285f4 0%, #5a9cf5 100%);
}

.changeover-bar {
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  border: 2px dashed #92400E;
}

.scheduled-order {
  border: 2px solid #f56565 !important;  // 红色边框
  box-sizing: border-box;
}
</style>

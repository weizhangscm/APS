<template>
  <div class="gantt-wrapper">
    <!-- Toolbar - 可通过 hideToolbar prop 隐藏 -->
    <div v-if="!props.hideToolbar" class="gantt-toolbar">
      <div class="zoom-controls">
        <el-button-group>
          <el-button @click="zoomIn" :disabled="currentZoom >= zoomLevels.length - 1">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
          <el-button @click="zoomOut" :disabled="currentZoom <= 0">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
        </el-button-group>
        <el-select v-model="currentZoom" style="width: 120px; margin-left: 8px;" @change="applyZoom">
          <el-option 
            v-for="(level, index) in zoomLevels" 
            :key="index" 
            :label="level.label" 
            :value="index" 
          />
        </el-select>
      </div>
      <div class="toolbar-info">
        <span class="legend-item">
          <span class="legend-box planned"></span>计划订单
        </span>
        <span class="legend-item">
          <span class="legend-box production"></span>生产订单
        </span>
        <span class="legend-item">
          <span class="legend-box changeover"></span>切换准备
        </span>
        <el-tag type="info" effect="plain" style="margin-left: 12px;">
          <el-icon><Pointer /></el-icon>
          计划订单可拖拽调整
        </el-tag>
      </div>
    </div>
    <div ref="ganttContainer" class="gantt-chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { gantt } from 'dhtmlx-gantt'

const props = defineProps({
  tasks: {
    type: Object,
    default: () => ({ data: [], links: [] })
  },
  viewType: {
    type: String,
    default: 'order'
  },
  strategy: {
    type: String,
    default: 'EDD'
  },
  hideToolbar: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['task-updated', 'task-clicked', 'link-added'])

const ganttContainer = ref(null)
let isInitialized = false

// Zoom levels configuration
const zoomLevels = ref([
  { label: '小时', scales: [
    { unit: "day", step: 1, format: "%m/%d" },
    { unit: "hour", step: 1, format: "%H:00" }
  ]},
  { label: '4小时', scales: [
    { unit: "day", step: 1, format: "%Y-%m-%d" },
    { unit: "hour", step: 4, format: "%H:00" }
  ]},
  { label: '天', scales: [
    { unit: "week", step: 1, format: "第%W周" },
    { unit: "day", step: 1, format: "%m/%d" }
  ]},
  { label: '周', scales: [
    { unit: "month", step: 1, format: "%Y年%m月" },
    { unit: "week", step: 1, format: "第%W周" }
  ]},
  { label: '月', scales: [
    { unit: "year", step: 1, format: "%Y年" },
    { unit: "month", step: 1, format: "%m月" }
  ]}
])

const currentZoom = ref(1) // Default to 4-hour view

const applyZoom = () => {
  if (!isInitialized) return
  const level = zoomLevels.value[currentZoom.value]
  gantt.config.scales = level.scales
  gantt.render()
}

const zoomIn = () => {
  if (currentZoom.value > 0) {
    currentZoom.value--
    applyZoom()
  }
}

const zoomOut = () => {
  if (currentZoom.value < zoomLevels.value.length - 1) {
    currentZoom.value++
    applyZoom()
  }
}

const initGantt = () => {
  if (!ganttContainer.value || isInitialized) return
  
  // ========== 布局配置（必须在 init 之前设置）==========
  // 配置带滚动条的布局
  gantt.config.layout = {
    css: "gantt_container",
    rows: [
      {
        cols: [
          { view: "grid", scrollX: "scrollHor", scrollY: "scrollVer" },
          { resizer: true, width: 1 },
          { view: "timeline", scrollX: "scrollHor", scrollY: "scrollVer" },
          { view: "scrollbar", id: "scrollVer", scroll: "y" }
        ]
      },
      { view: "scrollbar", id: "scrollHor", scroll: "x", height: 20 }
    ]
  }
  
  // Configure gantt
  gantt.config.date_format = "%Y-%m-%d %H:%i"
  gantt.config.xml_date = "%Y-%m-%d %H:%i"
  
  // Initial scales
  gantt.config.scales = zoomLevels.value[currentZoom.value].scales
  
  // Grid columns - 根据视图类型设置第一列标题
  const firstColumnLabel = props.viewType === 'product' ? '产品' : '任务名称'
  gantt.config.columns = [
    { name: "text", label: firstColumnLabel, tree: true, width: 260, resize: true },
    { name: "start_date", label: "开始时间", align: "center", width: 130, resize: true },
    { name: "duration", label: "时长(H)", align: "center", width: 70, 
      template: (task) => {
        if (task.start_date && task.end_date) {
          const hours = (task.end_date - task.start_date) / (1000 * 60 * 60)
          return hours.toFixed(1)
        }
        return ''
      }
    }
  ]
  
  // ========== 手工排程调整配置 ==========
  // Enable drag and drop
  gantt.config.drag_move = true      // 允许拖动移动
  gantt.config.drag_resize = true    // 允许拖动调整大小
  gantt.config.drag_progress = false // 禁用进度拖动
  gantt.config.drag_links = true     // 允许创建链接
  
  // Allow dragging for all tasks
  gantt.config.drag_mode = {
    move: "move",
    resize: "resize",
    progress: "progress",
    ignore: "ignore"
  }
  
  // Round to nearest hour when dragging
  gantt.config.round_dnd_dates = true
  gantt.config.time_step = 60 // 60 minutes
  
  // Column resizing
  gantt.config.grid_resize = true
  
  // M3 Style row heights
  gantt.config.row_height = 44
  gantt.config.bar_height = 28
  gantt.config.scale_height = 56
  
  gantt.config.smart_rendering = true
  gantt.config.show_progress = true
  gantt.config.open_tree_initially = true
  
  // Auto scheduling disabled - allow manual adjustments
  gantt.config.auto_scheduling = false
  
  // ========== 外观样式 ==========
  // M3 Task colors - 区分计划订单、生产订单和切换工序
  gantt.templates.task_class = (start, end, task) => {
    const classes = ['m3-task']
    
    // 检查是否是切换工序 (changeover/setup)
    if (task.task_type === 'changeover' || task.status === 'changeover') {
      classes.push('m3-changeover')
      return classes.join(' ')
    }
    
    // 检查是否是生产订单 (通过任务文本前缀判断，或检查父任务，或order_type字段)
    let isProduction = task.order_type === 'production' || (task.text && task.text.startsWith('[生产]'))
    
    // 如果是子任务，检查父任务是否是生产订单
    if (!isProduction && task.parent) {
      try {
        const parentTask = gantt.getTask(task.parent)
        if (parentTask && (parentTask.order_type === 'production' || (parentTask.text && parentTask.text.startsWith('[生产]')))) {
          isProduction = true
        }
      } catch (e) {
        // Parent task not found
      }
    }
    
    if (isProduction) {
      classes.push('m3-production')
    }
    
    if (task.type === 'project' || task.$level === 0) {
      classes.push('m3-project')
      if (isProduction) {
        classes.push('m3-production-project')
      }
    } else if (task.status === 'completed') {
      classes.push('m3-completed')
    } else if (task.status === 'in_progress') {
      classes.push('m3-inprogress')
    } else if (task.status === 'pending') {
      classes.push('m3-pending')
    } else {
      classes.push(isProduction ? 'm3-production-scheduled' : 'm3-scheduled')
    }
    return classes.join(' ')
  }
  
  gantt.templates.task_text = (start, end, task) => {
    return task.text
  }
  
  // Grid row class for highlighting
  gantt.templates.grid_row_class = (start, end, task) => {
    if (task.$level === 0) return 'gantt-group-row'
    return ''
  }
  
  // 甘特图 tooltip 中开始/结束格式：日期 + 时间
  const tooltipDateTimeFormat = (d) => {
    const date = d instanceof Date ? d : new Date(d)
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const h = String(date.getHours()).padStart(2, '0')
    const min = String(date.getMinutes()).padStart(2, '0')
    return `${y}-${m}-${day} ${h}:${min}`
  }

  // Tooltip with more details
  gantt.templates.tooltip_text = (start, end, task) => {
    const duration = ((end - start) / (1000 * 60 * 60)).toFixed(1)
    const isProduction = task.order_type === 'production' || (task.text && task.text.startsWith('[生产]'))
    const isChangeover = task.task_type === 'changeover' || task.status === 'changeover'
    
    let orderTypeLabel = isProduction ? '生产订单' : '计划订单'
    if (isChangeover) {
      orderTypeLabel = '切换准备'
    }
    
    let tagClass = isProduction ? 'production-tag' : 'planned-tag'
    if (isChangeover) {
      tagClass = 'changeover-tag'
    }
    
    let html = `<div class="gantt-tooltip-content">
      <div class="tooltip-title">${task.text}</div>
      <div class="tooltip-row"><span>类型:</span> <span class="${tagClass}">${orderTypeLabel}</span></div>
      <div class="tooltip-row"><span>开始:</span> ${tooltipDateTimeFormat(start)}</div>
      <div class="tooltip-row"><span>结束:</span> ${tooltipDateTimeFormat(end)}</div>
      <div class="tooltip-row"><span>时长:</span> ${duration} 小时</div>`
    
    if (isChangeover) {
      html += `<div class="tooltip-row" style="color: #F59E0B; font-size: 12px; margin-top: 8px;">
        ⚙️ 产品切换准备时间（来自切换矩阵配置）
      </div>`
    } else if (task.changeover_time && task.changeover_time > 0) {
      html += `<div class="tooltip-row"><span>切换时间:</span> ${task.changeover_time.toFixed(1)} 小时</div>`
    }
    
    if (task.status && !isChangeover) {
      const statusLabels = {
        pending: '待排程',
        scheduled: '已排程',
        in_progress: '进行中',
        completed: '已完成'
      }
      html += `<div class="tooltip-row"><span>状态:</span> ${statusLabels[task.status] || task.status}</div>`
    }
    
    if (isProduction && !isChangeover) {
      html += `<div class="tooltip-row" style="color: #9aa0a6; font-size: 12px; margin-top: 8px;">生产订单已锁定，不可调整</div>`
    }
    html += '</div>'
    return html
  }
  
  // ========== 事件处理 ==========
  // Before drag - check if task can be dragged
  gantt.attachEvent("onBeforeTaskDrag", (id, mode, e) => {
    const task = gantt.getTask(id)
    // Only allow dragging operation tasks (not project/parent tasks)
    if (task.type === 'project' || task.$level === 0) {
      return false
    }
    
    // 切换工序（dummy product）不允许拖拽
    if (task.task_type === 'changeover' || task.status === 'changeover') {
      return false
    }
    
    // 检查父任务是否是生产订单 - 生产订单不允许拖拽
    if (task.parent) {
      const parentTask = gantt.getTask(task.parent)
      if (parentTask && (parentTask.order_type === 'production' || (parentTask.text && parentTask.text.startsWith('[生产]')))) {
        return false // 生产订单的工序不允许拖拽
      }
    }
    
    // 检查当前任务是否属于生产订单
    if (task.order_type === 'production' || (task.text && (task.text.startsWith('[生产]') || task.is_production))) {
      return false
    }
    
    return true
  })
  
  // After drag - emit update event
  gantt.attachEvent("onAfterTaskDrag", (id, mode, e) => {
    const task = gantt.getTask(id)
    if (task.operation_id) {
      emit('task-updated', {
        operationId: task.operation_id,
        newStart: task.start_date,
        newEnd: task.end_date,
        resourceId: task.resource_id,
        mode: mode // 'move' or 'resize'
      })
    }
  })

  // ========== 联动拖拽逻辑（支持策略配置）==========
  // 当拖动一个任务时，根据策略同步移动该订单的关联任务
  gantt.attachEvent("onTaskDrag", (id, mode, task, original) => {
    if (mode === "move") {
      const diff = task.start_date.getTime() - original.start_date.getTime()
      if (diff === 0) return

      // 找到同一个订单的所有后续任务
      const orderId = task.order_id
      if (!orderId) return

      const allTasks = gantt.getTaskByTime()
      
      // 根据策略决定联动逻辑
      const strategy = props.strategy
      
      allTasks.forEach(t => {
        // 属于同一个订单
        if (t.order_id === orderId && t.id !== id) {
          // 策略联动规则
          let shouldMove = false
          
          // 所有策略都需要保持工序关系：后续工序跟随移动
          if (t.sequence > task.sequence) {
            shouldMove = true
          }
          
          // 如果是 EDD (最早交期) 策略，检查是否会影响交期
          if (strategy === 'EDD' && shouldMove) {
            // EDD 策略下移动后续工序
            shouldMove = true
          }
          
          // 如果是 FIFO 策略，保持先进先出顺序
          if (strategy === 'FIFO' && shouldMove) {
            shouldMove = true
          }
          
          if (shouldMove) {
            t.start_date = new Date(t.start_date.getTime() + diff)
            t.end_date = new Date(t.end_date.getTime() + diff)
            gantt.updateTask(t.id)
          }
        }
      })
      
      // 检测资源冲突
      detectResourceConflicts(task)
    }
  })
  
  // 资源冲突检测函数
  const detectResourceConflicts = (task) => {
    if (!task.resource_id) return
    
    const allTasks = gantt.getTaskByTime()
    const conflicts = []
    
    allTasks.forEach(t => {
      if (t.id !== task.id && t.resource_id === task.resource_id) {
        // 检查时间重叠
        if (task.start_date < t.end_date && task.end_date > t.start_date) {
          conflicts.push(t)
        }
      }
    })
    
    if (conflicts.length > 0) {
      // 标记冲突任务（可通过 CSS 类实现视觉提示）
      task._conflict = true
    } else {
      task._conflict = false
    }
  }
  
  // Task click
  gantt.attachEvent("onTaskClick", (id, e) => {
    const task = gantt.getTask(id)
    emit('task-clicked', task)
    return true
  })
  
  // Double click to edit
  gantt.attachEvent("onTaskDblClick", (id, e) => {
    const task = gantt.getTask(id)
    if (task.operation_id) {
      emit('task-clicked', task)
    }
    return false // Prevent default lightbox
  })
  
  // Link added
  gantt.attachEvent("onLinkAdd", (id, link) => {
    emit('link-added', link)
    return false // Prevent default - let backend handle
  })
  
  // Initialize
  gantt.init(ganttContainer.value)
  isInitialized = true
  loadData()
}

const loadData = () => {
  if (!isInitialized) return
  
  gantt.clearAll()
  
  if (props.tasks && props.tasks.data && props.tasks.data.length > 0) {
    const tasks = props.tasks.data.map(task => ({
      ...task,
      id: task.id,
      text: task.text,
      start_date: task.start_date,
      end_date: task.end_date,
      parent: task.parent || 0,
      progress: task.progress || 0,
      open: true,
      color: task.color,
      // Mark project/parent tasks
      type: task.type || (task.parent === null || task.parent === undefined || task.parent === 0 ? 'project' : 'task')
    }))
    
    const links = props.tasks.links.map(link => ({
      id: link.id,
      source: link.source,
      target: link.target,
      type: link.type || "0"
    }))
    
    gantt.parse({ data: tasks, links: links })
    
    if (tasks.length > 0) {
      const startDates = tasks.filter(t => t.start_date).map(t => new Date(t.start_date))
      const endDates = tasks.filter(t => t.end_date).map(t => new Date(t.end_date))
      
      if (startDates.length > 0) {
        const minDate = new Date(Math.min(...startDates))
        const maxDate = new Date(Math.max(...endDates))
        
        minDate.setDate(minDate.getDate() - 1)
        maxDate.setDate(maxDate.getDate() + 2)
        
        gantt.config.start_date = minDate
        gantt.config.end_date = maxDate
        gantt.render()
      }
    }
  }
}

// Watch for data changes
watch(() => props.tasks, () => {
  nextTick(() => {
    loadData()
  })
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    initGantt()
  })
})

onUnmounted(() => {
  if (isInitialized) {
    gantt.clearAll()
  }
})

// Expose methods
defineExpose({
  refresh: loadData,
  zoomIn,
  zoomOut,
  setZoom: (level) => {
    if (level >= 0 && level < zoomLevels.value.length) {
      currentZoom.value = level
      applyZoom()
    }
  }
})
</script>

<style scoped>
.gantt-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.gantt-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e3e5e8;
}

.zoom-controls {
  display: flex;
  align-items: center;
}

.toolbar-info {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .el-tag {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    font-size: 13px;
    color: #444746;
  }
  
  .legend-box {
    display: inline-block;
    width: 14px;
    height: 14px;
    border-radius: 4px;
    margin-right: 6px;
  }
  
  .legend-box.planned {
    background: #1a73e8;
  }
  
  .legend-box.production {
    background: #6B7280;
  }
  
  .legend-box.changeover {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
    border: 1px dashed #92400E;
  }
}

.gantt-chart {
  flex: 1;
  width: 100%;
  min-height: 450px;
}
</style>

<style>
/* Material 3 Task Colors */
.m3-task .gantt_task_line {
  cursor: move !important;
}

.m3-completed .gantt_task_line {
  background: #1e8e3e !important;
  border: none !important;
  border-radius: 8px !important;
}

.m3-inprogress .gantt_task_line {
  background: #f9ab00 !important;
  border: none !important;
  border-radius: 8px !important;
}

.m3-pending .gantt_task_line {
  background: #9aa0a6 !important;
  border: none !important;
  border-radius: 8px !important;
}

.m3-scheduled .gantt_task_line {
  background: #1a73e8 !important;
  border: none !important;
  border-radius: 8px !important;
}

/* 计划订单项目头 - 蓝色 */
.m3-project .gantt_task_line,
.gantt_task_line.gantt_project {
  background: #4285f4 !important;
  border: none !important;
  border-radius: 8px !important;
}

/* 生产订单项目头 - 灰色 (覆盖上面的蓝色) */
.m3-production.m3-project .gantt_task_line,
.m3-production .gantt_task_line.gantt_project {
  background: #6B7280 !important;
}

/* ========== 切换工序样式 (Changeover/Setup - Dummy Product) ========== */
.m3-changeover .gantt_task_line {
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
  border: 2px dashed #92400E !important;
  border-radius: 6px !important;
  box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3) !important;
}

.m3-changeover .gantt_task_content {
  font-style: italic !important;
  font-size: 11px !important;
}

.m3-changeover .gantt_task_line:hover {
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4) !important;
}

/* 切换工序不允许拖动 */
.m3-changeover .gantt_task_line {
  cursor: default !important;
}

.m3-changeover .gantt_task_drag {
  display: none !important;
}

/* Drag handles */
.gantt_task_drag {
  cursor: ew-resize !important;
}

.gantt_task_line:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
}

/* M3 Gantt base styling */
.gantt_container {
  font-family: 'Roboto', 'Google Sans', sans-serif !important;
  border: none !important;
}

.gantt_grid_scale .gantt_grid_head_cell,
.gantt_task_scale .gantt_scale_cell {
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #444746 !important;
  background: #f1f3f4 !important;
}

.gantt_tree_content {
  font-size: 14px !important;
  font-weight: 400 !important;
}

.gantt_task_content {
  font-size: 12px !important;
  color: #fff !important;
  font-weight: 500 !important;
}

.gantt_task_progress {
  background: rgba(255, 255, 255, 0.35) !important;
  border-radius: 8px !important;
}

/* Group row styling */
.gantt-group-row {
  background: #f8fafd !important;
  font-weight: 500 !important;
}

/* Resize handles visibility */
.gantt_task_line .gantt_task_drag {
  visibility: visible !important;
  width: 8px !important;
}

/* Link styling */
.gantt_link_line_left,
.gantt_link_line_right {
  box-sizing: border-box;
}

.gantt_task_link .gantt_line_wrapper div {
  background-color: #1a73e8 !important;
}

.gantt_link_arrow {
  border-color: #1a73e8 !important;
}

/* M3 tooltip style */
.gantt_tooltip {
  background: #1f1f1f !important;
  color: #fff !important;
  border-radius: 12px !important;
  padding: 0 !important;
  box-shadow: 0 4px 8px 3px rgba(0, 0, 0, 0.15), 0 1px 3px rgba(0, 0, 0, 0.3) !important;
  border: none !important;
  max-width: 300px;
}

.gantt-tooltip-content {
  padding: 12px 16px;
}

.gantt-tooltip-content .tooltip-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  border-bottom: 1px solid #444;
  padding-bottom: 8px;
}

.gantt-tooltip-content .tooltip-row {
  font-size: 13px;
  margin: 4px 0;
  display: flex;
  gap: 8px;
}

.gantt-tooltip-content .tooltip-row span {
  color: #9aa0a6;
  min-width: 40px;
}

/* Highlight row on hover */
.gantt_row:hover,
.gantt_task_row:hover {
  background: #f1f3f4 !important;
}

/* Selected task */
.gantt_selected .gantt_task_line {
  box-shadow: 0 0 0 2px #1a73e8 !important;
}

/* ========== 生产订单样式 (灰色系 - 已锁定) ========== */
/* 生产订单所有任务条都是灰色 */
.m3-production .gantt_task_line,
.m3-production.m3-task .gantt_task_line,
.m3-production-scheduled .gantt_task_line,
.m3-production-project .gantt_task_line {
  background: #9CA3AF !important;
  border: none !important;
  border-radius: 8px !important;
  cursor: not-allowed !important;
}

/* 生产订单项目头 - 深灰色 */
.m3-production.m3-project .gantt_task_line,
.m3-production-project .gantt_task_line,
.m3-production .gantt_task_line.gantt_project {
  background: #6B7280 !important;
}

/* 生产订单工序 - 隐藏拖拽手柄 */
.m3-production .gantt_task_drag,
.m3-production-scheduled .gantt_task_drag,
.m3-production-project .gantt_task_drag {
  display: none !important;
}

/* 生产订单悬停效果 - 不显示可拖拽的阴影 */
.m3-production .gantt_task_line:hover,
.m3-production-scheduled .gantt_task_line:hover,
.m3-production-project .gantt_task_line:hover {
  box-shadow: none !important;
  cursor: not-allowed !important;
}

/* 生产订单选中效果 */
.m3-production.gantt_selected .gantt_task_line,
.m3-production-scheduled.gantt_selected .gantt_task_line {
  box-shadow: 0 0 0 2px #6B7280 !important;
}

/* Tooltip中的订单类型标签 */
.gantt-tooltip-content .planned-tag {
  color: #1a73e8;
  font-weight: 500;
}

.gantt-tooltip-content .changeover-tag {
  color: #F59E0B;
  font-weight: 500;
}

.gantt-tooltip-content .production-tag {
  color: #6B7280;
  font-weight: 500;
}
</style>

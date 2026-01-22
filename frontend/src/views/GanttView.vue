<template>
  <div class="gantt-view">
    <div class="page-header">
      <h1>
        <el-icon><DataLine /></el-icon>
        订单排程甘特图
      </h1>
      <div class="header-actions">
        <el-button-group class="schedule-direction">
          <el-button 
            :type="schedulingOptions.direction === 'forward' ? 'primary' : 'default'"
            @click="schedulingOptions.direction = 'forward'"
          >
            正向排程
          </el-button>
          <el-button 
            :type="schedulingOptions.direction === 'backward' ? 'primary' : 'default'"
            @click="schedulingOptions.direction = 'backward'"
          >
            逆向排程
          </el-button>
        </el-button-group>
        
        <el-select v-model="schedulingOptions.priorityRule" style="width: 140px;">
          <el-option label="最早交期(EDD)" value="EDD" />
          <el-option label="最短时间(SPT)" value="SPT" />
          <el-option label="先进先出(FIFO)" value="FIFO" />
          <el-option label="按优先级" value="PRIORITY" />
        </el-select>
        
        <el-checkbox v-model="schedulingOptions.considerCapacity" border>
          有限产能
        </el-checkbox>
        
        <el-button type="primary" @click="handleSchedule" :loading="loading">
          <el-icon><VideoPlay /></el-icon>
          执行排程
        </el-button>
        
        <el-button @click="handleClear" :loading="loading">
          <el-icon><Delete /></el-icon>
          清除排程
        </el-button>
        
        <el-button @click="handleValidate">
          <el-icon><Check /></el-icon>
          验证约束
        </el-button>
      </div>
    </div>
    
    <!-- Conflicts Alert -->
    <el-alert 
      v-if="conflicts.length > 0"
      :title="`发现 ${conflicts.length} 个约束问题`"
      type="warning"
      show-icon
      :closable="true"
      style="margin-bottom: 16px;"
    >
      <template #default>
        <ul style="margin: 8px 0 0 0; padding-left: 20px;">
          <li v-for="(conflict, index) in conflicts.slice(0, 3)" :key="index">
            {{ conflict.message }}
          </li>
          <li v-if="conflicts.length > 3">...还有 {{ conflicts.length - 3 }} 个问题</li>
        </ul>
      </template>
    </el-alert>
    
    <!-- Gantt Chart Container -->
    <el-card class="gantt-card">
      <!-- Order Type Filter -->
      <template #header>
        <div class="gantt-filter">
          <span class="filter-label">显示订单:</span>
          <el-checkbox-group v-model="orderTypeFilter" @change="handleFilterChange">
            <el-checkbox label="planned">
              <span class="filter-checkbox">
                <span class="legend-dot planned"></span>
                计划订单(可调整)
              </span>
            </el-checkbox>
            <el-checkbox label="production">
              <span class="filter-checkbox">
                <span class="legend-dot production"></span>
                生产订单(已锁定)
              </span>
            </el-checkbox>
          </el-checkbox-group>
        </div>
      </template>
      
      <GanttChart 
        ref="ganttRef"
        :tasks="filteredGanttData"
        view-type="order"
        @task-updated="handleTaskUpdated"
        @task-clicked="handleTaskClicked"
      />
    </el-card>
    
    <!-- Task Detail Dialog -->
    <el-dialog 
      v-model="taskDialogVisible" 
      title="工序详情"
      width="520px"
    >
      <el-descriptions v-if="selectedTask" :column="1" border>
        <el-descriptions-item label="任务名称">{{ selectedTask.text }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ selectedTask.start_date }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ selectedTask.end_date }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedTask.status)">
            {{ getStatusLabel(selectedTask.status) }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
      
      <div v-if="selectedTask && selectedTask.operation_id && !isProductionTask(selectedTask)" class="manual-adjust-section">
        <el-divider>手工调整排程</el-divider>
        <el-form :model="adjustForm" label-width="100px">
          <el-form-item label="新开始时间">
            <el-date-picker 
              v-model="adjustForm.newStart" 
              type="datetime"
              placeholder="选择新的开始时间"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleManualAdjust" :loading="adjusting">
              应用调整
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <div v-if="selectedTask && isProductionTask(selectedTask)" class="production-notice">
        <el-alert type="info" :closable="false">
          生产订单已锁定，不可调整排程时间
        </el-alert>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useSchedulingStore } from '@/stores/scheduling'
import GanttChart from '@/components/GanttChart.vue'

const schedulingStore = useSchedulingStore()
const ganttRef = ref(null)

const loading = computed(() => schedulingStore.loading)
const ganttData = computed(() => schedulingStore.ganttData)
const conflicts = computed(() => schedulingStore.conflicts)

// Order type filter
const orderTypeFilter = ref(['planned', 'production'])

// Filter gantt data based on selected order types
const filteredGanttData = computed(() => {
  if (!ganttData.value || !ganttData.value.data) {
    return { data: [], links: [] }
  }
  
  // If both selected, return all
  if (orderTypeFilter.value.includes('planned') && orderTypeFilter.value.includes('production')) {
    return ganttData.value
  }
  
  // Filter tasks
  const showPlanned = orderTypeFilter.value.includes('planned')
  const showProduction = orderTypeFilter.value.includes('production')
  
  const filteredTasks = ganttData.value.data.filter(task => {
    const isProduction = task.text && task.text.startsWith('[生产]')
    const isPlanned = task.text && task.text.startsWith('[计划]')
    
    // For child tasks, check parent
    if (task.parent && !isProduction && !isPlanned) {
      const parentTask = ganttData.value.data.find(t => t.id === task.parent)
      if (parentTask) {
        const parentIsProduction = parentTask.text && parentTask.text.startsWith('[生产]')
        return parentIsProduction ? showProduction : showPlanned
      }
    }
    
    if (isProduction) return showProduction
    if (isPlanned) return showPlanned
    return true // Show tasks without prefix
  })
  
  // Filter links to only include those between visible tasks
  const visibleTaskIds = new Set(filteredTasks.map(t => t.id))
  const filteredLinks = ganttData.value.links.filter(link => 
    visibleTaskIds.has(link.source) && visibleTaskIds.has(link.target)
  )
  
  return { data: filteredTasks, links: filteredLinks }
})

const handleFilterChange = () => {
  // Ensure at least one is selected
  if (orderTypeFilter.value.length === 0) {
    orderTypeFilter.value = ['planned', 'production']
  }
}

const schedulingOptions = ref({
  direction: 'forward',
  priorityRule: 'EDD',
  considerCapacity: true
})

const taskDialogVisible = ref(false)
const selectedTask = ref(null)
const adjusting = ref(false)
const adjustForm = reactive({
  newStart: null
})

const isProductionTask = (task) => {
  if (!task) return false
  if (task.text && task.text.startsWith('[生产]')) return true
  
  // Check if parent is production
  if (task.parent && ganttData.value && ganttData.value.data) {
    const parentTask = ganttData.value.data.find(t => t.id === task.parent)
    if (parentTask && parentTask.text && parentTask.text.startsWith('[生产]')) {
      return true
    }
  }
  return false
}

const handleSchedule = async () => {
  try {
    const result = await schedulingStore.runScheduling({
      direction: schedulingOptions.value.direction,
      priorityRule: schedulingOptions.value.priorityRule,
      considerCapacity: schedulingOptions.value.considerCapacity
    })
    ElMessage.success(result.message)
  } catch (error) {
    ElMessage.error('排程失败: ' + (error.message || '未知错误'))
  }
}

const handleClear = async () => {
  try {
    await ElMessageBox.confirm('确定要清除所有排程结果吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await schedulingStore.clearScheduling()
    ElMessage.success('排程已清除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清除失败')
    }
  }
}

const handleValidate = async () => {
  try {
    const result = await schedulingStore.validateScheduling()
    if (result.total_violations === 0) {
      ElMessage.success('排程验证通过，无约束违反')
    } else {
      ElMessage.warning(`发现 ${result.errors} 个错误，${result.warnings} 个警告`)
    }
  } catch (error) {
    ElMessage.error('验证失败')
  }
}

// Handle drag & drop updates from Gantt
const handleTaskUpdated = async (data) => {
  try {
    const result = await schedulingStore.rescheduleOperation(
      data.operationId,
      data.newStart.toISOString(),
      data.resourceId
    )
    if (result.success) {
      ElMessage.success(`工序已${data.mode === 'move' ? '移动' : '调整'}`)
    } else {
      ElMessage.error(result.message)
      await schedulingStore.fetchGanttData('order')
    }
  } catch (error) {
    ElMessage.error('更新失败')
    await schedulingStore.fetchGanttData('order')
  }
}

const handleTaskClicked = (task) => {
  if (task.operation_id) {
    selectedTask.value = task
    adjustForm.newStart = task.start_date ? new Date(task.start_date) : null
    taskDialogVisible.value = true
  }
}

// Manual adjustment via dialog
const handleManualAdjust = async () => {
  if (!adjustForm.newStart || !selectedTask.value?.operation_id) {
    ElMessage.warning('请选择新的开始时间')
    return
  }
  
  adjusting.value = true
  try {
    const result = await schedulingStore.rescheduleOperation(
      selectedTask.value.operation_id,
      adjustForm.newStart.toISOString(),
      selectedTask.value.resource_id
    )
    if (result.success) {
      ElMessage.success('工序排程已调整')
      taskDialogVisible.value = false
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error('调整失败')
  } finally {
    adjusting.value = false
  }
}

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    scheduled: 'primary',
    in_progress: 'warning',
    completed: 'success'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    pending: '待排程',
    scheduled: '已排程',
    in_progress: '进行中',
    completed: '已完成'
  }
  return labels[status] || status
}

onMounted(() => {
  schedulingStore.fetchGanttData('order')
})
</script>

<style lang="scss" scoped>
.gantt-view {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  
  .schedule-direction {
    .el-button {
      min-width: 90px;
    }
  }
  
  .el-checkbox {
    margin: 0;
  }
}

.gantt-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  :deep(.el-card__header) {
    padding: 12px 16px;
    border-bottom: 1px solid #e4e7ed;
  }
  
  :deep(.el-card__body) {
    flex: 1;
    padding: 0;
    display: flex;
    overflow: hidden;
  }
}

.gantt-filter {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .filter-label {
    font-weight: 500;
    color: #606266;
  }
  
  .filter-checkbox {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  
  .legend-dot {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 3px;
    
    &.planned {
      background: #1a73e8;
    }
    
    &.production {
      background: #6B7280;
    }
  }
}

.manual-adjust-section {
  margin-top: 16px;
}

.production-notice {
  margin-top: 16px;
}
</style>

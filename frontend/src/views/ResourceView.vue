<template>
  <div class="resource-view">
    <div class="page-header">
      <h1>
        <el-icon><Grid /></el-icon>
        资源负荷视图
      </h1>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <!-- Gantt Chart Container -->
    <el-card class="gantt-card">
      <GanttChart 
        ref="ganttRef"
        :tasks="ganttData"
        view-type="resource"
        @task-updated="handleTaskUpdated"
        @task-clicked="handleTaskClicked"
      />
    </el-card>
    
    <!-- Order Operations Dialog -->
    <el-dialog 
      v-model="orderDialogVisible" 
      :title="`订单工序详情 - ${currentOrder?.order_number || ''}`"
      width="950px"
    >
      <div v-if="currentOrder" class="order-detail">
        <!-- Order Info -->
        <el-descriptions :column="4" border size="small" style="margin-bottom: 16px;">
          <el-descriptions-item label="订单号">{{ currentOrder.order_number }}</el-descriptions-item>
          <el-descriptions-item label="产品">{{ currentOrder.product?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="数量">{{ currentOrder.quantity }}</el-descriptions-item>
          <el-descriptions-item label="交货期">{{ formatDate(currentOrder.due_date) }}</el-descriptions-item>
        </el-descriptions>
        
        <!-- Operations Table -->
        <el-table 
          :data="currentOrder.operations || []" 
          size="small"
          :row-class-name="getOperationRowClass"
          highlight-current-row
        >
          <el-table-column label="工序" width="150">
            <template #default="{ row }">
              <span :class="{ 'current-op': row.id === selectedTask?.operation_id }">
                {{ row.sequence }} {{ row.name }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="资源" width="140">
            <template #default="{ row }">
              <el-tag 
                :type="row.id === selectedTask?.operation_id ? 'primary' : 'info'" 
                size="small"
                effect="plain"
              >
                {{ row.resource?.name || '未分配' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="计划开始" width="140">
            <template #default="{ row }">
              {{ row.scheduled_start ? formatDateTime(row.scheduled_start) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="计划结束" width="140">
            <template #default="{ row }">
              {{ row.scheduled_end ? formatDateTime(row.scheduled_end) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="时长(h)" width="80">
            <template #default="{ row }">
              {{ row.run_time?.toFixed(1) || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- Visual Timeline -->
        <div class="operations-timeline">
          <div class="timeline-header">工序资源分布</div>
          <div class="timeline-content">
            <div 
              v-for="op in currentOrder.operations" 
              :key="op.id"
              class="timeline-item"
              :class="{ 'is-current': op.id === selectedTask?.operation_id }"
            >
              <div class="op-seq">{{ op.sequence }}</div>
              <div class="op-info">
                <div class="op-name">{{ op.name }}</div>
                <div class="op-resource">
                  <el-icon><Monitor /></el-icon>
                  {{ op.resource?.name || '未分配' }}
                </div>
              </div>
              <div class="op-arrow" v-if="op !== currentOrder.operations[currentOrder.operations.length - 1]">
                <el-icon><Right /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="orderDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="goToGanttView">
          <el-icon><DataLine /></el-icon>
          在甘特图中查看
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useSchedulingStore } from '@/stores/scheduling'
import { ordersApi } from '@/api'
import GanttChart from '@/components/GanttChart.vue'
import dayjs from 'dayjs'

const router = useRouter()
const schedulingStore = useSchedulingStore()
const ganttRef = ref(null)

const loading = computed(() => schedulingStore.loading)
const ganttData = computed(() => schedulingStore.ganttData)

const orderDialogVisible = ref(false)
const selectedTask = ref(null)
const currentOrder = ref(null)
const loadingOrder = ref(false)

const refreshData = () => {
  schedulingStore.fetchGanttData('resource')
}

const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD') : ''
}

const formatDateTime = (date) => {
  return date ? dayjs(date).format('MM-DD HH:mm') : ''
}

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
      await schedulingStore.fetchGanttData('resource')
    }
  } catch (error) {
    ElMessage.error('更新失败')
    await schedulingStore.fetchGanttData('resource')
  }
}

const handleTaskClicked = async (task) => {
  if (task.operation_id && task.order_id) {
    selectedTask.value = task
    loadingOrder.value = true
    
    try {
      // Fetch full order details with operations
      const order = await ordersApi.getOrder(task.order_id)
      currentOrder.value = order
      orderDialogVisible.value = true
    } catch (error) {
      ElMessage.error('获取订单信息失败')
    } finally {
      loadingOrder.value = false
    }
  }
}

const getOperationRowClass = ({ row }) => {
  if (row.id === selectedTask.value?.operation_id) {
    return 'current-operation-row'
  }
  return ''
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

const goToGanttView = () => {
  orderDialogVisible.value = false
  router.push('/gantt')
}

onMounted(() => {
  schedulingStore.fetchGanttData('resource')
})
</script>

<style lang="scss" scoped>
.resource-view {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.gantt-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  :deep(.el-card__body) {
    flex: 1;
    padding: 0;
    display: flex;
    overflow: hidden;
  }
}

.order-detail {
  .current-op {
    font-weight: 600;
    color: #1a73e8;
  }
}

// Current operation row highlight
:deep(.current-operation-row) {
  background-color: #e8f4fd !important;
  
  td {
    background-color: #e8f4fd !important;
  }
}

// Operations Timeline
.operations-timeline {
  margin-top: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  
  .timeline-header {
    background: #f5f7fa;
    padding: 10px 16px;
    font-weight: 500;
    color: #606266;
    border-bottom: 1px solid #e4e7ed;
  }
  
  .timeline-content {
    display: flex;
    align-items: center;
    padding: 16px;
    overflow-x: auto;
    gap: 8px;
  }
  
  .timeline-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: #f5f7fa;
    border-radius: 8px;
    border: 2px solid transparent;
    min-width: 160px;
    transition: all 0.2s;
    
    &.is-current {
      background: #e8f4fd;
      border-color: #1a73e8;
      
      .op-seq {
        background: #1a73e8;
        color: #fff;
      }
    }
    
    .op-seq {
      width: 32px;
      height: 32px;
      background: #909399;
      color: #fff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      font-size: 12px;
      flex-shrink: 0;
    }
    
    .op-info {
      flex: 1;
      min-width: 0;
      
      .op-name {
        font-weight: 500;
        font-size: 13px;
        color: #303133;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .op-resource {
        font-size: 12px;
        color: #909399;
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 4px;
        
        .el-icon {
          font-size: 14px;
        }
      }
    }
    
    .op-arrow {
      color: #c0c4cc;
      font-size: 18px;
      margin-left: 8px;
    }
  }
}
</style>

<template>
  <div class="ds-resource-view">
    <!-- 筛选状态提示 -->
    <div v-if="dsFiltersStore.selectedResourceIds.length > 0" class="filter-hint">
      <el-icon><Filter /></el-icon>
      <span>已关联"详细计划表"筛选条件，显示 {{ resourceList.length }} 个资源</span>
      <el-tag v-for="name in dsFiltersStore.selectedResourceNames.slice(0, 3)" :key="name" size="small" type="info" class="filter-tag">
        {{ name }}
      </el-tag>
      <span v-if="dsFiltersStore.selectedResourceNames.length > 3" class="more-hint">
        等 {{ dsFiltersStore.selectedResourceNames.length }} 个资源
      </span>
      <el-button type="primary" link size="small" @click="goToDetailedPlan">修改筛选</el-button>
    </div>
    
    <!-- 顶部功能按钮栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button @click="handleDefineShift">定义班次</el-button>
        <el-button @click="handleDefineShiftOrder">定义班次顺序</el-button>
      </div>
    </div>
    
    <!-- 数据表格 -->
    <div class="table-container">
      <el-table
        ref="tableRef"
        :data="resourceList"
        v-loading="loading"
        border
        size="small"
        class="ds-resource-table"
        @selection-change="handleSelectionChange"
      >
        <!-- 复选框列 -->
        <el-table-column type="selection" width="40" align="center" />
        
        <!-- 资源 -->
        <el-table-column prop="code" label="资源" min-width="160" />
        
        <!-- 资源名称 -->
        <el-table-column prop="name" label="资源名称" min-width="120" />
        
        <!-- 位置 -->
        <el-table-column prop="location" label="位置" min-width="80" align="center" />
        
        <!-- 开始 -->
        <el-table-column prop="start_time" label="开始" min-width="90" align="center" />
        
        <!-- 结束 -->
        <el-table-column prop="end_time" label="结束" min-width="90" align="center" />
        
        <!-- 休息期间 -->
        <el-table-column prop="break_time" label="休息期间" min-width="90" align="center" />
        
        <!-- 利用率百分比 -->
        <el-table-column prop="utilization_percent" label="利用率百分比" min-width="100" align="right">
          <template #default="{ row }">
            {{ row.utilization_percent.toFixed(3) }}
          </template>
        </el-table-column>
        
        <!-- 生产时间/小时 -->
        <el-table-column prop="production_hours" label="生产时间/小时" min-width="110" align="right">
          <template #default="{ row }">
            {{ row.production_hours.toFixed(2) }}
          </template>
        </el-table-column>
        
        <!-- 容量 -->
        <el-table-column prop="capacity" label="容量" min-width="80" align="right">
          <template #default="{ row }">
            {{ row.capacity !== null && row.capacity !== undefined && row.capacity !== '' ? row.capacity.toFixed(3) : '' }}
          </template>
        </el-table-column>
        
        <!-- 有限计划 -->
        <el-table-column prop="finite_planning" label="有限计划" min-width="80" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row.finite_planning" disabled />
          </template>
        </el-table-column>
        
        <!-- 瓶颈资源 -->
        <el-table-column prop="is_bottleneck" label="瓶颈资源" min-width="80" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row.is_bottleneck" disabled />
          </template>
        </el-table-column>
        
        <!-- 资源模式 -->
        <el-table-column prop="resource_mode" label="资源模式" min-width="80" align="center">
          <template #default="{ row }">
            {{ getResourceMode(row.capacity) }}
          </template>
        </el-table-column>
        
        <!-- 时区 -->
        <el-table-column prop="timezone" label="时区" min-width="60" align="center" />
        
        <!-- 工厂日历 -->
        <el-table-column prop="factory_calendar" label="工厂日历" min-width="80" align="center" />
        
        <!-- 计划人员组 -->
        <el-table-column prop="planning_group" label="计划人员组" min-width="90" align="center" />
      </el-table>
    </div>
    
    <!-- 定义班次对话框 -->
    <el-dialog v-model="shiftDialogVisible" title="定义班次" width="600px">
      <el-form :model="shiftForm" label-width="100px">
        <el-form-item label="班次名称">
          <el-input v-model="shiftForm.name" placeholder="请输入班次名称" />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-time-picker v-model="shiftForm.start_time" placeholder="选择开始时间" format="HH:mm:ss" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-time-picker v-model="shiftForm.end_time" placeholder="选择结束时间" format="HH:mm:ss" />
        </el-form-item>
        <el-form-item label="休息时间">
          <el-time-picker v-model="shiftForm.break_time" placeholder="选择休息时间" format="HH:mm:ss" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shiftDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleShiftSave">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 定义班次顺序对话框 -->
    <el-dialog v-model="shiftOrderDialogVisible" title="定义班次顺序" width="600px">
      <el-form :model="shiftOrderForm" label-width="100px">
        <el-form-item label="班次顺序">
          <el-select v-model="shiftOrderForm.order" multiple placeholder="选择班次顺序" style="width: 100%">
            <el-option label="早班" value="morning" />
            <el-option label="中班" value="afternoon" />
            <el-option label="晚班" value="night" />
          </el-select>
        </el-form-item>
        <el-form-item label="循环模式">
          <el-radio-group v-model="shiftOrderForm.cycle_mode">
            <el-radio value="daily">每日</el-radio>
            <el-radio value="weekly">每周</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shiftOrderDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleShiftOrderSave">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Filter } from '@element-plus/icons-vue'
import { masterDataApi } from '@/api'
import { useDSFiltersStore } from '@/stores/dsFilters'

const router = useRouter()

// 共享筛选store
const dsFiltersStore = useDSFiltersStore()

// 加载状态
const loading = ref(false)

// 表格引用
const tableRef = ref(null)

// 资源列表数据（所有资源）
const allResourceList = ref([])

// 根据详细计划表筛选条件过滤后的资源列表
const resourceList = computed(() => {
  const selectedIds = dsFiltersStore.selectedResourceIds
  // 如果详细计划表没有选择资源，显示所有资源
  if (!selectedIds || selectedIds.length === 0) {
    return allResourceList.value
  }
  // 否则只显示选中的资源
  return allResourceList.value.filter(r => selectedIds.includes(r.id))
})

// 选中的资源
const selectedResources = ref([])

// 定义班次对话框
const shiftDialogVisible = ref(false)
const shiftForm = reactive({
  name: '',
  start_time: null,
  end_time: null,
  break_time: null
})

// 定义班次顺序对话框
const shiftOrderDialogVisible = ref(false)
const shiftOrderForm = reactive({
  order: [],
  cycle_mode: 'daily'
})

// 资源模式计算逻辑
const getResourceMode = (capacity) => {
  return (capacity === null || capacity === undefined || capacity === '') 
    ? '单一' 
    : '多重'
}

// 将 "HH:mm:ss" 或 "HH:mm" 转为从 0 点起的分钟数
const timeToMinutes = (timeStr) => {
  if (!timeStr) return 0
  const s = String(timeStr).trim()
  const parts = s.split(':').map(Number)
  const h = parts[0] || 0
  const m = parts[1] || 0
  const sec = parts[2] || 0
  return h * 60 + m + sec / 60
}

// 生产时间/小时 = 结束 - 开始 - 休息时间
const calcProductionHours = (startTime, endTime, breakTime) => {
  const startMin = timeToMinutes(startTime)
  const endMin = timeToMinutes(endTime)
  const breakMin = timeToMinutes(breakTime)
  const minutes = Math.max(0, endMin - startMin - breakMin)
  return Math.round(minutes / 60 * 100) / 100
}

// 加载资源数据
const loadResources = async () => {
  loading.value = true
  try {
    const data = await masterDataApi.getResources()
    const defaultStart = '09:00:00'
    const defaultEnd = '18:00:00'
    const defaultBreak = '00:00:00'
    allResourceList.value = data.map(resource => {
      const start_time = defaultStart
      const end_time = defaultEnd
      const break_time = defaultBreak
      const production_hours = calcProductionHours(start_time, end_time, break_time)
      return {
        id: resource.id,
        code: resource.code,
        name: resource.name,
        location: resource.work_center?.code || resource.work_center_id || '1020',
        start_time,
        end_time,
        break_time,
        utilization_percent: (resource.efficiency || 1) * 100,
        production_hours,
        capacity: getCapacityValue(resource),
        finite_planning: true,
        is_bottleneck: resource.name?.includes('CNC') || resource.name?.includes('加工') || resource.name?.includes('瓶颈') || false,
        timezone: 'CET',
        factory_calendar: resource.work_center?.code === 'CN' ? 'CN' : '01',
        planning_group: 'A'
      }
    })
  } catch (error) {
    console.error('Failed to load resources:', error)
    ElMessage.error('加载资源数据失败')
  } finally {
    loading.value = false
  }
}

// 根据资源获取容量值（模拟逻辑：部分资源有容量，部分没有）
const getCapacityValue = (resource) => {
  // 模拟：如果 capacity_per_day > 10，则认为有容量值
  if (resource.capacity_per_day && resource.capacity_per_day > 10) {
    return resource.capacity_per_day
  }
  // 模拟：如果名称包含特定关键字，设置容量
  if (resource.name?.includes('多') || resource.name?.includes('并行')) {
    return 10.0
  }
  return null
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedResources.value = selection
}

// 打开定义班次对话框
const handleDefineShift = () => {
  shiftForm.name = ''
  shiftForm.start_time = null
  shiftForm.end_time = null
  shiftForm.break_time = null
  shiftDialogVisible.value = true
}

// 保存班次定义
const handleShiftSave = () => {
  ElMessage.success('班次定义已保存')
  shiftDialogVisible.value = false
}

// 打开定义班次顺序对话框
const handleDefineShiftOrder = () => {
  shiftOrderForm.order = []
  shiftOrderForm.cycle_mode = 'daily'
  shiftOrderDialogVisible.value = true
}

// 保存班次顺序定义
const handleShiftOrderSave = () => {
  ElMessage.success('班次顺序已保存')
  shiftOrderDialogVisible.value = false
}

// 跳转到详细计划表
const goToDetailedPlan = () => {
  router.push('/ds')
}

// 初始化
onMounted(() => {
  loadResources()
})
</script>

<style lang="scss" scoped>
.ds-resource-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  background: #fff;
}

// 筛选状态提示
.filter-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #ecf5ff;
  border-bottom: 1px solid #d9ecff;
  font-size: 13px;
  color: #409eff;
  
  .el-icon {
    font-size: 16px;
  }
  
  .filter-tag {
    margin: 0 2px;
  }
  
  .more-hint {
    color: #909399;
  }
}

// 工具栏样式
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  
  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

// 表格容器
.table-container {
  flex: 1;
  padding: 0;
  overflow: auto;
}

// DS资源表格样式 - 参照附件图片风格
.ds-resource-table {
  width: 100%;
  
  // 表头样式
  :deep(.el-table__header-wrapper) {
    th.el-table__cell {
      background-color: #f5f5f5 !important;
      color: #333;
      font-weight: 500;
      font-size: 12px;
      padding: 8px 0;
      border-bottom: 1px solid #dcdcdc;
      border-right: 1px solid #dcdcdc;
      
      .cell {
        padding: 0 8px;
        line-height: 1.4;
      }
    }
  }
  
  // 行样式
  :deep(.el-table__body-wrapper) {
    tr.el-table__row {
      background-color: #fff;
      
      &:hover > td.el-table__cell {
        background-color: #f5f7fa !important;
      }
      
      td.el-table__cell {
        padding: 6px 0;
        font-size: 12px;
        color: #333;
        border-bottom: 1px solid #e8e8e8;
        border-right: 1px solid #e8e8e8;
        
        .cell {
          padding: 0 8px;
          line-height: 1.4;
        }
      }
    }
  }
  
  // 边框样式
  :deep(.el-table__inner-wrapper::before) {
    display: none;
  }
  
  // checkbox 样式
  :deep(.el-checkbox) {
    .el-checkbox__inner {
      width: 14px;
      height: 14px;
    }
    
    &.is-disabled {
      .el-checkbox__inner {
        background-color: #fff;
        border-color: #dcdfe6;
        
        &::after {
          border-color: #c0c4cc;
        }
      }
      
      &.is-checked .el-checkbox__inner {
        background-color: #f5f5f5;
        border-color: #c0c4cc;
        
        &::after {
          border-color: #606266;
        }
      }
    }
  }
}
</style>

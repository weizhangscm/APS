<template>
  <div class="ds-resource-view">
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
import { ElMessage } from 'element-plus'
import { useMasterDataStore } from '@/stores/masterData'
import { useDSFiltersStore } from '@/stores/dsFilters'

// 主数据store
const store = useMasterDataStore()

// 共享筛选store
const dsFiltersStore = useDSFiltersStore()

// 加载状态
const loading = ref(false)

// 表格引用
const tableRef = ref(null)

// 资源列表数据（全部数据，DS资源是数据源）
const resourceList = ref([])

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

// 加载资源数据
const loadResources = async () => {
  loading.value = true
  try {
    // 通过store获取数据
    await store.fetchResources()
    const data = store.resources
    // 将后端数据映射为界面字段
    const mappedData = (data || []).map(resource => ({
      id: resource.id,
      code: resource.code,
      name: resource.name,
      location: resource.work_center?.code || resource.work_center_id || '1020',
      start_time: '09:00:00',
      end_time: '18:00:00',
      break_time: '00:00:00',
      utilization_percent: (resource.efficiency || 1) * 100,
      production_hours: resource.capacity_per_day || 9,
      capacity: getCapacityValue(resource),
      finite_planning: true,
      is_bottleneck: resource.name?.includes('CNC') || resource.name?.includes('加工') || resource.name?.includes('瓶颈') || false,
      timezone: 'CET',
      factory_calendar: resource.work_center?.code === 'CN' ? 'CN' : '01',
      planning_group: 'A'
    }))
    resourceList.value = mappedData
    // 同步到共享store，供详细计划表使用
    dsFiltersStore.setDSResources(mappedData)
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

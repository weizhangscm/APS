<template>
  <div class="ds-view">
    <!-- 工具栏第一行 - 筛选器区域 -->
    <div class="toolbar toolbar-filters">
      <div class="filter-group">
        <label class="filter-label">
          显示区间:<span class="required">*</span>
        </label>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :shortcuts="dateShortcuts"
          format="YYYY.MM.DD"
          value-format="YYYY-MM-DD"
          style="width: 280px"
          :prefix-icon="Calendar"
        />
      </div>
      
      <div class="filter-group">
        <label class="filter-label">资源名称:</label>
        <el-select
          v-model="selectedResources"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择资源"
          style="width: 220px"
          @change="handleResourceChange"
        >
          <template #header>
            <div class="select-header-options">
              <el-checkbox
                v-model="allResourcesSelected"
                :indeterminate="resourcesIndeterminate"
                @change="handleSelectAllResources"
              >
                全选
              </el-checkbox>
              <el-checkbox
                v-model="bottleneckOnly"
                @change="handleBottleneckChange"
              >
                瓶颈
              </el-checkbox>
            </div>
          </template>
          <el-option
            v-for="resource in filteredResourceOptions"
            :key="resource.id"
            :label="resource.name"
            :value="resource.id"
          />
        </el-select>
      </div>
      
      <div class="filter-group">
        <label class="filter-label">产品:</label>
        <el-select
          v-model="selectedProducts"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择产品"
          style="width: 220px"
          @change="handleProductChange"
        >
          <template #header>
            <el-checkbox
              v-model="allProductsSelected"
              :indeterminate="productsIndeterminate"
              @change="handleSelectAllProducts"
            >
              全选
            </el-checkbox>
          </template>
          <el-option
            v-for="product in productOptions"
            :key="product.id"
            :label="product.name"
            :value="product.id"
          />
        </el-select>
      </div>
    </div>
    
    <!-- 工具栏第二行 - 操作控制区域 -->
    <div class="toolbar toolbar-actions">
      <!-- 左侧 - 图表选择 -->
      <div class="toolbar-left">
        <span class="section-label">选择图表</span>
        <el-select
          v-model="selectedCharts"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择图表"
          style="width: 200px"
        >
          <el-option
            v-for="chart in chartOptions"
            :key="chart.value"
            :label="chart.label"
            :value="chart.value"
          />
        </el-select>
      </div>
      
      <!-- 中央 - 操作按钮 -->
      <div class="toolbar-center">
        <!-- 缩放控制 -->
        <el-button-group class="zoom-controls">
          <el-button :icon="ZoomIn" @click="handleZoomIn" title="放大" />
          <el-button :icon="ZoomOut" @click="handleZoomOut" title="缩小" />
        </el-button-group>
        <el-select v-model="currentZoom" style="width: 100px; margin-right: 8px;" @change="handleZoomChange">
          <el-option label="小时" :value="0" />
          <el-option label="4小时" :value="1" />
          <el-option label="天" :value="2" />
          <el-option label="周" :value="3" />
          <el-option label="月" :value="4" />
        </el-select>
        
        <!-- 刷新按钮 -->
        <el-button :icon="Refresh" @click="handleRefresh">刷新</el-button>
        
        <!-- 警报按钮 -->
        <el-dropdown trigger="click" @command="handleAlertCommand">
          <el-button class="btn-outline">
            <el-icon><WarningFilled /></el-icon>
            警报
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="order-delay">订单延误</el-dropdown-item>
              <el-dropdown-item command="material-shortage">物料短缺</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <!-- 策略按钮 -->
        <el-button @click="strategyDialogVisible = true">策略</el-button>
        
        <!-- 取消计划按钮 -->
        <el-button class="btn-outline" @click="handleCancelPlan" :loading="cancellingPlan">
          取消计划
        </el-button>
        
        <!-- 重新计划按钮 -->
        <el-button class="btn-outline" @click="handleReplan" :loading="replanning">
          重新计划
        </el-button>
        
        <!-- 自动计划按钮 -->
        <el-dropdown trigger="click" @command="handleAutoPlanCommand">
          <el-button class="btn-outline">
            自动计划
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="heuristic">启发式</el-dropdown-item>
              <el-dropdown-item command="optimizer">优化器</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <!-- 丢弃计划按钮 - 仅在有未保存更改时显示 -->
        <el-button 
          v-if="hasUnsavedChanges" 
          type="warning" 
          @click="handleDiscardPlan" 
          :loading="discardingPlan"
        >
          丢弃计划
        </el-button>
        
        <!-- 保存计划按钮 -->
        <el-button 
          type="primary" 
          @click="handleSavePlan" 
          :loading="savingPlan"
          :class="{ 'btn-highlight': hasUnsavedChanges }"
        >
          {{ hasUnsavedChanges ? '保存计划 *' : '保存计划' }}
        </el-button>
        
      </div>
      
      <!-- 图例 - 靠右显示 -->
      <div class="toolbar-right">
        <div class="legend-group">
          <span class="legend-item">
            <span class="legend-box planned"></span>计划订单
          </span>
          <span class="legend-item">
            <span class="legend-box production"></span>生产订单
          </span>
          <span class="legend-item">
            <span class="legend-box changeover"></span>切换准备
          </span>
        </div>
      </div>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-container">
      <!-- 资源图表 -->
      <div v-show="selectedCharts.includes('resource')" class="chart-panel">
        <div class="chart-header">
          <span class="chart-title">
            <a href="javascript:;">资源</a> ({{ resourceCount }})
          </span>
        </div>
        <div class="chart-content">
          <SimpleGanttTable
            ref="resourceGanttRef"
            :tasks="resourceGanttData"
            :date-range="dateRange"
            :zoom-level="currentZoom"
          />
        </div>
      </div>
      
      <!-- 分隔条 -->
      <div 
        v-if="selectedCharts.includes('resource') && (selectedCharts.includes('product') || selectedCharts.includes('utilization'))"
        class="chart-resizer"
      >
        <div class="resizer-handle"></div>
      </div>
      
      <!-- 产品图表 - 使用自定义组件避免 dhtmlx-gantt 单例冲突 -->
      <div v-show="selectedCharts.includes('product')" class="chart-panel">
        <div class="chart-header">
          <span class="chart-title">
            <a href="javascript:;">产品</a> ({{ productCount }})
          </span>
        </div>
        <div class="chart-content">
          <SimpleProductTable
            ref="productGanttRef"
            :tasks="productGanttData"
            :date-range="dateRange"
            :zoom-level="currentZoom"
          />
        </div>
      </div>
      
      <!-- 分隔条 -->
      <div 
        v-if="selectedCharts.includes('product') && selectedCharts.includes('utilization')"
        class="chart-resizer"
      >
        <div class="resizer-handle"></div>
      </div>
      
      <!-- 资源利用图表 -->
      <div v-show="selectedCharts.includes('utilization')" class="chart-panel">
        <div class="chart-header">
          <span class="chart-title">
            <a href="javascript:;">资源利用率</a> ({{ utilizationCount }})
          </span>
        </div>
        <div class="chart-content">
          <UtilizationChart
            ref="utilizationChartRef"
            :data="utilizationData"
            :date-range="dateRange"
            :zoom-level="currentZoom"
          />
        </div>
      </div>
    </div>
    
    <!-- 策略配置对话框 -->
    <el-dialog v-model="strategyDialogVisible" title="策略配置" width="600px">
      <el-form :model="strategyForm" label-width="140px">
        <el-form-item label="排序规则">
          <el-select v-model="strategyForm.sortingRule" style="width: 100%">
            <el-option value="订单优先级" label="订单优先级" />
          </el-select>
          <div class="form-item-hint">决定订单的排程顺序，优先级高的订单先排程</div>
        </el-form-item>
        <el-form-item label="计划模式">
          <el-select v-model="strategyForm.planningMode" style="width: 100%">
            <el-option value="查找槽位" label="查找槽位" />
          </el-select>
          <div class="form-item-hint">在资源的现有排程中搜索足够大的空闲时间段（有限产能）</div>
        </el-form-item>
        <el-form-item label="计划方向">
          <el-select v-model="strategyForm.planningDirection" style="width: 100%">
            <el-option value="向前" label="向前" />
            <el-option value="向后" label="向后" />
          </el-select>
          <div class="form-item-hint">向前：从期望日期向未来搜索；向后：从交期向过去搜索</div>
        </el-form-item>
        <el-form-item label="期望日期">
          <el-select v-model="strategyForm.expectedDate" style="width: 100%">
            <el-option value="当前日期" label="当前日期" />
            <el-option value="指定日期" label="指定日期" />
          </el-select>
          <div class="form-item-hint">当前日期：使用系统当前时间；指定日期：使用订单的最早开始日期/交期</div>
        </el-form-item>
        <el-form-item label="订单内部关系">
          <el-select v-model="strategyForm.orderInternalRelation" style="width: 100%">
            <el-option value="不考虑" label="不考虑" />
            <el-option value="始终考虑" label="始终考虑" />
          </el-select>
          <div class="form-item-hint">不考虑：只排选中资源上的工序；始终考虑：自动调整订单内其他工序以维护时间关系</div>
        </el-form-item>
        <el-form-item label="子计划模式">
          <el-select v-model="strategyForm.subPlanningMode" style="width: 100%">
            <el-option value="根据调度模式调度相关操作" label="根据调度模式调度相关操作" />
            <el-option value="以无限方式调度相关操作" label="以无限方式调度相关操作" />
          </el-select>
          <div class="form-item-hint">控制关联工序的排程方式：使用相同模式（有限产能）或无限产能模式</div>
        </el-form-item>
        <el-form-item label="计划出错的操作">
          <el-select v-model="strategyForm.errorHandling" style="width: 100%">
            <el-option value="立即终止" label="立即终止" />
          </el-select>
          <div class="form-item-hint">当某工序无法排程时，立即停止整个排程操作</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="strategyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleStrategySave">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 启发式配置对话框 -->
    <el-dialog v-model="heuristicDialogVisible" title="启发式" width="400px">
      <el-form :model="heuristicForm" label-width="100px">
        <el-form-item label="选择启发式">
          <el-select v-model="heuristicForm.selected" style="width: 200px">
            <el-option value="stable_forward" label="稳定向前计划" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="heuristicDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleHeuristicExecute" :loading="autoPlanning">执行</el-button>
      </template>
    </el-dialog>
    
    <!-- 优化器配置对话框 -->
    <el-dialog v-model="optimizerDialogVisible" title="优化器配置" width="500px">
      <el-form :model="optimizerForm" label-width="120px">
        <el-form-item label="延迟成本权重">
          <el-slider v-model="optimizerForm.delayCost" :max="100" show-input />
        </el-form-item>
        <el-form-item label="库存成本权重">
          <el-slider v-model="optimizerForm.inventoryCost" :max="100" show-input />
        </el-form-item>
        <el-form-item label="切换成本权重">
          <el-slider v-model="optimizerForm.setupCost" :max="100" show-input />
        </el-form-item>
        <el-form-item label="产能利用权重">
          <el-slider v-model="optimizerForm.utilizationWeight" :max="100" show-input />
        </el-form-item>
        <el-form-item label="优化时间限制">
          <el-input-number v-model="optimizerForm.timeLimit" :min="10" :max="3600" />
          <span style="margin-left: 8px">秒</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="optimizerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleOptimizerExecute" :loading="autoPlanning">执行</el-button>
      </template>
    </el-dialog>
    
    <!-- 警报详情对话框 -->
    <el-dialog v-model="alertDialogVisible" :title="alertDialogTitle" width="800px">
      <el-table :data="alertData" style="width: 100%">
        <el-table-column prop="order_number" label="订单号" width="150" />
        <el-table-column prop="product_name" label="产品" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="row.severity === 'high' ? 'danger' : row.severity === 'medium' ? 'warning' : 'info'">
              {{ row.severity === 'high' ? '高' : row.severity === 'medium' ? '中' : '低' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Calendar,
  ArrowDown,
  WarningFilled,
  Refresh,
  ZoomIn,
  ZoomOut
} from '@element-plus/icons-vue'
import { useSchedulingStore } from '@/stores/scheduling'
import { useDSFiltersStore } from '@/stores/dsFilters'
import { masterDataApi } from '@/api'
import SimpleGanttTable from '@/components/SimpleGanttTable.vue'
import SimpleProductTable from '@/components/SimpleProductTable.vue'
import UtilizationChart from '@/components/UtilizationChart.vue'

const schedulingStore = useSchedulingStore()
const dsFiltersStore = useDSFiltersStore()

// ===== 筛选条件持久化 =====
const STORAGE_KEY = 'ds_view_filters'
const EXPIRY_DURATION = 10 * 60 * 1000 // 10分钟（毫秒）

// 保存筛选条件到 localStorage
const saveFiltersToStorage = () => {
  const filters = {
    dateRange: dateRange.value,
    selectedResources: selectedResources.value,
    selectedProducts: selectedProducts.value,
    selectedCharts: selectedCharts.value,
    currentZoom: currentZoom.value,
    bottleneckOnly: bottleneckOnly.value,
    timestamp: Date.now()
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filters))
  } catch (e) {
    console.warn('Failed to save filters to localStorage:', e)
  }
}

// 从 localStorage 加载筛选条件
const loadFiltersFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return null
    
    const filters = JSON.parse(stored)
    const now = Date.now()
    
    // 检查是否过期（10分钟）
    if (now - filters.timestamp > EXPIRY_DURATION) {
      localStorage.removeItem(STORAGE_KEY)
      return null
    }
    
    return filters
  } catch (e) {
    console.warn('Failed to load filters from localStorage:', e)
    return null
  }
}

// 清除存储的筛选条件
const clearFiltersFromStorage = () => {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (e) {
    console.warn('Failed to clear filters from localStorage:', e)
  }
}

// ===== 日期筛选 =====
const today = new Date()
const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0)

// 默认：前5天到未来一个月
const defaultStart = new Date()
defaultStart.setDate(defaultStart.getDate() - 5)
const defaultEnd = new Date()
defaultEnd.setMonth(defaultEnd.getMonth() + 1)

// 尝试从存储中恢复筛选条件
const savedFilters = loadFiltersFromStorage()

const dateRange = ref(
  savedFilters?.dateRange || [
    defaultStart.toISOString().split('T')[0],
    defaultEnd.toISOString().split('T')[0]
  ]
)

const dateShortcuts = [
  {
    text: '前5天到未来1月',
    value: () => {
      const start = new Date()
      start.setDate(start.getDate() - 5)
      const end = new Date()
      end.setMonth(end.getMonth() + 1)
      return [start, end]
    }
  },
  {
    text: '本周',
    value: () => {
      const start = new Date()
      start.setDate(start.getDate() - start.getDay())
      const end = new Date()
      end.setDate(end.getDate() + (6 - end.getDay()))
      return [start, end]
    }
  },
  {
    text: '本月',
    value: () => [startOfMonth, endOfMonth]
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 30)
      return [start, end]
    }
  }
]

// ===== 资源筛选 =====
const selectedResources = ref(savedFilters?.selectedResources || [])
const resourceOptions = ref([])  // 所有资源
const bottleneckOnly = ref(savedFilters?.bottleneckOnly ?? true)  // 是否只显示瓶颈资源，默认勾选

// 根据瓶颈筛选后的资源列表
const filteredResourceOptions = computed(() => {
  if (bottleneckOnly.value) {
    return resourceOptions.value.filter(r => r.is_bottleneck)
  }
  return resourceOptions.value
})

// 资源全选相关 - 基于筛选后的列表
const allResourcesSelected = computed(() => {
  const options = filteredResourceOptions.value
  return options.length > 0 && 
         selectedResources.value.length === options.length &&
         options.every(r => selectedResources.value.includes(r.id))
})

const resourcesIndeterminate = computed(() => {
  const options = filteredResourceOptions.value
  const selectedInOptions = options.filter(r => selectedResources.value.includes(r.id)).length
  return selectedInOptions > 0 && selectedInOptions < options.length
})

const handleSelectAllResources = (val) => {
  if (val) {
    // 全选当前筛选后的资源
    selectedResources.value = filteredResourceOptions.value.map(r => r.id)
  } else {
    // 取消选择当前筛选后的资源
    const filteredIds = new Set(filteredResourceOptions.value.map(r => r.id))
    selectedResources.value = selectedResources.value.filter(id => !filteredIds.has(id))
  }
}

// 瓶颈筛选变化时的处理
const handleBottleneckChange = (val) => {
  // 清空已选择的资源，让用户重新选择
  selectedResources.value = []
}

// ===== 产品筛选 =====
const selectedProducts = ref(savedFilters?.selectedProducts || [])
const productOptions = ref([])

// 产品全选相关
const allProductsSelected = computed(() => {
  return productOptions.value.length > 0 && 
         selectedProducts.value.length === productOptions.value.length
})

const productsIndeterminate = computed(() => {
  return selectedProducts.value.length > 0 && 
         selectedProducts.value.length < productOptions.value.length
})

const handleSelectAllProducts = (val) => {
  if (val) {
    selectedProducts.value = productOptions.value.map(p => p.id)
  } else {
    selectedProducts.value = []
  }
}

// ===== 图表选择 =====
const selectedCharts = ref(savedFilters?.selectedCharts || ['resource'])
const chartOptions = [
  { value: 'resource', label: '资源图表' },
  { value: 'product', label: '产品图表' },
  { value: 'utilization', label: '资源利用图表' }
]

// ===== 缩放控制 =====
const currentZoom = ref(savedFilters?.currentZoom ?? 1) // 默认4小时视图
const productGanttRef = ref(null)

const handleZoomIn = () => {
  if (currentZoom.value > 0) {
    currentZoom.value--
    handleZoomChange()
  }
}

const handleZoomOut = () => {
  if (currentZoom.value < 4) {
    currentZoom.value++
    handleZoomChange()
  }
}

const handleZoomChange = () => {
  // 通知产品甘特图更新缩放
  if (productGanttRef.value && productGanttRef.value.setZoom) {
    productGanttRef.value.setZoom(currentZoom.value)
  }
}

// ===== 策略 =====
const currentStrategy = ref('订单优先级')
const strategyDialogVisible = ref(false)
const strategyForm = reactive({
  sortingRule: '订单优先级',           // 排序规则
  planningMode: '查找槽位',            // 计划模式
  planningDirection: '向前',           // 计划方向
  expectedDate: '当前日期',            // 期望日期
  orderInternalRelation: '不考虑',     // 订单内部关系
  subPlanningMode: '根据调度模式调度相关操作',  // 子计划模式
  errorHandling: '立即终止'            // 计划出错的操作
})

// ===== 启发式对话框 =====
const heuristicDialogVisible = ref(false)
const heuristicForm = reactive({
  selected: 'stable_forward'  // 默认选择稳定向前计划，未来可扩展更多启发式
})

// ===== 优化器对话框 =====
const optimizerDialogVisible = ref(false)
const optimizerForm = reactive({
  delayCost: 30,
  inventoryCost: 20,
  setupCost: 25,
  utilizationWeight: 25,
  timeLimit: 60
})

// ===== 警报对话框 =====
const alertDialogVisible = ref(false)
const alertDialogTitle = ref('警报')
const alertData = ref([])

// ===== 加载状态 =====
const replanning = ref(false)
const autoPlanning = ref(false)

// ===== 甘特图引用 =====
const resourceGanttRef = ref(null)
const utilizationChartRef = ref(null)

// ===== 计算属性 =====
// 资源甘特图数据 - 根据选择的资源和产品过滤
const resourceGanttData = computed(() => {
  const rawData = schedulingStore.ganttData
  if (!rawData || !rawData.data) return { data: [], links: [] }
  
  // 如果资源和产品都没选择，返回空数据
  if (selectedResources.value.length === 0 && selectedProducts.value.length === 0) {
    return { data: [], links: [] }
  }
  
  const hasResourceFilter = selectedResources.value.length > 0
  const hasProductFilter = selectedProducts.value.length > 0
  
  // 构建过滤集合
  const selectedResourceIdSet = hasResourceFilter 
    ? new Set(selectedResources.value.map(id => `resource_${id}`))
    : null
  const productIds = hasProductFilter 
    ? new Set(selectedProducts.value)
    : null
  
  // 找出所有顶级项（资源）和子任务
  const topLevelItems = rawData.data.filter(item => !item.parent || item.parent === 0)
  const childItems = rawData.data.filter(item => item.parent && item.parent !== 0)
  
  // 过滤子任务
  let filteredChildren = [...childItems]
  
  // 过滤逻辑：
  // - 如果只选择了资源：显示选中资源上的所有任务
  // - 如果只选择了产品：显示选中产品的所有任务（在任意资源上）
  // - 如果同时选择：显示选中资源上的选中产品任务（交集）
  if (hasResourceFilter && hasProductFilter) {
    // 交集：必须同时满足资源和产品条件
    filteredChildren = filteredChildren.filter(item => 
      selectedResourceIdSet.has(item.parent) && productIds.has(item.product_id)
    )
  } else if (hasResourceFilter) {
    // 只按资源过滤
    filteredChildren = filteredChildren.filter(item => selectedResourceIdSet.has(item.parent))
  } else if (hasProductFilter) {
    // 只按产品过滤
    filteredChildren = filteredChildren.filter(item => productIds.has(item.product_id))
  }
  
  // 找出有子任务的顶级项
  const parentIdsWithChildren = new Set(filteredChildren.map(item => item.parent))
  
  // 过滤顶级项：必须有匹配的子任务
  let filteredTopLevel = topLevelItems.filter(item => {
    // 如果选择了资源，检查是否在选中的资源中
    if (hasResourceFilter && !selectedResourceIdSet.has(item.id)) {
      return false
    }
    // 检查是否有匹配的子任务
    return parentIdsWithChildren.has(item.id)
  })
  
  // 合并结果
  const filteredData = [...filteredTopLevel, ...filteredChildren]
  
  return { data: filteredData, links: rawData.links || [] }
})

// 产品甘特图数据 - 根据选择的产品过滤
const productGanttData = computed(() => {
  const rawData = schedulingStore.productGanttData
  if (!rawData || !rawData.data) return { data: [], links: [] }
  
  // 如果资源和产品都没选择，返回空数据
  if (selectedResources.value.length === 0 && selectedProducts.value.length === 0) {
    return { data: [], links: [] }
  }
  
  const hasResourceFilter = selectedResources.value.length > 0
  const hasProductFilter = selectedProducts.value.length > 0
  
  const resourceIds = hasResourceFilter ? new Set(selectedResources.value) : null
  const productIds = hasProductFilter ? new Set(selectedProducts.value) : null
  
  // 找出所有顶级项（产品）和子任务
  const topLevelItems = rawData.data.filter(item => 
    item.parent === 0 || item.parent === null || item.parent === undefined
  )
  const childItems = rawData.data.filter(item => 
    item.parent && item.parent !== 0
  )
  
  // 过滤子任务
  let filteredChildren = [...childItems]
  
  // 如果只选择了资源，按资源过滤
  if (hasResourceFilter && !hasProductFilter) {
    filteredChildren = filteredChildren.filter(item => resourceIds.has(item.resource_id))
  }
  
  // 如果只选择了产品，根据顶级产品ID过滤
  if (hasProductFilter && !hasResourceFilter) {
    // 找出选中产品对应的顶级项ID
    const selectedTopLevelIds = new Set()
    topLevelItems.forEach(item => {
      if (productIds.has(item.product_id)) {
        selectedTopLevelIds.add(item.id)
      }
    })
    filteredChildren = filteredChildren.filter(item => selectedTopLevelIds.has(item.parent))
  }
  
  // 如果同时选择了资源和产品（交集）
  if (hasResourceFilter && hasProductFilter) {
    // 找出选中产品对应的顶级项ID
    const selectedTopLevelIds = new Set()
    topLevelItems.forEach(item => {
      if (productIds.has(item.product_id)) {
        selectedTopLevelIds.add(item.id)
      }
    })
    // 子任务需要同时满足：属于选中的产品 且 在选中的资源上
    filteredChildren = filteredChildren.filter(item => 
      selectedTopLevelIds.has(item.parent) && resourceIds.has(item.resource_id)
    )
  }
  
  // 找出有子任务的顶级项
  const parentIdsWithChildren = new Set(filteredChildren.map(item => item.parent))
  
  // 过滤顶级项：必须有匹配的子任务
  let filteredTopLevel = topLevelItems.filter(item => {
    // 如果选择了产品，检查是否在选中的产品中
    if (hasProductFilter && !productIds.has(item.product_id)) {
      return false
    }
    // 检查是否有匹配的子任务
    return parentIdsWithChildren.has(item.id)
  })
  
  // 只保留属于已过滤顶级项的子任务
  const filteredTopLevelIds = new Set(filteredTopLevel.map(item => item.id))
  filteredChildren = filteredChildren.filter(item => filteredTopLevelIds.has(item.parent))
  
  // 合并结果
  const filteredData = [...filteredTopLevel, ...filteredChildren]
  
  return { data: filteredData, links: rawData.links || [] }
})

// 从资源甘特图数据中提取资源列表并生成利用率数据
const utilizationData = computed(() => {
  // 优先使用 store 中的数据
  if (schedulingStore.utilizationData && schedulingStore.utilizationData.length > 0) {
    return schedulingStore.utilizationData
  }
  
  // 否则从资源甘特图数据中提取资源信息生成利用率数据
  // 使用过滤后的数据，这样利用率也会根据筛选条件变化
  const ganttData = resourceGanttData.value?.data || []
  if (ganttData.length === 0) return []
  
  const [startStr, endStr] = dateRange.value || []
  if (!startStr || !endStr) return []
  
  const start = new Date(startStr)
  start.setHours(0, 0, 0, 0)
  const end = new Date(endStr)
  end.setHours(23, 59, 59, 999)
  
  // 首先建立资源ID到资源名称的映射
  // resource view 的顶级项 ID 格式是 "resource_{id}"
  const resourceIdToName = {}
  ganttData.forEach(item => {
    const isTopLevel = !item.parent || item.parent === 0
    if (isTopLevel) {
      // 这是顶级项（资源），text 是资源名称
      resourceIdToName[item.id] = item.text
    }
  })
  
  // 收集所有任务，按资源分组
  const tasksByResource = {}
  const resourceInfo = {}
  
  // 遍历所有甘特图数据
  ganttData.forEach(item => {
    // 跳过没有时间信息的项
    if (!item.start_date || !item.end_date) return
    
    // 跳过顶级项（资源本身不是任务）
    const isTopLevel = !item.parent || item.parent === 0
    if (isTopLevel) return
    
    // 使用父ID作为资源标识（格式如 "resource_1"）
    const resourceId = item.parent
    // 从资源ID映射中获取资源名称
    const resourceName = resourceIdToName[resourceId] || `资源 ${resourceId}`
    
    // 初始化资源分组
    if (!tasksByResource[resourceId]) {
      tasksByResource[resourceId] = []
      resourceInfo[resourceId] = {
        name: resourceName,
        description: ''
      }
    }
    
    // 添加任务
    tasksByResource[resourceId].push({
      start_date: item.start_date,
      end_date: item.end_date,
      text: item.text
    })
  })
  
  // 如果没有按资源分组的数据，使用顶级项作为资源并获取其子任务
  if (Object.keys(tasksByResource).length === 0) {
    // 找出所有顶级项（parent 为 0 或 null）
    const topLevelItems = ganttData.filter(d => d.parent === 0 || d.parent === null || d.parent === undefined)
    
    topLevelItems.forEach(resource => {
      const resourceId = resource.id
      const resourceTasks = ganttData.filter(d => d.parent === resource.id && d.start_date && d.end_date)
      
      if (resourceTasks.length > 0) {
        tasksByResource[resourceId] = resourceTasks.map(t => ({
          start_date: t.start_date,
          end_date: t.end_date,
          text: t.text
        }))
        resourceInfo[resourceId] = {
          name: resource.text || resource.name || `资源 ${resourceId}`,
          description: resource.description || ''
        }
      }
    })
  }
  
  // 为每个资源生成利用率数据
  return Object.keys(tasksByResource).map(resourceId => {
    const tasks = tasksByResource[resourceId]
    const info = resourceInfo[resourceId] || { name: `资源 ${resourceId}`, description: '' }
    const timeSlots = generateUtilizationSlots(start, end, tasks)
    
    return {
      resource_id: resourceId,
      resource_name: info.name,
      description: info.description,
      capacity: 24,
      time_slots: timeSlots
    }
  })
})

// 生成利用率时间槽
const generateUtilizationSlots = (start, end, tasks) => {
  const slots = []
  const current = new Date(start)
  const slotDuration = 8 * 60 * 60 * 1000 // 8小时
  
  while (current < end) {
    const slotStart = new Date(current)
    const slotEnd = new Date(current.getTime() + slotDuration)
    
    // 计算该时间槽内的任务占用时间
    let occupiedHours = 0
    tasks.forEach(task => {
      if (!task.start_date || !task.end_date) return
      
      const taskStart = new Date(task.start_date)
      const taskEnd = new Date(task.end_date)
      
      // 检查任务是否与时间槽重叠
      if (taskStart < slotEnd && taskEnd > slotStart) {
        const overlapStart = Math.max(taskStart.getTime(), slotStart.getTime())
        const overlapEnd = Math.min(taskEnd.getTime(), slotEnd.getTime())
        occupiedHours += (overlapEnd - overlapStart) / (1000 * 60 * 60)
      }
    })
    
    // 利用率 = 占用时间 / 时间槽总时长（8小时）
    const utilization = occupiedHours / 8
    
    slots.push({
      start: slotStart.toISOString(),
      end: slotEnd.toISOString(),
      utilization: utilization
    })
    
    current.setTime(current.getTime() + slotDuration)
  }
  
  return slots
}

const resourceCount = computed(() => {
  const data = resourceGanttData.value?.data || []
  return data.filter(d => d.parent === 0 || d.parent === null || d.parent === undefined).length
})

const productCount = computed(() => {
  const data = productGanttData.value?.data || []
  return data.filter(d => d.parent === 0 || d.parent === null || d.parent === undefined).length
})

const utilizationCount = computed(() => {
  return utilizationData.value?.length || 0
})

// ===== 方法 =====
const loadResources = async () => {
  try {
    const data = await masterDataApi.getResources()
    // 模拟瓶颈资源：将名称包含 "CNC" 或 "加工" 的资源标记为瓶颈
    // 实际项目中应该从后端获取 is_bottleneck 字段
    resourceOptions.value = data.map(r => ({ 
      id: r.id, 
      name: r.name,
      is_bottleneck: r.name.includes('CNC') || r.name.includes('加工') || r.name.includes('瓶颈')
    }))
  } catch (error) {
    console.error('Failed to load resources:', error)
  }
}

const loadProducts = async () => {
  try {
    const data = await masterDataApi.getProducts()
    productOptions.value = data.map(p => ({ id: p.id, name: p.product_number || p.name }))
  } catch (error) {
    console.error('Failed to load products:', error)
  }
}

const loadGanttData = async () => {
  const [startDate, endDate] = dateRange.value || []
  
  // 资源图表使用 'resource' 视图类型 - 第一级是资源名称，第二级是订单+工序
  await schedulingStore.fetchGanttData('resource', startDate, endDate)
  
  if (selectedCharts.value.includes('product')) {
    await schedulingStore.fetchProductGanttData(startDate, endDate)
  }
  
  if (selectedCharts.value.includes('utilization')) {
    await schedulingStore.fetchUtilizationData(selectedResources.value, startDate, endDate, currentZoom.value)
  }
}

const handleResourceChange = () => {
  loadGanttData()
}

const handleProductChange = () => {
  loadGanttData()
}

const handleRefresh = () => {
  loadGanttData()
  ElMessage.success('数据已刷新')
}

const handleAlertCommand = (command) => {
  if (command === 'order-delay') {
    alertDialogTitle.value = '订单延误警报'
    // 模拟数据
    alertData.value = [
      { order_number: 'ORD-001', product_name: '产品A', description: '预计延误2天', severity: 'high' },
      { order_number: 'ORD-002', product_name: '产品B', description: '预计延误1天', severity: 'medium' }
    ]
  } else if (command === 'material-shortage') {
    alertDialogTitle.value = '物料短缺警报'
    alertData.value = [
      { order_number: 'ORD-003', product_name: '产品C', description: '物料M001短缺', severity: 'high' }
    ]
  }
  alertDialogVisible.value = true
}

const handleAutoPlanCommand = (command) => {
  if (command === 'heuristic') {
    heuristicDialogVisible.value = true
  } else if (command === 'optimizer') {
    optimizerDialogVisible.value = true
  }
}

const handleStrategySave = () => {
  currentStrategy.value = strategyForm.sortingRule
  strategyDialogVisible.value = false
  ElMessage.success('策略配置已保存')
}

const handleHeuristicExecute = async () => {
  // 检查是否选择了资源
  if (selectedResources.value.length === 0) {
    ElMessage.warning('请先选择要排程的资源')
    return
  }
  
  autoPlanning.value = true
  try {
    // 使用算法参数，排序规则和策略配置从"策略"对话框中获取
    const config = {
      finite_capacity: true,
      resolve_backlog: true,
      resolve_overload: true,
      preserve_scheduled: true,
      sorting_rule: strategyForm.sortingRule,           // 排序规则
      planning_mode: strategyForm.planningMode,         // 计划模式
      planning_direction: strategyForm.planningDirection, // 计划方向
      expected_date: strategyForm.expectedDate,         // 期望日期
      order_internal_relation: strategyForm.orderInternalRelation, // 订单内部关系
      sub_planning_mode: strategyForm.subPlanningMode,  // 子计划模式
      error_handling: strategyForm.errorHandling,       // 计划出错的操作
      planning_horizon: 90,
      schedule_selected_resources_only: true            // 只排程选中资源上的工序
    }
    await schedulingStore.autoPlan('heuristic', heuristicForm.selected, config, selectedResources.value)
    
    ElMessage.success('启发式计划执行成功')
    heuristicDialogVisible.value = false
    await loadGanttData()
  } catch (error) {
    ElMessage.error('启发式计划执行失败')
  } finally {
    autoPlanning.value = false
  }
}

const handleOptimizerExecute = async () => {
  autoPlanning.value = true
  try {
    const config = {
      delay_cost: optimizerForm.delayCost,
      inventory_cost: optimizerForm.inventoryCost,
      setup_cost: optimizerForm.setupCost,
      utilization_weight: optimizerForm.utilizationWeight,
      time_limit: optimizerForm.timeLimit
    }
    await schedulingStore.autoPlan('optimizer', null, config, selectedResources.value)
    ElMessage.success('优化器计划执行成功')
    optimizerDialogVisible.value = false
    await loadGanttData()
  } catch (error) {
    ElMessage.error('优化器计划执行失败')
  } finally {
    autoPlanning.value = false
  }
}

// 取消计划
const cancellingPlan = ref(false)

const handleCancelPlan = async () => {
  if (selectedResources.value.length === 0 && selectedProducts.value.length === 0) {
    ElMessage.warning('请先选择资源或产品')
    return
  }
  
  cancellingPlan.value = true
  try {
    // 调用取消计划 API - 根据选中的资源和产品清除排程
    const result = await schedulingStore.cancelPlan(
      selectedResources.value.length > 0 ? selectedResources.value : null,
      selectedProducts.value.length > 0 ? selectedProducts.value : null
    )
    
    if (result.success) {
      ElMessage.success(result.message || '取消计划成功')
    } else {
      ElMessage.warning(result.message || '没有找到需要取消的排程')
    }
    
    await loadGanttData()
  } catch (error) {
    console.error('Cancel plan error:', error)
    ElMessage.error('取消计划失败')
  } finally {
    cancellingPlan.value = false
  }
}

// 保存计划
const savingPlan = ref(false)

// 是否有未保存的排程更改
const hasUnsavedChanges = computed(() => schedulingStore.hasUnsavedChanges)

const handleSavePlan = async () => {
  // 如果有未保存的更改，优先保存缓存数据
  if (hasUnsavedChanges.value) {
    savingPlan.value = true
    try {
      const result = await schedulingStore.savePlan(
        selectedResources.value.length > 0 ? selectedResources.value : null,
        selectedProducts.value.length > 0 ? selectedProducts.value : null
      )
      
      if (result.success) {
        ElMessage.success(result.message || '保存计划成功')
      } else {
        ElMessage.warning(result.message || '保存计划失败')
      }
      
      await loadGanttData()
    } catch (error) {
      console.error('Save plan error:', error)
      ElMessage.error('保存计划失败')
    } finally {
      savingPlan.value = false
    }
    return
  }
  
  // 没有缓存数据时，走原有逻辑
  if (selectedResources.value.length === 0 && selectedProducts.value.length === 0) {
    ElMessage.warning('请先选择资源或产品')
    return
  }
  
  savingPlan.value = true
  try {
    // 调用保存计划 API - 将排程的计划订单状态改为已排程
    const result = await schedulingStore.savePlan(
      selectedResources.value.length > 0 ? selectedResources.value : null,
      selectedProducts.value.length > 0 ? selectedProducts.value : null
    )
    
    if (result.success) {
      if (result.saved_orders > 0) {
        ElMessage.success(result.message || '保存计划成功')
      } else {
        ElMessage.warning(result.message || '没有找到需要保存的排程')
      }
    } else {
      ElMessage.warning(result.message || '保存计划失败')
    }
    
    await loadGanttData()
  } catch (error) {
    console.error('Save plan error:', error)
    ElMessage.error('保存计划失败')
  } finally {
    savingPlan.value = false
  }
}

// 丢弃计划
const discardingPlan = ref(false)

const handleDiscardPlan = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要丢弃当前的排程更改吗？所有未保存的更改将会丢失，订单将恢复到之前的状态。',
      '丢弃计划',
      {
        confirmButtonText: '确定丢弃',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    discardingPlan.value = true
    try {
      const result = await schedulingStore.discardPlan()
      
      if (result.success) {
        ElMessage.success(result.message || '已丢弃排程更改')
      } else {
        ElMessage.warning(result.message || '丢弃计划失败')
      }
      
      await loadGanttData()
    } catch (error) {
      console.error('Discard plan error:', error)
      ElMessage.error('丢弃计划失败')
    } finally {
      discardingPlan.value = false
    }
  } catch {
    // 用户取消操作
  }
}

const handleReplan = async () => {
  if (selectedResources.value.length === 0) {
    ElMessage.warning('请先选择资源')
    return
  }
  
  replanning.value = true
  try {
    await schedulingStore.rescheduleResource(selectedResources.value, currentStrategy.value)
    ElMessage.success('重新计划成功')
    await loadGanttData()
  } catch (error) {
    ElMessage.error('重新计划失败')
  } finally {
    replanning.value = false
  }
}

const handleTaskUpdated = async (data) => {
  try {
    const result = await schedulingStore.rescheduleOperation(
      data.operationId,
      data.newStart.toISOString(),
      data.resourceId
    )
    if (result.success) {
      ElMessage.success('工序已调整')
    } else {
      ElMessage.error(result.message)
      await loadGanttData()
    }
  } catch (error) {
    ElMessage.error('更新失败')
    await loadGanttData()
  }
}

const handleTaskClicked = (task) => {
  console.log('Task clicked:', task)
}

// ===== 监听图表选择变化 =====
watch(selectedCharts, async (newVal) => {
  if (newVal.includes('product') && !schedulingStore.productGanttData?.data?.length) {
    const [startDate, endDate] = dateRange.value || []
    await schedulingStore.fetchProductGanttData(startDate, endDate)
  }
  if (newVal.includes('utilization') && !schedulingStore.utilizationData?.length) {
    const [startDate, endDate] = dateRange.value || []
    await schedulingStore.fetchUtilizationData(selectedResources.value, startDate, endDate, currentZoom.value)
  }
})

// ===== 监听日期范围变化 =====
watch(dateRange, async () => {
  await loadGanttData()
})

// ===== 监听缩放级别变化，重新加载利用率数据 =====
watch(currentZoom, async () => {
  if (selectedCharts.value.includes('utilization')) {
    const [startDate, endDate] = dateRange.value || []
    await schedulingStore.fetchUtilizationData(selectedResources.value, startDate, endDate, currentZoom.value)
  }
})

// ===== 监听筛选条件变化，自动保存并同步到共享store =====
watch(
  [dateRange, selectedResources, selectedProducts, selectedCharts, currentZoom, bottleneckOnly],
  () => {
    saveFiltersToStorage()
    // 同步到共享store，供其他DS页面使用
    dsFiltersStore.setSelectedResources(selectedResources.value)
    dsFiltersStore.setSelectedProducts(selectedProducts.value)
    dsFiltersStore.setDateRange(dateRange.value)
    dsFiltersStore.setBottleneckOnly(bottleneckOnly.value)
  },
  { deep: true }
)

// ===== 初始化 =====
onMounted(async () => {
  await Promise.all([
    loadResources(),
    loadProducts(),
    loadGanttData()
  ])
  
  // 初始化时同步筛选条件到共享store
  dsFiltersStore.setSelectedResources(selectedResources.value)
  dsFiltersStore.setSelectedProducts(selectedProducts.value)
  dsFiltersStore.setDateRange(dateRange.value)
  dsFiltersStore.setResourceOptions(resourceOptions.value)
  dsFiltersStore.setProductOptions(productOptions.value)
  dsFiltersStore.setBottleneckOnly(bottleneckOnly.value)
})

// ===== 离开页面时保存筛选条件 =====
onBeforeUnmount(() => {
  saveFiltersToStorage()
})
</script>

<style lang="scss" scoped>
.ds-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  background: #fff;
}

// 工具栏样式
.toolbar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  gap: 16px;
  flex-wrap: wrap;
}

.toolbar-filters {
  .filter-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .select-header-options {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 4px 0;
  }
  
  .filter-label {
    font-size: 14px;
    color: #606266;
    white-space: nowrap;
    
    .required {
      color: #f56c6c;
      margin-left: 2px;
    }
  }
  
  .copy-btn {
    padding: 4px;
    color: #909399;
    
    &:hover {
      color: #1a73e8;
    }
  }
}

.toolbar-actions {
  justify-content: space-between;
  
  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .section-label {
      font-size: 14px;
      color: #606266;
    }
  }
  
  .toolbar-center {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  
  // 白色背景黑色字体按钮
  .btn-outline {
    background: #fff !important;
    color: #303133 !important;
    border: 1px solid #dcdfe6 !important;
    
    &:hover {
      background: #f5f7fa !important;
      border-color: #c0c4cc !important;
    }
    
    .el-icon {
      color: #606266;
    }
  }
  
  .toolbar-right {
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }
  
  .time-nav,
  .zoom-controls {
    margin: 0 4px;
  }
  
  .legend-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    font-size: 13px;
    color: #606266;
  }
  
  .legend-box {
    display: inline-block;
    width: 14px;
    height: 14px;
    border-radius: 3px;
    margin-right: 6px;
    
    &.planned {
      background: #409EFF;
    }
    
    &.production {
      background: #909399;
    }
    
    &.changeover {
      background: #E6A23C;
    }
  }
}

// 图表容器
.charts-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chart-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 200px;
  overflow: hidden; // dhtmlx-gantt 自己管理滚动
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  
  .chart-title {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
    
    a {
      color: #1a73e8;
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
  
  .chart-actions {
    display: flex;
    gap: 4px;
  }
}

.chart-content {
  flex: 1;
  min-height: 0; // 允许在flex容器中正确收缩
  overflow: hidden; // dhtmlx-gantt 自己管理滚动
}

// 分隔条样式
.chart-resizer {
  height: 8px;
  background: #f5f7fa;
  cursor: row-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .resizer-handle {
    width: 40px;
    height: 4px;
    background: #dcdfe6;
    border-radius: 2px;
    
    &::before {
      content: '';
      display: block;
      width: 100%;
      height: 100%;
      background: repeating-linear-gradient(
        90deg,
        #c0c4cc 0px,
        #c0c4cc 2px,
        transparent 2px,
        transparent 6px
      );
    }
  }
  
  &:hover {
    background: #e4e7ed;
    
    .resizer-handle {
      background: #c0c4cc;
    }
  }
}

// 对话框中的 radio 组
:deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

// 表单提示文字
.form-hint {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

// 表单项提示文字（策略对话框）
.form-item-hint {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
}

// 高亮保存按钮（有未保存更改时）
.btn-highlight {
  animation: highlight-pulse 1.5s ease-in-out infinite;
}

@keyframes highlight-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(64, 158, 255, 0);
  }
}

</style>

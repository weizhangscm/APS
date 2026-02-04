<template>
  <div class="ds-product-view">
    <!-- 顶部筛选区域 -->
    <div class="filter-bar">
      <div class="filter-row">
        <!-- 搜索框 -->
        <div class="filter-item">
          <span class="filter-label">搜索</span>
          <el-input
            v-model="searchText"
            placeholder=""
            clearable
            size="small"
            class="filter-input"
            @input="handleFilter"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <!-- 产品标识 -->
        <div class="filter-item">
          <span class="filter-label">产品标识:</span>
          <el-input
            v-model="filterProductCode"
            placeholder=""
            clearable
            size="small"
            class="filter-input"
            @input="handleFilter"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <!-- 位置 -->
        <div class="filter-item">
          <span class="filter-label">位置:</span>
          <el-input
            v-model="filterLocation"
            placeholder=""
            clearable
            size="small"
            class="filter-input"
            @input="handleFilter"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <!-- MRP 控制员 -->
        <div class="filter-item">
          <span class="filter-label">MRP 控制员:</span>
          <el-input
            v-model="filterMrpController"
            placeholder=""
            clearable
            size="small"
            class="filter-input"
            @input="handleFilter"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <!-- 产品类型 -->
        <div class="filter-item">
          <span class="filter-label">产品类型:</span>
          <el-input
            v-model="filterProductType"
            placeholder=""
            clearable
            size="small"
            class="filter-input"
            @input="handleFilter"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>
    </div>
    
    <!-- 表格标题 -->
    <div class="table-header">
      <span class="table-title">位置产品({{ filteredProductList.length }}) <span class="title-suffix">标准</span><span class="required-mark">*</span></span>
    </div>
    
    <!-- 数据表格 -->
    <div class="table-container">
      <el-table
        ref="tableRef"
        :data="filteredProductList"
        v-loading="loading"
        border
        size="small"
        class="ds-product-table"
        @selection-change="handleSelectionChange"
      >
        <!-- 产品标识 -->
        <el-table-column prop="product_code" label="产品标识" min-width="100" />
        
        <!-- 产品描述 -->
        <el-table-column prop="product_description" label="产品描述" min-width="200" show-overflow-tooltip />
        
        <!-- 基本计量单位 -->
        <el-table-column prop="base_unit" label="基本计量单位" min-width="100" align="center" />
        
        <!-- 产品类型 -->
        <el-table-column prop="product_type" label="产品类型" min-width="80" align="center" />
        
        <!-- 位置 -->
        <el-table-column prop="location" label="位置" min-width="60" align="center" />
        
        <!-- 位置名称 1 -->
        <el-table-column prop="location_name" label="位置名称 1" min-width="120" />
        
        <!-- MRP 控制员 -->
        <el-table-column prop="mrp_controller" label="MRP 控制员" min-width="90" align="center" />
        
        <!-- MRP 控制员姓名 -->
        <el-table-column prop="mrp_controller_name" label="MRP控制员姓名" min-width="110" />
        
        <!-- 已加删除标记 -->
        <el-table-column prop="deletion_flag" label="已加删除标记..." min-width="100" align="center">
          <template #default="{ row }">
            {{ row.deletion_flag ? '是' : '' }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
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

// 产品列表数据（全部数据，DS产品是数据源）
const productList = ref([])

// 选中的产品
const selectedProducts = ref([])

// 筛选条件
const searchText = ref('')
const filterProductCode = ref('')
const filterLocation = ref('')
const filterMrpController = ref('')
const filterProductType = ref('')

// 位置映射数据
const locationMap = {
  '1020': 'Frankfurt Plant',
  '1110': 'Beijing Plant',
  '1120': 'Shanghai Plant',
  '1121': 'Shanghai Plant2'
}

// 产品类型列表
const productTypes = ['HALB', 'FERT']

// 单位映射
const unitMap = {
  'PCS': '个 (PCS)',
  'KG': '千克 (KG)',
  'EA': '个 (EA)',
  'M': '米 (M)',
  'L': '升 (L)',
  'SET': '套 (SET)'
}

// 过滤后的产品列表
const filteredProductList = computed(() => {
  let result = productList.value
  
  // 搜索文本过滤
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(item => 
      item.product_code?.toLowerCase().includes(search) ||
      item.product_description?.toLowerCase().includes(search) ||
      item.location?.toLowerCase().includes(search) ||
      item.location_name?.toLowerCase().includes(search)
    )
  }
  
  // 产品标识过滤
  if (filterProductCode.value) {
    const code = filterProductCode.value.toLowerCase()
    result = result.filter(item => item.product_code?.toLowerCase().includes(code))
  }
  
  // 位置过滤
  if (filterLocation.value) {
    const location = filterLocation.value.toLowerCase()
    result = result.filter(item => 
      item.location?.toLowerCase().includes(location) ||
      item.location_name?.toLowerCase().includes(location)
    )
  }
  
  // MRP 控制员过滤
  if (filterMrpController.value) {
    const mrp = filterMrpController.value.toLowerCase()
    result = result.filter(item => 
      item.mrp_controller?.toLowerCase().includes(mrp) ||
      item.mrp_controller_name?.toLowerCase().includes(mrp)
    )
  }
  
  // 产品类型过滤
  if (filterProductType.value) {
    const type = filterProductType.value.toUpperCase()
    result = result.filter(item => item.product_type?.toUpperCase().includes(type))
  }
  
  return result
})

// 加载产品数据
const loadProducts = async () => {
  loading.value = true
  try {
    // 通过store获取数据
    await store.fetchProducts()
    const data = store.products
    // 将后端数据映射为界面字段
    const mappedData = (data || []).map((product, index) => {
      // 模拟分配位置和类型
      const locationKeys = Object.keys(locationMap)
      const locationCode = locationKeys[index % locationKeys.length]
      const productType = productTypes[index % productTypes.length]
      
      return {
        id: product.id,
        product_code: product.code,
        product_description: product.name,
        base_unit: unitMap[product.unit] || `${product.unit}`,
        product_type: productType,
        location: locationCode,
        location_name: locationMap[locationCode],
        mrp_controller: '001',
        mrp_controller_name: '',
        deletion_flag: false
      }
    })
    productList.value = mappedData
    // 同步到共享store，供详细计划表使用
    dsFiltersStore.setDSProducts(mappedData)
  } catch (error) {
    console.error('Failed to load products:', error)
    ElMessage.error('加载产品数据失败')
  } finally {
    loading.value = false
  }
}

// 处理筛选
const handleFilter = () => {
  // 筛选逻辑在 computed 属性中自动处理
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedProducts.value = selection
}

// 初始化
onMounted(() => {
  loadProducts()
})
</script>

<style lang="scss" scoped>
.ds-product-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  background: #fff;
}

// 筛选区域样式
.filter-bar {
  background: #f5f5f5;
  padding: 8px 16px;
  border-bottom: 1px solid #dcdcdc;
  
  .filter-row {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  
  .filter-item {
    display: flex;
    align-items: center;
    gap: 4px;
    
    .filter-label {
      font-size: 12px;
      color: #333;
      white-space: nowrap;
    }
    
    .filter-input {
      width: 140px;
      
      :deep(.el-input__wrapper) {
        background: #fff;
        box-shadow: none;
        border: 1px solid #c4c4c4;
        border-radius: 0;
        padding: 0 8px;
        
        .el-input__inner {
          font-size: 12px;
          height: 24px;
          line-height: 24px;
        }
        
        .el-input__prefix {
          color: #666;
        }
      }
    }
  }
}

// 表格标题
.table-header {
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  
  .table-title {
    font-size: 12px;
    color: #0066cc;
    font-weight: 500;
    
    .title-suffix {
      color: #333;
      font-weight: normal;
    }
    
    .required-mark {
      color: #ff0000;
      margin-left: 2px;
    }
  }
}

// 表格容器
.table-container {
  flex: 1;
  padding: 0;
  overflow: auto;
}

// DS产品表格样式 - 参照附件图片风格
.ds-product-table {
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
}
</style>

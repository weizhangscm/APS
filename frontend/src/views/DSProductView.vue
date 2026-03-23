<template>
  <div class="master-data-page">
    <div class="page-header">
      <h1>
        <el-icon><Box /></el-icon>
        {{ t('dsProduct.title') }}
      </h1>
      <div class="header-actions">
        <DataExcelToolbar
          :entities="[{ id: 'products', labelKey: 'dataManagement.products' }]"
          @imported="loadProducts"
        />
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          {{ t('dsProduct.addProduct') }}
        </el-button>
      </div>
    </div>
    
    <el-card>
      <el-table :data="filteredProductList" v-loading="loading" stripe table-layout="auto">
        <el-table-column prop="product_code" :label="t('dsProduct.productCode')" min-width="100" />
        <el-table-column prop="product_description" :label="t('dsProduct.productDescription')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="base_unit" :label="t('dsProduct.baseUnit')" min-width="100" align="center" />
        <el-table-column prop="product_type" :label="t('dsProduct.productType')" min-width="80" align="center" />
        <el-table-column prop="location" :label="t('dsProduct.location')" min-width="60" align="center" />
        <el-table-column prop="location_name" :label="t('dsProduct.locationName')" min-width="120" />
        <el-table-column prop="mrp_controller" :label="t('dsProduct.mrpController')" min-width="90" align="center" />
        <el-table-column prop="mrp_controller_name" :label="t('dsProduct.mrpControllerName')" min-width="110" />
        <el-table-column :label="t('masterData.actions')" width="220" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleView(row)">{{ t('dsProduct.viewDetails') }}</el-button>
              <el-button type="primary" link @click="handleEdit(row)">{{ t('masterData.edit') }}</el-button>
              <el-button type="primary" link @click="handleDelete(row)">{{ t('masterData.delete') }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog 
      v-model="viewDialogVisible" 
      :title="`${t('dsProduct.productDetails')} - ${currentProduct?.product_description || ''}`"
      width="700px"
    >
      <el-descriptions :column="2" border v-if="currentProduct">
        <el-descriptions-item :label="t('dsProduct.productCode')">{{ currentProduct.product_code }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsProduct.productDescription')">{{ currentProduct.product_description }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsProduct.baseUnit')">{{ currentProduct.base_unit }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsProduct.productType')">{{ currentProduct.product_type }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsProduct.location')">{{ currentProduct.location }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsProduct.locationName')">{{ currentProduct.location_name }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsProduct.mrpController')">{{ currentProduct.mrp_controller }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsProduct.mrpControllerName')">{{ currentProduct.mrp_controller_name || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsProduct.deletionFlag')">
          <el-tag :type="currentProduct.deletion_flag ? 'danger' : 'success'" size="small">
            {{ currentProduct.deletion_flag ? t('common.yes') : t('common.no') }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewDialogVisible = false">{{ t('dsResource.close') }}</el-button>
      </template>
    </el-dialog>
    
    <el-dialog 
      v-model="editDialogVisible" 
      :title="isEdit ? t('dsProduct.editProduct') : t('dsProduct.addProduct')"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rulesRef" label-width="120px">
        <el-form-item :label="t('dsProduct.productCode')" prop="product_code">
          <el-input v-model="form.product_code" :disabled="isEdit" :placeholder="t('dsProduct.enterProductCode')" />
        </el-form-item>
        <el-form-item :label="t('dsProduct.productDescription')" prop="product_description">
          <el-input v-model="form.product_description" :placeholder="t('dsProduct.enterProductDescription')" />
        </el-form-item>
        <el-form-item :label="t('dsProduct.baseUnit')" prop="base_unit">
          <el-select v-model="form.base_unit" :placeholder="t('dsProduct.selectUnit')" style="width: 100%">
            <el-option label="个 (PCS)" value="PCS" />
            <el-option label="千克 (KG)" value="KG" />
            <el-option label="个 (EA)" value="EA" />
            <el-option label="米 (M)" value="M" />
            <el-option label="升 (L)" value="L" />
            <el-option label="套 (SET)" value="SET" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('dsProduct.productType')" prop="product_type">
          <el-select v-model="form.product_type" :placeholder="t('dsProduct.selectProductType')" style="width: 100%">
            <el-option label="HALB" value="HALB" />
            <el-option label="FERT" value="FERT" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('dsProduct.location')" prop="location">
          <el-select v-model="form.location" :placeholder="t('dsProduct.selectLocation')" style="width: 100%">
            <el-option
              v-for="loc in locations"
              :key="loc.code"
              :label="loc.description ? `${loc.code} — ${loc.description}` : loc.code"
              :value="loc.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('dsProduct.mrpController')">
          <el-input v-model="form.mrp_controller" :placeholder="t('dsProduct.enterMRPControllerCode')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Box, Plus } from '@element-plus/icons-vue'
import { useMasterDataStore } from '@/stores/masterData'
import { useDSFiltersStore } from '@/stores/dsFilters'
import { useI18nStore } from '@/stores/i18n'
import { masterDataApi } from '@/api'
import DataExcelToolbar from '@/components/DataExcelToolbar.vue'

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)
const store = useMasterDataStore()

// 共享筛选store
const dsFiltersStore = useDSFiltersStore()

// 加载状态
const loading = ref(false)
const locations = ref([])

// 产品列表数据
const productList = ref([])

// 对话框状态
const viewDialogVisible = ref(false)
const editDialogVisible = ref(false)
const isEdit = ref(false)
const currentProduct = ref(null)
const submitting = ref(false)
const formRef = ref(null)

// 表单数据
const form = ref({
  product_code: '',
  product_description: '',
  base_unit: 'PCS',
  product_type: 'FERT',
  location: '',
  mrp_controller: '001'
})

const rulesRef = computed(() => ({
  product_code: [{ required: true, message: i18nStore.t('dsProduct.enterProductCode'), trigger: 'blur' }],
  product_description: [{ required: true, message: i18nStore.t('dsProduct.enterProductDescription'), trigger: 'blur' }],
  base_unit: [{ required: true, message: i18nStore.t('dsProduct.selectUnit'), trigger: 'change' }],
  product_type: [{ required: true, message: i18nStore.t('dsProduct.selectProductType'), trigger: 'change' }],
  location: [{ required: true, message: i18nStore.t('dsProduct.selectLocation'), trigger: 'change' }]
}))

const apiDetailMessage = (error) => {
  const d = error?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d.length) {
    return d.map((x) => (typeof x === 'object' && x?.msg ? x.msg : String(x))).join('; ') || null
  }
  return null
}

const locationDescription = (code) => {
  const row = locations.value.find((l) => l.code === code)
  return row?.description || ''
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

// 过滤后的产品列表（目前显示所有，可以后续添加筛选功能）
const filteredProductList = computed(() => {
  return productList.value
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
      const loc = product.location || (locations.value[0]?.code ?? '')
      const productType = product.product_type || productTypes[index % productTypes.length]
      const rawUnit = product.unit || 'PCS'
      return {
        id: product.id,
        product_code: product.code,
        product_description: product.name,
        base_unit: unitMap[rawUnit] || rawUnit,
        product_type: productType,
        location: loc,
        location_name: product.location_name || locationDescription(loc) || '',
        mrp_controller: product.mrp_controller || '001',
        mrp_controller_name: product.mrp_controller_name || '',
        deletion_flag: !!(product.deletion_flag === true || product.deletion_flag === 1)
      }
    })
    productList.value = mappedData
    // 同步到共享store，供详细计划表使用
    dsFiltersStore.setDSProducts(mappedData)
  } catch (error) {
    console.error('Failed to load products:', error)
    ElMessage.error(t('dsProduct.loadProductsFailed'))
  } finally {
    loading.value = false
  }
}

// 显示产品详情
const handleView = (row) => {
  currentProduct.value = row
  viewDialogVisible.value = true
}

// 新增产品
const handleAdd = () => {
  isEdit.value = false
  form.value = {
    product_code: '',
    product_description: '',
    base_unit: 'PCS',
    product_type: 'FERT',
    location: locations.value[0]?.code || '',
    mrp_controller: '001'
  }
  editDialogVisible.value = true
}

// 编辑产品
const handleEdit = (row) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    product_code: row.product_code,
    product_description: row.product_description,
    base_unit: row.base_unit.match(/\(([^)]+)\)/)?.[1] || row.base_unit,
    product_type: row.product_type,
    location: row.location,
    mrp_controller: row.mrp_controller
  }
  editDialogVisible.value = true
}

// 删除产品
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      t('dsProduct.confirmDeleteProduct').replace('{name}', row.product_description),
      t('orders.confirmDeleteTitle'),
      { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
    await store.deleteProduct(row.id)
    ElMessage.success(t('messages.deleteSuccess'))
    await loadProducts()
  } catch (error) {
    if (error === 'cancel') return
    const msg = apiDetailMessage(error)
    ElMessage.error(msg || t('messages.deleteFailed'))
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    const loc = form.value.location
    const payloadBase = {
      name: form.value.product_description,
      unit: form.value.base_unit,
      product_type: form.value.product_type,
      location: loc,
      location_name: locationDescription(loc) || null,
      mrp_controller: form.value.mrp_controller?.trim() ? form.value.mrp_controller.trim() : null
    }

    if (isEdit.value) {
      await store.updateProduct(form.value.id, payloadBase)
      ElMessage.success(t('messages.updateSuccess'))
    } else {
      await store.createProduct({
        code: form.value.product_code,
        ...payloadBase
      })
      ElMessage.success(t('messages.createSuccess'))
    }

    editDialogVisible.value = false
    await loadProducts()
  } catch (error) {
    if (error === false) return
    const msg = apiDetailMessage(error)
    ElMessage.error(msg || (isEdit.value ? t('messages.updateFailed') : t('messages.createFailed')))
  } finally {
    submitting.value = false
  }
}

const loadLocations = async () => {
  try {
    locations.value = await masterDataApi.getLocations()
  } catch {
    locations.value = []
  }
}

// 初始化
onMounted(async () => {
  await loadLocations()
  await loadProducts()
})
</script>

<style lang="scss" scoped>
.master-data-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  
  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}
</style>

<template>
  <div class="data-management-view">
    <h2 class="page-title">{{ t('dataManagement.title') }}</h2>

    <el-alert
      type="warning"
      :title="t('dataManagement.warningTitle')"
      :description="t('dataManagement.warningDesc')"
      show-icon
      :closable="false"
      class="warn-banner"
    />

    <div class="toolbar">
      <el-button
        type="danger"
        plain
        :disabled="selectedTypes.length === 0"
        :loading="loading"
        @click="handleClearSelected"
      >
        {{ t('dataManagement.clearSelected') }}
      </el-button>
      <el-button type="danger" :loading="loading" @click="handleClearAll">
        {{ t('dataManagement.clearAll') }}
      </el-button>
    </div>

    <el-table :data="tableRows" border class="type-table" size="default">
      <el-table-column width="52" align="center">
        <template #header>
          <el-checkbox
            :model-value="allChecked"
            :indeterminate="indeterminate"
            @change="(v) => onToggleAll(!!v)"
          />
        </template>
        <template #default="{ row }">
          <el-checkbox v-model="row.checked" />
        </template>
      </el-table-column>
      <el-table-column :label="t('dataManagement.columnType')" min-width="200">
        <template #default="{ row }">
          {{ t(row.labelKey) }}
        </template>
      </el-table-column>
      <el-table-column :label="t('dataManagement.columnDependency')" min-width="360">
        <template #default="{ row }">
          <span class="desc">{{ t(row.descKey) }}</span>
        </template>
      </el-table-column>
    </el-table>

    <el-card v-if="lastResult" shadow="never" class="last-result">
      <template #header>{{ t('dataManagement.lastResult') }}</template>
      <p class="result-cleared"><strong>cleared:</strong> {{ lastResult.cleared?.join(', ') }}</p>
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item
          v-for="(n, key) in lastResult.deleted_counts"
          :key="key"
          :label="String(key)"
        >
          {{ n }}
        </el-descriptions-item>
      </el-descriptions>
      <el-button type="primary" class="reload-btn" @click="reloadApp">
        {{ t('dataManagement.reloadApp') }}
      </el-button>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { dataManagementApi } from '@/api'
import { useI18nStore } from '@/stores/i18n'

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)
const router = useRouter()

/** 与后端 data_management.DATA_TYPES 顺序一致 */
const TYPE_DEFS = [
  { id: 'locations', labelKey: 'dataManagement.locations', descKey: 'dataManagement.locationsDesc' },
  { id: 'work_centers', labelKey: 'dataManagement.workCenters', descKey: 'dataManagement.workCentersDesc' },
  { id: 'resources', labelKey: 'dataManagement.resources', descKey: 'dataManagement.resourcesDesc' },
  { id: 'shifts', labelKey: 'dataManagement.shifts', descKey: 'dataManagement.shiftsDesc' },
  { id: 'products', labelKey: 'dataManagement.products', descKey: 'dataManagement.productsDesc' },
  { id: 'routings', labelKey: 'dataManagement.routings', descKey: 'dataManagement.routingsDesc' },
  { id: 'routing_operations', labelKey: 'dataManagement.routingOperations', descKey: 'dataManagement.routingOperationsDesc' },
  { id: 'setup_groups', labelKey: 'dataManagement.setupGroups', descKey: 'dataManagement.setupGroupsDesc' },
  { id: 'product_setup_groups', labelKey: 'dataManagement.productSetupGroups', descKey: 'dataManagement.productSetupGroupsDesc' },
  { id: 'setup_matrix', labelKey: 'dataManagement.setupMatrix', descKey: 'dataManagement.setupMatrixDesc' },
  { id: 'production_orders', labelKey: 'dataManagement.productionOrders', descKey: 'dataManagement.productionOrdersDesc' }
]

const tableRows = ref(TYPE_DEFS.map((d) => ({ ...d, checked: false })))
const loading = ref(false)
const lastResult = ref(null)

const selectedTypes = computed(() => tableRows.value.filter((r) => r.checked).map((r) => r.id))

const allChecked = computed(
  () => tableRows.value.length > 0 && tableRows.value.every((r) => r.checked)
)
const indeterminate = computed(
  () => selectedTypes.value.length > 0 && selectedTypes.value.length < tableRows.value.length
)

function onToggleAll(val) {
  const v = val === true
  tableRows.value.forEach((r) => {
    r.checked = v
  })
}

function isAdmin() {
  try {
    const u = JSON.parse(localStorage.getItem('user') || '{}')
    return !!u.is_admin
  } catch {
    return false
  }
}

onMounted(() => {
  if (!isAdmin()) {
    ElMessage.warning(t('user.clearDataAdminOnly'))
    router.replace('/dashboard')
  }
})

function reloadApp() {
  window.location.reload()
}

function formatApiError(error) {
  const d = error?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x?.msg || JSON.stringify(x)).join('; ')
  return error?.message || t('common.fail')
}

async function handleClearSelected() {
  if (selectedTypes.value.length === 0) {
    ElMessage.warning(t('dataManagement.selectAtLeastOne'))
    return
  }
  try {
    await ElMessageBox.confirm(
      t('dataManagement.confirmSelected'),
      t('dataManagement.confirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('dataManagement.clearSelected'),
        cancelButtonText: t('common.cancel'),
        confirmButtonClass: 'el-button--danger'
      }
    )
  } catch {
    return
  }
  loading.value = true
  lastResult.value = null
  try {
    const res = await dataManagementApi.clearData({ data_types: [...selectedTypes.value] })
    lastResult.value = res
    ElMessage.success(t('dataManagement.clearSuccess'))
    tableRows.value.forEach((r) => {
      r.checked = false
    })
  } catch (e) {
    ElMessage.error(formatApiError(e))
  } finally {
    loading.value = false
  }
}

async function handleClearAll() {
  try {
    await ElMessageBox.confirm(
      t('dataManagement.confirmAll'),
      t('dataManagement.confirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('dataManagement.clearAll'),
        cancelButtonText: t('common.cancel'),
        confirmButtonClass: 'el-button--danger'
      }
    )
  } catch {
    return
  }
  loading.value = true
  lastResult.value = null
  try {
    const res = await dataManagementApi.clearData({ all: true })
    lastResult.value = res
    ElMessage.success(t('dataManagement.clearSuccess'))
    tableRows.value.forEach((r) => {
      r.checked = false
    })
  } catch (e) {
    ElMessage.error(formatApiError(e))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.data-management-view {
  max-width: 960px;
}

.page-title {
  margin: 0 0 16px;
  font-size: 24px;
  font-weight: 500;
  color: var(--m3-on-surface, #1f1f1f);
}

.warn-banner {
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.type-table {
  margin-bottom: 24px;
}

.desc {
  font-size: 13px;
  color: var(--m3-on-surface-variant, #444746);
}

.last-result {
  margin-top: 8px;
}

.result-cleared {
  margin: 0 0 12px;
  font-size: 14px;
  word-break: break-all;
}

.reload-btn {
  margin-top: 16px;
}
</style>

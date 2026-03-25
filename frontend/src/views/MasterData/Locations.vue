<template>
  <div class="master-data-page">
    <div class="page-header">
      <h1>
        <el-icon><MapLocation /></el-icon>
        {{ t('menu.locations') }}
      </h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        {{ t('locations.add') }}
      </el-button>
    </div>

    <el-card>
      <el-table :data="items" v-loading="loading" stripe table-layout="auto">
        <el-table-column prop="code" :label="t('locations.code')" min-width="120" />
        <el-table-column prop="description" :label="t('locations.description')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" :label="t('locations.createdAt')" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('masterData.actions')" width="140" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleEdit(row)">{{ t('masterData.edit') }}</el-button>
              <el-button
                type="primary"
                link
                :disabled="row.code === '1001'"
                @click="handleDelete(row)"
              >
                {{ t('masterData.delete') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? t('locations.edit') : t('locations.add')" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item :label="t('locations.code')" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" :placeholder="t('locations.enterCode')" />
        </el-form-item>
        <el-form-item :label="t('locations.description')">
          <el-input v-model="form.description" type="textarea" rows="3" :placeholder="t('locations.enterDescription')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MapLocation, Plus } from '@element-plus/icons-vue'
import { masterDataApi } from '@/api'
import { useI18nStore } from '@/stores/i18n'
import { formatDisplayDateTime as formatDate } from '@/utils/displayDateTime'

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const loading = ref(false)
const items = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editCode = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  code: '',
  description: ''
})

const rules = computed(() => ({
  code: [{ required: true, message: t('locations.enterCode'), trigger: 'blur' }]
}))


async function load() {
  loading.value = true
  try {
    items.value = await masterDataApi.getLocations()
  } catch {
    ElMessage.error(t('locations.loadFailed'))
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editCode.value = null
  form.value = { code: '', description: '' }
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  editCode.value = row.code
  form.value = { code: row.code, description: row.description || '' }
  dialogVisible.value = true
}

async function handleDelete(row) {
  if (row.code === '1001') return
  try {
    await ElMessageBox.confirm(t('locations.confirmDelete').replace('{code}', row.code), t('orders.confirmDeleteTitle'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await masterDataApi.deleteLocation(row.code)
    ElMessage.success(t('messages.deleteSuccess'))
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(t('messages.deleteFailed'))
  }
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
    submitting.value = true
    const desc = form.value.description?.trim() ? form.value.description.trim() : null
    if (isEdit.value) {
      await masterDataApi.updateLocation(editCode.value, { description: desc })
      ElMessage.success(t('messages.updateSuccess'))
    } else {
      await masterDataApi.createLocation({ code: form.value.code.trim(), description: desc })
      ElMessage.success(t('messages.createSuccess'))
    }
    dialogVisible.value = false
    await load()
  } catch (e) {
    if (e !== false) ElMessage.error(isEdit.value ? t('messages.updateFailed') : t('messages.createFailed'))
  } finally {
    submitting.value = false
  }
}

onMounted(() => load())
</script>

<style lang="scss" scoped>
.master-data-page {
  min-height: calc(100vh - 100px);
}

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
}
</style>

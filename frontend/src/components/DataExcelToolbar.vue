<template>
  <div class="data-excel-toolbar">
    <template v-if="entities.length > 1">
      <el-dropdown trigger="click" @command="onDownloadCommand">
        <el-button>
          {{ t('dataExcel.downloadTemplate') }}
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-for="e in entities" :key="e.id" :command="e.id">
              {{ t(e.labelKey) }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-dropdown trigger="click" @command="onUploadCommand">
        <el-button>
          {{ t('dataExcel.uploadData') }}
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-for="e in entities" :key="'u-' + e.id" :command="e.id">
              {{ t(e.labelKey) }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </template>
    <template v-else-if="entities.length === 1">
      <el-button @click="download(entities[0].id)">{{ t('dataExcel.downloadTemplate') }}</el-button>
      <el-button @click="openFilePicker(entities[0].id)">{{ t('dataExcel.uploadData') }}</el-button>
    </template>
    <input
      ref="fileInputRef"
      type="file"
      accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      class="hidden-file-input"
      @change="onFileSelected"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { useI18nStore } from '@/stores/i18n'
import { dataManagementApi } from '@/api'

const props = defineProps({
  /** { id: data_type, labelKey: i18n key } */
  entities: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['imported'])

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const fileInputRef = ref(null)
const pendingDataType = ref('')

const locale = () => localStorage.getItem('locale') || 'zh-CN'

const download = async (dataType) => {
  try {
    await dataManagementApi.downloadTemplate(dataType, locale())
  } catch (e) {
    if (e?.response?.status === 401) return
    ElMessage.error(e?.message || t('dataExcel.downloadFailed'))
  }
}

const onDownloadCommand = (cmd) => download(cmd)

const openFilePicker = (dataType) => {
  pendingDataType.value = dataType
  fileInputRef.value && (fileInputRef.value.value = '')
  fileInputRef.value?.click()
}

const onUploadCommand = (cmd) => openFilePicker(cmd)

const onFileSelected = async (ev) => {
  const file = ev.target?.files?.[0]
  let dt = pendingDataType.value
  if (!dt && props.entities.length === 1) {
    dt = props.entities[0].id
  }
  if (!file || !dt) return
  try {
    const res = await dataManagementApi.importExcel(dt, file)
    if (res?.failed > 0) {
      const firstErr = res.errors?.[0]
      const extra = firstErr ? ` (${firstErr.row}: ${firstErr.message})` : ''
      ElMessage.warning(
        t('dataExcel.importPartial')
          .replace('{ok}', String(res.imported))
          .replace('{fail}', String(res.failed)) + extra
      )
    } else {
      const tpl = t('dataExcel.importSuccess') || 'OK {n}'
      ElMessage.success(tpl.replace('{n}', String(res?.imported ?? 0)))
    }
    emit('imported', res)
  } catch (e) {
    if (e?.response?.status === 401) {
      return
    }
    const d = e?.response?.data?.detail
    let msg =
      typeof d === 'string'
        ? d
        : Array.isArray(d)
          ? d.map((x) => x?.msg || JSON.stringify(x)).join('; ')
          : e?.message
    if (!msg) msg = t('dataExcel.importFailed')
    ElMessage.error(msg)
  } finally {
    pendingDataType.value = ''
    if (fileInputRef.value) fileInputRef.value.value = ''
  }
}
</script>

<style scoped>
.data-excel-toolbar {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.hidden-file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}
</style>

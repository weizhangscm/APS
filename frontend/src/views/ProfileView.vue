<template>
  <div class="profile-page">
    <div class="page-header">
      <h1>
        <el-icon><User /></el-icon>
        {{ t('profilePage.title') }}
      </h1>
    </div>

    <el-card class="profile-card" shadow="never" v-loading="loading">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
        class="profile-form"
        @submit.prevent
      >
        <el-form-item :label="t('profilePage.username')">
          <el-input v-model="form.username" disabled :placeholder="t('profilePage.usernameHint')" />
        </el-form-item>
        <el-form-item :label="t('profilePage.fullName')" prop="full_name">
          <el-input v-model="form.full_name" clearable maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item :label="t('profilePage.email')" prop="email">
          <el-input v-model="form.email" clearable maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item :label="t('profilePage.department')" prop="department">
          <el-input v-model="form.department" clearable maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item :label="t('profilePage.dateFormat')" prop="date_format">
          <el-select
            v-model="form.date_format"
            clearable
            filterable
            :placeholder="t('profilePage.selectDateFormatPlaceholder')"
            class="field-wide"
          >
            <el-option
              v-for="opt in dateFormatOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('profilePage.timeFormat')" prop="time_format">
          <el-select
            v-model="form.time_format"
            clearable
            :placeholder="t('profilePage.selectTimeFormatPlaceholder')"
            class="field-wide"
          >
            <el-option
              v-for="opt in timeFormatOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('profilePage.timezone')" prop="user_timezone">
          <el-select
            v-model="form.user_timezone"
            clearable
            filterable
            :placeholder="t('profilePage.selectTimezonePlaceholder')"
            class="field-wide"
          >
            <el-option v-for="tz in timezoneOptions" :key="tz" :label="tz" :value="tz" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">
            {{ t('profilePage.save') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { authApi } from '@/api'
import { useI18nStore } from '@/stores/i18n'
import { useUserDisplayPrefsStore } from '@/stores/userDisplayPrefs'

const DATE_FORMAT_VALUES = [
  'YYYY-MM-DD',
  'MM/DD/YYYY',
  'DD/MM/YYYY',
  'DD.MM.YYYY',
  'YYYY/MM/DD',
  'YYYY年MM月DD日'
]

const TIME_FORMAT_VALUES = ['24h', '12h']

function buildTimezoneList() {
  try {
    if (typeof Intl !== 'undefined' && typeof Intl.supportedValuesOf === 'function') {
      return Intl.supportedValuesOf('timeZone')
    }
  } catch {
    /* ignore */
  }
  return [
    'UTC',
    'Asia/Shanghai',
    'Asia/Tokyo',
    'Asia/Singapore',
    'Europe/London',
    'Europe/Berlin',
    'America/New_York',
    'America/Los_Angeles'
  ]
}

const i18nStore = useI18nStore()
const { currentMessages } = storeToRefs(i18nStore)
const t = (key) => i18nStore.t(key)

const formRef = ref(null)
const loading = ref(true)
const saving = ref(false)

const form = reactive({
  username: '',
  full_name: '',
  email: '',
  department: '',
  date_format: '',
  time_format: '',
  user_timezone: ''
})

const timezoneOptions = buildTimezoneList()

const dateFormatOptions = computed(() => {
  const pack = currentMessages.value?.profilePage?.dateFormats || {}
  return DATE_FORMAT_VALUES.map((value) => ({
    value,
    label: pack[value] || value
  }))
})

const timeFormatOptions = computed(() => {
  const pack = currentMessages.value?.profilePage?.timeFormats || {}
  return TIME_FORMAT_VALUES.map((value) => ({
    value,
    label: pack[value] || value
  }))
})

const rules = computed(() => ({
  email: [
    {
      validator: (_rule, value, callback) => {
        const v = (value || '').trim()
        if (!v) {
          callback()
          return
        }
        const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
        if (!ok) callback(new Error(i18nStore.t('profilePage.emailInvalid')))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}))

function mergeStoredUser(serverUser) {
  try {
    const raw = localStorage.getItem('user')
    const prev = raw ? JSON.parse(raw) : {}
    localStorage.setItem('user', JSON.stringify({ ...prev, ...serverUser }))
  } catch {
    localStorage.setItem('user', JSON.stringify(serverUser))
  }
  useUserDisplayPrefsStore().hydrateFromLocalStorage()
}

async function loadProfile() {
  loading.value = true
  try {
    const data = await authApi.getCurrentUser()
    form.username = data.username || ''
    form.full_name = data.full_name || ''
    form.email = data.email || ''
    form.department = data.department || ''
    form.date_format = data.date_format || ''
    form.time_format = data.time_format || ''
    form.user_timezone = data.user_timezone || ''
    mergeStoredUser({
      id: data.id,
      username: data.username,
      full_name: data.full_name,
      email: data.email,
      department: data.department,
      date_format: data.date_format,
      time_format: data.time_format,
      user_timezone: data.user_timezone,
      is_admin: data.is_admin
    })
  } catch (e) {
    ElMessage.error(i18nStore.t('profilePage.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const payload = {
        full_name: form.full_name.trim() || null,
        email: form.email.trim() || null,
        department: form.department.trim() || null,
        date_format: form.date_format || null,
        time_format: form.time_format || null,
        user_timezone: form.user_timezone || null
      }
      const res = await authApi.updateProfile(payload)
      if (res.user) {
        mergeStoredUser(res.user)
      }
      ElMessage.success(i18nStore.t('profilePage.saveSuccess'))
    } catch (error) {
      const msg = error.response?.data?.detail
      ElMessage.error(
        typeof msg === 'string' ? msg : i18nStore.t('profilePage.saveFailed')
      )
    } finally {
      saving.value = false
    }
  })
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped lang="scss">
.profile-page {
  max-width: 720px;
}

.page-header {
  margin-bottom: 20px;

  h1 {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 22px;
    font-weight: 600;
    color: #1f1f1f;
    margin: 0;
  }
}

.profile-card {
  border-radius: 16px;
  border: 1px solid #e3e5e8;
}

.profile-form {
  padding-top: 8px;
  max-width: 560px;
}

.field-wide {
  width: 100%;
  max-width: 400px;
}
</style>

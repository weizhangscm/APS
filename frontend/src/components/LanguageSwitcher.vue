<template>
  <el-button
    type="text"
    @click="toggleLanguage"
    class="language-switcher"
    :title="currentLanguageTitle"
  >
    <el-icon class="language-icon">
      <component :is="currentLanguageIcon" />
    </el-icon>
    <span>{{ currentLanguageText }}</span>
  </el-button>
</template>

<script setup>
import { computed } from 'vue'
import { useI18nStore } from '@/stores/i18n'
import { Flag, Management } from '@element-plus/icons-vue'

const i18nStore = useI18nStore()

const currentLanguageText = computed(() => {
  return i18nStore.t('language.current')
})

const currentLanguageTitle = computed(() => {
  return i18nStore.t('language.switchTo')
})

const currentLanguageIcon = computed(() => {
  return i18nStore.currentLocale === 'zh-CN' ? Management : Flag
})

const toggleLanguage = () => {
  i18nStore.toggleLocale()
}
</script>

<style lang="scss" scoped>
.language-switcher {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;

  &:hover {
    background-color: #f5f5f5;
    color: #333;
  }

  .language-icon {
    font-size: 16px;
  }

  span {
    font-weight: 500;
  }
}
</style>
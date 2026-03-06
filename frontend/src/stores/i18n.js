import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { messages, defaultLocale } from '@/i18n'

export const useI18nStore = defineStore('i18n', () => {
  // 当前语言
  const currentLocale = ref(localStorage.getItem('locale') || defaultLocale)

  // 当前语言包
  const currentMessages = computed(() => messages[currentLocale.value] || messages[defaultLocale])

  // 设置语言
  const setLocale = (locale) => {
    if (messages[locale]) {
      currentLocale.value = locale
      localStorage.setItem('locale', locale)
    }
  }

  // 切换语言
  const toggleLocale = () => {
    const newLocale = currentLocale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
    setLocale(newLocale)
  }

  // 获取翻译文本
  const t = (key) => {
    const keys = key.split('.')
    let value = currentMessages.value

    for (const k of keys) {
      value = value?.[k]
    }

    return value || key
  }

  return {
    currentLocale,
    currentMessages,
    setLocale,
    toggleLocale,
    t
  }
})
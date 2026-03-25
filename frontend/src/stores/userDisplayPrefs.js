import { defineStore } from 'pinia'

/**
 * 与 localStorage user 同步的展示偏好（日期/时间/时区），供全局格式化与 Element 控件 format 绑定。
 */
export const useUserDisplayPrefsStore = defineStore('userDisplayPrefs', {
  state: () => ({
    date_format: null,
    time_format: null,
    user_timezone: null
  }),
  actions: {
    hydrateFromLocalStorage() {
      try {
        const u = JSON.parse(localStorage.getItem('user') || '{}')
        this.date_format = u.date_format ?? null
        this.time_format = u.time_format ?? null
        this.user_timezone = u.user_timezone ?? null
      } catch {
        this.date_format = null
        this.time_format = null
        this.user_timezone = null
      }
    }
  }
})

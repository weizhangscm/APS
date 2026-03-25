import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.extend(utc)
dayjs.extend(timezone)

import { useUserDisplayPrefsStore } from '@/stores/userDisplayPrefs'

const DEFAULT_PROFILE_DATE = 'YYYY-MM-DD'

/** 与个人信息 / 后端 ALLOWED_DATE_FORMATS 一致 */
const PROFILE_TO_DAYJS = {
  'YYYY-MM-DD': 'YYYY-MM-DD',
  'MM/DD/YYYY': 'MM/DD/YYYY',
  'DD/MM/YYYY': 'DD/MM/YYYY',
  'DD.MM.YYYY': 'DD.MM.YYYY',
  'YYYY/MM/DD': 'YYYY/MM/DD',
  'YYYY年MM月DD日': 'YYYY年MM月DD日'
}

/** dhtmlx-gantt 时间轴 strftime 风格 */
const PROFILE_TO_GANTT_FULL = {
  'YYYY-MM-DD': '%Y-%m-%d',
  'MM/DD/YYYY': '%m/%d/%Y',
  'DD/MM/YYYY': '%d/%m/%Y',
  'DD.MM.YYYY': '%d.%m.%Y',
  'YYYY/MM/DD': '%Y/%m/%d',
  'YYYY年MM月DD日': '%Y年%m月%d日'
}

const PROFILE_TO_GANTT_COMPACT = {
  'YYYY-MM-DD': '%m-%d',
  'MM/DD/YYYY': '%m/%d',
  'DD/MM/YYYY': '%d/%m',
  'DD.MM.YYYY': '%d.%m',
  'YYYY/MM/DD': '%m/%d',
  'YYYY年MM月DD日': '%m月%d日'
}

export function profileDateFormatToDayjs(profileKey) {
  const k = profileKey || DEFAULT_PROFILE_DATE
  return PROFILE_TO_DAYJS[k] || PROFILE_TO_DAYJS[DEFAULT_PROFILE_DATE]
}

export function profileDateFormatToGanttFull(profileKey) {
  const k = profileKey || DEFAULT_PROFILE_DATE
  return PROFILE_TO_GANTT_FULL[k] || PROFILE_TO_GANTT_FULL[DEFAULT_PROFILE_DATE]
}

export function profileDateFormatToGanttCompact(profileKey) {
  const k = profileKey || DEFAULT_PROFILE_DATE
  return PROFILE_TO_GANTT_COMPACT[k] || PROFILE_TO_GANTT_COMPACT[DEFAULT_PROFILE_DATE]
}

export function timeFormatToDayjsPattern(timeFormat) {
  return timeFormat === '12h' ? 'hh:mm A' : 'HH:mm'
}

export function ganttHourScaleFormat(timeFormat) {
  return timeFormat === '12h' ? '%h:%i %A' : '%H:00'
}

/**
 * 将时刻转换到用户偏好时区再格式化（无时区偏好则用本地解析）。
 */
export function toDisplayDayjs(input, userTimezone) {
  if (input == null || input === '') return null
  const str = typeof input === 'string' ? input.trim() : ''

  if (userTimezone) {
    try {
      if (str && /^\d{4}-\d{2}-\d{2}$/.test(str)) {
        const d = dayjs.tz(str, userTimezone)
        if (d.isValid()) return d
      }
      // 后端/SQLite 多为「无时区」的 ISO（无 Z / 无 ±offset）。若先按 UTC 再换算到用户时区，
      // 墙钟会整体偏移（例如 +8h），订单工序时间与甘特/数据库语义不一致。
      const hasTzSuffix =
        str && (/Z$/i.test(str) || /[+-]\d{2}:\d{2}$/.test(str) || /[+-]\d{4}$/.test(str))
      const looksNaiveDateTime =
        str &&
        /^\d{4}-\d{2}-\d{2}[T ]\d{1,2}:\d{2}/.test(str) &&
        !hasTzSuffix
      if (looksNaiveDateTime) {
        const norm = str.replace(' ', 'T').split('.')[0]
        const clipped = norm.length >= 19 ? norm.slice(0, 19) : norm
        const d = dayjs.tz(clipped, userTimezone)
        if (d.isValid()) return d
      }
      const asUtc = dayjs.utc(input)
      if (asUtc.isValid()) return asUtc.tz(userTimezone)
    } catch {
      /* fall through */
    }
  }

  const d = dayjs(input)
  return d.isValid() ? d : null
}

export function formatDisplayDateWithPrefs(input, prefs) {
  const tz = prefs?.user_timezone || null
  const df = profileDateFormatToDayjs(prefs?.date_format)
  const d = toDisplayDayjs(input, tz)
  return d ? d.format(df) : ''
}

export function formatDisplayDateTimeWithPrefs(input, prefs) {
  const tz = prefs?.user_timezone || null
  const df = profileDateFormatToDayjs(prefs?.date_format)
  const tf = timeFormatToDayjsPattern(prefs?.time_format === '12h' ? '12h' : '24h')
  const d = toDisplayDayjs(input, tz)
  return d ? d.format(`${df} ${tf}`) : ''
}

export function formatDisplayTimeWithPrefs(input, prefs) {
  const tz = prefs?.user_timezone || null
  const tf = timeFormatToDayjsPattern(prefs?.time_format === '12h' ? '12h' : '24h')
  const d = toDisplayDayjs(input, tz)
  return d ? d.format(tf) : ''
}

/** 表格/描述列表等：依赖 store，模板中调用会随偏好更新 */
export function formatDisplayDate(input) {
  const s = useUserDisplayPrefsStore()
  return formatDisplayDateWithPrefs(input, s)
}

export function formatDisplayDateTime(input) {
  const s = useUserDisplayPrefsStore()
  return formatDisplayDateTimeWithPrefs(input, s)
}

export function formatDisplayTime(input) {
  const s = useUserDisplayPrefsStore()
  return formatDisplayTimeWithPrefs(input, s)
}

/** Element Plus date-picker 展示用（value-format 仍用 YYYY-MM-DD） */
export function elementDatePickerDisplayFormat() {
  const s = useUserDisplayPrefsStore()
  return profileDateFormatToDayjs(s.date_format)
}

/** datetime 组合展示格式 */
export function elementDateTimePickerDisplayFormat() {
  const s = useUserDisplayPrefsStore()
  const df = profileDateFormatToDayjs(s.date_format)
  const tf = timeFormatToDayjsPattern(s.time_format === '12h' ? '12h' : '24h')
  return `${df} ${tf}`
}

/** Element Plus time-picker 展示（value-format 仍可 HH:mm） */
export function elementTimePickerDisplayFormat() {
  const s = useUserDisplayPrefsStore()
  return timeFormatToDayjsPattern(s.time_format === '12h' ? '12h' : '24h')
}

/** 甘特/利用率图横轴：当天 0–23 点刻度文字 */
export function formatDisplayHourOfDay(hour) {
  const s = useUserDisplayPrefsStore()
  const d = dayjs().hour(hour).minute(0).second(0).millisecond(0)
  return formatDisplayTimeWithPrefs(d, s)
}

/** 班次等「HH:mm」字符串按当前用户时间格式展示 */
export function formatDisplayTimeFromHm(hm) {
  if (hm == null || hm === '') return ''
  const s = String(hm).trim()
  const m = s.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?/)
  if (!m) return s
  const d = dayjs().hour(Number(m[1])).minute(Number(m[2])).second(Number(m[3] || 0))
  return formatDisplayTime(d)
}

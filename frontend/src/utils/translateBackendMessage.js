/**
 * Translates backend Chinese messages to the current locale for display.
 * Used for plan result messages and plan log message/error details.
 * @param {string} message - Raw message from API (may be Chinese)
 * @param {function} t - i18n t(key) function
 * @param {string} locale - Current locale, e.g. 'en-US' or 'zh-CN'
 * @returns {string} Message to display
 */
export function translateBackendMessage (message, t, locale) {
  if (!message || typeof message !== 'string') return message || ''
  if (locale !== 'en-US') return message

  const m = message.trim()

  // 已保存 X 个订单的 Y 道工序排程
  const savedMatch = m.match(/^已保存 (\d+) 个订单的 (\d+) 道工序排程$/)
  if (savedMatch) {
    return t('dsView.savedOrdersOperations').replace('{orders}', savedMatch[1]).replace('{ops}', savedMatch[2])
  }

  // 已取消 X 个订单的 Y 道工序排程
  const cancelledMatch = m.match(/^已取消 (\d+) 个订单的 (\d+) 道工序排程$/)
  if (cancelledMatch) {
    return t('dsView.cancelledOrdersOperations').replace('{orders}', cancelledMatch[1]).replace('{ops}', cancelledMatch[2])
  }

  // 已丢弃 X 道工序的排程更改
  const discardedMatch = m.match(/^已丢弃 (\d+) 道工序的排程更改$/)
  if (discardedMatch) {
    return t('dsView.discardedOperationsCount').replace('{count}', discardedMatch[1])
  }

  if (m === '没有找到需要保存的排程') return t('dsView.noScheduleToSave')
  if (m === '没有找到需要取消的排程') return t('dsView.noScheduleToCancel')
  if (m === '没有需要丢弃的排程更改') return t('dsView.noChangesToDiscard')
  if (m === '请指定要保存计划的资源或产品') return t('dsView.specifyResourceOrProductForSave')
  if (m === '请指定要取消计划的资源或产品') return t('dsView.specifyResourceOrProductForCancel')

  // 显示区间内产能已用尽，排程已终止。以下订单无法排程：PLN123（工序 功能测试 在资源上找不到可用时间槽）；...
  const prefixZh = '显示区间内产能已用尽，排程已终止。以下订单无法排程：'
  if (m.startsWith(prefixZh)) {
    const rest = m.slice(prefixZh.length)
    const parts = rest.split('；').map(part => {
      const bracket = part.indexOf('（')
      if (bracket === -1) return part
      const orderPart = part.slice(0, bracket).trim()
      const errorPart = part.slice(bracket + 1, part.endsWith('）') ? part.length - 1 : part.length).trim()
      const translatedError = translateBackendError(errorPart, t, locale)
      return `${orderPart} (${translatedError})`
    })
    return t('dsView.capacityExhaustedPrefix') + parts.join('; ')
  }

  return message
}

/**
 * Translates backend error detail (e.g. plan log detail.error) to current locale.
 * @param {string} error - Raw error string from API
 * @param {function} t - i18n t(key) function
 * @param {string} locale - Current locale
 * @returns {string} Error text to display
 */
export function translateBackendError (error, t, locale) {
  if (!error || typeof error !== 'string') return error || ''
  if (locale !== 'en-US') return error

  // 工序 XXX 在资源上找不到可用时间槽
  const opMatch = error.match(/^工序 (.+) 在资源上找不到可用时间槽$/)
  if (opMatch) {
    return t('dsView.operationNoTimeSlot').replace('{op}', opMatch[1].trim())
  }

  return error
}

<template>
  <div class="chatbot-wrapper">
    <!-- 浮动按钮：WE APS / AI Agent -->
    <el-button
      class="chatbot-float-btn"
      type="primary"
      circle
      @click="drawerVisible = true"
    >
      <!-- 默认：We（与附件图片一致）；Hover：两行 WE APS / AI Agent -->
      <span class="we-float-logo" aria-hidden="true">
        <img class="we-float-logo__img" src="@/assets/we-logo.png" alt="We" />
      </span>
      <span class="ai-pilot-hover-label" aria-hidden="true">APS AI Agent</span>
    </el-button>

    <!-- 聊天抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      size="400px"
      class="chatbot-drawer"
      :with-header="true"
      :show-close="false"
      :modal="false"
      :lock-scroll="false"
      modal-penetrable
      modal-class="chatbot-drawer-overlay"
    >
      <template #header>
        <div class="pilot-header-bar">
          <div class="pilot-left">
            <div class="pilot-avatar" aria-hidden="true">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="pilot-meta">
              <div class="pilot-title">We APS AI Agent</div>
            </div>
          </div>
          <div class="pilot-header-actions">
            <button
              v-show="messages.length > 0"
              class="pilot-back"
              type="button"
              @click="goBackToInitial"
              :title="t('chatbot.back')"
            >
              <el-icon><ArrowLeft /></el-icon>
            </button>
            <button class="pilot-close" type="button" @click="drawerVisible = false" :title="t('common.cancel')">
              <el-icon><Close /></el-icon>
            </button>
          </div>
        </div>
      </template>
      <div class="chatbot-body">
        <!-- 消息列表 -->
        <div class="chat-messages" ref="messagesRef">
          <div v-if="!loading && messages.length === 0" class="pilot-hero">
            <div class="pilot-hero__logo" aria-hidden="true">
              <div class="pilot-hero__logo-main">Westernacher</div>
              <div class="pilot-hero__logo-sub">NONSTOP INNOVATION</div>
            </div>
            <div class="pilot-hero__title">{{ t('chatbot.heroTitle') }}</div>
            <div class="pilot-hero__subtitle">{{ t('chatbot.heroSubtitle') }}</div>
            <div class="pilot-hero__quick">
              <button
                v-for="(q, idx) in quickPrompts"
                :key="idx"
                class="pilot-quick-btn"
                type="button"
                :disabled="q.disabled || loading"
                @click="handleQuickPrompt(q)"
              >
                <span class="pilot-quick-btn__icon" aria-hidden="true">{{ q.icon }}</span>
                <span class="pilot-quick-btn__text">{{ t(q.labelKey) }}</span>
              </button>
            </div>
          </div>

          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['chat-message', msg.role]"
          >
            <div class="message-avatar" :class="{ 'avatar-ai': msg.role === 'assistant' }">
              <el-icon v-if="msg.role === 'user'"><User /></el-icon>
              <el-icon v-else class="ai-icon"><Cpu /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text">{{ msg.content }}</div>
            </div>
          </div>
          <div v-if="loading" class="chat-message assistant">
            <div class="message-avatar avatar-ai"><el-icon class="ai-icon"><Cpu /></el-icon></div>
            <div class="message-content">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>{{ t('chatbot.thinking') }}</span>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="chat-input-area">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :placeholder="t('chatbot.placeholder')"
            :autosize="{ minRows: 2, maxRows: 4 }"
            @keydown.enter.exact.prevent="sendMessage"
            :disabled="loading"
          />
          <el-button
            type="primary"
            :loading="loading"
            :icon="Promotion"
            @click="sendMessage"
            class="send-btn"
          >
            {{ t('chatbot.send') }}
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onUnmounted } from 'vue'
import { Cpu, Close, User, Promotion, Loading, ArrowLeft } from '@element-plus/icons-vue'
import { useI18nStore } from '@/stores/i18n'
import { useSchedulingStore } from '@/stores/scheduling'
import { chatbotApi } from '@/api'

const i18nStore = useI18nStore()
const schedulingStore = useSchedulingStore()
const t = (key) => i18nStore.t(key)

function getLocale() {
  // Pinia setup store 的 ref 在部分场景下不会自动解包，这里统一取字符串
  return i18nStore.currentLocale?.value ?? i18nStore.currentLocale ?? 'zh-CN'
}

const drawerVisible = ref(false)
const inputMessage = ref('')
const loading = ref(false)
const messages = ref([])
const messagesRef = ref(null)
// 下一轮发送时带给后端的上下文（如已记录的启发式参数）
const chatContext = ref({})
// 会话ID，用于维持多轮对话上下文
const conversationId = ref(null)

// 初始化会话ID（在组件加载时生成）
if (!conversationId.value) {
  conversationId.value = `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

const quickPrompts = [
  {
    icon: '⏰',
    labelKey: 'chatbot.quickDelayedOrders',
    text: '展示延误订单信息',
    textEn: 'Which orders are delayed?'
  },
  {
    icon: '⚡',
    labelKey: 'chatbot.quickHeuristic',
    text: '请执行启发式排程',
    textEn: 'Run heuristic scheduling'
  },
  {
    icon: '📊',
    labelKey: 'chatbot.quickDemo2',
    text: '对比 EDD 与 SPT 排程',
    textEn: 'Compare EDD vs SPT scheduling'
  },
  {
    icon: '⚡',
    labelKey: 'chatbot.quickDemo4',
    text: 'CNC-01 故障事件',
    textEn: 'CNC-01 Breakdown Event'
  },
  {
    icon: '✓',
    labelKey: 'chatbot.quickDemo5',
    text: '计划员确认方案 C',
    textEn: 'Planner confirms Scenario C'
  }
]

function handleQuickPrompt(q) {
  if (!q || loading.value) return
  const locale = getLocale()
  const msg = String(locale).toLowerCase().startsWith('en') ? (q.textEn || q.text) : q.text
  inputMessage.value = msg
  sendMessage()
}

async function sendMessage() {
  const text = (inputMessage.value || '').trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputMessage.value = ''
  loading.value = true

  try {
    const ctx = { ...chatContext.value, locale: getLocale() }
    const res = await chatbotApi.sendMessage(text, ctx, conversationId.value)
    const reply = res?.reply ?? t('chatbot.noReply')
    const actionResult = res?.action_result ?? null
    const actionType = res?.action_type ?? null
    if (res?.context_for_next != null) {
      chatContext.value = res.context_for_next
    } else {
      chatContext.value = {}
    }
    messages.value.push({
      role: 'assistant',
      content: reply,
      action_result: actionResult,
      action_type: actionType
    })
    // We Agent 运行启发式排程或保存计划成功后，自动刷新详细计划表页面
    if (actionResult?.success && (actionType === 'run_heuristic' || actionType === 'save_plan')) {
      schedulingStore.requestScheduleRefresh()
    }
  } catch (err) {
    const msg = err.response?.data?.detail ?? err.message ?? t('chatbot.sendFailed')
    messages.value.push({
      role: 'assistant',
      content: t('chatbot.errorPrefix') + msg,
      action_result: null,
      action_type: null
    })
  } finally {
    loading.value = false
    await nextTick()
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  }
}

function goBackToInitial() {
  if (loading.value) return
  messages.value = []
  chatContext.value = {}
  // 生成新的会话ID，开始新的对话
  conversationId.value = `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

const BODY_DRAWER_OPEN_CLASS = 'we-agent-drawer-open'
const DRAWER_WIDTH_PX = 400

watch(drawerVisible, (visible) => {
  if (visible) {
    document.body.classList.add(BODY_DRAWER_OPEN_CLASS)
    nextTick(() => {
      if (messagesRef.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight
      }
    })
  } else {
    document.body.classList.remove(BODY_DRAWER_OPEN_CLASS)
  }
})

onUnmounted(() => {
  document.body.classList.remove(BODY_DRAWER_OPEN_CLASS)
})
</script>

<style lang="scss" scoped>
/* Shared tokens for the float button hover overlay */
$we-agent-blue: #1e88e5;
$we-agent-white: #ffffff;

.chatbot-wrapper {
  position: fixed;
  right: 24px;
  bottom: 48px;
  z-index: 1000;
}

.pilot-hero {
  padding: 14px 12px 10px;
  border-radius: 18px;
  background: radial-gradient(1000px 520px at 50% 0%, rgba(66, 153, 225, 0.24), transparent 60%),
    linear-gradient(180deg, rgba(11, 18, 32, 0.94) 0%, rgba(10, 16, 32, 0.94) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
  margin-bottom: 14px;
  text-align: center;
}

.pilot-hero__logo {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  background: #ffffff;
  color: #1f2937;
  border-radius: 10px;
  padding: 12px 16px;
  min-width: 260px;
  margin: 4px auto 14px;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.18);
}

.pilot-hero__logo-main {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 0.00em;
  line-height: 1.05;
}

.pilot-hero__logo-sub {
  font-size: 11px;
  font-weight: 800;
  color: #0099cc;
  margin-top: 4px;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  align-self: flex-end;
}

.pilot-hero__title {
  font-size: 18px;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.95);
  margin-top: 2px;
}

.pilot-hero__subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.70);
  margin-top: 8px;
}

.pilot-hero__quick {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pilot-quick-btn {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.92);
  border-radius: 14px;
  padding: 12px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  text-align: left;
  transition: transform 0.12s, background 0.12s, border-color 0.12s;

  &:hover:enabled {
    transform: translateY(-1px);
    background: rgba(255, 255, 255, 0.09);
    border-color: rgba(66, 153, 225, 0.32);
  }

  &:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
}

.pilot-quick-btn__icon {
  width: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.pilot-quick-btn__text {
  font-size: 14px;
  font-weight: 650;
  letter-spacing: 0.01em;
}

.pilot-header-bar {
  // el-drawer 默认 header 有 padding，这里用负 margin 让背景铺满到边缘
  margin: -14px -16px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: calc(100% + 32px);
  background: radial-gradient(1200px 500px at 20% -20%, rgba(66, 153, 225, 0.35), transparent 60%),
    linear-gradient(180deg, #0b1220 0%, #0a1020 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.92);
}

.pilot-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.pilot-avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0099cc;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
  .el-icon {
    font-size: 20px;
    color: rgba(255, 255, 255, 0.95);
  }
}

.pilot-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.pilot-title {
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pilot-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pilot-back,
.pilot-close {
  appearance: none;
  border: none;
  background: transparent;
  cursor: pointer;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.85);
  transition: background 0.15s, color 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.10);
    color: rgba(255, 255, 255, 0.95);
  }
}

/* We 按钮：恢复为圆形 */
.chatbot-float-btn {
  width: 56px;
  height: 56px;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 50% !important;
  overflow: visible;
  background: transparent !important;
  box-shadow: none !important;
  position: relative;
}

.we-float-logo {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
}

.we-float-logo__img {
  width: 56px;
  height: 56px;
  display: block;
  object-fit: cover;
}

.ai-pilot-hover-label {
  position: absolute;
  display: none;
  align-items: center;
  justify-content: center;
  user-select: none;
  /* show text at the LEFT side of button */
  right: calc(100% + 10px);
  top: 50%;
  transform: translateY(-50%);
  padding: 4px 8px;
  border-radius: 8px;
  background: $we-agent-blue;
  box-shadow: none;
  pointer-events: none;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
  font-weight: 800;
  font-size: 10px;
  letter-spacing: 0.02em;
  white-space: nowrap;
  color: #fff;
}

.chatbot-float-btn:hover .ai-pilot-hover-label {
  display: inline-flex;
}

.chatbot-drawer :deep(.el-drawer__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chatbot-body {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-message {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  max-width: 100%;

  &.user {
    flex-direction: row-reverse;
    .message-content { align-items: flex-end; }
    .message-text { background: var(--el-color-primary); color: #fff; border-radius: 12px 12px 4px 12px; }
  }

  &.assistant .message-text {
    background: var(--el-fill-color-light);
    color: var(--el-text-color-primary);
    border-radius: 12px 12px 12px 4px;
  }
}

.message-avatar {
  width: 36px;
  height: 36px;
  min-width: 36px;
  border-radius: 50%;
  background: var(--el-fill-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--el-text-color-secondary);
}

.message-content {
  max-width: 80%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.message-text {
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-line;  /* 保留换行，每行一条（如延误订单列表） */
}

.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--el-bg-color);
}

.send-btn {
  align-self: flex-end;
}
</style>

<style lang="scss">
/* 遮罩不阻挡主界面点击，抽屉打开时仍可操作 APS */
.chatbot-drawer-overlay {
  pointer-events: none !important;
}

/* 打开 We APS AI Agent 时为主页面增加横向滚动条，避免内容被遮挡 */
body.we-agent-drawer-open {
  overflow-x: auto;
}
body.we-agent-drawer-open #app {
  min-width: calc(100vw + 400px);
}
</style>

<template>
  <div class="chatbot-wrapper">
    <!-- 浮动按钮 -->
    <el-button
      class="chatbot-float-btn"
      type="primary"
      circle
      :icon="ChatDotRound"
      @click="drawerVisible = true"
      :title="t('chatbot.open')"
    />

    <!-- 聊天抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="t('chatbot.title')"
      direction="rtl"
      size="400px"
      class="chatbot-drawer"
      :with-header="true"
    >
      <div class="chatbot-body">
        <!-- 消息列表 -->
        <div class="chat-messages" ref="messagesRef">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['chat-message', msg.role]"
          >
            <div class="message-avatar">
              <el-icon v-if="msg.role === 'user'"><User /></el-icon>
              <el-icon v-else><ChatDotRound /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text">{{ msg.content }}</div>
              <div v-if="msg.action_result" class="message-action">
                <el-tag size="small" type="info">{{ msg.action_type }}</el-tag>
                <pre class="action-result">{{ formatActionResult(msg.action_result) }}</pre>
              </div>
            </div>
          </div>
          <div v-if="loading" class="chat-message assistant">
            <div class="message-avatar"><el-icon><ChatDotRound /></el-icon></div>
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
import { ref, nextTick, watch } from 'vue'
import { ChatDotRound, User, Promotion, Loading } from '@element-plus/icons-vue'
import { useI18nStore } from '@/stores/i18n'
import { chatbotApi } from '@/api'

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const drawerVisible = ref(false)
const inputMessage = ref('')
const loading = ref(false)
const messages = ref([])
const messagesRef = ref(null)

function formatActionResult(obj) {
  if (obj == null) return ''
  if (typeof obj === 'string') return obj
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

async function sendMessage() {
  const text = (inputMessage.value || '').trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputMessage.value = ''
  loading.value = true

  try {
    const res = await chatbotApi.sendMessage(text, {})
    const reply = res?.reply ?? t('chatbot.noReply')
    const actionResult = res?.action_result ?? null
    const actionType = res?.action_type ?? null
    messages.value.push({
      role: 'assistant',
      content: reply,
      action_result: actionResult,
      action_type: actionType
    })
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

watch(drawerVisible, (visible) => {
  if (visible) {
    nextTick(() => {
      if (messagesRef.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight
      }
    })
  }
})
</script>

<style lang="scss" scoped>
.chatbot-wrapper {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1000;
}

.chatbot-float-btn {
  width: 56px;
  height: 56px;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
}

.message-action {
  width: 100%;
  margin-top: 4px;
  .action-result {
    margin: 6px 0 0;
    padding: 8px;
    font-size: 12px;
    background: var(--el-fill-color-dark);
    border-radius: 6px;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
  }
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

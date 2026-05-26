<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="router.push('/home')">← 返回</button>
      <h1>资源中心</h1>
    </header>

    <div class="layout">
      <!-- 左栏：章节树 + 会话 + 对话 -->
      <div class="left-panel">
        <!-- 章节树 -->
        <div class="chapter-tree" :class="{ collapsed: treeCollapsed }">
          <div class="tree-header" @click="treeCollapsed = !treeCollapsed">
            <span>📂 知识章节</span>
            <span class="tree-toggle">{{ treeCollapsed ? '▶' : '▼' }}</span>
          </div>
          <div class="tree-body" v-show="!treeCollapsed">
            <div v-if="chapters.length === 0" class="tree-empty">暂无章节</div>
            <div v-for="ch in chapters" :key="ch.id" class="tree-node"
                 @click="quickAsk(ch)">
              {{ ch.title }}
            </div>
          </div>
        </div>

        <!-- 会话管理 -->
        <div class="session-bar">
          <div class="session-header">
            <span>💬 对话</span>
            <button class="new-session-btn" @click="newSession" :disabled="waiting">+ 新建</button>
          </div>
          <div class="session-list" v-if="sessions.length">
            <div v-for="s in sessions" :key="s.id" class="session-item"
                 :class="{ active: s.id === sessionId }"
                 @click="switchSession(s)">
              <span class="s-title" :title="s.title">{{ s.title }}</span>
              <span class="s-actions" v-if="s.id === sessionId">
                <button class="s-action-btn" @click.stop="renameSession(s)" title="重命名">✏️</button>
                <button class="s-action-btn" @click.stop="deleteSession(s)" title="删除">🗑️</button>
              </span>
            </div>
          </div>
        </div>

        <!-- 对话区 -->
        <div class="chat-area">
          <div class="messages" ref="msgBox">
            <div v-if="messages.length === 0" class="msg ai">
              👋 你好！我是学习助手。可以问我知识问题，或者说「帮我学习XXX」来生成课程文档。
            </div>

            <div v-for="(m, i) in messages" :key="i" :class="'msg ' + m.role">
              <template v-if="m.role === 'user'">{{ m.content || m.text }}</template>

              <template v-else>
                <p>{{ m.content || m.reply }}</p>
                <div v-if="m.intent === 'generate'" class="gen-card">
                  <span class="gen-chapter" v-if="m.matched_chapter">
                    📌 {{ m.matched_chapter.title }}
                  </span>
                  <span class="gen-chapter" v-else>
                    🔍 为你生成「{{ m.user_query }}」的学习文档
                  </span>
                  <button class="gen-btn"
                    :disabled="m.generating"
                    @click="doGenerate(m)">
                    {{ m.generating ? '⏳ 生成中...' : '✨ 生成文档' }}
                  </button>
                </div>
              </template>
            </div>

            <div v-if="waiting" class="msg ai">
              <span class="thinking">思考中...</span>
            </div>
          </div>

          <div class="input-row">
            <input v-model="input" placeholder="输入问题或想学的内容..."
                   @keyup.enter="send" :disabled="waiting" />
            <button @click="send" :disabled="waiting || !input.trim()">发送</button>
          </div>
        </div>
      </div>

      <!-- 右栏：文档预览 -->
      <div class="right-panel">
        <div class="preview-header">
          <h3>📄 文档预览</h3>
          <div class="preview-tabs">
            <button :class="{ active: previewTab === 'current' }" @click="previewTab = 'current'">当前</button>
            <button :class="{ active: previewTab === 'history' }" @click="previewTab = 'history'">历史 ({{ docs.length }})</button>
          </div>
        </div>

        <div class="preview-body" v-if="previewTab === 'current'">
          <div v-if="streamingText" class="doc-content" v-html="renderMarkdown(streamingText)"></div>
          <div v-else-if="streaming" class="streaming-placeholder">
            <span class="thinking">等待生成开始...</span>
          </div>
          <div v-else-if="currentDoc" class="doc-content" v-html="renderMarkdown(currentDoc.content || '')"></div>
          <div v-else class="preview-empty">
            <span class="empty-icon">📖</span>
            <p>选择一篇文档或生成新的文档来预览</p>
          </div>
        </div>

        <div class="preview-body" v-else>
          <div v-if="docs.length === 0" class="preview-empty">
            <span class="empty-icon">📋</span>
            <p>暂无历史文档</p>
          </div>
          <div v-for="d in docs" :key="d.id" class="history-item"
               :class="{ active: currentDoc && currentDoc.id === d.id }"
               @click="selectDoc(d)">
            <span class="h-title">{{ d.title }}</span>
            <span class="h-time">{{ d.created_time?.slice(0, 16).replace('T', ' ') }}</span>
            <span class="h-status">{{ d.status === 'completed' ? '✅' : '❌' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  getDocs, getChapters, generateDocStream, resourceChat,
  getResourceSessions, createResourceSession,
  deleteResourceSession, renameResourceSession, getResourceSession,
  deleteDoc
} from '../http/http.js'
import { marked } from 'marked'

const router = useRouter()
const msgBox = ref(null)

const chapters = ref([])
const docs = ref([])
const sessions = ref([])
const sessionId = ref(null)
const messages = ref([])
const input = ref('')
const waiting = ref(false)
const streaming = ref(false)
const streamingText = ref('')
const treeCollapsed = ref(false)
const currentDoc = ref(null)
const previewTab = ref('current')

onMounted(async () => {
  try {
    const [chData, docData, sessData] = await Promise.all([
      getChapters(), getDocs(), getResourceSessions()
    ])
    chapters.value = Array.isArray(chData) ? chData : []
    docs.value = Array.isArray(docData) ? docData : []
    sessions.value = Array.isArray(sessData) ? sessData : []

    // 自动激活最近会话
    if (sessions.value.length > 0) {
      await switchSession(sessions.value[0])
    }
  } catch (e) {
    console.error('加载失败:', e)
    alert('加载资源中心数据失败：' + (e.message || '网络错误，请检查后端服务是否启动'))
  }
})

async function newSession() {
  const title = '资源学习对话'
  try {
    const s = await createResourceSession(title)
    sessions.value.unshift(s)
    sessionId.value = s.id
    messages.value = []
  } catch (e) {
    alert('创建失败：' + e.message)
  }
}

async function switchSession(s) {
  sessionId.value = s.id
  try {
    const data = await getResourceSession(s.id)
    messages.value = (data.messages || []).map(m => ({
      role: m.role,
      content: m.content,
      text: m.content,
    }))
  } catch (e) {
    console.error('加载会话失败:', e)
    messages.value = []
    alert('加载对话记录失败：' + (e.message || '网络错误'))
  }
  scrollDown()
}

async function deleteSession(s) {
  if (!confirm('确定删除这个对话？')) return
  try {
    await deleteResourceSession(s.id)
    sessions.value = sessions.value.filter(x => x.id !== s.id)
    if (sessionId.value === s.id) {
      sessionId.value = sessions.value[0]?.id || null
      messages.value = []
      if (sessionId.value) {
        await switchSession(sessions.value[0])
      }
    }
  } catch (e) {
    alert('删除失败：' + e.message)
  }
}

async function renameSession(s) {
  const title = prompt('新名称：', s.title)
  if (!title) return
  try {
    await renameResourceSession(s.id, title)
    s.title = title
  } catch (e) {
    alert('重命名失败：' + e.message)
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || waiting.value) return
  input.value = ''

  // 自动创建会话
  if (!sessionId.value) {
    await newSession()
  }

  messages.value.push({ role: 'user', content: text })
  waiting.value = true
  scrollDown()

  try {
    const result = await resourceChat(text, sessionId.value)
    messages.value.push({
      role: 'ai',
      content: result.reply,
      reply: result.reply,
      intent: result.intent,
      matched_chapter: result.matched_chapter,
      user_query: result.user_query,
      suggested_action: result.suggested_action,
      generating: false,
    })
  } catch (e) {
    messages.value.push({
      role: 'ai',
      content: '抱歉，出了点问题：' + e.message,
      intent: 'chat',
    })
  } finally {
    waiting.value = false
    scrollDown()
  }
}

async function doGenerate(msg) {
  msg.generating = true
  streaming.value = true
  streamingText.value = ''
  previewTab.value = 'current'

  const chapterId = msg.matched_chapter?.id || 0
  const userQuery = msg.user_query || null

  await generateDocStream(
    chapterId, userQuery,
    (text) => { streamingText.value += text },
    (result) => {
      const doc = {
        id: result.id,
        title: result.title || msg.user_query || '学习文档',
        content: streamingText.value,
        resource_type: 'doc',
        status: 'completed',
        created_time: new Date().toISOString(),
      }
      docs.value.unshift(doc)
      currentDoc.value = doc
      streaming.value = false
      streamingText.value = ''
      msg.generating = false
    },
    (e) => {
      streaming.value = false
      streamingText.value = ''
      msg.generating = false
      alert('生成失败：' + e.message)
    }
  )
}

function quickAsk(chapter) {
  input.value = '帮我学习《' + chapter.title + '》'
  send()
}

async function deleteDocument(doc) {
  if (!confirm('?????' + doc.title + '??')) return
  try {
    await deleteDoc(doc.id)
    docs.value = docs.value.filter(x => x.id !== doc.id)
    if (currentDoc.value && currentDoc.value.id === doc.id) {
      currentDoc.value = null
    }
  } catch (e) {
    alert('?????' + e.message)
  }
}

function selectDoc(doc) {
  currentDoc.value = doc
  previewTab.value = 'current'
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked(text)
}

function scrollDown() {
  nextTick(() => {
    if (msgBox.value) {
      msgBox.value.scrollTop = msgBox.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.page { max-width: 1200px; margin: 0 auto; padding: 0 16px; height: 100vh; display: flex; flex-direction: column; }
.topbar { display: flex; align-items: center; gap: 16px; padding: 12px 0; flex-shrink: 0; }
.back { background: none; border: none; font-size: 16px; cursor: pointer; color: #4A90D9; }
h1 { font-size: 20px; }

.layout { flex: 1; display: flex; gap: 12px; min-height: 0; padding-bottom: 12px; }

/* 左栏 */
.left-panel { width: 420px; flex-shrink: 0; display: flex; flex-direction: column; gap: 8px; min-height: 0; }

/* 章节树 */
.chapter-tree { background: #fff; border-radius: 10px; box-shadow: var(--shadow); overflow: hidden; flex-shrink: 0; }
.tree-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; cursor: pointer; font-size: 14px; font-weight: 600; background: #f8f9fa; user-select: none; }
.tree-toggle { font-size: 10px; color: #909399; }
.tree-body { padding: 6px 0; max-height: 150px; overflow-y: auto; }
.tree-empty { padding: 12px 14px; font-size: 12px; color: #909399; }
.tree-node { padding: 7px 14px; font-size: 13px; color: #303133; cursor: pointer; transition: background 0.15s; }
.tree-node:hover { background: #e6f0fa; color: #4A90D9; }

/* 会话管理 */
.session-bar { background: #fff; border-radius: 10px; box-shadow: var(--shadow); overflow: hidden; flex-shrink: 0; }
.session-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 14px; font-size: 13px; font-weight: 600; background: #f8f9fa; }
.new-session-btn { padding: 3px 10px; background: #4A90D9; color: #fff; border: none; border-radius: 12px; font-size: 12px; cursor: pointer; }
.new-session-btn:disabled { opacity: 0.5; }
.session-list { max-height: 120px; overflow-y: auto; }
.session-item { display: flex; align-items: center; justify-content: space-between; padding: 7px 14px; cursor: pointer; transition: background 0.15s; border-bottom: 1px solid #f5f5f5; }
.session-item:hover, .session-item.active { background: #e6f0fa; }
.s-title { font-size: 12px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.s-actions { display: flex; gap: 2px; flex-shrink: 0; }
.s-action-btn { padding: 2px 5px; background: none; border: none; font-size: 11px; cursor: pointer; opacity: 0.6; }
.s-action-btn:hover { opacity: 1; }

/* 对话区 */
.chat-area { flex: 1; display: flex; flex-direction: column; background: #fff; border-radius: 10px; box-shadow: var(--shadow); min-height: 0; }
.messages { flex: 1; overflow-y: auto; padding: 14px; }
.msg { max-width: 90%; margin-bottom: 12px; font-size: 13px; line-height: 1.6; padding: 10px 14px; border-radius: 10px; word-break: break-word; }
.msg.user { background: #4A90D9; color: #fff; margin-left: auto; }
.msg.ai { background: #f0f2f5; color: #303133; }
.thinking { color: #909399; animation: pulse 1.2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

.gen-card { margin-top: 8px; padding: 10px 12px; background: #e6f0fa; border-radius: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.gen-chapter { font-size: 13px; color: #303133; font-weight: 500; flex: 1; }
.gen-btn { padding: 5px 14px; background: #4A90D9; color: #fff; border: none; border-radius: 14px; font-size: 12px; cursor: pointer; white-space: nowrap; flex-shrink: 0; }
.gen-btn:hover { background: #3A7BC8; }
.gen-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.input-row { display: flex; gap: 8px; padding: 10px 14px; border-top: 1px solid #f0f0f0; }
.input-row input { flex: 1; height: 38px; border: 1px solid #e0e0e0; border-radius: 19px; padding: 0 14px; font-size: 13px; outline: none; }
.input-row button { height: 38px; padding: 0 16px; background: #4A90D9; color: #fff; border: none; border-radius: 19px; font-size: 13px; cursor: pointer; }
.input-row button:disabled { opacity: 0.5; }

/* 右栏 */
.right-panel { flex: 1; display: flex; flex-direction: column; background: #fff; border-radius: 10px; box-shadow: var(--shadow); min-height: 0; }
.preview-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-bottom: 1px solid #f0f0f0; flex-shrink: 0; }
.preview-header h3 { font-size: 14px; }
.preview-tabs { display: flex; gap: 4px; }
.preview-tabs button { padding: 4px 12px; border: 1px solid #e0e0e0; background: #fff; border-radius: 14px; font-size: 12px; cursor: pointer; color: #606266; }
.preview-tabs button.active { background: #e6f0fa; color: #4A90D9; border-color: #4A90D9; }

.preview-body { flex: 1; overflow-y: auto; padding: 16px; }
.preview-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #909399; }
.empty-icon { font-size: 48px; margin-bottom: 10px; }
.preview-empty p { font-size: 14px; }
.streaming-placeholder { display: flex; align-items: center; justify-content: center; height: 100%; }

.doc-content { font-size: 14px; line-height: 1.8; }
.doc-content :deep(h1), .doc-content :deep(h2), .doc-content :deep(h3) { margin: 16px 0 8px; }
.doc-content :deep(pre) { background: #f5f5f5; padding: 12px; border-radius: 8px; overflow-x: auto; font-size: 13px; }
.doc-content :deep(code) { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
.doc-content :deep(blockquote) { border-left: 3px solid #4A90D9; padding-left: 12px; color: #606266; margin: 10px 0; }

.history-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: background 0.15s; border-bottom: 1px solid #f5f5f5; }
.history-item:hover, .history-item.active { background: #e6f0fa; }
.h-title { flex: 1; font-size: 13px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.h-time { font-size: 11px; color: #909399; white-space: nowrap; }
.h-status { font-size: 13px; }
.h-delete { padding: 2px 6px; background: none; border: none; font-size: 14px; cursor: pointer; opacity: 0.4; flex-shrink: 0; }
.h-delete:hover { opacity: 1; color: #f56c6c; }
</style>
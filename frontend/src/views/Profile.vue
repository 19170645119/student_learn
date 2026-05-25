<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="$router.push('/home')">← 返回</button>
      <h1>学习画像</h1>
      <button class="new-btn" @click="newSession">+ 新对话</button>
    </header>

    <div class="layout">
      <div class="sidebar">
        <div class="sidebar-title">历史对话</div>
        <div class="session-list">
          <div
            v-for="s in sessions"
            :key="s.id"
            :class="['session-item', { active: s.id === activeId }]"
            @click="switchTo(s.id)"
          >
            <span
              v-if="editingId !== s.id"
              class="session-title"
              @dblclick.stop="startRename(s)"
            >{{ s.title || '未命名对话' }}</span>
            <input
              v-else
              v-model="editTitle"
              class="rename-input"
              @keydown.enter.prevent="saveRename(s)"
              @blur="saveRename(s)"
              @click.stop
              ref="renameInput"
            />
            <span v-if="streamingSids.has(s.id)" class="dot">●</span>
            <span class="session-time">{{ formatTime(s.updated_time) }}</span>
            <button class="del-btn" @click.stop="delSession(s.id)">×</button>
          </div>
          <div v-if="sessions.length === 0" class="empty-session">暂无历史对话</div>
        </div>
      </div>

      <div class="chat-area">
        <div class="profile-card">
          <h3>📊 我的学习画像</h3>
          <div class="dims">
            <div class="dim" v-for="d in dims" :key="d.key">
              <span class="dl">{{ d.label }}</span>
              <span class="dv">{{ profile[d.key] || '待完善' }}</span>
            </div>
          </div>
        </div>

        <div class="chat-box">
          <div class="messages" ref="msgBox">
            <div v-for="(m, i) in messages" :key="i" :class="'msg ' + m.role">
              {{ m.content }}
            </div>
            <div v-if="activeStreamText" class="msg ai">
              {{ activeStreamText }}<span class="cursor">|</span>
            </div>
          </div>
          <div class="input-row">
            <input v-model="input" placeholder="说说你的学习情况..." @keyup.enter="send" :disabled="streamingSids.has(activeId)" />
            <button @click="send" :disabled="streamingSids.has(activeId) || !input">发送</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { getProfile } from '../http/http.js'

const BASE_URL = 'http://127.0.0.1:8000'
const dims = [
  { key: 'knowledge_base', label: '知识基础' },
  { key: 'cognitive_style', label: '认知风格' },
  { key: 'learning_goal', label: '学习目标' },
  { key: 'error_prone', label: '易错点' },
  { key: 'learning_pace', label: '学习节奏' },
  { key: 'interest_direction', label: '兴趣方向' },
]
const profile = reactive({ knowledge_base: "", cognitive_style: "", learning_goal: "", error_prone: "", learning_pace: "", interest_direction: "" })
const sessions = ref([])
const activeId = ref(null)
const messages = ref([])
const input = ref('')
const streamingSids = reactive(new Set())
const activeStreamText = ref('')
const streamBuffers = reactive({})
const msgBox = ref(null)
const editingId = ref(null)
const editTitle = ref('')

onMounted(async () => {
  try { Object.assign(profile, await getProfile()) } catch (e) { console.error("加载画像失败:", e) }
  await loadSessions()
})

async function apiReq(path, options = {}) {
  const token = localStorage.getItem('token')
  const res = await fetch(BASE_URL + path, {
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
    ...options,
  })
  if (!res.ok) throw new Error('API error')
  return res.json()
}

async function loadSessions() {
  try {
    sessions.value = await apiReq('/profile/sessions')
    if (sessions.value.length > 0 && !activeId.value) {
      activeId.value = sessions.value[0].id
      await loadMessages(activeId.value)
    }
  } catch (e) {}
}

async function loadMessages(sid) {
  try {
    const s = await apiReq('/profile/sessions/' + sid)
    const msgs = s.messages || []
    const buf = streamBuffers[sid]
    if (buf && buf.text) {
      msgs.push({ role: 'assistant', content: buf.text, _streaming: true })
    }
    messages.value = msgs
    scrollDown()
  } catch (e) {}
}

function switchTo(sid) {
  if (activeId.value === sid) return
  if (activeStreamText.value && activeId.value) {
    streamBuffers[activeId.value] = { text: activeStreamText.value, time: Date.now() }
  }
  activeId.value = sid
  activeStreamText.value = ''
  if (streamBuffers[sid]) {
    activeStreamText.value = streamBuffers[sid].text
  }
  loadMessages(sid)
}

async function newSession() {
  const t = prompt('请输入对话名称：')
  try {
    const s = await apiReq('/profile/sessions', {
      method: 'POST',
      body: JSON.stringify({ title: (t || '').trim() }),
    })
    sessions.value.unshift({ id: s.id, title: s.title, status: s.status, updated_time: '' })
    switchTo(s.id)
  } catch (e) { alert('创建失败') }
}

async function delSession(sid) {
  if (!confirm('确定删除？')) return
  try {
    await apiReq('/profile/sessions/' + sid, { method: 'DELETE' })
    sessions.value = sessions.value.filter(s => s.id !== sid)
    delete streamBuffers[sid]
    streamingSids.delete(sid)
    if (activeId.value === sid) {
      activeId.value = sessions.value.length > 0 ? sessions.value[0].id : null
      if (activeId.value) await loadMessages(activeId.value)
      else messages.value = []
    }
  } catch (e) { alert('删除失败') }
}

async function send() {
  if (!input.value.trim() || streamingSids.has(activeId.value)) return
  const msg = input.value.trim()
  const sid = activeId.value
  input.value = ''

  messages.value.push({ role: 'user', content: msg })

  streamingSids.add(sid)
  activeStreamText.value = ''
  streamBuffers[sid] = { text: '', time: Date.now() }
  scrollDown()

  runSSE(sid, msg, localStorage.getItem('token'))
}

async function runSSE(sid, msg, token) {
  try {
    const res = await fetch(BASE_URL + '/profile/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
      body: JSON.stringify({ message: msg, session_id: sid }),
    })

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'token') {
            if (!streamBuffers[sid]) streamBuffers[sid] = { text: '', time: Date.now() }
            streamBuffers[sid].text += data.text
            streamBuffers[sid].time = Date.now()
            if (activeId.value === sid) {
              activeStreamText.value = streamBuffers[sid].text
              scrollDown()
            }
          } else if (data.type === 'done') {
            streamingSids.delete(sid)
            delete streamBuffers[sid]

            const idx = sessions.value.findIndex(s => s.id === sid)
            if (idx >= 0) {
              sessions.value[idx].updated_time = new Date().toISOString()
              if (data.message_summary) {
                sessions.value[idx].title = data.message_summary.slice(0, 20)
              }
            }

            if (activeId.value === sid) {
              activeStreamText.value = ''
              messages.value.push({ role: 'assistant', content: data.message })
              if (data.profile_update && Object.keys(data.profile_update).length > 0) {
                try { Object.assign(profile, await getProfile()) } catch (e) { console.error("加载画像失败:", e) }
              }
            }
            scrollDown()
          }
        }
      }
    }
  } catch (e) {
    streamingSids.delete(sid)
    delete streamBuffers[sid]
    if (activeId.value === sid) {
      activeStreamText.value = ''
      messages.value.push({ role: 'assistant', content: '出错了，请重试' })
    }
  }
}

function scrollDown() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}

async function startRename(s) {
  editingId.value = s.id
  editTitle.value = s.title || ''
  nextTick(() => {
    const inp = document.querySelector('.rename-input')
    if (inp) inp.focus()
  })
}

async function saveRename(s) {
  if (editingId.value !== s.id) return  // 防止 enter+blur 双重触发
  if (!editTitle.value.trim()) {
    editingId.value = null
    return
  }
  try {
    await apiReq('/profile/sessions/' + s.id + '/rename', {
      method: 'PUT',
      body: JSON.stringify({ title: editTitle.value.trim() }),
    })
    s.title = editTitle.value.trim()
  } catch (e) {
    alert('重命名失败：' + e.message)
  }
  editingId.value = null
}

function formatTime(t) {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}
</script>

<style scoped>
.page { max-width: 1000px; margin: 0 auto; }
.topbar { display: flex; align-items: center; gap: 16px; padding: 12px 16px; }
.back { background: none; border: none; font-size: 16px; cursor: pointer; color: #4A90D9; }
h1 { font-size: 20px; flex: 1; }
.new-btn { padding: 6px 14px; background: #4A90D9; color: #fff; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
.layout { display: flex; gap: 16px; padding: 0 16px; height: calc(100vh - 56px); }
.sidebar { width: 200px; flex-shrink: 0; background: #fff; border-radius: 12px; padding: 12px; box-shadow: var(--shadow); display: flex; flex-direction: column; }
.sidebar-title { font-size: 14px; font-weight: bold; color: #303133; margin-bottom: 10px; }
.session-list { flex: 1; overflow-y: auto; }
.session-item { padding: 10px 8px; border-radius: 8px; cursor: pointer; margin-bottom: 4px; position: relative; }
.session-item:hover { background: #f0f2f5; }
.session-item.active { background: #e6f0fa; }
.session-title { font-size: 13px; color: #303133; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: default; }
.rename-input { font-size: 13px; width: 100%; padding: 2px 4px; border: 1px solid #4A90D9; border-radius: 4px; outline: none; box-sizing: border-box; }
.dot { color: #4A90D9; font-size: 10px; margin-left: 4px; animation: blink 0.8s infinite; }
@keyframes blink { 50% { opacity: 0; } }
.session-time { font-size: 11px; color: #c0c4cc; display: block; }
.edit-btn { position: absolute; right: 30px; top: 4px; background: none; border: none; color: #ccc; font-size: 14px; cursor: pointer; display: none; }
.edit-btn:hover { color: #4A90D9; }
.del-btn { position: absolute; right: 6px; top: 6px; background: none; border: none; color: #ccc; font-size: 16px; cursor: pointer; display: none; }
.session-item:hover .del-btn { display: block; }
.session-item:hover .edit-btn { display: block; }
.del-btn:hover { color: #f56c6c; }
.empty-session { text-align: center; color: #c0c4cc; font-size: 13px; padding: 20px 0; }
.chat-area { flex: 1; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.profile-card { background: #fff; padding: 16px; border-radius: 12px; box-shadow: var(--shadow); }
.profile-card h3 { font-size: 16px; margin-bottom: 10px; }
.dims { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
.dim { background: #f5f7fa; border-radius: 8px; padding: 8px 12px; }
.dl { font-size: 11px; color: #909399; display: block; }
.dv { font-size: 13px; color: #303133; display: block; margin-top: 1px; }
.chat-box { background: #fff; border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); display: flex; flex-direction: column; flex: 1; }
.messages { flex: 1; overflow-y: auto; padding: 16px; }
.msg { max-width: 75%; padding: 10px 16px; border-radius: 12px; margin-bottom: 12px; font-size: 14px; line-height: 1.5; white-space: pre-wrap; }
.msg.user { background: #4A90D9; color: #fff; margin-left: auto; }
.msg.ai { background: #f0f2f5; color: #303133; }
.cursor { animation: blink 0.8s infinite; }
.input-row { display: flex; gap: 10px; padding: 12px 16px; border-top: 1px solid #f0f0f0; }
.input-row input { flex: 1; height: 40px; border: 1px solid #e8e8e8; border-radius: 20px; padding: 0 16px; font-size: 14px; outline: none; }
.input-row button { height: 40px; padding: 0 20px; background: #4A90D9; color: #fff; border: none; border-radius: 20px; font-size: 14px; cursor: pointer; }
.input-row button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>

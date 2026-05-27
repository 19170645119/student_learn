<template>
  <div class="profile">
    <nav class="topnav glass-panel">
      <button class="nav-back" @click="goHome">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <h1 class="gradient-text">学习画像</h1>
      <button class="btn-new-session" @click="newSession">+ 新对话</button>
    </nav>
    <div class="layout">
      <div class="sidebar glass-panel">
        <div class="sidebar-title">历史对话</div>
        <div class="session-list">
          <div v-for="s in sessions" :key="s.id" :class="['session-item', { active: s.id === activeId }]" @click="switchTo(s.id)">
            <span v-if="editingId !== s.id" class="session-title" @dblclick.stop="startRename(s)">{{ s.title || '未命名对话' }}</span>
            <input v-else v-model="editTitle" class="rename-input" @keydown.enter.prevent="saveRename(s)" @blur="saveRename(s)" @click.stop />
            <span v-if="streamingSids.has(s.id)" class="dot">●</span>
            <span class="session-time">{{ formatTime(s.updated_time) }}</span>
            <button class="del-btn" @click.stop="delSession(s.id)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
            </button>
          </div>
          <div v-if="sessions.length === 0" class="empty-session">暂无历史对话</div>
        </div>
      </div>
      <div class="chat-area-wrap">
        <div class="profile-card glass-panel-glow">
          <h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="5"/><path d="M3 21v-2a7 7 0 017-7h4a7 7 0 017 7v2"/></svg>
            我的学习画像
          </h3>
          <div class="dims">
            <div class="dim" v-for="d in dims" :key="d.key">
              <span class="dl">{{ d.label }}</span>
              <span class="dv">{{ profile[d.key] || '待完善' }}</span>
            </div>
          </div>
        </div>
        <div class="chat-box glass-panel">
          <div class="messages" ref="msgBox">
            <div v-for="(m, i) in messages" :key="i" :class="'msg ' + m.role">{{ m.content }}</div>
            <div v-if="activeStreamText" class="msg ai">{{ activeStreamText }}<span class="cursor">|</span></div>
          </div>
          <div class="input-row">
            <input v-model="input" placeholder="说说你的学习情况..." @keyup.enter="send" :disabled="streamingSids.has(activeId)" />
            <button class="btn-send" @click="send" :disabled="streamingSids.has(activeId) || !input">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { getProfile } from '../http/http.js'

const router = useRouter()
const BASE_URL = 'http://127.0.0.1:8000'

function goHome() { router.push('/home') }
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
.profile { height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
.topnav { display: flex; align-items: center; padding: 10px 20px; margin: 10px 16px 0; border-radius: 18px; flex-shrink: 0; z-index: 10; }
.nav-back { display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 10px; background: rgba(255,255,255,0.04); color: var(--text-regular); transition: all var(--transition); }
.nav-back:hover { background: rgba(255,255,255,0.08); color: var(--text-primary); }
.topnav h1 { font-size: 1.1rem; font-weight: 700; margin-left: 14px; flex: 1; }
.btn-new-session { padding: 8px 18px; background: var(--gradient-brand); color: #fff; border: none; border-radius: 10px; font-size: 0.8rem; font-weight: 600; }
.btn-new-session:hover { box-shadow: var(--shadow-glow); transform: translateY(-1px); }
.layout { display: flex; gap: 12px; padding: 12px 16px 16px; flex: 1; min-height: 0; overflow: hidden; }
.sidebar { width: 200px; flex-shrink: 0; border-radius: var(--radius); padding: 14px; display: flex; flex-direction: column; }
.sidebar-title { font-size: 0.82rem; font-weight: 600; color: var(--text-primary); margin-bottom: 10px; }
.session-list { flex: 1; overflow-y: auto; }
.session-item { padding: 10px 8px; border-radius: 8px; cursor: pointer; margin-bottom: 4px; position: relative; transition: all var(--transition); }
.session-item:hover { background: rgba(255,255,255,0.04); }
.session-item.active { background: var(--primary-bg); border: 1px solid rgba(91,127,255,0.1); }
.session-title { font-size: 0.8rem; color: var(--text-primary); display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: default; }
.rename-input { font-size: 0.78rem; width: 100%; padding: 2px 4px; border: 1px solid var(--primary); border-radius: 4px; outline: none; box-sizing: border-box; }
.dot { color: var(--primary-light); font-size: 10px; margin-left: 4px; animation: blink 0.8s infinite; }
@keyframes blink { 50% { opacity: 0; } }
.session-time { font-size: 0.7rem; color: var(--text-secondary); display: block; }
.del-btn { position: absolute; right: 6px; top: 8px; width: 22px; height: 22px; display: none; align-items: center; justify-content: center; background: transparent; color: var(--text-disabled); border-radius: 4px; }
.session-item:hover .del-btn { display: flex; }
.del-btn:hover { color: var(--danger); background: var(--danger-bg); }
.empty-session { text-align: center; color: var(--text-secondary); font-size: 0.8rem; padding: 20px 0; }
.chat-area-wrap { flex: 1; display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.profile-card { padding: 16px 20px; border-radius: var(--radius); }
.profile-card h3 { font-size: 0.95rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.dims { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
.dim { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 10px 14px; border: 1px solid var(--border-light); }
.dl { font-size: 0.7rem; color: var(--text-secondary); display: block; }
.dv { font-size: 0.82rem; color: var(--text-primary); display: block; margin-top: 2px; }
.chat-box { flex: 1; border-radius: var(--radius); display: flex; flex-direction: column; overflow: hidden; }
.messages { flex: 1; overflow-y: auto; padding: 16px; }
.msg { max-width: 75%; padding: 10px 16px; border-radius: 14px; margin-bottom: 12px; font-size: 0.85rem; line-height: 1.55; white-space: pre-wrap; }
.msg.user { background: var(--gradient-brand); color: #fff; margin-left: auto; }
.msg.ai { background: rgba(255,255,255,0.04); color: var(--text-primary); }
.cursor { animation: blink 0.8s infinite; color: var(--primary-light); font-weight: 300; }
.input-row { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--border-light); }
.input-row input { flex: 1; height: 40px; background: rgba(10,16,40,0.5); border: 1px solid var(--border); border-radius: 20px; padding: 0 16px; font-size: 0.85rem; color: var(--text-primary); outline: none; }
.input-row input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); }
.input-row input::placeholder { color: var(--text-disabled); }
.btn-send { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: var(--gradient-brand); color: #fff; border-radius: 50%; flex-shrink: 0; }
.btn-send:hover { box-shadow: var(--shadow-glow); transform: scale(1.05); }
.btn-send:disabled { opacity: 0.3; cursor: not-allowed; }
</style>

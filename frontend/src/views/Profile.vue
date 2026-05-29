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

      <div class="chat-col">
        <div v-if="allEmpty && !streamingSids.has(activeId)" class="wizard glass-panel">
          <p class="wizard-hint">👋 快速告诉 AI 你的情况：</p>
          <div class="wizard-chips">
            <button v-for="opt in quickOptions" :key="opt" class="wiz-chip" @click="sendQuick(opt)">{{ opt }}</button>
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

      <div class="profile-col">
        <div class="profile-card glass-panel-glow">
          <div class="pc-header">
            <h3>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="5"/><path d="M3 21v-2a7 7 0 017-7h4a7 7 0 017 7v2"/></svg>
              学习画像
            </h3>
            <div class="pc-actions">
              <span class="pc-progress">{{ filledCount }}/6</span>
              <button class="pc-btn-self" @click="showSelfAssess = !showSelfAssess" title="快速自评">✏️</button>
              <button class="pc-btn-clear" @click="clearProfile" title="清空画像">🗑️</button>
            </div>
          </div>
          <div class="pc-body">
            <ProfileRadar :dimensions="radarDims" :size="200" />
          </div>
        </div>

        <!-- Extra Info Cards -->
        <div class="extra-cards">
          <div class="extra-card">
            <span class="extra-icon">🎓</span>
            <span class="extra-label">专业年级</span>
            <span class="extra-val">{{ profile.major_grade || '待完善' }}</span>
          </div>
          <div class="extra-card">
            <span class="extra-icon">⏰</span>
            <span class="extra-label">每周可用时间</span>
            <span class="extra-val">{{ profile.weekly_hours || '待完善' }}</span>
          </div>
        </div>

        <div v-if="showSelfAssess" class="self-assess glass-panel">
          <div class="sa-header">
            <span>快速自评</span>
            <button class="sa-close" @click="showSelfAssess = false">✕</button>
          </div>
          <div class="sa-dims">
            <div v-for="d in dims" :key="d.key" class="sa-dim">
              <label>{{ d.label }}</label>
              <div class="sa-row">
                <input type="range" min="1" max="5" v-model.number="selfScores[d.key]" class="sa-slider" />
                <span class="sa-score">{{ selfScores[d.key] }}</span>
              </div>
              <input v-model="selfValues[d.key]" class="sa-input" :placeholder="'描述你的' + d.label + '...'" />
            </div>
          </div>
          <button class="sa-submit" @click="submitSelfAssess" :disabled="selfSubmitting">
            {{ selfSubmitting ? '保存中...' : '保存自评' }}
          </button>
        </div>

        <div v-if="filledCount >= 2" class="insights glass-panel">
          <div class="insights-title">💡 学习洞察</div>
          <div class="insight-item" v-if="profile.cognitive_style">
            <span class="insight-icon">📖</span>
            <span class="insight-text">推荐学习方式：<strong>{{ styleAdvice }}</strong></span>
          </div>
          <div class="insight-item" v-if="profile.error_prone">
            <span class="insight-icon">⚠️</span>
            <span class="insight-text">优先补强：<strong>{{ profile.error_prone }}</strong></span>
          </div>
          <div class="insight-item" v-if="profile.interest_direction">
            <span class="insight-icon">🎯</span>
            <span class="insight-text">建议方向：<strong>{{ profile.interest_direction }}</strong></span>
          </div>
          <div class="insights-actions">
            <button class="insights-btn" @click="goResources">生成学习资源 →</button>
            <button class="insights-btn outline" @click="goPath">学习路径 →</button>
          </div>
        </div>

        <div v-if="allEmpty" class="profile-empty glass-panel">
          <p>🎯 尚未构建画像</p>
          <p class="profile-empty-hint">在左侧对话中告诉 AI 你的学习情况</p>
        </div>

        <div v-if="snapshots.length > 0" class="history glass-panel">
          <div class="history-title" @click="showHistory = !showHistory">
            📈 画像演变
            <span class="history-toggle">{{ showHistory ? '▼' : '▶' }}</span>
          </div>
          <div v-if="showHistory" class="history-list">
            <div v-for="s in snapshots" :key="s.id" class="history-item">
              <div class="history-dot"></div>
              <div class="history-content">
                <span class="history-time">{{ formatTime(s.created_time) }}</span>
                <button class="hist-restore" @click="restoreSnapshot(s)" title="恢复到此版本">↩️</button>
                <span class="history-changes">
                  <template v-for="(v, k) in s.snapshot" :key="k">
                    <span v-if="v" class="hist-tag">{{ dimLabel(k) }}: {{ v }}</span>
                  </template>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { getProfile } from '../http/http.js'
import ProfileRadar from '../components/ProfileRadar.vue'

const router = useRouter()
const BASE_URL = 'http://127.0.0.1:8000'

function goHome() { router.push('/home') }
function goResources() { router.push('/resources') }
function goPath() { router.push('/learning-path') }

const dims = [
  { key: 'knowledge_base', label: '知识基础' },
  { key: 'cognitive_style', label: '认知风格' },
  { key: 'learning_goal', label: '学习目标' },
  { key: 'error_prone', label: '易错点' },
  { key: 'learning_pace', label: '学习节奏' },
  { key: 'interest_direction', label: '兴趣方向' },
]

function dimLabel(key) {
  const found = dims.find(d => d.key === key)
  if (found) return found.label
  const extraLabels = { major_grade: '专业年级', weekly_hours: '每周时间' }
  return extraLabels[key] || key
}

const profile = reactive({ knowledge_base: "", cognitive_style: "", learning_goal: "", error_prone: "", learning_pace: "", interest_direction: "", major_grade: "", weekly_hours: "" })
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
const showSelfAssess = ref(false)
const showHistory = ref(false)
const snapshots = ref([])

// Self-assessment
const selfScores = reactive({ knowledge_base: 1, cognitive_style: 1, learning_goal: 1, error_prone: 1, learning_pace: 1, interest_direction: 1, major_grade: 1, weekly_hours: 1 })
const selfValues = reactive({ knowledge_base: '', cognitive_style: '', learning_goal: '', error_prone: '', learning_pace: '', interest_direction: '', major_grade: '', weekly_hours: '' })
const selfSubmitting = ref(false)

// Quick options for wizard
const quickOptions = ['我学过Python', '我喜欢看视频学习', '我在准备考试', '我喜欢动手实践', '我基础不太好', '我对AI/CV感兴趣']

// Computed
const radarDims = computed(() => dims.map(d => ({ ...d, value: profile[d.key] || '' })))
const filledCount = computed(() => dims.filter(d => profile[d.key] && profile[d.key].trim()).length)
const allEmpty = computed(() => filledCount.value === 0)

const styleAdvice = computed(() => {
  const cs = profile.cognitive_style || ''
  if (cs.includes('视觉')) return '视频 + 图文教程'
  if (cs.includes('动手')) return '实操练习 + 项目驱动'
  if (cs.includes('听觉')) return '音频讲解 + 讨论式学习'
  return '视频 + 图文教程'
})

onMounted(async () => {
  try { Object.assign(profile, await getProfile()) } catch (e) { console.error("加载画像失败:", e) }
  await loadSessions()
  await loadHistory()
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
    messages.value = s.messages || []
  } catch (e) {}
}

async function loadHistory() {
  try {
    snapshots.value = await apiReq('/profile/history')
  } catch (e) { snapshots.value = [] }
}

async function newSession() {
  try {
    const s = await apiReq('/profile/sessions', { method: 'POST', body: JSON.stringify({}) })
    sessions.value.unshift({ id: s.id, title: s.title || '画像构建对话', status: 'active', updated_time: new Date().toISOString() })
    activeId.value = s.id
    messages.value = []
    activeStreamText.value = ''
  } catch (e) { alert('创建失败: ' + e.message) }
}

async function switchTo(sid) {
  if (sid === activeId.value) return
  await apiReq('/profile/sessions/' + sid + '/activate', { method: 'PUT' })
  activeId.value = sid
  await loadMessages(sid)
  activeStreamText.value = ''
}

async function delSession(sid) {
  if (!confirm('删除此对话？')) return
  try {
    await apiReq('/profile/sessions/' + sid, { method: 'DELETE' })
    sessions.value = sessions.value.filter(s => s.id !== sid)
    if (activeId.value === sid) {
      activeId.value = sessions.value.length > 0 ? sessions.value[0].id : null
      if (activeId.value) await loadMessages(activeId.value)
      else messages.value = []
    }
  } catch (e) { alert('删除失败: ' + e.message) }
}

function sendQuick(text) {
  input.value = text
  send()
}

async function send() {
  const msg = input.value.trim()
  if (!msg || streamingSids.has(activeId.value)) return
  input.value = ''

  let sid = activeId.value
  if (!sid) { await newSession(); sid = activeId.value }
  streamingSids.add(sid)
  activeStreamText.value = ''
  streamBuffers[sid] = ''

  messages.value.push({ role: 'user', content: msg })

  try {
    const token = localStorage.getItem('token')
    const res = await fetch(BASE_URL + '/profile/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
      body: JSON.stringify({ message: msg, session_id: sid }),
    })
    if (!res.ok) throw new Error('请求失败')

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'token') {
              streamBuffers[sid] = (streamBuffers[sid] || '') + data.text
              activeStreamText.value = streamBuffers[sid]
              await nextTick()
              if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
            } else if (data.type === 'done') {
              const finalText = data.message || streamBuffers[sid] || ''
              messages.value.push({ role: 'assistant', content: finalText })
              activeStreamText.value = ''
              delete streamBuffers[sid]
              // Update profile if returned
              if (data.profile_update && Object.keys(data.profile_update).length > 0) {
                Object.assign(profile, data.profile_update)
                await loadHistory()
              }
              // Update session title
              const sidx = sessions.value.findIndex(s => s.id === data.session_id)
              if (sidx >= 0 && data.message_summary) {
                sessions.value[sidx].title = data.message_summary
              }
            }
          } catch (e) {}
        }
      }
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，连接出错了: ' + e.message })
  }
  streamingSids.delete(sid)
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}

// Self-assessment
function resetSelfAssess() {
  for (const d of dims) {
    const val = profile[d.key] || ''
    selfValues[d.key] = val
    selfScores[d.key] = val ? Math.min(5, Math.max(1, Math.ceil(val.length / 6))) : 1
  }
  selfValues.major_grade = profile.major_grade || ''
  selfScores.major_grade = profile.major_grade ? 3 : 1
  selfValues.weekly_hours = profile.weekly_hours || ''
  selfScores.weekly_hours = profile.weekly_hours ? 3 : 1
}

async function submitSelfAssess() {
  selfSubmitting.value = true
  try {
    const data = {}
    for (const d of dims) {
      data[d.key] = selfValues[d.key] || (selfScores[d.key] > 1 ? dims.find(x => x.key === d.key)?.label + ' Lv' + selfScores[d.key] : '')
    }
    data.major_grade = selfValues.major_grade
    data.weekly_hours = selfValues.weekly_hours
    await apiReq('/profile/', { method: 'PUT', body: JSON.stringify(data) })
    Object.assign(profile, data)
    showSelfAssess.value = false
    await loadHistory()
  } catch (e) { alert('保存失败: ' + e.message) }
  selfSubmitting.value = false
}

function startRename(s) {
  editingId.value = s.id
  editTitle.value = s.title || ''
}

async function saveRename(s) {
  try {
    await apiReq('/profile/sessions/' + s.id + '/rename', { method: 'PUT', body: JSON.stringify({ title: editTitle.value.trim() }) })
    s.title = editTitle.value.trim()
  } catch (e) { alert('重命名失败: ' + e.message) }
  editingId.value = null
}

async function clearProfile() {
  if (!confirm('确定清空所有画像数据？此操作不可恢复。')) return
  const empty = { knowledge_base: '', cognitive_style: '', learning_goal: '', error_prone: '', learning_pace: '', interest_direction: '', major_grade: '', weekly_hours: '' }
  try {
    await apiReq('/profile/', { method: 'PUT', body: JSON.stringify(empty) })
    Object.assign(profile, empty)
    await loadHistory()
  } catch (e) { alert('清空失败: ' + e.message) }
}

async function restoreSnapshot(s) {
  if (!confirm('恢复到此版本的画像？')) return
  try {
    await apiReq('/profile/', { method: 'PUT', body: JSON.stringify(s.snapshot) })
    Object.assign(profile, s.snapshot)
    await loadHistory()
  } catch (e) { alert('恢复失败: ' + e.message) }
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
.btn-new-session { padding: 8px 18px; background: var(--gradient-brand); color: #fff; border: none; border-radius: 10px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
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
.chat-col { flex: 1; display: flex; flex-direction: column; gap: 10px; min-width: 0; overflow-y: auto; }

/* Profile Card */
.profile-card { padding: 12px 14px; border-radius: var(--radius); flex-shrink: 0; }
.profile-col { width: 280px; flex-shrink: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding: 0; }
.profile-empty { padding: 20px; border-radius: var(--radius); text-align: center; font-size: 0.85rem; color: var(--text-secondary); }
.extra-cards { display: flex; gap: 8px; }
.extra-card { flex: 1; padding: 8px 10px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 8px; display: flex; flex-direction: column; gap: 2px; }
.extra-icon { font-size: 0.9rem; }
.extra-label { font-size: 0.65rem; color: var(--text-secondary); }
.extra-val { font-size: 0.78rem; color: var(--text-primary); font-weight: 500; }

.profile-empty-hint { font-size: 0.75rem; color: var(--text-disabled); margin-top: 6px; }
.chat-col { flex: 1; display: flex; flex-direction: column; gap: 10px; min-width: 0; overflow: hidden; }

.profile-card { padding: 16px 20px; border-radius: var(--radius); }
.pc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.pc-header h3 { font-size: 0.85rem; display: flex; align-items: center; gap: 6px; margin: 0; }
.pc-actions { display: flex; align-items: center; gap: 10px; }
.pc-progress { font-size: 0.7rem; color: var(--primary-light); background: var(--primary-bg); padding: 3px 10px; border-radius: 12px; }
.pc-btn-clear { font-size: 0.7rem; padding: 3px 8px; border-radius: 12px; background: rgba(239,68,68,0.08); color: #ef4444; border: 1px solid rgba(239,68,68,0.2); cursor: pointer; }
.pc-btn-clear:hover { background: rgba(239,68,68,0.15); }
.hist-restore { background: none; border: none; color: var(--primary-light); cursor: pointer; font-size: 0.75rem; padding: 0 4px; opacity: 0; transition: opacity 0.2s; }
.history-item:hover .hist-restore { opacity: 1; }
.hist-restore:hover { transform: scale(1.2); }

.pc-btn-self { font-size: 0.7rem; padding: 3px 10px; border-radius: 12px; background: rgba(255,255,255,0.05); color: var(--text-secondary); border: 1px solid var(--border); cursor: pointer; }
.pc-btn-self:hover { background: rgba(255,255,255,0.1); color: var(--text-primary); }
.pc-body { display: flex; justify-content: center; padding: 4px 0; }

/* Self-Assess */
.self-assess { padding: 16px; border-radius: var(--radius); animation: vpFadeUp 0.3s ease; }
@keyframes vpFadeUp { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
.sa-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 0.9rem; margin-bottom: 12px; }
.sa-close { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 1rem; }
.sa-dims { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.sa-dim { margin-bottom: 4px; }
.sa-dim label { font-size: 0.72rem; color: var(--text-secondary); display: block; margin-bottom: 2px; }
.sa-row { display: flex; align-items: center; gap: 8px; }
.sa-slider { flex: 1; height: 4px; -webkit-appearance: none; appearance: none; background: rgba(255,255,255,0.1); border-radius: 2px; outline: none; }
.sa-slider::-webkit-slider-thumb { -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%; background: var(--primary); cursor: pointer; }
.sa-score { font-size: 0.75rem; font-weight: 600; color: var(--primary-light); min-width: 16px; }
.sa-input { width: 100%; padding: 4px 8px; font-size: 0.72rem; background: rgba(255,255,255,0.04); border: 1px solid var(--border); border-radius: 6px; color: var(--text-primary); outline: none; margin-top: 2px; }
.sa-input:focus { border-color: var(--primary); }
.sa-submit { margin-top: 12px; width: 100%; padding: 8px; background: var(--gradient-brand); color: #fff; border: none; border-radius: 8px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.sa-submit:disabled { opacity: 0.5; cursor: not-allowed; }

/* Insights */
.insights { padding: 14px 18px; border-radius: var(--radius); }
.insights-title { font-size: 0.85rem; font-weight: 600; margin-bottom: 10px; }
.insight-item { display: flex; align-items: flex-start; gap: 8px; padding: 6px 0; font-size: 0.82rem; color: var(--text-secondary); }
.insight-icon { flex-shrink: 0; }
.insight-text strong { color: var(--text-primary); }
.insights-actions { display: flex; gap: 10px; margin-top: 10px; }
.insights-btn { padding: 6px 14px; border-radius: 8px; font-size: 0.75rem; font-weight: 600; cursor: pointer; background: var(--primary-bg); color: var(--primary-light); border: 1px solid rgba(91,127,255,0.2); }
.insights-btn.outline { background: transparent; border: 1px solid var(--border); color: var(--text-secondary); }
.insights-btn:hover { transform: translateY(-1px); }

/* Wizard */
.wizard { padding: 12px 16px; border-radius: var(--radius); }
.wizard-hint { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 8px; }
.wizard-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.wiz-chip { padding: 5px 12px; border-radius: 16px; font-size: 0.75rem; background: rgba(91,127,255,0.08); color: var(--primary-light); border: 1px solid rgba(91,127,255,0.15); cursor: pointer; transition: all 0.2s; }
.wiz-chip:hover { background: rgba(91,127,255,0.18); border-color: rgba(91,127,255,0.3); }

/* Chat */
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
.btn-send { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: var(--gradient-brand); color: #fff; border-radius: 50%; flex-shrink: 0; border: none; cursor: pointer; }
.btn-send:hover { box-shadow: var(--shadow-glow); transform: scale(1.05); }
.btn-send:disabled { opacity: 0.3; cursor: not-allowed; }

/* History */
.history { padding: 12px 16px; border-radius: var(--radius); }
.history-title { font-size: 0.82rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; user-select: none; }
.history-toggle { font-size: 0.65rem; color: var(--text-disabled); }
.history-list { margin-top: 8px; }
.history-item { display: flex; gap: 10px; padding: 6px 0; }
.history-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--primary-light); margin-top: 4px; flex-shrink: 0; }
.history-content { flex: 1; }
.history-time { font-size: 0.7rem; color: var(--text-disabled); display: block; }
.history-changes { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 2px; }
.hist-tag { font-size: 0.68rem; padding: 1px 8px; border-radius: 8px; background: rgba(91,127,255,0.08); color: var(--primary-light); }


/* Responsive */
@media (max-width: 900px) {
  .profile-col { display: none; }
  .profile-col.mobile-show { display: flex; position: fixed; right: 0; top: 70px; bottom: 0; z-index: 50; background: var(--bg); border-left: 1px solid var(--border); }
  .btn-show-profile { display: flex !important; }
}
@media (max-width: 600px) {
  .sidebar { display: none; }
}
.btn-show-profile { display: none; }
</style>

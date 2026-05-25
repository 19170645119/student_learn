<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="$router.push('/home')">← 返回</button>
      <h1>资源中心</h1>
    </header>

    <div class="rec-bar" v-if="recNodes.length">
      <span class="rec-label">💡 根据你的画像推荐：</span>
      <button v-for="n in recNodes" :key="n.id" class="rec-tag" @click="quickGen(n)" :disabled="generating">
        {{ n.title }}
      </button>
    </div>

    <div class="layout">
      <div class="chat-area">
        <div class="messages" ref="msgBox">
          <div v-for="(m,i) in messages" :key="i" :class="'msg ' + m.role">
            <template v-if="m.role === 'ai' && m.resources">
              <p>{{ m.text }}</p>
              <div class="res-cards">
                <div v-for="r in m.resources" :key="r.id" class="res-card" @click="viewResource(r)">
                  <span class="type-tag">{{ typeLabel(r.resource_type) }}</span>
                  <img v-if="r.resource_type==='mindmap' && r.extra_data?.image_url" :src="r.extra_data.image_url" class="card-img" />
                  <h4>{{ r.title }}</h4>
                </div>
              </div>
            </template>
            <template v-else>{{ m.text }}</template>
          </div>
          <div v-if="streaming" class="msg ai">{{ streamText }}<span class="cursor">|</span></div>
        </div>
        <div class="input-row">
          <input v-model="input" placeholder="想学什么？比如“我想学习深度学习”..." @keyup.enter="send" :disabled="generating" />
          <button @click="send" :disabled="generating || !input.trim()">发送</button>
        </div>
      </div>
    </div>

    <div class="modal" v-if="viewing" @click.self="viewing=null">
      <div class="modal-inner">
        <h3>{{ viewing.title }}</h3>
        <div v-if="viewing.resource_type==='mindmap' && viewing.extra_data?.image_url" class="modal-img">
          <img :src="viewing.extra_data.image_url" style="max-width:100%;border-radius:8px" />
        </div>
        <div class="modal-body" v-html="renderContent(viewing)"></div>
        <button @click="viewing=null">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'

const BASE_URL = 'http://127.0.0.1:8000'
const messages = ref([])
const input = ref('')
const generating = ref(false)
const streaming = ref(false)
const streamText = ref('')
const viewing = ref(null)
const recNodes = ref([])
const msgBox = ref(null)

onMounted(async () => {
  try {
    const res = await apiReq('/resource/recommend')
    recNodes.value = res.nodes || []
  } catch(e) {}
})

async function apiReq(path, opts={}) {
  const token = localStorage.getItem('token')
  const res = await fetch(BASE_URL + path, {
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
    ...opts,
  })
  if (!res.ok) throw new Error('API error')
  return res.json()
}

function typeLabel(t) {
  return {doc:'文档',mindmap:'导图',quiz:'题库',code:'代码',video:'视频'}[t]||t
}

function renderContent(r) {
  if (r.resource_type === 'mindmap') {
    let html = '<p style="color:#909399;font-size:12px">导图已上方展示，以下为Mermaid源码：</p><pre style="background:#f5f7fa;padding:12px;border-radius:8px;overflow-x:auto;font-size:12px">'
    html += (r.extra_data?.mermaid || r.content || '').replace(/</g,'&lt;')
    html += '</pre>'
    return html
  }
  return (r.content||'').replace(/\n/g,'<br>')
}

async function quickGen(node) {
  input.value = '生成《' + node.title + '》相关资源'
  await send()
}

async function send() {
  if (!input.value.trim() || generating.value) return
  const msg = input.value.trim()
  input.value = ''
  generating.value = true
  streaming.value = true
  streamText.value = ''

  messages.value.push({ role: 'user', text: msg })
  scrollDown()

  try {
    const analysis = await apiReq('/resource/chat', {
      method: 'POST',
      body: JSON.stringify({ message: msg }),
    })

    const note = analysis.profile_note || ''
    const reply = analysis.reply || '分析完成，正在生成资源...'
    streamText.value = note ? note + '\n\n' + reply : reply
    scrollDown()

    if (analysis.matched_nodes && analysis.matched_nodes.length > 0) {
      const node = analysis.matched_nodes[0]
      const types = analysis.suggested_types || ['doc','mindmap']
      const result = await apiReq('/resource/generate', {
        method: 'POST',
        body: JSON.stringify({ chapter_id: node.id, resource_types: types }),
      })

      streaming.value = false
      messages.value.push({
        role: 'ai',
        text: '✅ 已为《' + node.title + '》生成以下资源：',
        resources: result.resources || [],
      })
    } else {
      streaming.value = false
      messages.value.push({ role: 'ai', text: '未找到匹配的知识点，请尝试更具体的描述' })
    }
  } catch (e) {
    streaming.value = false
    messages.value.push({ role: 'ai', text: '生成失败：' + e.message })
  }
  generating.value = false
  scrollDown()
}

function viewResource(r) {
  viewing.value = r
}

function scrollDown() {
  nextTick(() => {
    if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
  })
}
</script>

<style scoped>
.page { max-width: 900px; margin: 0 auto; padding: 0 16px; }
.topbar { display: flex; align-items: center; gap: 16px; padding: 16px 0; }
.back { background: none; border: none; font-size: 16px; cursor: pointer; color: #4A90D9; }
h1 { font-size: 20px; }
.rec-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 10px 16px; background: #f0f7ff; border-radius: 12px; margin-bottom: 12px; }
.rec-label { font-size: 13px; color: #303133; white-space: nowrap; }
.rec-tag { padding: 4px 14px; background: #4A90D9; color: #fff; border: none; border-radius: 16px; font-size: 12px; cursor: pointer; }
.rec-tag:disabled { opacity: 0.5; }
.layout { display: flex; height: calc(100vh - 140px); }
.chat-area { flex: 1; display: flex; flex-direction: column; background: #fff; border-radius: 12px; box-shadow: var(--shadow); }
.messages { flex: 1; overflow-y: auto; padding: 16px; }
.msg { max-width: 85%; margin-bottom: 14px; font-size: 14px; line-height: 1.6; }
.msg.user { background: #4A90D9; color: #fff; padding: 10px 16px; border-radius: 12px; margin-left: auto; }
.msg.ai { background: #f0f2f5; color: #303133; padding: 12px 16px; border-radius: 12px; }
.cursor { animation: blink 0.8s infinite; }
@keyframes blink { 50% { opacity: 0; } }
.res-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 8px; margin-top: 10px; }
.res-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 10px; padding: 12px; cursor: pointer; transition: box-shadow 0.2s; }
.res-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.type-tag { font-size: 11px; background: #e6f0fa; color: #4A90D9; padding: 2px 8px; border-radius: 4px; margin-bottom: 6px; display: inline-block; }
.card-img { width: 100%; height: 80px; object-fit: contain; margin: 6px 0; border-radius: 4px; }
.res-card h4 { font-size: 13px; color: #303133; margin: 4px 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.input-row { display: flex; gap: 10px; padding: 12px 16px; border-top: 1px solid #f0f0f0; }
.input-row input { flex: 1; height: 40px; border: 1px solid #e8e8e8; border-radius: 20px; padding: 0 16px; font-size: 14px; outline: none; }
.input-row button { height: 40px; padding: 0 20px; background: #4A90D9; color: #fff; border: none; border-radius: 20px; font-size: 14px; cursor: pointer; }
.input-row button:disabled { opacity: 0.5; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-inner { background: #fff; border-radius: 16px; padding: 24px; width: 90%; max-width: 650px; max-height: 85vh; overflow-y: auto; }
.modal-inner h3 { margin-bottom: 16px; }
.modal-img { margin-bottom: 12px; }
.modal-body { font-size: 14px; line-height: 1.8; }
.modal-inner button { margin-top: 16px; height: 40px; padding: 0 20px; background: #f0f2f5; border: none; border-radius: 8px; cursor: pointer; }
</style>
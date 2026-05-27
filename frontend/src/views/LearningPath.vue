<template>
  <div class="learning-path">
    <nav class="topnav glass-panel">
      <button class="nav-back" @click="goHome">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <h1 class="gradient-text">学习路径</h1>
      <div class="nav-spacer"></div>
    </nav>
    <div class="content">
      <button class="gen-btn" @click="generate" :disabled="genLoading">
        <svg v-if="!genLoading" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
        <span>{{ genLoading ? '生成中...' : nodes.length ? '重新规划' : '生成我的学习路径' }}</span>
      </button>
      <div class="timeline" v-if="nodes.length">
        <div class="tl-item" v-for="(n, i) in nodes" :key="i">
          <div class="tl-dot">{{ i + 1 }}</div>
          <div class="tl-card glass-panel">
            <h4>{{ n.title || '节点 ' + (i+1) }}</h4>
            <p v-if="n.reason" class="reason">{{ n.reason }}</p>
            <div class="tags" v-if="n.resource_types">
              <span class="tag" v-for="rt in n.resource_types" :key="rt">{{ rt }}</span>
            </div>
          </div>
          <div class="tl-line" v-if="i < nodes.length - 1"></div>
        </div>
      </div>
      <div v-else class="empty">
        <div class="empty-icon">
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
        <p>还没有学习路径</p>
        <p class="empty-hint">学习路径需要基于你的学习画像生成</p>
        <button class="gen-btn outline" @click="goProfile">先去完善学习画像</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getLearningPath, generateLearningPath } from '../http/http.js'

const router = useRouter()
const nodes = ref([])

function goHome() { router.push('/home') }
function goProfile() { router.push('/profile') }
const genLoading = ref(false)

onMounted(async () => {
  try { const r = await getLearningPath(); nodes.value = r.nodes || [] } catch (e) {}
})

async function generate() {
  genLoading.value = true
  try {
    await generateLearningPath()
    const r = await getLearningPath()
    nodes.value = r.nodes || []
    alert('路径生成成功')
  } catch (e) {
    const msg = e.message || '生成失败'
    if (msg.includes('学习画像')) {
      alert('请先去「学习画像」页面完成画像构建，再生成学习路径')
    } else {
      alert(msg)
    }
  }
  genLoading.value = false
}
</script>

<style scoped>
.learning-path { height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
.topnav { display: flex; align-items: center; padding: 10px 20px; margin: 10px 16px 0; border-radius: 18px; flex-shrink: 0; z-index: 10; }
.nav-back { display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 10px; background: rgba(255,255,255,0.04); color: var(--text-regular); transition: all var(--transition); }
.nav-back:hover { background: rgba(255,255,255,0.08); color: var(--text-primary); }
.topnav h1 { font-size: 1.1rem; font-weight: 700; margin-left: 14px; }
.nav-spacer { flex: 1; }
.content { flex: 1; max-width: 700px; margin: 0 auto; padding: 20px; overflow-y: auto; width: 100%; }
.gen-btn { width: 100%; height: 46px; background: var(--gradient-brand); color: #fff; border: none; border-radius: 14px; font-size: 0.95rem; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 28px; }
.gen-btn:hover { box-shadow: var(--shadow-glow); transform: translateY(-1px); }
.gen-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.gen-btn.outline { background: transparent; color: var(--primary-light); border: 1px solid rgba(91,127,255,0.3); width: auto; margin: 20px auto 0; padding: 10px 28px; height: auto; }
.gen-btn.outline:hover { background: var(--primary-bg); }
.timeline { padding-left: 48px; position: relative; }
.tl-item { position: relative; padding-bottom: 28px; }
.tl-dot { width: 38px; height: 38px; border-radius: 50%; background: var(--gradient-brand); color: #fff; text-align: center; line-height: 38px; font-size: 0.85rem; font-weight: 700; position: absolute; left: -56px; top: 0; box-shadow: var(--shadow-glow); }
.tl-card { padding: 18px 22px; border-radius: var(--radius); }
.tl-card h4 { font-size: 1rem; margin-bottom: 6px; }
.reason { font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 10px; line-height: 1.5; }
.tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag { font-size: 0.72rem; background: var(--primary-bg); color: var(--primary-light); padding: 3px 12px; border-radius: 8px; border: 1px solid rgba(91,127,255,0.15); }
.tl-line { position: absolute; left: -38px; top: 38px; width: 2px; height: calc(100% - 10px); background: linear-gradient(180deg, var(--primary) 0%, rgba(91,127,255,0.1) 100%); }
.empty { text-align: center; padding: 60px 20px; }
.empty-icon { margin-bottom: 16px; }
.empty p { color: var(--text-secondary); font-size: 0.95rem; }
.empty-hint { font-size: 0.82rem !important; margin: 10px 0 20px; color: var(--text-disabled) !important; }
</style>

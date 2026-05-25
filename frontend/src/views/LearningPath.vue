<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="$router.push('/home')">← 返回</button>
      <h1>学习路径</h1>
    </header>

    <button class="gen-btn" @click="generate" :disabled="genLoading">
      {{ genLoading ? '生成中...' : nodes.length ? '重新规划' : '生成我的学习路径' }}
    </button>

    <div class="timeline" v-if="nodes.length">
      <div class="tl-item" v-for="(n, i) in nodes" :key="i">
        <div class="tl-dot">{{ i + 1 }}</div>
        <div class="tl-card">
          <h4>{{ n.title || '节点 ' + (i+1) }}</h4>
          <p v-if="n.reason" class="reason">{{ n.reason }}</p>
          <div class="tags" v-if="n.resource_types">
            <span class="tag" v-for="rt in n.resource_types" :key="rt">{{ rt }}</span>
          </div>
        </div>
        <div class="tl-line" v-if="i < nodes.length - 1"></div>
      </div>
    </div>
    <div v-else class="empty">还没有学习路径，请先生成</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLearningPath, generateLearningPath } from '../http/http.js'

const nodes = ref([])
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
  } catch (e) { alert(e.message || '生成失败') }
  genLoading.value = false
}
</script>

<style scoped>
.page { max-width: 700px; margin: 0 auto; padding: 0 16px; }
.topbar { display: flex; align-items: center; gap: 16px; padding: 16px 0; }
.back { background: none; border: none; font-size: 16px; cursor: pointer; color: #4A90D9; }
h1 { font-size: 20px; }
.gen-btn { width: 100%; height: 44px; background: #4A90D9; color: #fff; border: none; border-radius: 10px; font-size: 15px; cursor: pointer; margin-bottom: 20px; }
.gen-btn:disabled { opacity: 0.6; }
.timeline { padding-left: 40px; position: relative; }
.tl-item { position: relative; padding-bottom: 24px; }
.tl-dot { width: 36px; height: 36px; border-radius: 18px; background: #4A90D9; color: #fff; text-align: center; line-height: 36px; font-size: 14px; font-weight: bold; position: absolute; left: -50px; top: 4px; }
.tl-card { background: #fff; border-radius: 12px; padding: 16px 20px; box-shadow: var(--shadow); }
.tl-card h4 { font-size: 16px; color: #303133; margin-bottom: 6px; }
.reason { font-size: 13px; color: #909399; margin-bottom: 8px; }
.tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag { font-size: 12px; background: #e6f0fa; color: #4A90D9; padding: 2px 10px; border-radius: 6px; }
.tl-line { position: absolute; left: -33px; top: 40px; width: 2px; height: calc(100% - 16px); background: #e8e8e8; }
.empty { text-align: center; padding: 60px; color: #909399; font-size: 15px; }
</style>

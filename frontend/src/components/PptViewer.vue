<template>
  <div class="ppt-viewer" @keydown.left="prevSlide" @keydown.right="nextSlide" tabindex="0" ref="container">
    <!-- 顶部工具栏 -->
    <div class="pv-toolbar">
      <span class="pv-title">{{ pptData?.title || 'PPT课件' }}</span>
      <div class="pv-actions">
        <span class="pv-page-indicator">{{ currentPage }} / {{ totalPages }}</span>
        <button class="pv-btn" @click="downloadPptx" :disabled="!resourceId">📥 导出PPTX</button>
        <button class="pv-btn" @click="toggleFullscreen">🖥 全屏</button>
      </div>
    </div>

    <div class="pv-main">
      <!-- 缩略图列 -->
      <div class="pv-thumbnails" v-if="!isFullscreen">
        <div
          v-for="(slide, idx) in slides"
          :key="idx"
          class="pv-thumb"
          :class="{ active: currentPage === idx + 1 }"
          @click="goToSlide(idx + 1)"
        >
          <span class="pv-thumb-num">{{ idx + 1 }}</span>
          <span class="pv-thumb-title">{{ slide.title }}</span>
        </div>
      </div>

      <!-- 主舞台 -->
      <div class="pv-stage" :class="{ fullscreen: isFullscreen }">
        <!-- 标题页 -->
        <div v-if="currentSlide?.layout === 'title_slide'" class="pv-title-slide">
          <div class="pv-ts-bar"></div>
          <h1 class="pv-ts-title">{{ pptData?.title || currentSlide?.title }}</h1>
          <p v-if="currentSlide?.bullets?.length" class="pv-ts-subtitle">
            {{ currentSlide.bullets.join(' | ') }}
          </p>
        </div>

        <!-- 内容/小结页 -->
        <div v-else-if="currentSlide?.layout === 'title_content' || currentSlide?.layout === 'summary'" class="pv-content-slide">
          <h2 class="pv-slide-title">{{ currentSlide?.title }}</h2>
          <ul class="pv-bullets">
            <li v-for="(b, i) in currentSlide?.bullets" :key="i">{{ b }}</li>
          </ul>
          <p v-if="currentSlide?.key_point" class="pv-key-point">★ {{ currentSlide?.key_point }}</p>
        </div>

        <!-- 对比页 -->
        <div v-else-if="currentSlide?.layout === 'two_column'" class="pv-compare-slide">
          <h2 class="pv-slide-title">{{ currentSlide?.title }}</h2>
          <div class="pv-columns">
            <div class="pv-col">
              <ul><li v-for="(b, i) in leftBullets" :key="i">{{ b }}</li></ul>
            </div>
            <div class="pv-col">
              <ul><li v-for="(b, i) in rightBullets" :key="i">{{ b }}</li></ul>
            </div>
          </div>
        </div>

        <!-- 表格页 -->
        <div v-else-if="currentSlide?.layout === 'table'" class="pv-table-slide">
          <h2 class="pv-slide-title">{{ currentSlide?.title }}</h2>
          <table class="pv-table" v-if="currentSlide?.table">
            <thead>
              <tr>
                <th v-for="(h, i) in currentSlide.table.headers" :key="i">{{ h }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in currentSlide.table.rows" :key="ri">
                <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 图表页 -->
        <div v-else-if="currentSlide?.layout === 'diagram'" class="pv-diagram-slide">
          <h2 class="pv-slide-title">{{ currentSlide?.title }}</h2>
          <pre class="pv-diagram-code">{{ currentSlide?.diagram }}</pre>
        </div>

        <!-- 默认内容页 -->
        <div v-else class="pv-content-slide">
          <h2 class="pv-slide-title">{{ currentSlide?.title || '幻灯片' }}</h2>
          <ul class="pv-bullets" v-if="currentSlide?.bullets">
            <li v-for="(b, i) in currentSlide.bullets" :key="i">{{ b }}</li>
          </ul>
        </div>

        <!-- 演讲者备注 -->
        <div v-if="currentSlide?.speaker_notes" class="pv-notes" :class="{ collapsed: notesCollapsed }">
          <div class="pv-notes-header" @click="notesCollapsed = !notesCollapsed">
            📝 演讲者备注 {{ notesCollapsed ? '▶' : '▼' }}
          </div>
          <p v-if="!notesCollapsed" class="pv-notes-text">{{ currentSlide?.speaker_notes }}</p>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="pv-nav">
      <button class="pv-nav-btn" @click="prevSlide" :disabled="currentPage <= 1">← 上一页</button>
      <div class="pv-dots">
        <span
          v-for="(s, i) in slides"
          :key="i"
          class="pv-dot"
          :class="{ active: currentPage === i + 1, [s.layout || '']: true }"
          @click="goToSlide(i + 1)"
          :title="s.title"
        ></span>
      </div>
      <button class="pv-nav-btn" @click="nextSlide" :disabled="currentPage >= totalPages">下一页 →</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { downloadPptx as apiDownloadPptx } from '../http/http.js'

const props = defineProps({
  content: { type: String, default: '' },
  resourceId: { type: [Number, String], default: null },
})

const currentPage = ref(1)
const notesCollapsed = ref(true)
const isFullscreen = ref(false)
const container = ref(null)

const pptData = computed(() => {
  if (!props.content) return null
  try { return JSON.parse(props.content) } catch { return null }
})

const slides = computed(() => pptData.value?.slides || [])
const totalPages = computed(() => slides.value.length || 0)
const currentSlide = computed(() => slides.value[currentPage.value - 1] || null)

const leftBullets = computed(() => {
  const b = currentSlide.value?.bullets || []
  const mid = Math.ceil(b.length / 2)
  return b.slice(0, mid)
})
const rightBullets = computed(() => {
  const b = currentSlide.value?.bullets || []
  const mid = Math.ceil(b.length / 2)
  return b.slice(mid)
})

function goToSlide(page) { currentPage.value = Math.max(1, Math.min(page, totalPages.value)) }
function prevSlide() { goToSlide(currentPage.value - 1) }
function nextSlide() { goToSlide(currentPage.value + 1) }

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  if (container.value) container.value.focus()
}

async function downloadPptx() {
  if (!props.resourceId) return
  try {
    await apiDownloadPptx(props.resourceId)
  } catch (e) {
    alert('导出失败: ' + e.message)
  }
}

function handleKeydown(e) {
  if (e.key === 'ArrowLeft') { e.preventDefault(); prevSlide() }
  if (e.key === 'ArrowRight') { e.preventDefault(); nextSlide() }
}

watch(() => props.content, () => { currentPage.value = 1 })

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  if (container.value) container.value.focus()
})
onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))
</script>

<style scoped>
.ppt-viewer { display: flex; flex-direction: column; height: 100%; min-height: 500px; outline: none; background: #0f0f1a; border-radius: 8px; overflow: hidden; color: #eee; }
.pv-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 8px 16px; background: #1a1a2e; border-bottom: 1px solid #2a2a4a; flex-shrink: 0; }
.pv-title { font-size: 15px; font-weight: 600; color: #5B7FFF; }
.pv-actions { display: flex; align-items: center; gap: 10px; }
.pv-page-indicator { font-size: 13px; color: #888; }
.pv-btn { padding: 5px 12px; border: 1px solid #5B7FFF; background: transparent; color: #5B7FFF; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all .2s; }
.pv-btn:hover { background: #5B7FFF; color: #fff; }
.pv-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.pv-main { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
.pv-thumbnails { display: flex; gap: 4px; overflow-x: auto; padding: 6px 12px; border-bottom: 1px solid #2a2a4a; flex-shrink: 0; min-height: 50px; align-items: center; }
.pv-thumb { display: flex; align-items: center; gap: 4px; padding: 4px 8px; cursor: pointer; border-radius: 4px; transition: all .15s; flex-shrink: 0; white-space: nowrap; }
.pv-thumb:hover { background: #2a2a4a; }
.pv-thumb.active { background: #1a3a6a; border-bottom: 3px solid #5B7FFF; }
.pv-thumb-num { width: 22px; height: 22px; border-radius: 3px; background: #333; display: flex; align-items: center; justify-content: center; font-size: 11px; flex-shrink: 0; }
.pv-thumb.active .pv-thumb-num { background: #5B7FFF; }
.pv-thumb-title { display: none; }
.pv-stage { flex: 1; padding: 32px 48px; overflow-y: auto; display: flex; flex-direction: column; position: relative; justify-content: center; }
.pv-stage.fullscreen { padding: 60px 120px; justify-content: center; }
/* Title slide */
.pv-title-slide { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; text-align: center; }
.pv-ts-bar { width: 60%; height: 4px; background: linear-gradient(90deg, #5B7FFF, #a78bfa, #FF6B6B); border-radius: 2px; margin-bottom: 48px; align-self: center; }
.pv-ts-title { font-size: 42px; font-weight: 800; background: linear-gradient(135deg, #5B7FFF, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 24px; }
.pv-ts-subtitle { font-size: 18px; color: #888; max-width: 700px; line-height: 1.8; }
/* Content slide */
.pv-content-slide { flex: 1; }
.pv-slide-title { font-size: 28px; font-weight: 700; color: #e8e8f0; margin-bottom: 28px; padding-bottom: 10px; border-bottom: 2px solid #5B7FFF; }
.pv-bullets { list-style: none; padding: 0; }
.pv-bullets li { padding: 12px 0; padding-left: 24px; position: relative; font-size: 17px; color: #d0d0e0; line-height: 1.7; }
.pv-bullets li::before { content: '▸'; position: absolute; left: 0; color: #5B7FFF; font-size: 14px; }
.pv-key-point { margin-top: 28px; padding: 14px 20px; background: rgba(91, 127, 255, 0.12); border-left: 4px solid #5B7FFF; border-radius: 6px; font-size: 15px; color: #8aadff; font-weight: 500; }
/* Compare */
.pv-columns { display: flex; gap: 24px; }
.pv-col { flex: 1; background: #1a1a2e; border-radius: 8px; padding: 16px; }
.pv-col ul { list-style: disc; padding-left: 20px; }
.pv-col li { color: #ccc; padding: 6px 0; font-size: 15px; }
/* Table */
.pv-table { border-collapse: collapse; width: 100%; margin-top: 16px; }
.pv-table th { background: #5B7FFF; color: #fff; padding: 10px 14px; text-align: left; font-size: 14px; }
.pv-table td { padding: 10px 14px; border-bottom: 1px solid #2a2a4a; font-size: 14px; color: #d0d0e0; }
.pv-table tr:hover td { background: rgba(91, 127, 255, 0.05); }
/* Diagram */
.pv-diagram-code { background: #1a1a2e; padding: 16px; border-radius: 6px; font-family: monospace; font-size: 13px; color: #aab; white-space: pre-wrap; }
/* Notes */
.pv-notes { margin-top: auto; background: #1a1a2e; border-radius: 6px; overflow: hidden; flex-shrink: 0; }
.pv-notes-header { padding: 8px 16px; font-size: 13px; color: #888; cursor: pointer; border-bottom: 1px solid #2a2a4a; }
.pv-notes-header:hover { color: #ccc; }
.pv-notes-text { padding: 12px 16px; font-size: 13px; color: #aaa; line-height: 1.6; }
/* Nav */
.pv-nav { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 10px 16px; background: #1a1a2e; border-top: 1px solid #2a2a4a; flex-shrink: 0; }
.pv-nav-btn { padding: 6px 16px; background: transparent; border: 1px solid #555; color: #ccc; border-radius: 4px; cursor: pointer; font-size: 13px; }
.pv-nav-btn:hover:not(:disabled) { border-color: #5B7FFF; color: #5B7FFF; }
.pv-nav-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.pv-dots { display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; }
.pv-dot { width: 10px; height: 10px; border-radius: 50%; background: #333; cursor: pointer; transition: all .2s; }
.pv-dot:hover { background: #666; }
.pv-dot.active { background: #5B7FFF; transform: scale(1.3); }


</style>

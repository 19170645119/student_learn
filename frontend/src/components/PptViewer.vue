<template>
  <div class="ppt-viewer" tabindex="0" ref="container"
    @keydown.left.prevent="prevSlide"
    @keydown.right.prevent="nextSlide"
    @keydown.f.prevent="toggleFullscreen"
    @keydown.p.prevent="togglePresenter"
    @keydown.home.prevent="goToSlide(1)"
    @keydown.end.prevent="goToSlide(totalPages)"
    @keydown.escape.prevent="exitModes"
  >
    <!-- 顶部工具栏 -->
    <div class="pv-toolbar" v-if="!isPresenter">
      <span class="pv-title">{{ pptData?.title || 'PPT课件' }}</span>
      <div class="pv-actions">
        <span class="pv-page-indicator">{{ currentPage }} / {{ totalPages }}</span>
        <button class="pv-btn" @click="downloadPptx" :disabled="!resourceId">📎 导出PPTX</button>
        <button class="pv-btn" @click="togglePresenter" title="演讲模式 (P键)">🎤 演讲模式</button>
        <button class="pv-btn" @click="toggleFullscreen" title="全屏 (F键)">🖼 全屏</button>
      </div>
    </div>

    <!-- 演讲者模式工具栏 -->
    <div class="pv-toolbar presenter-bar" v-else>
      <span class="pv-title">🎤 演讲者视图</span>
      <div class="pv-actions">
        <span class="pv-page-indicator">{{ currentPage }} / {{ totalPages }}</span>
        <button class="pv-btn" @click="togglePresenter">退出演讲模式</button>
      </div>
    </div>

    <!-- 演讲者模式：左右分屏 -->
    <div class="pv-main" v-if="isPresenter">
      <div class="pv-presenter-layout">
        <div class="pv-presenter-slide">
          <Transition name="slide-fade" mode="out-in">
            <div :key="currentPage" class="pv-stage presenter-stage">
              <component :is="slideComponent" :slide="currentSlide" :pptData="pptData" />
            </div>
          </Transition>
        </div>
        <div class="pv-presenter-sidebar">
          <div class="pv-presenter-notes">
            <h4>📝 演讲备注</h4>
            <p>{{ currentSlide?.speaker_notes || '无备注' }}</p>
          </div>
          <div class="pv-presenter-next">
            <h4>▶ 下一页预览</h4>
            <div class="pv-next-mini" v-if="nextSlideData">
              <strong>{{ nextSlideData.title }}</strong>
              <ul v-if="nextSlideData.bullets?.length">
                <li v-for="(b, i) in nextSlideData.bullets?.slice(0, 3)" :key="i">{{ b }}</li>
              </ul>
            </div>
            <p v-else class="pv-no-next">已是最后一页</p>
          </div>
          <div class="pv-presenter-timer">
            <span>{{ elapsedStr }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 普通模式 -->
    <template v-else>
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
            <span class="pv-thumb-icon">{{ getLayoutIcon(slide.layout) }}</span>
            <span class="pv-thumb-num">{{ idx + 1 }}</span>
            <span class="pv-thumb-title">{{ slide.title }}</span>
          </div>
        </div>

        <!-- 主舞台 -->
        <Transition :name="transitionName" mode="out-in">
          <div :key="currentPage" class="pv-stage" :class="{ fullscreen: isFullscreen }">
            <component :is="slideComponent" :slide="currentSlide" :pptData="pptData" :mermaidSvg="currentMermaidSvg" />

            <!-- 演讲者备注 -->
            <div v-if="currentSlide?.speaker_notes" class="pv-notes" :class="{ collapsed: notesCollapsed }">
              <div class="pv-notes-header" @click="notesCollapsed = !notesCollapsed">
                📝 演讲者备注 {{ notesCollapsed ? '▶' : '▼' }}
              </div>
              <p v-if="!notesCollapsed" class="pv-notes-text">{{ currentSlide?.speaker_notes }}</p>
            </div>
          </div>
        </Transition>
      </div>
    </template>

    <!-- 底部导航 -->
    <div class="pv-nav">
      <button class="pv-nav-btn" @click="prevSlide" :disabled="currentPage <= 1">← 上一页</button>
      <div class="pv-dots">
        <span
          v-for="(s, i) in slides"
          :key="i"
          class="pv-dot"
          :class="{ active: currentPage === i + 1 }"
          @click="goToSlide(i + 1)"
          :title="`${i+1}. ${s.title}`"
        >{{ getLayoutIcon(s.layout) }}</span>
      </div>
      <button class="pv-nav-btn" @click="nextSlide" :disabled="currentPage >= totalPages">下一页 →</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, shallowRef } from 'vue'
import { downloadPptx as apiDownloadPptx } from '../http/http.js'

const props = defineProps({
  content: { type: String, default: '' },
  resourceId: { type: [Number, String], default: null },
})

const currentPage = ref(1)
const notesCollapsed = ref(true)
const isFullscreen = ref(false)
const isPresenter = ref(false)
const container = ref(null)
const currentMermaidSvg = ref('')
const elapsedSeconds = ref(0)
let timerInterval = null

// 数据计算
const pptData = computed(() => {
  if (!props.content) return null
  try { return JSON.parse(props.content) } catch { return null }
})
const slides = computed(() => pptData.value?.slides || [])
const totalPages = computed(() => slides.value.length || 0)
const currentSlide = computed(() => slides.value[currentPage.value - 1] || null)
const nextSlideData = computed(() => slides.value[currentPage.value] || null)

// 过渡动画名称（根据layout变化）
const transitionName = computed(() => {
  const layout = currentSlide.value?.layout
  if (layout === 'title_slide') return 'slide-up'
  if (layout === 'data_highlight') return 'slide-pop'
  if (layout === 'case_study') return 'slide-right'
  return 'slide-fade'
})

// 左右分列
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

const elapsedStr = computed(() => {
  const m = Math.floor(elapsedSeconds.value / 60)
  const s = elapsedSeconds.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

// Layout图标
function getLayoutIcon(layout) {
  const map = {
    title_slide: '🏠', title_content: '📖', two_column: '⚖️',
    table: '📊', diagram: '📐', summary: '🏁',
    chapter_divider: '📂', case_study: '💼', data_highlight: '📈',
    audience_question: '❓', key_quote: '💡'
  }
  return map[layout] || '📄'
}

// 动态幻灯片组件
const slideComponent = computed(() => {
  const layout = currentSlide.value?.layout || 'title_content'
  const compMap = {
    title_slide: 'TitleSlide',
    title_content: 'ContentSlide',
    summary: 'ContentSlide',
    two_column: 'CompareSlide',
    table: 'TableSlide',
    diagram: 'DiagramSlide',
    chapter_divider: 'ChapterDivider',
    case_study: 'CaseStudySlide',
    data_highlight: 'DataHighlight',
    audience_question: 'AudienceQuestion',
    key_quote: 'KeyQuote',
  }
  return compMap[layout] || 'ContentSlide'
})

// 导航
function goToSlide(page) { currentPage.value = Math.max(1, Math.min(page, totalPages.value)) }
function prevSlide() { goToSlide(currentPage.value - 1) }
function nextSlide() { goToSlide(currentPage.value + 1) }

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  if (isPresenter.value && isFullscreen.value) isPresenter.value = false
  nextTickFocus()
}
function togglePresenter() {
  isPresenter.value = !isPresenter.value
  if (isPresenter.value) {
    isFullscreen.value = false
    elapsedSeconds.value = 0
    startTimer()
  } else {
    stopTimer()
  }
  nextTickFocus()
}
function exitModes() {
  if (isPresenter.value) togglePresenter()
  else if (isFullscreen.value) toggleFullscreen()
}

function nextTickFocus() {
  setTimeout(() => { if (container.value) container.value.focus() }, 50)
}

// 计时器
function startTimer() {
  stopTimer()
  timerInterval = setInterval(() => { elapsedSeconds.value++ }, 1000)
}
function stopTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
}

// Mermaid 渲染
async function renderMermaid(diagramText) {
  if (!diagramText) { currentMermaidSvg.value = ''; return }
  try {
    const mermaid = (await import('mermaid')).default
    mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })
    const { svg } = await mermaid.render('mermaid-diagram', diagramText)
    currentMermaidSvg.value = svg
  } catch (e) {
    currentMermaidSvg.value = ''
    console.warn('Mermaid render failed:', e.message)
  }
}

// 监听页面切换
watch(currentPage, () => {
  const slide = currentSlide.value
  if (slide?.layout === 'diagram' && slide?.diagram) {
    renderMermaid(slide.diagram)
  } else {
    currentMermaidSvg.value = ''
  }
})

// 导出PPTX
async function downloadPptx() {
  if (!props.resourceId) return
  try {
    await apiDownloadPptx(props.resourceId)
  } catch (e) {
    alert('导出失败：' + e.message)
  }
}

onMounted(() => {
  if (currentSlide.value?.layout === 'diagram' && currentSlide.value?.diagram) {
    renderMermaid(currentSlide.value.diagram)
  }
  if (container.value) container.value.focus()
})

onBeforeUnmount(() => { stopTimer() })
</script>

<script>
// 注册全局子组件（用于动态component渲染）
import { h } from 'vue'

// 标题封面页
const TitleSlide = {
  props: ['slide', 'pptData'],
  render() {
    const slide = this.slide || {}
    const bullets = slide.bullets || []
    const title = this.pptData?.title || slide.title || ''
    return h('div', { class: 'pv-title-slide' }, [
      h('div', { class: 'pv-ts-bar' }),
      h('h1', { class: 'pv-ts-title' }, title),
      bullets.length ? h('p', { class: 'pv-ts-subtitle' }, bullets.join(' | ')) : null,
      slide.key_point ? h('p', { class: 'pv-ts-hook' }, '💬 ' + slide.key_point) : null,
    ])
  }
}

// 标题内容页 / 小结页
const ContentSlide = {
  props: ['slide'],
  render() {
    const slide = this.slide || {}
    const bullets = slide.bullets || []
    const isSummary = slide.layout === 'summary'
    return h('div', { class: isSummary ? 'pv-summary-slide' : 'pv-content-slide' }, [
      h('h2', { class: 'pv-slide-title' }, slide.title || ''),
      bullets.length ? h('ul', { class: 'pv-bullets' }, bullets.map(b => h('li', b))) : null,
      slide.elaboration ? h('div', { class: 'pv-elaboration' }, slide.elaboration) : null,
      slide.key_point ? h('p', { class: 'pv-key-point' }, '⭐ ' + slide.key_point) : null,
    ])
  }
}

// 对比页
const CompareSlide = {
  props: ['slide'],
  render() {
    const slide = this.slide || {}
    const bullets = slide.bullets || []
    const mid = Math.ceil(bullets.length / 2)
    return h('div', { class: 'pv-compare-slide' }, [
      h('h2', { class: 'pv-slide-title' }, slide.title || ''),
      h('div', { class: 'pv-columns' }, [
        h('div', { class: 'pv-col' }, [
          h('h4', { class: 'pv-col-label' }, slide.table?.headers?.[0] || 'A'),
          h('ul', bullets.slice(0, mid).map(b => h('li', b))),
        ]),
        h('div', { class: 'pv-col' }, [
          h('h4', { class: 'pv-col-label' }, slide.table?.headers?.[1] || 'B'),
          h('ul', bullets.slice(mid).map(b => h('li', b))),
        ]),
      ]),
    ])
  }
}

// 表格页
const TableSlide = {
  props: ['slide'],
  render() {
    const slide = this.slide || {}
    const table = slide.table
    return h('div', { class: 'pv-table-slide' }, [
      h('h2', { class: 'pv-slide-title' }, slide.title || ''),
      table ? h('table', { class: 'pv-table' }, [
        h('thead', [h('tr', table.headers?.map(hh => h('th', hh)))]),
        h('tbody', table.rows?.map(row => h('tr', row.map(cell => h('td', String(cell)))))),
      ]) : null,
    ])
  }
}

// 图表页（Mermaid）
const DiagramSlide = {
  props: ['slide', 'mermaidSvg'],
  render() {
    const slide = this.slide || {}
    const svg = this.mermaidSvg || ''
    const bullets = slide.bullets || []
    return h('div', { class: 'pv-diagram-slide' }, [
      h('h2', { class: 'pv-slide-title' }, slide.title || ''),
      svg ? h('div', { class: 'pv-mermaid-wrap', innerHTML: svg }) :
        h('pre', { class: 'pv-diagram-code' }, slide.diagram || ''),
      bullets.length ? h('ul', { class: 'pv-diagram-bullets' }, bullets.map(b => h('li', b))) : null,
    ])
  }
}

// 章节过渡页
const ChapterDivider = {
  props: ['slide'],
  render() {
    const slide = this.slide || {}
    return h('div', { class: 'pv-chapter-divider' }, [
      h('div', { class: 'pv-chapter-num' }, slide.section_num ? `第${slide.section_num}部分` : ''),
      h('h2', { class: 'pv-chapter-title' }, slide.section_title || slide.title || ''),
      slide.key_point ? h('p', { class: 'pv-chapter-desc' }, slide.key_point) : null,
    ])
  }
}

// 案例页
const CaseStudySlide = {
  props: ['slide'],
  render() {
    const slide = this.slide || {}
    return h('div', { class: 'pv-case-study' }, [
      h('div', { class: 'pv-case-badge' }, '📋 案例'),
      h('h2', { class: 'pv-case-title' }, slide.case_title || slide.title || ''),
      h('p', { class: 'pv-case-content' }, slide.case_content || ''),
      slide.case_insight ? h('div', { class: 'pv-case-insight' }, [
        h('span', { class: 'pv-case-insight-label' }, '💡 洞察：'),
        h('span', slide.case_insight),
      ]) : null,
      slide.bullets?.length ? h('ul', { class: 'pv-bullets' }, slide.bullets.map(b => h('li', b))) : null,
    ])
  }
}

// 数据亮点页
const DataHighlight = {
  props: ['slide'],
  render() {
    const slide = this.slide || {}
    const metrics = slide.metrics || []
    return h('div', { class: 'pv-data-highlight' }, [
      h('h2', { class: 'pv-slide-title' }, slide.title || ''),
      h('div', { class: 'pv-metrics' }, metrics.map((m, i) =>
        h('div', { class: 'pv-metric-card', style: { animationDelay: `${i * 0.15}s` } }, [
          h('div', { class: 'pv-metric-value' }, String(m.value)),
          h('div', { class: 'pv-metric-label' }, m.label),
          m.desc ? h('div', { class: 'pv-metric-desc' }, m.desc) : null,
        ])
      )),
      slide.bullets?.length ? h('p', { class: 'pv-key-point' }, slide.bullets[0]) : null,
    ])
  }
}

// 互动提问页
const AudienceQuestion = {
  props: ['slide'],
  setup(props) {
    const showHint = ref(false)
    return () => {
      const slide = props.slide || {}
      return h('div', { class: 'pv-audience-question' }, [
        h('div', { class: 'pv-question-icon' }, '❓'),
        h('h2', { class: 'pv-question-text' }, slide.question || slide.title || ''),
        slide.hint ? h('div', { class: 'pv-question-hint-wrap' }, [
          h('button', { class: 'pv-hint-btn', onClick: () => showHint.value = !showHint.value },
            showHint.value ? '🔽 隐藏提示' : '🔼 点击查看提示'),
          showHint.value ? h('p', { class: 'pv-question-hint' }, slide.hint) : null,
        ]) : null,
        slide.key_point ? h('p', { class: 'pv-question-note' }, slide.key_point) : null,
      ])
    }
  }
}

// 金句引用页
const KeyQuote = {
  props: ['slide'],
  render() {
    const slide = this.slide || {}
    return h('div', { class: 'pv-key-quote' }, [
      h('div', { class: 'pv-quote-mark' }, '"'),
      h('blockquote', { class: 'pv-quote-text' }, slide.quote || slide.title || ''),
      slide.author ? h('p', { class: 'pv-quote-author' }, '—— ' + slide.author) : null,
      slide.key_point ? h('p', { class: 'pv-quote-note' }, slide.key_point) : null,
    ])
  }
}

// 注册组件
export default {
  components: {
    TitleSlide, ContentSlide, CompareSlide, TableSlide, DiagramSlide,
    ChapterDivider, CaseStudySlide, DataHighlight, AudienceQuestion, KeyQuote,
  }
}
</script>
<style scoped>
.ppt-viewer { display: flex; flex-direction: column; height: 100%; min-height: 500px; outline: none; background: #0f0f1a; border-radius: 8px; overflow: hidden; color: #eee; }

/* 工具栏 */
.pv-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 8px 16px; background: #1a1a2e; border-bottom: 1px solid #2a2a4a; flex-shrink: 0; }
.pv-toolbar.presenter-bar { background: #1a1a00; border-bottom: 1px solid #4a4a00; }
.pv-title { font-size: 15px; font-weight: 600; color: #5B7FFF; }
.pv-actions { display: flex; align-items: center; gap: 10px; }
.pv-page-indicator { font-size: 13px; color: #888; }
.pv-btn { padding: 5px 12px; border: 1px solid #5B7FFF; background: transparent; color: #5B7FFF; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all .2s; }
.pv-btn:hover { background: #5B7FFF; color: #fff; }
.pv-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* 主区域 */
.pv-main { display: flex; flex-direction: column; flex: 1; overflow: hidden; }

/* 缩略图 */
.pv-thumbnails { display: flex; gap: 4px; overflow-x: auto; padding: 6px 12px; border-bottom: 1px solid #2a2a4a; flex-shrink: 0; min-height: 50px; align-items: center; }
.pv-thumb { display: flex; align-items: center; gap: 4px; padding: 4px 8px; cursor: pointer; border-radius: 4px; transition: all .15s; flex-shrink: 0; white-space: nowrap; }
.pv-thumb:hover { background: #2a2a4a; }
.pv-thumb.active { background: #1a3a6a; border-bottom: 3px solid #5B7FFF; }
.pv-thumb-icon { font-size: 11px; }
.pv-thumb-num { width: 22px; height: 22px; border-radius: 3px; background: #333; display: flex; align-items: center; justify-content: center; font-size: 11px; flex-shrink: 0; }
.pv-thumb.active .pv-thumb-num { background: #5B7FFF; }
.pv-thumb-title { font-size: 12px; color: #aaa; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* 舞台 */
.pv-stage { flex: 1; padding: 32px 48px; overflow-y: auto; display: flex; flex-direction: column; position: relative; justify-content: center; }
.pv-stage.fullscreen { padding: 60px 120px; justify-content: center; }

/* === 幻灯片过渡动画 === */
.slide-fade-enter-active, .slide-fade-leave-active { transition: opacity .35s ease, transform .35s ease; }
.slide-fade-enter-from { opacity: 0; transform: translateX(20px); }
.slide-fade-leave-to { opacity: 0; transform: translateX(-20px); }

.slide-up-enter-active, .slide-up-leave-active { transition: opacity .4s ease, transform .4s ease; }
.slide-up-enter-from { opacity: 0; transform: translateY(30px); }
.slide-up-leave-to { opacity: 0; transform: translateY(-20px); }

.slide-right-enter-active, .slide-right-leave-active { transition: opacity .35s ease, transform .35s ease; }
.slide-right-enter-from { opacity: 0; transform: translateX(40px); }
.slide-right-leave-to { opacity: 0; transform: translateX(-30px); }

.slide-pop-enter-active { transition: all .3s ease; }
.slide-pop-leave-active { transition: all .2s ease; }
.slide-pop-enter-from { opacity: 0; transform: scale(0.9); }
.slide-pop-leave-to { opacity: 0; transform: scale(1.05); }

/* === 标题封面页 === */
.pv-title-slide { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; text-align: center; }
.pv-ts-bar { width: 60%; height: 4px; background: linear-gradient(90deg, #5B7FFF, #a78bfa, #FF6B6B); border-radius: 2px; margin-bottom: 48px; align-self: center; }
.pv-ts-title { font-size: 42px; font-weight: 800; background: linear-gradient(135deg, #5B7FFF, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 24px; }
.pv-ts-subtitle { font-size: 18px; color: #888; max-width: 700px; line-height: 1.8; }
.pv-ts-hook { margin-top: 24px; font-size: 16px; color: #FF6B6B; font-style: italic; }

/* === 标题内容页 === */
.pv-content-slide { flex: 1; }
.pv-slide-title { font-size: 28px; font-weight: 700; color: #e8e8f0; margin-bottom: 28px; padding-bottom: 10px; border-bottom: 2px solid #5B7FFF; }
.pv-bullets { list-style: none; padding: 0; }
.pv-bullets li { padding: 12px 0; padding-left: 24px; position: relative; font-size: 17px; color: #d0d0e0; line-height: 1.7; }
.pv-bullets li::before { content: '▸'; position: absolute; left: 0; color: #5B7FFF; font-size: 14px; }
.pv-key-point { margin-top: 28px; padding: 14px 20px; background: rgba(91, 127, 255, 0.12); border-left: 4px solid #5B7FFF; border-radius: 6px; font-size: 15px; color: #8aadff; font-weight: 500; }

.pv-elaboration { margin-top: 20px; padding: 14px 18px; background: rgba(167,139,250,0.08); border-radius: 8px; font-size: 15px; color: #c8c8d8; line-height: 1.8; }

/* === 小结页 === */
.pv-summary-slide { flex: 1; }
.pv-summary-slide .pv-slide-title { border-bottom-color: #a78bfa; }
.pv-summary-slide .pv-bullets li { font-size: 18px; font-weight: 500; }
.pv-summary-slide .pv-bullets li::before { content: '✅'; color: #4ade80; }

/* === 对比页 === */
.pv-columns { display: flex; gap: 24px; }
.pv-col { flex: 1; background: #1a1a2e; border-radius: 8px; padding: 20px; }
.pv-col-label { color: #5B7FFF; font-size: 15px; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #2a2a4a; }
.pv-col ul { list-style: disc; padding-left: 20px; }
.pv-col li { color: #ccc; padding: 6px 0; font-size: 15px; }

/* === 表格页 === */
.pv-table { border-collapse: collapse; width: 100%; margin-top: 16px; }
.pv-table th { background: #5B7FFF; color: #fff; padding: 10px 14px; text-align: left; font-size: 14px; }
.pv-table td { padding: 10px 14px; border-bottom: 1px solid #2a2a4a; font-size: 14px; color: #d0d0e0; }
.pv-table tr:hover td { background: rgba(91, 127, 255, 0.05); }

/* === 图表页 (Mermaid) === */
.pv-diagram-slide { flex: 1; display: flex; flex-direction: column; }
.pv-mermaid-wrap { display: flex; justify-content: center; align-items: center; padding: 16px; overflow: auto; flex: 1; }
.pv-mermaid-wrap :deep(svg) { max-width: 100%; max-height: 400px; }
.pv-diagram-code { background: #1a1a2e; padding: 16px; border-radius: 6px; font-family: monospace; font-size: 13px; color: #aab; white-space: pre-wrap; overflow: auto; }
.pv-diagram-bullets { list-style: none; padding: 0; margin-top: 12px; }
.pv-diagram-bullets li { font-size: 13px; color: #aaa; padding: 3px 0; padding-left: 16px; position: relative; }
.pv-diagram-bullets li::before { content: '•'; position: absolute; left: 0; color: #5B7FFF; }

/* === 章节过渡页 === */
.pv-chapter-divider { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; text-align: center; background: linear-gradient(135deg, rgba(91,127,255,0.1), rgba(167,139,250,0.1)); border-radius: 12px; margin: 20px 0; padding: 60px 40px; }
.pv-chapter-num { font-size: 14px; color: #5B7FFF; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 16px; }
.pv-chapter-title { font-size: 36px; font-weight: 700; color: #e8e8f0; margin: 0 0 16px 0; }
.pv-chapter-desc { font-size: 16px; color: #888; max-width: 500px; line-height: 1.6; }

/* === 案例页 === */
.pv-case-study { flex: 1; }
.pv-case-badge { display: inline-block; padding: 4px 12px; background: rgba(255, 107, 107, 0.15); color: #FF6B6B; border-radius: 20px; font-size: 13px; font-weight: 600; margin-bottom: 16px; }
.pv-case-title { font-size: 24px; font-weight: 700; color: #e8e8f0; margin-bottom: 16px; }
.pv-case-content { font-size: 16px; color: #d0d0e0; line-height: 1.8; background: #1a1a2e; padding: 20px; border-radius: 8px; border-left: 4px solid #FF6B6B; }
.pv-case-insight { margin-top: 16px; padding: 12px 16px; background: rgba(74, 222, 128, 0.1); border-radius: 6px; font-size: 15px; color: #4ade80; }
.pv-case-insight-label { font-weight: 600; }

/* === 数据亮点页 === */
.pv-data-highlight { flex: 1; }
.pv-metrics { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 24px; }
.pv-metric-card { flex: 1; min-width: 140px; background: linear-gradient(135deg, #1a1a2e, #1f1f3a); border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #2a2a4a; animation: metricPop .5s ease both; }
.pv-metric-value { font-size: 36px; font-weight: 800; background: linear-gradient(135deg, #5B7FFF, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 8px; }
.pv-metric-label { font-size: 14px; color: #ccc; font-weight: 500; }
.pv-metric-desc { font-size: 12px; color: #888; margin-top: 4px; }

@keyframes metricPop {
  from { opacity: 0; transform: translateY(20px) scale(0.8); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* === 互动提问页 === */
.pv-audience-question { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; text-align: center; }
.pv-question-icon { font-size: 64px; margin-bottom: 24px; animation: pulse 2s infinite; }
.pv-question-text { font-size: 28px; font-weight: 700; color: #e8e8f0; max-width: 600px; line-height: 1.5; margin-bottom: 24px; }
.pv-question-hint-wrap { margin-bottom: 16px; }
.pv-hint-btn { background: transparent; border: 1px dashed #555; color: #aaa; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-size: 14px; transition: all .2s; }
.pv-hint-btn:hover { border-color: #5B7FFF; color: #5B7FFF; }
.pv-question-hint { margin-top: 12px; font-size: 15px; color: #4ade80; max-width: 500px; line-height: 1.6; }
.pv-question-note { font-size: 14px; color: #666; margin-top: 16px; }

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

/* === 金句引用页 === */
.pv-key-quote { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; text-align: center; padding: 40px; }
.pv-quote-mark { font-size: 80px; color: #5B7FFF; opacity: 0.3; font-family: Georgia, serif; line-height: 1; margin-bottom: -20px; }
.pv-quote-text { font-size: 26px; font-weight: 600; color: #e8e8f0; max-width: 600px; line-height: 1.6; font-style: italic; margin: 0 0 20px 0; border: none; padding: 0; }
.pv-quote-author { font-size: 16px; color: #888; }
.pv-quote-note { font-size: 14px; color: #666; margin-top: 12px; }

/* === 演讲者备注 === */
.pv-notes { margin-top: auto; background: #1a1a2e; border-radius: 6px; overflow: hidden; flex-shrink: 0; }
.pv-notes-header { padding: 8px 16px; font-size: 13px; color: #888; cursor: pointer; border-bottom: 1px solid #2a2a4a; }
.pv-notes-header:hover { color: #ccc; }
.pv-notes-text { padding: 12px 16px; font-size: 13px; color: #aaa; line-height: 1.6; }

/* === 演讲者视图 === */
.pv-presenter-layout { display: flex; flex: 1; overflow: hidden; }
.pv-presenter-slide { flex: 1.5; border-right: 1px solid #2a2a4a; display: flex; align-items: center; justify-content: center; background: #0a0a14; padding: 20px; }
.pv-presenter-slide .pv-stage { padding: 24px; }
.pv-presenter-sidebar { flex: 1; display: flex; flex-direction: column; overflow-y: auto; padding: 20px; gap: 16px; background: #111; }
.pv-presenter-notes { background: #1a1a2e; border-radius: 8px; padding: 16px; min-height: 120px; }
.pv-presenter-notes h4 { margin: 0 0 10px 0; color: #5B7FFF; font-size: 14px; }
.pv-presenter-notes p { color: #ccc; font-size: 14px; line-height: 1.7; margin: 0; }
.pv-presenter-next { background: #1a1a2e; border-radius: 8px; padding: 16px; }
.pv-presenter-next h4 { margin: 0 0 8px 0; color: #a78bfa; font-size: 14px; }
.pv-next-mini strong { color: #e8e8f0; font-size: 15px; }
.pv-next-mini ul { list-style: disc; padding-left: 20px; margin: 8px 0 0 0; }
.pv-next-mini li { color: #aaa; font-size: 13px; padding: 2px 0; }
.pv-no-next { color: #666; font-size: 13px; font-style: italic; }
.pv-presenter-timer { text-align: center; padding: 8px; }
.pv-presenter-timer span { font-size: 24px; font-family: monospace; color: #888; }

/* === 导航 === */
.pv-nav { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 10px 16px; background: #1a1a2e; border-top: 1px solid #2a2a4a; flex-shrink: 0; }
.pv-nav-btn { padding: 6px 16px; background: transparent; border: 1px solid #555; color: #ccc; border-radius: 4px; cursor: pointer; font-size: 13px; transition: all .2s; }
.pv-nav-btn:hover:not(:disabled) { border-color: #5B7FFF; color: #5B7FFF; }
.pv-nav-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.pv-dots { display: flex; gap: 4px; flex-wrap: wrap; justify-content: center; align-items: center; }
.pv-dot { width: 22px; height: 22px; border-radius: 50%; background: transparent; cursor: pointer; transition: all .2s; display: flex; align-items: center; justify-content: center; font-size: 10px; filter: grayscale(1); }
.pv-dot:hover { filter: grayscale(0.3); background: #2a2a4a; }
.pv-dot.active { filter: grayscale(0); background: #1a3a6a; transform: scale(1.25); box-shadow: 0 0 6px rgba(91,127,255,.4); }
</style>

<template>
  <div class="vp-container" v-if="script">
    <!-- Top Control Bar -->
    <div class="vp-controls">
      <div class="vp-mode-toggle">
        <button :class="{ active: !interactiveMode }" @click="interactiveMode = false">自动播放</button>
        <button :class="{ active: interactiveMode }" @click="interactiveMode = true">交互模式</button>
      </div>
      <button class="vp-btn" @click="togglePlay" :title="playing ? '暂停' : '播放'">
        <svg v-if="!playing" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
      </button>
      <button class="vp-btn" @click="restart" title="重播">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
      </button>
      <div class="vp-speed">
        <button v-for="s in speeds" :key="s" class="vp-speed-btn" :class="{ active: speed === s }" @click="speed = s">{{ s }}x</button>
      </div>
      <div class="vp-spacer"></div>
      <button v-if="interactiveMode" class="vp-btn vp-btn-nav" @click="stepPrev" :disabled="!canStepPrev" title="上一步">◀</button>
      <button v-if="interactiveMode" class="vp-btn vp-btn-nav vp-btn-next" @click="stepNext" :disabled="!canStepNext" title="下一步 (Space/→)">▶</button>
      <button class="vp-btn vp-btn-toggle" :class="{ active: showSubtitle }" @click="showSubtitle = !showSubtitle" title="字幕 (T)">📝</button>
      <button class="vp-btn vp-btn-toggle" :class="{ active: showNotes }" @click="showNotes = !showNotes" title="笔记 (N)">✏️</button>
    </div>
    <div class="vp-main">
      <div class="vp-stage-wrapper" :class="{ 'with-sidebar': showSubtitle || showNotes }">
        <transition :name="transitionName" mode="out-in">
          <div class="vp-stage" :key="sceneKey">
            <!-- Particles bg for title -->
            <div class="vp-particles" v-if="scene.type === 'title'">
              <span v-for="i in 12" :key="i" class="vp-particle" :style="{ left: (i*8.3)+'%', animationDelay: (i*0.4)+'s', animationDuration: (2+(i%4))+'s' }"></span>
            </div>
            <!-- ===== TITLE ===== -->
            <div v-if="scene.type === 'title'" class="vp-scene vp-title">
              <h1 class="vp-title-text">{{ scene.text }}</h1>
              <p v-if="scene.subtitle" class="vp-subtitle-text">{{ scene.subtitle }}</p>
            </div>
            <!-- ===== TEXT REVEAL ===== -->
            <div v-else-if="scene.type === 'text_reveal'" class="vp-scene vp-text-reveal">
              <h2 class="vp-scene-h2">{{ scene.title }}</h2>
              <ul>
                <li v-for="(b, bi) in visibleBullets" :key="bi" class="vp-bullet-li" :class="{ reveal: bi <= lastRevealedBullet }">
                  <span class="vp-bullet-num">{{ bi + 1 }}</span>
                  <span class="vp-bullet-text">{{ b }}</span>
                </li>
              </ul>
              <div v-if="lastRevealedBullet < (scene.bullets?.length||0)-1" class="vp-tap-hint">
                <span class="vp-tap-hint-pulse">👆 点击继续</span>
              </div>
            </div>
            <!-- ===== CODE WALKTHROUGH ===== -->
            <div v-else-if="scene.type === 'code_walkthrough'" class="vp-scene vp-code">
              <h2 class="vp-scene-h2">代码讲解</h2>
              <div class="vp-code-block">
                <div class="vp-line-numbers">
                  <span v-for="(l, li) in codeLines" :key="li"
                    :class="{ 'hl-current': li === highlightedLine, 'hl-past': li < highlightedLine, 'hl-future': li > highlightedLine }">
                    {{ li + 1 }}
                  </span>
                </div>
                <pre><code v-html="highlightedCode"></code></pre>
              </div>
              <div v-if="highlightedLine < codeLines.length - 1" class="vp-tap-hint">
                <span class="vp-tap-hint-pulse">👆 点击查看下一行</span>
              </div>
            </div>
            <!-- ===== DIAGRAM ===== -->
            <div v-else-if="scene.type === 'diagram'" class="vp-scene vp-diagram">
              <h2 class="vp-scene-h2">图解</h2>
              <div class="vp-mermaid-wrap" v-html="renderedMermaid"></div>
              <div class="vp-build-steps" v-if="scene.build_steps && scene.build_steps > 1">
                <span v-for="s in scene.build_steps" :key="s" class="vp-step-dot" :class="{ active: s <= currentBuildStep }"></span>
              </div>
              <div v-if="scene.build_steps > 1 && currentBuildStep < scene.build_steps" class="vp-tap-hint">
                <span class="vp-tap-hint-pulse">👆 点击逐步构建</span>
              </div>
            </div>
            <!-- ===== COMPARE ===== -->
            <div v-else-if="scene.type === 'compare'" class="vp-scene vp-compare">
              <div class="vp-compare-col vp-compare-left" :class="{ reveal: compareReveal >= 0 }">
                <h3>{{ scene.left_title }}</h3>
                <ul><li v-for="(it, idx) in scene.left_items" :key="idx" :style="{ animationDelay: compareReveal >= 0 ? idx*0.2+'s' : '' }" :class="{ reveal: compareReveal >= 0 }">{{ it }}</li></ul>
              </div>
              <div class="vp-compare-vs" :class="{ reveal: compareReveal >= 1 }">VS</div>
              <div class="vp-compare-col vp-compare-right" :class="{ reveal: compareReveal >= 1 }">
                <h3>{{ scene.right_title }}</h3>
                <ul><li v-for="(it, idx) in scene.right_items" :key="idx" :style="{ animationDelay: compareReveal >= 1 ? idx*0.2+'s' : '' }" :class="{ reveal: compareReveal >= 1 }">{{ it }}</li></ul>
              </div>
              <div v-if="compareReveal < 1" class="vp-tap-hint">
                <span class="vp-tap-hint-pulse">👆 点击查看对比</span>
              </div>
            </div>
            <!-- ===== QUIZ CARD ===== -->
            <div v-else-if="scene.type === 'quiz_card'" class="vp-scene vp-quiz">
              <div class="vp-quiz-badge">🧪 随堂测验</div>
              <h2 class="vp-quiz-question">{{ scene.question }}</h2>
              <div class="vp-quiz-options">
                <button v-for="(opt, oi) in scene.options" :key="oi"
                  class="vp-quiz-opt"
                  :class="{
                    selected: quizSelected === oi,
                    correct: quizAnswered && oi === scene.answer,
                    wrong: quizAnswered && quizSelected === oi && oi !== scene.answer,
                    disabled: quizAnswered
                  }"
                  :disabled="quizAnswered"
                  @click="selectQuizOption(oi)">
                  <span class="vp-quiz-opt-letter">{{ ['A','B','C','D'][oi] }}</span>
                  <span class="vp-quiz-opt-text">{{ opt }}</span>
                  <span v-if="quizAnswered && oi === scene.answer" class="vp-quiz-opt-icon">✓</span>
                  <span v-else-if="quizAnswered && quizSelected === oi && oi !== scene.answer" class="vp-quiz-opt-icon vp-quiz-opt-icon-wrong">✗</span>
                </button>
              </div>
              <div v-if="quizAnswered" class="vp-quiz-feedback" :class="{ correct: quizCorrect, wrong: !quizCorrect }">
                <div class="vp-quiz-feedback-header">
                  <span v-if="quizCorrect">✅ 回答正确！</span>
                  <span v-else>❌ 回答错误</span>
                </div>
                <p class="vp-quiz-explanation">{{ scene.explanation }}</p>
              </div>
            </div>
            <!-- ===== SUMMARY ===== -->
            <div v-else-if="scene.type === 'summary'" class="vp-scene vp-summary">
              <h2 class="vp-scene-h2">小结</h2>
              <ul>
                <li v-for="(p, pi) in scene.key_points" :key="pi" :style="{ animationDelay: pi * 0.3 + 's' }">
                  <span class="vp-check">&#10003;</span>{{ p }}
                </li>
              </ul>
              <div v-if="quizTotal > 0" class="vp-quiz-summary">
                <h3>🧪 测验成绩</h3>
                <div class="vp-quiz-score">{{ quizScore }} / {{ quizTotal }}</div>
                <div class="vp-quiz-score-bar">
                  <div class="vp-quiz-score-fill" :style="{ width: quizPct + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </transition>
        <div v-if="interactiveMode && !finished && canStepNext && scene.type !== 'quiz_card'" class="vp-click-overlay" @click="stepNext">
          <span class="vp-click-hint">点击任意位置继续 ▶</span>
        </div>
      </div>
      <!-- Sidebar: Subtitle + Notes -->
      <div v-if="showSubtitle || showNotes" class="vp-sidebar">
        <div v-if="showSubtitle" class="vp-sidebar-panel">
          <div class="vp-sidebar-header">📝 字幕</div>
          <div class="vp-sidebar-content vp-subtitle-content">{{ scene.narration || '' }}</div>
        </div>
        <div v-if="showNotes" class="vp-sidebar-panel">
          <div class="vp-sidebar-header">✏️ 我的笔记</div>
          <textarea class="vp-notes-textarea" v-model="notesText" placeholder="在这里写下你的笔记..."></textarea>
        </div>
      </div>
    </div>
    <!-- Narration subtitle bar -->
    <div class="vp-subtitle-bar" v-if="scene.narration">
      <div class="vp-subtitle-text-inner">{{ scene.narration }}</div>
    </div>
    <!-- Scene Mini-Map -->
    <div class="vp-minimap">
      <span v-for="(s, si) in scenes" :key="si" class="vp-mm-dot"
        :class="{ active: si === sceneIndex, past: si < sceneIndex }"
        :title="getSceneLabel(s, si)"
        @click="jumpToScene(si)">
        <span class="vp-mm-icon">{{ getSceneIcon(s) }}</span>
      </span>
    </div>
    <!-- Finished -->
    <div v-if="finished" class="vp-finished">
      <span>🎉 播放完成</span>
      <span v-if="quizTotal > 0"> | 测验得分: {{ quizScore }}/{{ quizTotal }}</span>
      <button class="vp-btn vp-btn-restart" @click="restart">重新播放</button>
    </div>
  </div>
  <div v-else class="preview-empty"><p>暂无教学动画</p></div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount, onMounted, nextTick } from 'vue'
import mermaid from 'mermaid'

const props = defineProps({ script: { type: Object, default: null } })

// -- Core State --
const sceneIndex = ref(0)
const playing = ref(false)
const finished = ref(false)
const speed = ref(1)
const speeds = [0.5, 1, 1.5]
const transitionName = ref('vp-slide-next')
const interactiveMode = ref(true)
const showSubtitle = ref(true)
const showNotes = ref(false)

// -- Per-scene interaction state --
const lastRevealedBullet = ref(-1)
const highlightedLine = ref(-1)
const currentBuildStep = ref(1)
const compareReveal = ref(-1)
const quizSelected = ref(-1)
const quizAnswered = ref(false)
const quizCorrect = ref(false)
const quizScore = ref(0)
const quizTotal = ref(0)

const sceneKey = ref(0)

// Audio
let audioEl = null
let autoTimer = null
let buildTimer = null
let mermaidReady = false

// Notes
const notesText = ref('')
const notesKey = computed(() => 'vp-notes-' + (props.script?.title || 'untitled'))

// -- Computed --
const scenes = computed(() => props.script?.scenes || [])
const scene = computed(() => scenes.value[sceneIndex.value] || { type: 'title', text: '', narration: '' })
const codeLines = computed(() => (scene.value.code || '').split('\n'))
const visibleBullets = computed(() => scene.value.bullets || [])
const quizPct = computed(() => quizTotal.value > 0 ? Math.round(quizScore.value / quizTotal.value * 100) : 0)

const highlightedCode = computed(() => {
  if (scene.value.type !== 'code_walkthrough' || !scene.value.code) return ''
  const hl = highlightedLine.value
  return scene.value.code.split('\n').map((line, i) => {
    let cls = ''
    if (hl >= 0) {
      if (i === hl) cls = 'hl-line-current'
      else if (i < hl) cls = 'hl-line-past'
      else cls = 'hl-line-future'
    }
    return '<span class="' + cls + '">' + escapeHtml(line) + '</span>'
  }).join('\n')
})

const canStepPrev = computed(() => {
  if (sceneIndex.value > 0) return true
  const st = scene.value.type
  if (st === 'text_reveal' && lastRevealedBullet.value > 0) return true
  if (st === 'code_walkthrough' && highlightedLine.value > 0) return true
  if (st === 'diagram' && currentBuildStep.value > 1) return true
  if (st === 'compare' && compareReveal.value === 1) return true
  return false
})

const canStepNext = computed(() => {
  if (finished.value) return false
  if (sceneIndex.value < scenes.value.length - 1) return true
  const st = scene.value.type
  if (st === 'text_reveal') return !interactiveMode.value || lastRevealedBullet.value < (scene.value.bullets?.length || 0) - 1
  if (st === 'code_walkthrough') return !interactiveMode.value || highlightedLine.value < codeLines.value.length - 1
  if (st === 'diagram') return !interactiveMode.value || (scene.value.build_steps > 1 && currentBuildStep.value < scene.value.build_steps)
  if (st === 'compare') return !interactiveMode.value || compareReveal.value < 1
  if (st === 'quiz_card') return quizAnswered.value
  return false
})

const renderedMermaid = ref('')

// -- Scene watcher --
watch(scene, async (s) => {
  renderedMermaid.value = ''
  stopAudio()
  lastRevealedBullet.value = -1
  highlightedLine.value = -1
  currentBuildStep.value = 1
  compareReveal.value = -1
  quizSelected.value = -1
  quizAnswered.value = false
  quizCorrect.value = false
  sceneKey.value++

  if (s.type === 'diagram' && s.mermaid) {
    if (!mermaidReady) { mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' }); mermaidReady = true }
    try {
      const { svg } = await mermaid.render('vp-diagram-' + Date.now(), s.mermaid)
      renderedMermaid.value = svg
    } catch { renderedMermaid.value = '' }
  }
  if (!interactiveMode.value && playing.value) {
    await autoAdvanceScene()
  }
}, { immediate: true })

// -- Auto mode: advance scene + internal steps --
async function autoAdvanceScene() {
  const s = scene.value
  if (s.type === 'text_reveal') {
    const bullets = s.bullets || []
    for (let i = 0; i < bullets.length; i++) {
      lastRevealedBullet.value = i
      await new Promise(r => setTimeout(r, 800 / speed.value))
    }
    await new Promise(r => setTimeout(r, 1200 / speed.value))
  } else if (s.type === 'code_walkthrough') {
    for (let i = 0; i < codeLines.value.length; i++) {
      highlightedLine.value = i
      await new Promise(r => setTimeout(r, 700 / speed.value))
    }
    await new Promise(r => setTimeout(r, 1000 / speed.value))
  } else if (s.type === 'diagram' && s.build_steps > 1) {
    for (let i = 1; i <= s.build_steps; i++) {
      currentBuildStep.value = i
      await new Promise(r => setTimeout(r, 1000 / speed.value))
    }
    await new Promise(r => setTimeout(r, 800 / speed.value))
  } else if (s.type === 'compare') {
    compareReveal.value = 0
    await new Promise(r => setTimeout(r, 800 / speed.value))
    compareReveal.value = 1
    await new Promise(r => setTimeout(r, 1200 / speed.value))
  } else {
    await playAudio()
    const dur = (s.narration?.length || 100) * 75 / speed.value
    await new Promise(r => setTimeout(r, dur + 600))
  }
  nextScene()
}

// -- Step next (interactive) --
async function stepNext() {
  if (finished.value) return
  const s = scene.value
  if (interactiveMode.value) {
    if (s.type === 'text_reveal') {
      const bullets = s.bullets || []
      if (lastRevealedBullet.value < bullets.length - 1) { lastRevealedBullet.value++; return }
    }
    if (s.type === 'code_walkthrough') {
      if (highlightedLine.value < codeLines.value.length - 1) { highlightedLine.value++; return }
    }
    if (s.type === 'diagram' && s.build_steps > 1) {
      if (currentBuildStep.value < s.build_steps) { currentBuildStep.value++; return }
    }
    if (s.type === 'compare') {
      if (compareReveal.value < 0) { compareReveal.value = 0; return }
      if (compareReveal.value === 0) { compareReveal.value = 1; return }
    }
    if (s.type === 'quiz_card' && !quizAnswered.value) return
  }
  transitionName.value = 'vp-slide-next'
  if (sceneIndex.value < scenes.value.length - 1) {
    stopAudio()
    sceneIndex.value++
    await nextTick()
    if (!interactiveMode.value && playing.value) {
      await new Promise(r => setTimeout(r, 600))
      await autoAdvanceScene()
    }
  } else { finishPlayback() }
}

function stepPrev() {
  stopAudio()
  const s = scene.value
  if (interactiveMode.value) {
    if (s.type === 'text_reveal' && lastRevealedBullet.value > 0) { lastRevealedBullet.value--; return }
    if (s.type === 'code_walkthrough' && highlightedLine.value > 0) { highlightedLine.value--; return }
    if (s.type === 'diagram' && currentBuildStep.value > 1) { currentBuildStep.value--; return }
    if (s.type === 'compare' && compareReveal.value >= 0) { compareReveal.value = compareReveal.value > 0 ? compareReveal.value - 1 : -1; return }
  }
  if (sceneIndex.value > 0) {
    transitionName.value = 'vp-slide-prev'
    sceneIndex.value--
  }
}

// -- Quiz --
function selectQuizOption(oi) {
  if (quizAnswered.value) return
  quizSelected.value = oi
  quizAnswered.value = true
  const correct = oi === scene.value.answer
  quizCorrect.value = correct
  quizTotal.value++
  if (correct) quizScore.value++
}

// -- Scene helpers --
function getSceneIcon(s) {
  const icons = { title: '🎬', text_reveal: '📖', code_walkthrough: '💻', diagram: '📊', compare: '⚖️', quiz_card: '❓', summary: '📝' }
  return icons[s.type] || '●'
}
function getSceneLabel(s, i) {
  const labels = { title: '标题', text_reveal: '要点', code_walkthrough: '代码', diagram: '图表', compare: '对比', quiz_card: '测验', summary: '总结' }
  return (i + 1) + '. ' + (labels[s.type] || s.type)
}
function jumpToScene(idx) {
  stopAudio()
  transitionName.value = idx > sceneIndex.value ? 'vp-slide-next' : 'vp-slide-prev'
  sceneIndex.value = Math.max(0, Math.min(idx, scenes.value.length - 1))
  finished.value = false
}

// -- Audio --
function playAudio() {
  stopAudio()
  const s = scene.value
  if (!s.narration || s.narration.length < 5) return Promise.resolve()
  const key = 'scene_' + sceneIndex.value
  const b64 = props.script?.audio?.[key]
  if (b64) {
    return new Promise((resolve) => {
      const blob = base64ToBlob(b64, 'audio/mp3')
      const url = URL.createObjectURL(blob)
      audioEl = new Audio(url)
      audioEl.playbackRate = speed.value
      audioEl.onended = () => { URL.revokeObjectURL(url); resolve() }
      audioEl.onerror = () => { URL.revokeObjectURL(url); resolve() }
      audioEl.play().catch(() => resolve())
    })
  }
  return new Promise((resolve) => {
    const u = new SpeechSynthesisUtterance(s.narration)
    u.lang = 'zh-CN'; u.rate = speed.value
    u.onend = () => resolve(); u.onerror = () => resolve()
    window.speechSynthesis.speak(u)
  })
}
function base64ToBlob(b64, mime) {
  const chars = atob(b64); const nums = new Uint8Array(chars.length)
  for (let i = 0; i < chars.length; i++) nums[i] = chars.charCodeAt(i)
  return new Blob([nums], { type: mime })
}
function stopAudio() {
  if (audioEl) { audioEl.pause(); audioEl = null }
  window.speechSynthesis.cancel()
  clearTimeout(autoTimer); clearInterval(buildTimer)
}

// -- Core playback --
async function nextScene() {
  stopAudio()
  if (sceneIndex.value < scenes.value.length - 1) {
    transitionName.value = 'vp-slide-next'
    sceneIndex.value++
    if (playing.value && !interactiveMode.value) {
      await new Promise(r => setTimeout(r, 600))
      await autoAdvanceScene()
    }
  } else { finishPlayback() }
}
function finishPlayback() {
  finished.value = true
  playing.value = false
  lastRevealedBullet.value = 999
  highlightedLine.value = 999
  currentBuildStep.value = 999
  compareReveal.value = 1
}
async function togglePlay() {
  if (finished.value) { restart(); return }
  playing.value = !playing.value
  if (playing.value) {
    if (!interactiveMode.value) {
      await playAudio()
      const dur = (scene.value.narration?.length || 100) * 75 / speed.value
      autoTimer = setTimeout(nextScene, dur + 800)
    }
  } else { stopAudio() }
}
function restart() {
  stopAudio()
  transitionName.value = 'vp-slide-next'
  sceneIndex.value = 0; playing.value = false; finished.value = false
  interactiveMode.value = true
  quizScore.value = 0; quizTotal.value = 0
}

// -- Escape HTML --
function escapeHtml(t) {
  return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// -- Notes persistence --
watch(notesText, (v) => { try { localStorage.setItem(notesKey.value, v) } catch {} })
watch(() => props.script?.title, () => {
  try { notesText.value = localStorage.getItem(notesKey.value) || '' } catch { notesText.value = '' }
}, { immediate: true })

// -- Keyboard shortcuts --
function onKeydown(e) {
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return
  if (e.code === 'Space' || e.code === 'ArrowRight') { e.preventDefault(); stepNext() }
  else if (e.code === 'ArrowLeft') { e.preventDefault(); stepPrev() }
  else if (e.code === 'KeyN') { showNotes.value = !showNotes.value }
  else if (e.code === 'KeyT') { showSubtitle.value = !showSubtitle.value }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => { window.removeEventListener('keydown', onKeydown); stopAudio() })
watch(speed, () => { if (audioEl) audioEl.playbackRate = speed.value })
</script>

<style scoped>
.vp-container { display: flex; flex-direction: column; height: 100%; overflow: hidden; }

/* == Top Controls == */
.vp-controls { display: flex; align-items: center; gap: 6px; padding: 6px 0 8px; flex-shrink: 0; flex-wrap: wrap; }
.vp-mode-toggle { display: flex; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); margin-right: 4px; }
.vp-mode-toggle button { padding: 3px 10px; font-size: 0.7rem; background: transparent; color: var(--text-secondary); border: none; cursor: pointer; transition: all 0.2s; }
.vp-mode-toggle button.active { background: var(--primary-bg); color: var(--primary-light); }
.vp-btn { width: 28px; height: 28px; border-radius: 7px; background: rgba(255,255,255,0.05); color: var(--text-primary); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; transition: all 0.2s; font-size: 0.7rem; }
.vp-btn:hover { background: var(--primary-bg); border-color: rgba(91,127,255,0.3); }
.vp-btn-toggle { font-size: 0.8rem; }
.vp-btn-toggle.active { background: rgba(91,127,255,0.15); border-color: rgba(91,127,255,0.4); }
.vp-btn-nav { font-size: 0.75rem; }
.vp-btn-next { background: rgba(91,127,255,0.15); border-color: rgba(91,127,255,0.3); }
.vp-btn-next:hover { background: rgba(91,127,255,0.25); }
.vp-btn-restart { width: auto; padding: 0 14px; }
.vp-spacer { flex: 1; }
.vp-speed { display: flex; gap: 3px; }
.vp-speed-btn { padding: 2px 7px; border-radius: 5px; font-size: 0.65rem; background: transparent; color: var(--text-secondary); border: 1px solid transparent; cursor: pointer; }
.vp-speed-btn.active { background: var(--primary-bg); color: var(--primary-light); border-color: rgba(91,127,255,0.2); }

/* == Main Layout == */
.vp-main { flex: 1; display: flex; overflow: hidden; min-height: 0; }
.vp-stage-wrapper { flex: 1; overflow: hidden; position: relative; }
.vp-stage-wrapper.with-sidebar { flex: 1; }
.vp-stage { height: 100%; overflow-y: auto; padding: 12px 8px; position: relative; }

/* == Sidebar == */
.vp-sidebar { width: 200px; border-left: 1px solid var(--border); display: flex; flex-direction: column; flex-shrink: 0; overflow: hidden; }
.vp-sidebar-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; border-bottom: 1px solid rgba(255,255,255,0.04); }
.vp-sidebar-panel:last-child { border-bottom: none; }
.vp-sidebar-header { padding: 8px 10px; font-size: 0.72rem; font-weight: 600; color: var(--primary-light); background: rgba(91,127,255,0.05); border-bottom: 1px solid var(--border); flex-shrink: 0; }
.vp-sidebar-content { padding: 10px; font-size: 0.78rem; color: var(--text-secondary); line-height: 1.7; overflow-y: auto; flex: 1; }
.vp-notes-textarea { flex: 1; width: 100%; padding: 10px; font-size: 0.78rem; background: transparent; color: var(--text-primary); border: none; resize: none; outline: none; font-family: inherit; line-height: 1.7; }
.vp-notes-textarea::placeholder { color: var(--text-disabled); }

/* == Transitions == */
.vp-slide-next-enter-active, .vp-slide-next-leave-active { transition: all 0.35s ease; }
.vp-slide-next-enter-from { opacity: 0; transform: translateX(40px); }
.vp-slide-next-leave-to { opacity: 0; transform: translateX(-40px); }
.vp-slide-prev-enter-active, .vp-slide-prev-leave-active { transition: all 0.35s ease; }
.vp-slide-prev-enter-from { opacity: 0; transform: translateX(-40px); }
.vp-slide-prev-leave-to { opacity: 0; transform: translateX(40px); }

/* == Particles == */
.vp-particles { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.vp-particle { position: absolute; top: -10px; width: 3px; height: 3px; background: var(--primary-light); border-radius: 50%; opacity: 0; animation: vpParticleFall linear infinite; }
@keyframes vpParticleFall { 0% { opacity: 0; transform: translateY(0); } 10% { opacity: 0.8; } 90% { opacity: 0.3; } 100% { opacity: 0; transform: translateY(400px); } }

/* == Tap hint == */
.vp-tap-hint { text-align: center; padding: 12px 0 4px; }
.vp-tap-hint-pulse { font-size: 0.75rem; color: var(--primary-light); opacity: 0.7; animation: vpPulseHint 1.8s ease infinite; }
@keyframes vpPulseHint { 0%,100% { opacity: 0.4; } 50% { opacity: 0.9; } }

/* == Click overlay == */
.vp-click-overlay { position: absolute; inset: 0; z-index: 5; cursor: pointer; display: flex; align-items: flex-end; justify-content: center; padding-bottom: 16px; }
.vp-click-hint { background: rgba(91,127,255,0.9); color: #fff; padding: 6px 16px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; pointer-events: none; animation: vpPulseHint 1.8s ease infinite; }

/* == Title == */
.vp-title { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; padding: 20px; position: relative; z-index: 1; }
.vp-title-text { font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #5b7fff, #a78bfa, #f97316); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; animation: vpTitleIn 0.8s ease; }
@keyframes vpTitleIn { from { opacity: 0; transform: scale(0.8); filter: blur(8px); } to { opacity: 1; transform: scale(1); filter: blur(0); } }
.vp-subtitle-text { font-size: 1.1rem; color: var(--text-secondary); margin-top: 16px; animation: vpFadeUp 0.8s 0.3s ease both; }
@keyframes vpFadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

/* == Scene headings == */
.vp-scene-h2 { font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 14px; padding-bottom: 10px; border-bottom: 2px solid rgba(91,127,255,0.2); display: flex; align-items: center; gap: 8px; }
.vp-scene-h2::before { content: ''; width: 4px; height: 20px; background: linear-gradient(135deg, #5b7fff, #a78bfa); border-radius: 2px; }

/* == Text Reveal == */
.vp-text-reveal ul { list-style: none; padding: 0; margin: 0; }
.vp-bullet-li { display: flex; align-items: flex-start; gap: 10px; padding: 6px 0; opacity: 0; transform: translateX(-24px); transition: all 0.4s ease; }
.vp-bullet-li.reveal { opacity: 1; transform: translateX(0); }
.vp-bullet-num { width: 22px; height: 22px; border-radius: 50%; background: var(--primary-bg); color: var(--primary-light); font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.vp-bullet-li.reveal .vp-bullet-num { animation: vpPulse 2s ease infinite; }
@keyframes vpPulse { 0%,100% { box-shadow: 0 0 0 0 rgba(91,127,255,0.3); } 50% { box-shadow: 0 0 0 6px rgba(91,127,255,0); } }
.vp-bullet-text { font-size: 0.88rem; color: var(--text-primary); line-height: 1.6; padding-top: 1px; }

/* == Code Walkthrough == */
.vp-code-block { display: flex; background: rgba(5,8,20,0.7); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; animation: vpFadeUp 0.5s ease; }
.vp-line-numbers { display: flex; flex-direction: column; padding: 12px 8px; background: rgba(0,0,0,0.3); border-right: 1px solid var(--border); font-size: 0.75rem; color: var(--text-disabled); font-family: monospace; text-align: right; min-width: 36px; user-select: none; }
.vp-line-numbers span { line-height: 1.7; padding-right: 4px; transition: all 0.3s; }
.vp-line-numbers span.hl-current { color: #facc15; font-weight: 700; background: rgba(250,204,21,0.1); }
.vp-line-numbers span.hl-past { color: #4ade80; }
.vp-line-numbers span.hl-future { color: var(--text-disabled); }
.vp-code-block pre { flex: 1; padding: 12px 16px; margin: 0; overflow-x: auto; font-size: 0.8rem; line-height: 1.7; }
.vp-code-block code .hl-line-current { background: rgba(250,204,21,0.12); display: block; padding: 0 4px; margin: 0 -4px; border-left: 3px solid #facc15; animation: vpHlPulse 1.5s ease infinite; }
.vp-code-block code .hl-line-past { background: rgba(74,222,128,0.06); display: block; padding: 0 4px; margin: 0 -4px; }
.vp-code-block code .hl-line-future { display: block; padding: 0 4px; margin: 0 -4px; opacity: 0.5; }
@keyframes vpHlPulse { 0%,100% { background: rgba(250,204,21,0.12); } 50% { background: rgba(250,204,21,0.25); } }

/* == Diagram == */
.vp-mermaid-wrap { display: flex; justify-content: center; padding: 8px; animation: vpScaleIn 0.5s ease; }
@keyframes vpScaleIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
.vp-diagram :deep(svg) { max-width: 100%; max-height: 300px; }
.vp-build-steps { display: flex; justify-content: center; gap: 8px; margin-top: 10px; }
.vp-step-dot { width: 10px; height: 10px; border-radius: 50%; background: rgba(255,255,255,0.08); transition: all 0.4s; }
.vp-step-dot.active { background: var(--primary-light); box-shadow: 0 0 8px var(--primary); }

/* == Compare == */
.vp-compare { display: flex; gap: 12px; align-items: flex-start; }
.vp-compare-col { flex: 1; background: rgba(255,255,255,0.015); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.vp-compare-col h3 { font-size: 0.9rem; color: var(--primary-light); margin-bottom: 10px; }
.vp-compare-col li { font-size: 0.82rem; padding: 5px 0; color: var(--text-primary); opacity: 0; }
.vp-compare-col.reveal li { animation: vpFadeUp 0.4s ease forwards; }
.vp-compare-left.reveal { animation: vpSlideLeftAnim 0.5s ease; }
@keyframes vpSlideLeftAnim { from { opacity: 0; transform: translateX(-24px); } to { opacity: 1; transform: translateX(0); } }
.vp-compare-right.reveal { animation: vpSlideRightAnim 0.5s ease; }
@keyframes vpSlideRightAnim { from { opacity: 0; transform: translateX(24px); } to { opacity: 1; transform: translateX(0); } }
.vp-compare-vs { font-weight: 800; font-size: 1rem; color: var(--text-disabled); padding-top: 36px; opacity: 0; transition: all 0.3s; }
.vp-compare-vs.reveal { opacity: 1; animation: vpPulse 2s ease infinite; }

/* == Quiz Card == */
.vp-quiz { padding: 8px 0; animation: vpFadeUp 0.5s ease; }
.vp-quiz-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; background: rgba(250,204,21,0.12); color: #facc15; font-size: 0.7rem; font-weight: 600; margin-bottom: 10px; }
.vp-quiz-question { font-size: 1rem; color: var(--text-primary); margin-bottom: 16px; line-height: 1.6; }
.vp-quiz-options { display: flex; flex-direction: column; gap: 8px; }
.vp-quiz-opt { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 10px; cursor: pointer; transition: all 0.25s; text-align: left; font-size: 0.85rem; color: var(--text-primary); }
.vp-quiz-opt:hover:not(.disabled) { background: rgba(91,127,255,0.08); border-color: rgba(91,127,255,0.3); transform: translateX(4px); }
.vp-quiz-opt.selected { border-color: var(--primary); background: rgba(91,127,255,0.1); }
.vp-quiz-opt.correct { border-color: #22c55e; background: rgba(34,197,94,0.08); }
.vp-quiz-opt.wrong { border-color: #ef4444; background: rgba(239,68,68,0.08); }
.vp-quiz-opt.disabled { cursor: default; }
.vp-quiz-opt-letter { width: 26px; height: 26px; border-radius: 50%; background: rgba(255,255,255,0.06); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.75rem; flex-shrink: 0; }
.vp-quiz-opt.correct .vp-quiz-opt-letter { background: rgba(34,197,94,0.2); color: #22c55e; }
.vp-quiz-opt.wrong .vp-quiz-opt-letter { background: rgba(239,68,68,0.2); color: #ef4444; }
.vp-quiz-opt-icon { margin-left: auto; font-weight: 700; color: #22c55e; }
.vp-quiz-opt-icon-wrong { color: #ef4444; }
.vp-quiz-feedback { margin-top: 12px; padding: 12px 14px; border-radius: 10px; border: 1px solid; }
.vp-quiz-feedback.correct { border-color: rgba(34,197,94,0.3); background: rgba(34,197,94,0.06); }
.vp-quiz-feedback.wrong { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.06); }
.vp-quiz-feedback-header { font-weight: 700; font-size: 0.9rem; margin-bottom: 6px; }
.vp-quiz-feedback.correct .vp-quiz-feedback-header { color: #22c55e; }
.vp-quiz-feedback.wrong .vp-quiz-feedback-header { color: #ef4444; }
.vp-quiz-explanation { font-size: 0.82rem; color: var(--text-secondary); line-height: 1.6; }
.vp-quiz-summary { margin-top: 20px; padding: 14px; background: rgba(250,204,21,0.05); border: 1px solid rgba(250,204,21,0.15); border-radius: 12px; }
.vp-quiz-summary h3 { font-size: 0.85rem; color: #facc15; margin-bottom: 8px; }
.vp-quiz-score { font-size: 1.6rem; font-weight: 800; color: var(--text-primary); }
.vp-quiz-score-bar { height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; margin-top: 8px; overflow: hidden; }
.vp-quiz-score-fill { height: 100%; background: linear-gradient(90deg, #facc15, #f97316); border-radius: 3px; transition: width 0.6s ease; }

/* == Summary == */
.vp-summary li { display: flex; align-items: center; gap: 10px; padding: 7px 0; font-size: 0.88rem; color: var(--text-primary); opacity: 0; animation: vpSlideLeftAnim 0.4s ease forwards; }
.vp-check { color: #22c55e; font-weight: 700; }

/* == Subtitle bar == */
.vp-subtitle-bar { padding: 6px 14px; background: rgba(249,115,22,0.05); border-left: 3px solid #f97316; border-radius: 0 8px 8px 0; font-size: 0.78rem; color: var(--text-secondary); line-height: 1.5; margin-top: 4px; flex-shrink: 0; overflow: hidden; }
.vp-subtitle-text-inner { line-height: 1.6; max-height: 3.2em; overflow-y: auto; }

/* == Minimap == */
.vp-minimap { display: flex; align-items: center; justify-content: center; gap: 6px; padding: 6px 8px; flex-shrink: 0; border-top: 1px solid rgba(255,255,255,0.04); overflow-x: auto; }
.vp-mm-dot { width: 26px; height: 26px; border-radius: 50%; background: rgba(255,255,255,0.04); border: 1px solid transparent; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s; flex-shrink: 0; }
.vp-mm-dot.active { background: var(--primary-bg); border-color: var(--primary); transform: scale(1.15); box-shadow: 0 0 10px rgba(91,127,255,0.3); }
.vp-mm-dot.past { background: rgba(91,127,255,0.1); border-color: rgba(91,127,255,0.2); }
.vp-mm-dot:hover { border-color: rgba(91,127,255,0.4); }
.vp-mm-icon { font-size: 0.65rem; }

/* == Finished == */
.vp-finished { display: flex; align-items: center; gap: 12px; padding: 8px; justify-content: center; color: var(--success); font-weight: 600; font-size: 0.85rem; flex-shrink: 0; }

.preview-empty { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-disabled); font-size: 0.9rem; }
</style>

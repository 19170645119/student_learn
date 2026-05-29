<template>
  <div class="code-viewer">
    <div v-if="!codeData" class="preview-empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3">
        <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
      </svg>
      <p>在对话中说「用Python写快速排序」来生成代码实操案例</p>
    </div>

    <div v-else class="code-content">
      <div class="cd-header">
        <span class="cd-lang">{{ langLabel }}</span>
        <span class="cd-title">{{ codeData.title || '代码案例' }}</span>
        <span class="cd-difficulty" :class="'diff-' + (codeData.difficulty || 'medium')">{{ diffLabel }}</span>
      </div>

      <div class="cd-section" :class="{ open: sections.problem }">
        <div class="cd-section-hdr" @click="sections.problem = !sections.problem">
          <span class="cd-arrow">{{ sections.problem ? '▼' : '▶' }}</span>
          <span>题目描述</span>
        </div>
        <div v-if="sections.problem" class="cd-section-body">
          <p class="cd-problem-stmt">{{ codeData.problem?.statement || '' }}</p>
          <div v-if="codeData.problem?.input_spec" class="cd-meta-row"><span class="cd-meta-label">输入</span><code>{{ codeData.problem.input_spec }}</code></div>
          <div v-if="codeData.problem?.output_spec" class="cd-meta-row"><span class="cd-meta-label">输出</span><code>{{ codeData.problem.output_spec }}</code></div>
          <div v-if="codeData.problem?.constraints?.length" class="cd-constraints"><span class="cd-meta-label">约束</span><ul><li v-for="c in codeData.problem.constraints" :key="c">{{ c }}</li></ul></div>
        </div>
      </div>

      <div class="cd-section" :class="{ open: sections.approach }">
        <div class="cd-section-hdr" @click="sections.approach = !sections.approach">
          <span class="cd-arrow">{{ sections.approach ? '▼' : '▶' }}</span>
          <span>解题思路</span>
        </div>
        <div v-if="sections.approach" class="cd-section-body">
          <p v-if="codeData.approach?.thinking" class="cd-thinking">{{ codeData.approach.thinking }}</p>
          <ol v-if="codeData.approach?.steps?.length" class="cd-steps"><li v-for="(s, i) in codeData.approach.steps" :key="i">{{ s }}</li></ol>
          <div v-if="codeData.approach?.tip" class="cd-tip">{{ codeData.approach.tip }}</div>
        </div>
      </div>

      <div class="cd-section open">
        <div class="cd-section-hdr" @click="sections.starter = !sections.starter">
          <span class="cd-arrow">{{ sections.starter ? '▼' : '▶' }}</span>
          <span>动手试试</span>
          <span class="cd-badge">脚手架代码</span>
          <button class="cd-copy-sm" @click.stop="copyCode(codeData.starter_code || '')">{{ starterCopied ? '✔' : '复制' }}</button>
        </div>
        <div v-if="sections.starter" class="cd-section-body">
          <p class="cd-hint">下面的代码不完整，关键部分需要你来填充。先试试自己写。</p>
          <CodeEditor v-model="studentCode" :language="codeData?.language || 'python'" />
          <div class="cd-review-bar">
            <button class="cd-review-btn" @click="submitReview" :disabled="reviewing || !studentCode.trim()">
              {{ reviewing ? '审查中...' : 'AI 审查代码' }}
            </button>
          </div>
          <div v-if="reviewResult" class="cd-review-panel" :class="{ correct: reviewResult.correct }">
            <div class="cd-review-header">
              <span class="cd-review-score">{{ reviewResult.score }} 分</span>
              <span :class="reviewResult.correct ? 'cd-review-pass' : 'cd-review-fail'">
                {{ reviewResult.correct ? '✅ 通过' : '❌ 需要改进' }}
              </span>
            </div>
            <p class="cd-review-feedback">{{ reviewResult.feedback }}</p>
            <div v-if="reviewResult.highlights?.length" class="cd-review-highlights">
              <div class="cd-review-subtitle">做得好的地方</div>
              <ul><li v-for="(h, i) in reviewResult.highlights" :key="i">{{ h }}</li></ul>
            </div>
            <div v-if="reviewResult.issues?.length" class="cd-review-issues">
              <div class="cd-review-subtitle">需要改进</div>
              <div v-for="(iss, i) in reviewResult.issues" :key="i" class="cd-issue-item" :class="'sev-' + iss.severity">
                <div class="cd-issue-line">{{ iss.line || '?' }}</div>
                <div class="cd-issue-body">
                  <div class="cd-issue-msg">{{ iss.message }}</div>
                  <div v-if="iss.fix" class="cd-issue-fix">{{ iss.fix }}</div>
                </div>
              </div>
            </div>
            <div v-if="reviewResult.comparison" class="cd-review-compare">
              <div class="cd-review-subtitle">对比分析</div>
              <p>{{ reviewResult.comparison }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="cd-section" :class="{ open: sections.examples }">
        <div class="cd-section-hdr" @click="sections.examples = !sections.examples">
          <span class="cd-arrow">{{ sections.examples ? '▼' : '▶' }}</span>
          <span>测试用例</span>
        </div>
        <div v-if="sections.examples" class="cd-section-body">
          <div v-if="!codeData.examples?.length" class="cd-empty">暂无测试用例</div>
          <div v-for="(ex, i) in codeData.examples" :key="i" class="cd-test-case">
            <div class="cd-tc-num">Case {{ i + 1 }}</div>
            <div class="cd-io-row"><span class="cd-io-label">输入:</span><code>{{ ex.input }}</code></div>
            <div class="cd-io-row"><span class="cd-io-label">输出:</span><code>{{ ex.output }}</code></div>
            <div v-if="ex.explanation" class="cd-io-explain">{{ ex.explanation }}</div>
          </div>
        </div>
      </div>

      <div class="cd-section">
        <div class="cd-section-hdr" @click="sections.solution = !sections.solution">
          <span class="cd-arrow">{{ sections.solution ? '▼' : '▶' }}</span>
          <span>参考答案</span>
          <span class="cd-badge answer-badge">先自己写再看</span>
          <button v-if="sections.solution" class="cd-copy-sm" @click.stop="copyCode(codeData.solution?.code || '')">{{ solCopied ? '✔' : '复制' }}</button>
        </div>
        <div v-if="sections.solution" class="cd-section-body">
          <pre class="cd-code-block solution"><code v-html="highlightedSolution"></code></pre>
          <div v-if="codeData.solution?.line_explanation && Object.keys(codeData.solution.line_explanation).length" class="cd-line-notes">
            <div class="cd-ln-title">逐行解释</div>
            <div v-for="(note, range) in codeData.solution.line_explanation" :key="range" class="cd-ln-item"><span class="cd-ln-range">{{ range }}</span><span>{{ note }}</span></div>
          </div>
          <div v-if="codeData.solution?.time_complexity || codeData.solution?.space_complexity" class="cd-complexity">
            <span v-if="codeData.solution.time_complexity">时间: {{ codeData.solution.time_complexity }}</span>
            <span v-if="codeData.solution.space_complexity" style="margin-left:16px">空间: {{ codeData.solution.space_complexity }}</span>
          </div>
        </div>
      </div>

      <div class="cd-section" v-if="codeData.common_mistakes?.length">
        <div class="cd-section-hdr" @click="sections.mistakes = !sections.mistakes">
          <span class="cd-arrow">{{ sections.mistakes ? '▼' : '▶' }}</span>
          <span>常见错误</span>
        </div>
        <div v-if="sections.mistakes" class="cd-section-body">
          <div v-for="(m, i) in codeData.common_mistakes" :key="i" class="cd-mistake">
            <div class="cd-mistake-title">{{ m.mistake }}</div>
            <div class="cd-mistake-fix">{{ m.fix }}</div>
            <div v-if="m.example" class="cd-mistake-example">示例: <code>{{ m.example }}</code></div>
          </div>
        </div>
      </div>

      <div class="cd-section" v-if="codeData.practice?.length">
        <div class="cd-section-hdr" @click="sections.practice = !sections.practice">
          <span class="cd-arrow">{{ sections.practice ? '▼' : '▶' }}</span>
          <span>举一反三</span>
        </div>
        <div v-if="sections.practice" class="cd-section-body">
          <div v-for="(p, i) in codeData.practice" :key="i" class="cd-practice-item">
            <div class="cd-prac-num">{{ i + 1 }}</div>
            <div class="cd-prac-content">
              <div class="cd-prac-title">{{ p.title }}</div>
              <div class="cd-prac-desc">{{ p.description }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, reactive } from 'vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import CodeEditor from './CodeEditor.vue'
import { reviewCode } from '../http/http.js'

const props = defineProps({
  content: { type: String, default: '' },
  resourceId: { type: Number, default: 0 }
})

const codeData = ref(null)
const starterCopied = ref(false)
const solCopied = ref(false)
const studentCode = ref('')
const reviewing = ref(false)
const reviewResult = ref(null)

const sections = reactive({ problem: true, approach: true, starter: true, examples: true, solution: false, mistakes: false, practice: false })

const langLabel = computed(() => {
  const m = { python: 'Python', java: 'Java', cpp: 'C++', javascript: 'JavaScript', go: 'Go' }
  return m[codeData.value?.language] || (codeData.value?.language || 'code').toUpperCase()
})
const diffLabel = computed(() => {
  const m = { easy: '??', medium: '??', hard: '??' }
  return m[codeData.value?.difficulty] || '??'
})
const highlightedSolution = computed(() => {
  const code = codeData.value?.solution?.code || ''
  return code ? hljs.highlight(code, { language: codeData.value?.language || 'python' }).value : ''
})

async function copyCode(code) {
  if (!code) return
  try { await navigator.clipboard.writeText(code); starterCopied.value = true; solCopied.value = true; setTimeout(() => { starterCopied.value = false; solCopied.value = false }, 2000) }
  catch { const ta = document.createElement('textarea'); ta.value = code; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); starterCopied.value = true; solCopied.value = true; setTimeout(() => { starterCopied.value = false; solCopied.value = false }, 2000) }
}

async function submitReview() {
  if (!studentCode.value.trim()) return
  reviewing.value = true; reviewResult.value = null
  try {
    const rid = codeData.value?._resourceId || props.resourceId
    if (!rid) {
      reviewResult.value = { correct: true, score: 85, feedback: '????????????????????', issues: [], highlights: [], comparison: '' }
    } else {
      const result = await reviewCode(rid, studentCode.value, codeData.value?.language)
      reviewResult.value = result.review
    }
  } catch (e) {
    reviewResult.value = { correct: false, score: 0, feedback: '????: ' + e.message, issues: [], highlights: [], comparison: '' }
  }
  reviewing.value = false
}

function parseContent() {
  if (!props.content) { codeData.value = null; return }
  try {
    codeData.value = typeof props.content === 'string' ? JSON.parse(props.content) : props.content
    if (codeData.value) codeData.value._resourceId = props.resourceId
    if (codeData.value?.starter_code) studentCode.value = codeData.value.starter_code
  } catch { codeData.value = null }
}

watch(() => props.content, parseContent)
onMounted(parseContent)
</script>


<style scoped>
.code-viewer { height: 100%; overflow-y: auto; }
.code-content { display: flex; flex-direction: column; gap: 6px; padding: 4px 0; }
.cd-header { display: flex; align-items: center; gap: 10px; padding: 8px 14px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 4px; }
.cd-lang { font-size: 0.78rem; font-weight: 600; color: var(--primary-light); }
.cd-title { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); flex: 1; }
.cd-difficulty { font-size: 0.72rem; padding: 2px 10px; border-radius: 10px; font-weight: 500; }
.diff-easy { background: rgba(34,197,94,0.12); color: var(--success); }
.diff-medium { background: rgba(249,115,22,0.12); color: #f97316; }
.diff-hard { background: rgba(239,68,68,0.12); color: var(--danger); }
.cd-section { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; transition: border-color 0.2s; }
.cd-section.open { border-color: rgba(91,127,255,0.2); }
.cd-section-hdr { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: rgba(255,255,255,0.02); cursor: pointer; user-select: none; font-size: 0.84rem; color: var(--text-primary); transition: background 0.15s; }
.cd-section-hdr:hover { background: rgba(255,255,255,0.04); }
.cd-arrow { font-size: 0.65rem; width: 14px; color: var(--text-secondary); }
.cd-badge { font-size: 0.62rem; padding: 1px 8px; border-radius: 4px; background: rgba(91,127,255,0.12); color: var(--primary-light); margin-left: auto; margin-right: 6px; }
.answer-badge { background: rgba(34,197,94,0.1); color: var(--success); }
.cd-copy-sm { font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; border: 1px solid var(--border); background: transparent; color: var(--text-secondary); cursor: pointer; }
.cd-copy-sm:hover { border-color: var(--primary); color: var(--primary-light); }
.cd-section-body { padding: 10px 14px; font-size: 0.82rem; line-height: 1.7; color: var(--text-primary); }
.cd-problem-stmt { margin: 0 0 8px; white-space: pre-wrap; }
.cd-meta-row { display: flex; gap: 8px; margin-bottom: 4px; align-items: baseline; }
.cd-meta-label { font-size: 0.72rem; color: var(--text-secondary); min-width: 32px; }
.cd-meta-row code { font-size: 0.8rem; color: var(--primary-light); background: rgba(91,127,255,0.06); padding: 1px 8px; border-radius: 4px; }
.cd-constraints { margin-top: 6px; } .cd-constraints ul { margin: 4px 0 0 16px; font-size: 0.78rem; color: var(--text-secondary); } .cd-constraints li { margin-bottom: 2px; }
.cd-thinking { white-space: pre-wrap; margin: 0 0 8px; }
.cd-steps { margin: 0; padding-left: 20px; font-size: 0.8rem; } .cd-steps li { margin-bottom: 4px; }
.cd-tip { margin-top: 8px; padding: 8px 10px; border-radius: 6px; background: rgba(91,127,255,0.06); font-size: 0.78rem; color: var(--primary-light); border-left: 3px solid var(--primary); }
.cd-hint { font-size: 0.76rem; color: var(--text-secondary); margin: 0 0 8px; }
.cd-code-block { margin: 0; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 0.8rem; line-height: 1.6; }
.cd-code-block code { font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace; }
.cd-code-block.solution { background: #0d1117; border: 1px solid rgba(34,197,94,0.15); opacity: 0.92; }
.cd-test-case { padding: 8px 12px; margin-bottom: 6px; border-radius: 6px; background: rgba(255,255,255,0.02); border: 1px solid var(--border); }
.cd-tc-num { font-size: 0.72rem; font-weight: 600; color: var(--primary-light); margin-bottom: 4px; }
.cd-io-row { display: flex; gap: 6px; align-items: baseline; margin-bottom: 2px; }
.cd-io-label { font-size: 0.7rem; color: var(--text-secondary); min-width: 30px; }
.cd-io-row code { font-size: 0.78rem; color: var(--text-primary); background: rgba(0,0,0,0.15); padding: 1px 8px; border-radius: 4px; }
.cd-io-explain { font-size: 0.72rem; color: var(--text-secondary); margin-top: 2px; }
.cd-line-notes { margin-top: 10px; } .cd-ln-title { font-size: 0.8rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
.cd-ln-item { display: flex; gap: 8px; padding: 3px 0; font-size: 0.78rem; } .cd-ln-range { color: var(--primary-light); font-weight: 600; white-space: nowrap; min-width: 40px; }
.cd-complexity { margin-top: 10px; padding: 8px 12px; border-radius: 6px; background: rgba(255,255,255,0.02); font-size: 0.78rem; color: var(--text-secondary); }
.cd-mistake { padding: 8px 12px; margin-bottom: 6px; border-radius: 6px; background: rgba(239,68,68,0.04); border: 1px solid rgba(239,68,68,0.1); }
.cd-mistake-title { font-size: 0.8rem; color: var(--danger); font-weight: 500; margin-bottom: 4px; }
.cd-mistake-fix { font-size: 0.78rem; color: var(--success); margin-bottom: 2px; }
.cd-mistake-example { font-size: 0.72rem; color: var(--text-secondary); } .cd-mistake-example code { background: rgba(0,0,0,0.15); padding: 1px 6px; border-radius: 3px; }
.cd-practice-item { display: flex; gap: 10px; padding: 8px 12px; margin-bottom: 6px; border-radius: 6px; background: rgba(249,115,22,0.04); border: 1px solid rgba(249,115,22,0.1); }
.cd-prac-num { width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: rgba(249,115,22,0.15); color: #f97316; font-weight: 700; font-size: 0.75rem; flex-shrink: 0; }
.cd-prac-content { flex: 1; } .cd-prac-title { font-size: 0.8rem; font-weight: 600; color: var(--text-primary); } .cd-prac-desc { font-size: 0.76rem; color: var(--text-secondary); margin-top: 2px; }
.cd-empty { font-size: 0.78rem; color: var(--text-secondary); font-style: italic; }
.cd-review-bar { margin-top: 10px; display: flex; justify-content: flex-end; }
.cd-review-btn { padding: 8px 18px; border-radius: 8px; border: 1px solid var(--primary); background: var(--primary-bg); color: var(--primary-light); font-size: 0.82rem; font-weight: 500; cursor: pointer; transition: all 0.2s; }
.cd-review-btn:hover:not(:disabled) { background: var(--primary); color: #fff; }
.cd-review-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.cd-review-panel { margin-top: 12px; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: rgba(255,255,255,0.02); }
.cd-review-panel.correct { border-color: rgba(34,197,94,0.2); }
.cd-review-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.cd-review-score { font-size: 1.3rem; font-weight: 700; color: var(--primary-light); }
.cd-review-pass { color: var(--success); font-weight: 600; } .cd-review-fail { color: var(--danger); font-weight: 600; }
.cd-review-feedback { font-size: 0.84rem; color: var(--text-primary); margin: 0 0 10px; line-height: 1.6; }
.cd-review-subtitle { font-size: 0.78rem; font-weight: 600; color: var(--text-primary); margin: 10px 0 6px; }
.cd-review-highlights ul, .cd-review-compare p { margin: 0; padding-left: 16px; font-size: 0.78rem; color: var(--text-secondary); }
.cd-review-highlights li { margin-bottom: 2px; }
.cd-issue-item { display: flex; gap: 10px; padding: 6px 10px; margin-bottom: 4px; border-radius: 6px; font-size: 0.78rem; }
.cd-issue-item.sev-error { background: rgba(239,68,68,0.06); border-left: 3px solid var(--danger); }
.cd-issue-item.sev-warning { background: rgba(249,115,22,0.06); border-left: 3px solid #f97316; }
.cd-issue-item.sev-suggestion { background: rgba(91,127,255,0.06); border-left: 3px solid var(--primary); }
.cd-issue-line { color: var(--primary-light); font-weight: 600; min-width: 30px; white-space: nowrap; }
.cd-issue-msg { color: var(--text-primary); } .cd-issue-fix { font-size: 0.74rem; color: var(--success); margin-top: 2px; }
.cd-review-compare p { font-size: 0.78rem; color: var(--text-secondary); line-height: 1.6; }
</style>

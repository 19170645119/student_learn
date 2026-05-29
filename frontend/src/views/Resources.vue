<template>
  <div class="resources">
    <nav class="topnav glass-panel">
      <button class="nav-back" @click="router.push('/home')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <h1 class="gradient-text">资源中心</h1>
      <div class="nav-spacer"></div>
    </nav>
    <div class="layout">
      <div class="left-panel">
        <div class="panel-card glass-panel" :class="{ collapsed: treeCollapsed }">
          <div class="panel-header" @click="treeCollapsed = !treeCollapsed">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2Z"/></svg>
            <span>知识章节</span>
            <svg class="tree-toggle" :class="{ rotated: !treeCollapsed }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
          </div>
          <div class="panel-body" v-show="!treeCollapsed">
            <div v-if="chapters.length === 0" class="empty-hint">暂无章节数据</div>
            <div v-for="ch in chapters" :key="ch.id" class="tree-node" @click="quickAsk(ch)">
              <span class="node-dot"></span>{{ ch.title }}
            </div>
          </div>
        </div>
        <div class="panel-card glass-panel session-bar">
          <div class="panel-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <span>对话</span>
            <button class="btn-new" @click="newSession" :disabled="waiting">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
            </button>
          </div>
          <div class="panel-body slim" v-if="sessions.length">
            <div v-for="s in sessions" :key="s.id" class="session-item" :class="{ active: s.id === sessionId }" @click="switchSession(s)">
              <span class="s-title">{{ s.title }}</span>
              <span class="s-actions" v-if="s.id === sessionId">
                <button class="s-btn" @click.stop="renameSession(s)" title="重命名">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                </button>
                <button class="s-btn danger" @click.stop="deleteSession(s)" title="删除">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                </button>
              </span>
            </div>
          </div>
        </div>
        <div class="panel-card glass-panel chat-area">
          <div class="messages" ref="msgBox">
            <div v-if="messages.length === 0" class="msg ai welcome-msg">
              <div class="welcome">
                <div class="welcome-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--primary-light)" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                </div>
                <p>你好！我是 AI 学习助手</p>
                <p class="hint">问知识问题，或说「帮我学习XXX」生成课程文档</p>
              </div>
            </div>
            <div v-for="(m, i) in messages" :key="i" :class="'msg ' + m.role">
              <template v-if="m.role === 'user'">{{ m.content || m.text }}</template>
              <template v-else>
                <p>{{ m.content || m.reply }}</p>
                <div v-if="m.intent === 'generate'" class="gen-card">
                  <div class="gen-info">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--primary-light)" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                    <span v-if="m.matched_chapter">{{ m.matched_chapter.title }}</span>
                    <span v-else-if="m.resource_type === 'mindmap'">为你梳理《{{ m.user_query }}》的知识结构</span>
                    <span v-else-if="m.resource_type === 'quiz'">为你生成《{{ m.user_query }}》的练习题</span>
                    <span v-else>为你生成《{{ m.user_query }}》的学习文档</span>
                  </div>
                  <button class="btn-gen" :disabled="m.generating" @click="doGenerate(m)">
                    {{ m.generating ? '生成中...' : (m.resource_type === 'mindmap' ? '生成思维导图' : m.resource_type === 'mindmap' ? '生成思维导图' : m.resource_type === 'quiz' ? '生成练习题' : m.resource_type === 'video' ? '生成教学动画' : m.resource_type === 'code' ? '生成代码案例' : m.resource_type === 'ppt' ? '生成PPT课件' : m.resource_type === 'video_link' ? '推荐B站视频' : '生成文档') }}
                  </button>
                </div>
              </template>
            </div>
            <div v-if="waiting" class="typing"><span></span><span></span><span></span></div>
          </div>
          <div class="input-row">
            <input v-model="input" placeholder="输入你的问题..." @keyup.enter="send" :disabled="waiting" />
            <button class="btn-send" @click="send" :disabled="waiting || !input">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </div>
      </div>
      <div class="right-panel glass-panel-glow">
        <div class="preview-panel">
          <div class="preview-tabs">
            <button :class="{ active: previewTab === 'current' }" @click="previewTab = 'current'">课程文档</button>
            <button :class="{ active: previewTab === 'mindmap' }" @click="previewTab = 'mindmap'">思维导图</button>
            <button :class="{ active: previewTab === 'quiz' }" @click="switchToQuizTab()">练习题</button>
            <button :class="{ active: previewTab === 'video' }" @click="previewTab = 'video'">教学动画</button>
            <button :class="{ active: previewTab === 'code' }" @click="previewTab = 'code'">💻 代码实操</button>
            <button :class="{ active: previewTab === 'video_link' }" @click="previewTab = 'video_link'">🎬 视频推荐</button>
            <button :class="{ active: previewTab === 'ppt' }" @click="previewTab = 'ppt'">📊 PPT课件</button>
            <button :class="{ active: previewTab === 'history' }" @click="previewTab = 'history'">历史文档</button>
          </div>

          <!-- 教学动画 Tab -->
          <div class="preview-body" v-if="previewTab === 'video'">
            <VideoPlayer v-if="currentDoc && currentDoc.resource_type === 'video' && videoScript"
              :script="videoScript"
            />
            <div v-else class="preview-empty">
              <div class="pe-icon">🎬</div>
              <div class="pe-text">在对话中说「帮我做个教学动画」来生成</div>
            </div>
          </div>
          <!-- 代码实操 Tab -->
          <div class="preview-body" v-if="previewTab === 'code'">
            <CodeViewer v-if="currentDoc && currentDoc.resource_type === 'code'"
              :content="currentDoc?.content || ''"
              :resourceId="currentDoc?.id"
            />
            <div v-else class="preview-empty">
              <div class="pe-icon">💻</div>
              <div class="pe-text">在对话中说「用Python写快速排序」来生成代码案例</div>
            </div>
          </div>
          <!-- 视频推荐 Tab -->
          <div class="preview-body" v-if="previewTab === 'video_link'">
            <div v-if="currentDoc && currentDoc.resource_type === 'video_link' && vlVideos.length" class="vl-list">
              <div class="vl-header">
                <span class="vl-keyword">搜索关键词：{{ vlKeyword }}</span>
                <span class="vl-source">来源：B站</span>
              </div>
              <div v-for="(v, idx) in vlVideos" :key="idx" class="vl-card" @click="window.open(v.url, '_blank')">
                <div class="vl-rank">{{ idx + 1 }}</div>
                <div class="vl-info">
                  <div class="vl-title">{{ v.title }}</div>
                  <div class="vl-meta">
                    <span class="vl-author">{{ v.author }}</span>
                    <span class="vl-play">▶ {{ v.play }}</span>
                    <span class="vl-duration">{{ v.duration }}</span>
                  </div>
                </div>
                <svg class="vl-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg>
              </div>
            </div>
            <div v-else class="preview-empty">
              <div class="pe-icon">🎬</div>
              <div class="pe-text">在对话中说「帮我找深度学习的视频」来获取B站推荐</div>
            </div>
          </div>
          <!-- PPT课件 Tab -->
          <div class="preview-body" v-if="previewTab === 'ppt'">
            <PptViewer v-if="currentDoc && (currentDoc.resource_type === 'ppt' || previewTab === 'ppt')"
              :content="currentDoc?.content || ''"
              :resourceId="currentDoc?.id"
            />
            <div v-else class="preview-empty">
              <div class="pe-icon">📊</div>
              <div class="pe-text">在对话中说「帮我做个PPT」来生成课件</div>
            </div>
          </div>
          <div class="preview-body" v-if="previewTab === 'current'">
            <div v-if="currentDoc && (currentDoc.resource_type === 'mindmap' || (currentDoc.content && currentDoc.content.trimStart().startsWith('mindmap')))" class="preview-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              <p>这是思维导图，请切换到「思维导图」Tab 查看</p>
              <button class="btn-primary" style="margin-top:12px" @click="previewTab = 'mindmap'">查看思维导图</button>
            </div>
            <div v-else-if="currentDoc && currentDoc.resource_type === 'quiz'" class="preview-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><path d="M9 11V6a3 3 0 0 1 6 0v5"/><path d="M12 15h.01"/><rect x="3" y="11" width="18" height="11" rx="2"/></svg>
              <p>这是练习题，请切换到「练习题」Tab 查看</p>
              <button class="btn-primary" style="margin-top:12px" @click="switchToQuizTab()">查看练习题</button>
            </div>
            <div v-else-if="streamingText" class="doc-content" v-html="renderMarkdown(streamingText)"></div>
            <div v-if="currentDoc && (currentDoc.resource_type === 'mindmap' || (currentDoc.content && currentDoc.content.trimStart().startsWith('mindmap')))" class="preview-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              <p>这是思维导图，请切换到「思维导图」Tab 查看</p>
              <button class="btn-primary" style="margin-top:12px" @click="previewTab = 'mindmap'">查看思维导图</button>
            </div>
            <div v-else-if="currentDoc && currentDoc.resource_type === 'video'" class="preview-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              <p>这是教学动画，请切换到「教学动画」Tab 查看</p>
              <button class="btn-primary" style="margin-top:12px" @click="previewTab = 'video'">查看教学动画</button>
            </div>
            <div v-else-if="currentDoc && currentDoc.resource_type === 'video_link'" class="preview-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>
              <p>这是视频推荐，请切换到「视频推荐」Tab 查看</p>
              <button class="btn-primary" style="margin-top:12px" @click="previewTab = 'video_link'">查看视频推荐</button>
            </div>
            <div v-else-if="currentDoc" class="doc-content" v-html="renderMarkdown(currentDoc.content)"></div>
            <div v-else class="preview-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
              <p>在左侧对话中生成文档</p>
            </div>
          </div>
          <div class="preview-body" v-else-if="previewTab === 'mindmap'">
            <div v-if="mindmapGenerating || mindmapSvg" class="mindmap-container-wrap">
              <div class="mindmap-zoom-bar">
                <button @click="zoomOut" title="缩小">-</button>
                <span>{{ Math.round(mindmapZoom * 100) }}%</span>
                <button @click="zoomIn" title="放大">+</button>
                <button @click="zoomReset" title="复位">↺</button>
              </div>
              <div class="mindmap-container" @wheel.prevent="(e) => e.deltaY < 0 ? zoomIn() : zoomOut()" @mousedown="onMindmapMouseDown" @mousemove="onMindmapMouseMove" @mouseup="onMindmapMouseUp" @mouseleave="onMindmapMouseUp">
                <div v-if="mindmapSvg" v-html="mindmapSvg" :style="mindmapStyle"></div>
                <div v-else class="preview-empty"><p>思维导图生成中...</p></div>
              </div>
            </div>
            <div v-else class="preview-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              <p>在对话中说「帮我梳理XX的知识结构」来生成思维导图</p>
            </div>
          </div>
          <div class="preview-body" v-else-if="previewTab === 'quiz'">
            <div v-if="!quizQuestions.length" class="preview-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3"><path d="M9 11V6a3 3 0 0 1 6 0v5"/><path d="M12 15h.01"/><rect x="3" y="11" width="18" height="11" rx="2"/></svg>
              <p style="margin-bottom: 16px;">还没有练习题，设置参数并生成</p>
              <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:center">
                <select v-model="quizDifficulty" class="quiz-select">
                  <option value="easy">简单</option>
                  <option value="medium" selected>中等</option>
                  <option value="hard">困难</option>
                </select>
                <input v-model.number="quizCount" type="number" min="1" max="20" class="quiz-input" placeholder="题数" />
                <button class="btn-primary" @click="doGenerateQuiz" :disabled="quizGenerating">
                  {{ quizGenerating ? '生成中...' : '生成练习题' }}
                </button>
              </div>
            </div>
            <div v-else>
              <div class="quiz-toolbar">
                <span class="quiz-meta">共 {{ quizQuestions.length }} 题</span>
                <select v-model="quizDifficulty" class="quiz-select quiz-select-sm">
                  <option value="easy">简单</option>
                  <option value="medium">中等</option>
                  <option value="hard">困难</option>
                </select>
                <input v-model.number="quizCount" type="number" min="1" max="20" class="quiz-input quiz-input-sm" />
                <button class="btn-outline btn-sm" @click="doGenerateQuiz()" :disabled="quizGenerating">重新生成</button>
                <span style="flex:1"></span>
                <button v-if="!quizSubmitted && !quizShowAnswers" class="btn-outline btn-sm" @click="showQuizAnswers">查看答案</button>
                <button v-if="!quizSubmitted && !quizShowAnswers" class="btn-primary btn-sm" @click="submitQuiz">提交答案</button>
                <button v-else class="btn-outline btn-sm" @click="resetQuiz">重新做题</button>
              </div>
              <div v-if="quizSubmitted" class="quiz-score-bar">
                <span class="quiz-score">{{ quizScore }} / {{ quizQuestions.length }}</span>
                <span class="quiz-pct">正确率 {{ Math.round(quizScore / quizQuestions.length * 100) }}%</span>
              </div>
              <div class="quiz-list">
                <div v-for="(q, qi) in quizQuestions" :key="qi" class="quiz-item" :class="{ correct: (quizSubmitted || quizShowAnswers) && quizAnswers[qi] === q.answer, wrong: (quizSubmitted || quizShowAnswers) && quizAnswers[qi] !== q.answer }">
                  <div class="quiz-q-header">
                    <span class="quiz-q-num">{{ qi + 1 }}.</span>
                    <span class="quiz-q-type">{{ q.type === 'choice' ? '单选' : q.type === 'truefalse' ? '判断' : q.type === 'fillblank' ? '填空' : '简答' }}</span>
                    <span class="quiz-q-text">{{ q.question }}</span>
                  </div>
                  <div v-if="q.type === 'choice'" class="quiz-options">
                    <label v-for="(opt, oi) in q.options" :key="oi" class="quiz-opt" :class="{ selected: quizAnswers[qi] === opt.charAt(0), showCorrect: (quizSubmitted || quizShowAnswers) && opt.charAt(0) === q.answer, showWrong: (quizSubmitted || quizShowAnswers) && quizAnswers[qi] === opt.charAt(0) && opt.charAt(0) !== q.answer }">
                      <input type="radio" :name="'q' + qi" :value="opt.charAt(0)" v-model="quizAnswers[qi]" :disabled="quizSubmitted || quizShowAnswers" />
                      {{ opt }}
                    </label>
                  </div>
                  <div v-else-if="q.type === 'truefalse'" class="quiz-options">
                    <label class="quiz-opt" :class="{ selected: quizAnswers[qi] === true, showCorrect: (quizSubmitted || quizShowAnswers) && q.answer === true, showWrong: (quizSubmitted || quizShowAnswers) && quizAnswers[qi] === true && q.answer !== true }">
                      <input type="radio" :name="'q' + qi" :value="true" v-model="quizAnswers[qi]" :disabled="quizSubmitted || quizShowAnswers" /> ✔ 正确
                    </label>
                    <label class="quiz-opt" :class="{ selected: quizAnswers[qi] === false, showCorrect: (quizSubmitted || quizShowAnswers) && q.answer === false, showWrong: (quizSubmitted || quizShowAnswers) && quizAnswers[qi] === false && q.answer !== false }">
                      <input type="radio" :name="'q' + qi" :value="false" v-model="quizAnswers[qi]" :disabled="quizSubmitted || quizShowAnswers" /> ✘ 错误
                    </label>
                  </div>
                  <div v-else-if="q.type === 'fillblank'" class="quiz-fill">
                    <input v-model="quizAnswers[qi]" :disabled="quizSubmitted || quizShowAnswers" class="quiz-fill-input" placeholder="请输入答案" />
                    <span v-if="quizSubmitted || quizShowAnswers" class="quiz-fill-result" :class="{ correct: quizAnswers[qi] === q.answer }">正确答案: {{ q.answer }}</span>
                  </div>
                  <div v-else-if="q.type === 'shortanswer'" class="quiz-fill">
                    <textarea v-model="quizAnswers[qi]" :disabled="quizSubmitted || quizShowAnswers" class="quiz-fill-textarea" placeholder="请输入你的答案..." rows="3"></textarea>
                    <div v-if="quizSubmitted || quizShowAnswers" class="quiz-reference">参考答案: {{ q.reference_answer }}</div>
                  </div>
                  <div v-if="(quizSubmitted || quizShowAnswers) && q.explanation" class="quiz-explanation">{{ q.explanation }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="preview-body" v-if="previewTab === 'history'">
            <div v-if="docs.length > 0" class="history-toolbar">
              <button class="batch-toggle" :class="{ active: batchMode }" @click="toggleBatchMode">
                {{ batchMode ? '取消' : '批量管理' }}
              </button>
              <template v-if="batchMode">
                <button class="batch-btn" @click="selectAll">
                  {{ selectedIds.size === docs.length ? '取消全选' : '全选' }}
                </button>
                <button class="batch-btn danger" :disabled="selectedIds.size === 0" @click="batchDelete">
                  删除选中 ({{ selectedIds.size }})
                </button>
              </template>
            </div>
            <div v-if="docs.length === 0" class="preview-empty"><p>暂无历史文档</p></div>
            <div v-for="doc in docs" :key="doc.id" class="history-item" :class="{ active: currentDoc?.id === doc.id }" @click="selectDoc(doc)">
              <div v-if="batchMode" class="h-checkbox" @click.stop="toggleSelect(doc.id)">
                <svg v-if="selectedIds.has(doc.id)" width="18" height="18" viewBox="0 0 24 24" fill="var(--primary)" stroke="var(--primary)" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="4"/></svg>
              </div>
              <svg v-if="doc.resource_type === 'mindmap' || (doc.content && doc.content.trimStart().startsWith('mindmap'))" class="h-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              <svg v-else class="h-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
              <div class="h-info">
                <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
                  <span class="h-title">{{ doc.title }}</span>
                  <span v-if="doc.resource_type === 'mindmap' || (doc.content && doc.content.trimStart().startsWith('mindmap'))" class="h-badge mindmap">思维导图</span>
                  <span v-else-if="doc.resource_type === 'quiz'" class="h-badge quiz">练习题</span>
                  <span v-if="doc.resource_type === 'video'" class="h-badge video">教学动画</span>
                  <span v-else-if="doc.resource_type === 'video_link'" class="h-badge video-link">🎬 视频推荐</span>
                  <span v-else-if="doc.resource_type === 'mindmap' || (doc.content && doc.content.trimStart().startsWith('mindmap'))" class="h-badge mindmap">思维导图</span>
                  <span v-else-if="doc.resource_type === 'quiz'" class="h-badge quiz">练习题</span>
                  <span v-else-if="doc.resource_type === 'code'" class="h-badge code-badge">💻 代码实操</span>
                  <span v-else-if="doc.resource_type === 'ppt'" class="h-badge ppt-badge">📊 PPT课件</span>
                  <span v-else class="h-badge doc">课程文档</span>
                </div>
                <span class="h-time">{{ formatTime(doc.created_time) }}</span>
              </div>
              <span class="h-status">{{ doc.status === 'completed' ? '✅' : doc.status === 'generating' ? '⏳' : '❌' }}</span>
              <button v-if="doc.resource_type !== 'mindmap' && doc.resource_type !== 'quiz' && doc.resource_type !== 'video' && doc.resource_type !== 'video_link' && doc.resource_type !== 'code' && doc.resource_type !== 'ppt' && !(doc.content && doc.content.trimStart().startsWith('mindmap'))" class="h-export" @click.stop="exportHistoryDoc(doc)" title="导出Word">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              </button>
              <button class="h-delete" @click.stop="deleteDocument(doc)" title="删除文档">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  getDocs, getChapters, generateDocStream, resourceChat,
  getResourceSessions, createResourceSession,
  deleteResourceSession, renameResourceSession, getResourceSession,
  deleteDoc, generateQuiz, gradeQuiz, generatePpt, generateVideo, generateVideoLink, generateCode
} from '../http/http.js'
import { marked } from 'marked'
import VideoPlayer from '../components/VideoPlayer.vue'
import CodeViewer from '../components/CodeViewer.vue'
import PptViewer from '../components/PptViewer.vue'
import mermaid from 'mermaid'

const router = useRouter()
const msgBox = ref(null)
const chapters = ref([])
const docs = ref([])
const sessions = ref([])
const sessionId = ref(null)
const messages = ref([])
const input = ref('')
const waiting = ref(false)
const streaming = ref(false)
const streamingText = ref('')
const treeCollapsed = ref(false)
const currentDoc = ref(null)
const mindmapContent = ref('')
const mindmapSvg = ref('')
const mindmapGenerating = ref(false)
const batchMode = ref(false)
const selectedIds = ref(new Set())
const mindmapZoom = ref(1)
const mindmapPanX = ref(0)
const mindmapPanY = ref(0)
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const panStartX = ref(0)
const panStartY = ref(0)
const mindmapStyle = computed(() => ({ transform: `scale(${mindmapZoom.value}) translate(${mindmapPanX.value / mindmapZoom.value}px, ${mindmapPanY.value / mindmapZoom.value}px)`, transformOrigin: 'top left', transition: isDragging.value ? 'none' : 'transform 0.2s ease', cursor: isDragging.value ? 'grabbing' : 'grab' }))
const previewTab = ref('current')
const quizDifficulty = ref('medium')
const quizCount = ref(5)
const quizQuestions = ref([])
const quizAnswers = ref({})
const quizSubmitted = ref(false)
const quizScore = ref(0)
const quizGenerating = ref(false)
const quizResourceId = ref(null)
const quizShowAnswers = ref(false)
const videoScript = ref(null)
const vlVideos = ref([])
const vlKeyword = ref('')

let mermaidReady = false

function switchToQuizTab() {
  previewTab.value = 'quiz'
}
async function doGenerateQuiz(extraData = null) {
  quizGenerating.value = true
  quizQuestions.value = []
  quizAnswers.value = {}
  quizShowAnswers.value = false
  quizSubmitted.value = false
  quizScore.value = 0
  try {
    const chapId = currentDoc.value?.chapter_id || 0
    const difficulty = extraData?.difficulty || quizDifficulty.value
    const count = extraData?.count || quizCount.value
    const qtype = extraData?.question_type || null
    const result = await generateQuiz(chapId, currentDoc.value?.title || null, difficulty, count, qtype)
    if (result.extra_data?.questions) {
      quizQuestions.value = result.extra_data.questions
    } else if (result.content) {
      try { quizQuestions.value = JSON.parse(result.content) } catch { quizQuestions.value = [] }
    }
    quizResourceId.value = result.id
    quizAnswers.value = {}
    quizQuestions.value.forEach((q, i) => { quizAnswers.value[i] = q.type === 'truefalse' ? null : '' })
    previewTab.value = 'quiz'
    // Push to docs history
    const exists = docs.value.find(d => d.id === result.id)
    if (!exists) {
      docs.value.unshift({
        id: result.id, title: result.title || (currentDoc.value?.title || '练习题'),
        content: result.content, resource_type: 'quiz',
        extra_data: result.extra_data || {}, status: 'completed',
        created_time: new Date().toISOString()
      })
    }
  } catch (e) {
    alert('生成失败: ' + e.message)
  } finally {
    quizGenerating.value = false
  }
}
function submitQuiz() {
  let score = 0
  quizQuestions.value.forEach((q, i) => {
    const userAns = quizAnswers.value[i]
    if (q.type === 'choice') {
      if (userAns === q.answer) score++
    } else if (q.type === 'truefalse') {
      if (userAns === q.answer) score++
    } else if (q.type === 'fillblank') {
      if (userAns && userAns.trim() === q.answer.trim()) score++
    }
  })
  quizScore.value = score
  quizSubmitted.value = true
  if (quizResourceId.value) {
    const answers = quizQuestions.value.map((q, i) => ({ question: q.question, userAnswer: quizAnswers.value[i], correct: quizAnswers.value[i] === q.answer }))
    gradeQuiz(quizResourceId.value, score, quizQuestions.value.length, answers).catch(() => {})
  }
}
function showQuizAnswers() {
  quizShowAnswers.value = true
}
function resetQuiz() {
  quizSubmitted.value = false
  quizShowAnswers.value = false
  quizScore.value = 0
  quizQuestions.value = []
  quizAnswers.value = {}
}
function ensureMermaid() {
  if (!mermaidReady) {
    mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose', suppressErrorRendering: true })
    mermaidReady = true
  }
}
onMounted(async () => {
  try {
    const [chData, docData, sessData] = await Promise.all([getChapters(), getDocs(), getResourceSessions()])
    chapters.value = Array.isArray(chData) ? chData : []
    docs.value = Array.isArray(docData) ? docData : []
    sessions.value = Array.isArray(sessData) ? sessData : []
    if (sessions.value.length > 0) await switchSession(sessions.value[0])
    // Normalize: fix quiz docs mislabeled as doc
    for (const doc of docs.value) {
      if (doc.resource_type !== 'quiz' && doc.content && doc.content.trimStart().startsWith('[')) {
        try {
          const arr = JSON.parse(doc.content)
          if (Array.isArray(arr) && arr.length && arr[0].type && arr[0].question) {
            doc.resource_type = 'quiz'
          }
        } catch {}
      }
    }
    // Re-render mindmap SVGs from stored content
    for (const doc of docs.value) {
      if (doc.resource_type === 'mindmap' && doc.content) {
        renderMindmap(doc.content).then(svg => { doc._svg = svg })
      }
    }
  } catch (e) {
    console.error('加载失败:', e)
    alert('加载失败：' + (e.message || '网络错误'))
  }
})

async function newSession() {
  try {
    const s = await createResourceSession('资源学习对话')
    sessions.value.unshift(s); sessionId.value = s.id; messages.value = []
  } catch (e) { alert('创建失败：' + e.message) }
}
async function switchSession(s) {
  sessionId.value = s.id
  try {
    const data = await getResourceSession(s.id)
    messages.value = (data.messages || []).map(m => ({ role: m.role, content: m.content, text: m.content }))
  } catch (e) {
    messages.value = []; alert('加载失败：' + (e.message || '网络错误'))
  }
  scrollDown()
}
async function deleteSession(s) {
  if (!confirm('确定删除这个对话？')) return
  try {
    await deleteResourceSession(s.id)
    sessions.value = sessions.value.filter(x => x.id !== s.id)
    if (sessionId.value === s.id) {
      sessionId.value = sessions.value[0]?.id || null; messages.value = []
      if (sessionId.value) await switchSession(sessions.value[0])
    }
  } catch (e) { alert('删除失败：' + e.message) }
}
async function renameSession(s) {
  const title = prompt('新名称：', s.title)
  if (!title) return
  try { await renameResourceSession(s.id, title); s.title = title } catch (e) { alert('重命名失败：' + e.message) }
}
function toggleBatchMode() {
  batchMode.value = !batchMode.value
  if (!batchMode.value) selectedIds.value = new Set()
}
function toggleSelect(docId) {
  const s = new Set(selectedIds.value)
  if (s.has(docId)) s.delete(docId)
  else s.add(docId)
  selectedIds.value = s
}
function selectAll() {
  if (selectedIds.value.size === docs.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(docs.value.map(d => d.id))
  }
}
async function batchDelete() {
  if (selectedIds.value.size === 0) return
  if (!confirm('确定删除选中的 ' + selectedIds.value.size + ' 个文档？')) return
  const ids = Array.from(selectedIds.value)
  for (const id of ids) {
    try { await deleteDoc(id) } catch (e) { console.error('Delete failed:', id, e) }
  }
  docs.value = docs.value.filter(d => !selectedIds.value.has(d.id))
  if (currentDoc.value && selectedIds.value.has(currentDoc.value.id)) currentDoc.value = null
  selectedIds.value = new Set()
  batchMode.value = false
}
async function deleteDocument(doc) {
  if (!confirm('确定删除「' + doc.title + '」？')) return
  try {
    await deleteDoc(doc.id)
    docs.value = docs.value.filter(x => x.id !== doc.id)
    if (currentDoc.value && currentDoc.value.id === doc.id) currentDoc.value = null
  } catch (e) { alert('删除失败：' + e.message) }
}
async function send() {
  const text = input.value.trim()
  if (!text || waiting.value) return
  input.value = ''
  if (!sessionId.value) await newSession()
  messages.value.push({ role: 'user', content: text })
  waiting.value = true; scrollDown()
  try {
    const result = await resourceChat(text, sessionId.value)
    messages.value.push({ role: 'ai', content: result.reply, reply: result.reply, intent: result.intent, matched_chapter: result.matched_chapter, user_query: result.user_query, resource_type: result.resource_type || 'doc', suggested_action: result.suggested_action, generating: false })
  } catch (e) {
    messages.value.push({ role: 'ai', content: '抱歉，出了点问题：' + e.message, intent: 'chat' })
  }
  waiting.value = false; scrollDown()
}
async function doGenerate(msg) {
  msg.generating = true
  const rt = msg.resource_type || 'doc'
  const chapterId = msg.matched_chapter?.id || 0
  const userQuery = msg.user_query || null
  if (rt === 'quiz') {
    currentDoc.value = { chapter_id: chapterId, title: userQuery }
    await doGenerateQuiz(msg.extra || null)
    msg.generating = false
    return
  }
  if (rt === 'code') {
    msg.generating = true
    previewTab.value = 'code'
    try {
      const result = await generateCode(chapterId, userQuery, msg.extra?.language)
      const newDoc = { id: result.id, title: result.title || userQuery || '代码案例', content: result.content || '', resource_type: 'code', extra_data: result.extra_data || {}, status: 'completed', created_time: new Date().toISOString() }
      docs.value.unshift(newDoc); currentDoc.value = newDoc
    } catch (e) {
      alert('生成失败：' + e.message)
    }
    msg.generating = false
    return
  }
  if (rt === 'video_link') {
    msg.generating = true
    previewTab.value = 'video_link'
    try {
      const result = await generateVideoLink(chapterId, userQuery)
      const parsed = JSON.parse(result.content || '{}')
      vlVideos.value = parsed.videos || []
      vlKeyword.value = parsed.keyword || ''
      const newDoc = { id: result.id, title: userQuery || '视频推荐', content: result.content || '', resource_type: 'video_link', extra_data: result.extra_data || {}, status: 'completed', created_time: new Date().toISOString() }
      docs.value.unshift(newDoc); currentDoc.value = newDoc
    } catch (e) {
      alert('搜索失败：' + e.message)
    }
    msg.generating = false
    return
  }
  if (rt === 'ppt') {
    msg.generating = true
    previewTab.value = 'ppt'
    try {
      const result = await generatePpt(chapterId, userQuery)
      const newDoc = { id: result.id, title: result.title || userQuery || 'PPT课件', content: result.content || '', resource_type: 'ppt', status: 'completed', created_time: new Date().toISOString() }
      docs.value.unshift(newDoc); currentDoc.value = newDoc
    } catch (e) {
      alert('生成失败：' + e.message)
    }
    msg.generating = false
    return
  }
  if (rt === 'video') {
    msg.generating = true
    previewTab.value = 'video'
    try {
      const result = await generateVideo(chapterId, userQuery)
      try { videoScript.value = JSON.parse(result.content || '{}') } catch { videoScript.value = null }
      const newDoc = { id: result.id, title: result.title || userQuery || '教学动画', content: result.content || '', resource_type: 'video', status: 'completed', created_time: new Date().toISOString() }
      docs.value.unshift(newDoc); currentDoc.value = newDoc
    } catch (e) {
      alert('生成失败：' + e.message)
    }
    msg.generating = false
    return
  }
  if (rt === 'mindmap') {
    mindmapGenerating.value = true; mindmapContent.value = ''; mindmapSvg.value = ''
    previewTab.value = 'mindmap'
  } else {
    streaming.value = true; streamingText.value = ''
    previewTab.value = 'current'
  }
  await generateDocStream(chapterId, userQuery,
    (text) => {
      if (rt === 'mindmap') {
        mindmapContent.value += text
        renderMindmap(mindmapContent.value).then(svg => { if (svg) mindmapSvg.value = svg })
      } else { streamingText.value += text }
    },
    (result) => {
      const newDoc = { id: result.id, title: result.title || msg.user_query || (rt === 'mindmap' ? '思维导图' : '学习文档'), content: rt === 'mindmap' ? mindmapContent.value : streamingText.value, resource_type: rt, status: 'completed', created_time: new Date().toISOString() }
      docs.value.unshift(newDoc); currentDoc.value = newDoc
      streaming.value = false; streamingText.value = ''
      mindmapGenerating.value = false; mindmapContent.value = ''
      msg.generating = false
    },
    (e) => { streaming.value = false; streamingText.value = ''; mindmapGenerating.value = false; mindmapContent.value = ''; msg.generating = false; alert('生成失败：' + e.message) },
    [rt]
  )
}
function quickAsk(chapter) { input.value = '帮我学习《' + chapter.title + '》'; send() }
function quickMindmap(chapter) {
  const msg = { intent: 'generate', resource_type: 'mindmap', matched_chapter: { id: chapter.id, title: chapter.title }, user_query: chapter.title, generating: false }
  messages.value.push({ role: 'user', content: '帮我梳理《' + chapter.title + '》的知识结构' })
  messages.value.push({ role: 'ai', content: '好的，为你生成《' + chapter.title + '》的思维导图', reply: '好的，为你生成思维导图', intent: 'generate', matched_chapter: msg.matched_chapter, user_query: chapter.title, resource_type: 'mindmap', suggested_action: '生成思维导图', generating: false })
  scrollDown()
  doGenerate(msg)
}
function selectDoc(doc) {
  currentDoc.value = doc
  let isVideo = doc.resource_type === 'video'
  let isCode = doc.resource_type === 'code'
  const isVideoLink = doc.resource_type === 'video_link'
  const isPpt = doc.resource_type === 'ppt'
  const isMindmap = doc.resource_type === 'mindmap' || (doc.content && doc.content.trimStart().startsWith('mindmap'))
  let isQuiz = doc.resource_type === 'quiz'
  // Content-based fallback: detect JSON quiz array
  if (!isQuiz && doc.content && doc.content.trimStart().startsWith('[')) {
    try {
      const arr = JSON.parse(doc.content)
      if (Array.isArray(arr) && arr.length && arr[0].type && arr[0].question) {
        isQuiz = true
        doc.resource_type = 'quiz' // fix in-place for badge
      }
    } catch {}
  }
  if (isMindmap) {
    previewTab.value = 'mindmap'
    mindmapContent.value = doc.content || ''
    if (doc._svg) {
      mindmapSvg.value = doc._svg
    } else {
      renderMindmap(doc.content || '').then(svg => { if (svg) { mindmapSvg.value = svg; doc._svg = svg } })
    }
  } else if (isQuiz) {
    previewTab.value = 'quiz'
    try {
      const questions = typeof doc.content === 'string' ? JSON.parse(doc.content) : doc.content
      if (Array.isArray(questions) && questions.length) {
        quizQuestions.value = questions
        quizAnswers.value = {}
        questions.forEach((q, i) => { quizAnswers.value[i] = q.type === 'truefalse' ? null : '' })
        quizSubmitted.value = false
        quizScore.value = 0
        quizResourceId.value = doc.id
        quizDifficulty.value = (doc.extra_data && doc.extra_data.difficulty) || 'medium'
        quizCount.value = questions.length
      }
    } catch (e) {
      console.error('Failed to parse quiz:', e)
      previewTab.value = 'current'
    }
  } else { previewTab.value = 'current' }
}
function renderMarkdown(text) { return text ? marked(text) : '' }
function scrollDown() { nextTick(() => { if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight }) }
function zoomIn() { mindmapZoom.value = Math.min(mindmapZoom.value + 0.25, 3) }
function zoomOut() { mindmapZoom.value = Math.max(mindmapZoom.value - 0.25, 0.5) }
function zoomReset() { mindmapZoom.value = 1; mindmapPanX.value = 0; mindmapPanY.value = 0 }
function onMindmapMouseDown(e) {
  isDragging.value = true
  dragStartX.value = e.clientX
  dragStartY.value = e.clientY
  panStartX.value = mindmapPanX.value
  panStartY.value = mindmapPanY.value
  e.preventDefault()
}
function onMindmapMouseMove(e) {
  if (!isDragging.value) return
  mindmapPanX.value = panStartX.value + (e.clientX - dragStartX.value)
  mindmapPanY.value = panStartY.value + (e.clientY - dragStartY.value)
}
function onMindmapMouseUp() {
  isDragging.value = false
}
async function renderMindmap(code) {
  if (!code || !code.trim().startsWith('mindmap')) return ''
  ensureMermaid()
  try {
    const id = 'mermaid-' + Date.now()
    const { svg } = await mermaid.render(id, code)
    return svg
  } catch (e) {
    console.error('Mermaid render error:', e)
    return ''
  }
}
function exportHistoryDoc(doc) {
  if (!doc || !doc.content) return
  const htmlContent = marked(doc.content)
  const wordHtml = '<!DOCTYPE html><html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word"><head><meta charset="utf-8"><style>body{font-family:微软雅黑,sans-serif;line-height:1.8;color:#333;max-width:800px;margin:40px auto;padding:0 20px}h1{font-size:24px;border-bottom:2px solid #5B7FFF;padding-bottom:8px}h2{font-size:20px;margin-top:24px}h3{font-size:17px}pre{background:#f5f5f5;padding:12px;border-radius:4px;font-size:13px}code{background:#f0f0f0;padding:2px 6px;border-radius:3px;font-size:13px}blockquote{border-left:4px solid #5B7FFF;padding-left:16px;color:#666;margin:16px 0}table{border-collapse:collapse;width:100%;margin:16px 0}th,td{border:1px solid #ddd;padding:8px 12px}th{background:#f5f5f5}</style></head><body>' + htmlContent + '</body></html>'
  const blob = new Blob(['\ufeff' + wordHtml], { type: 'application/msword' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = (doc.title || '学习文档') + '.doc'
  a.click()
  URL.revokeObjectURL(a.href)
}
function exportWord() {
  const doc = currentDoc.value
  if (!doc || !doc.content) return alert('没有可导出的文档')
  const htmlContent = marked(doc.content)
  const wordHtml = `<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word">
<head><meta charset="utf-8"><style>
  body { font-family: 微软雅黑, sans-serif; line-height: 1.8; color: #333; max-width: 800px; margin: 40px auto; padding: 0 20px; }
  h1 { font-size: 24px; border-bottom: 2px solid #5B7FFF; padding-bottom: 8px; }
  h2 { font-size: 20px; margin-top: 24px; }
  h3 { font-size: 17px; }
  pre { background: #f5f5f5; padding: 12px; border-radius: 4px; font-size: 13px; overflow-x: auto; }
  code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
  blockquote { border-left: 4px solid #5B7FFF; padding-left: 16px; color: #666; margin: 16px 0; }
  table { border-collapse: collapse; width: 100%; margin: 16px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
  th { background: #f5f5f5; }
</style></head><body>${htmlContent}</body></html>`
  const blob = new Blob(['\ufeff' + wordHtml], { type: 'application/msword' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = (doc.title || '学习文档') + '.doc'
  a.click()
  URL.revokeObjectURL(url)
}
function formatTime(t) {
  if (!t) return ''
  const d = new Date(t)
  return d.getMonth()+1 + '/' + d.getDate() + ' ' + String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0')
}
</script>

<style scoped>
.resources { height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
.topnav { display: flex; align-items: center; padding: 10px 20px; margin: 10px 16px 0; border-radius: 18px; flex-shrink: 0; z-index: 10; }
.nav-back { display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 10px; background: rgba(255,255,255,0.04); color: var(--text-regular); transition: all var(--transition); }
.nav-back:hover { background: rgba(255,255,255,0.08); color: var(--text-primary); }
.topnav h1 { font-size: 1.1rem; font-weight: 700; margin-left: 14px; }
.nav-spacer { flex: 1; }
.layout { display: flex; gap: 12px; padding: 12px 16px 16px; flex: 1; min-height: 0; overflow: hidden; }
.left-panel { width: 380px; flex-shrink: 0; display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow: hidden; }
.panel-card { border-radius: var(--radius); overflow: hidden; display: flex; flex-direction: column; }
.panel-header { display: flex; align-items: center; gap: 8px; padding: 12px 16px; font-size: 0.85rem; font-weight: 600; color: var(--text-primary); cursor: pointer; user-select: none; }
.panel-header:hover { background: rgba(255,255,255,0.03); }
.panel-body { padding: 0 16px 12px; }
.panel-body.slim { padding: 6px 8px; max-height: 120px; overflow-y: auto; }
.tree-toggle { transition: transform var(--transition); margin-left: auto; opacity: 0.5; }
.tree-toggle.rotated { transform: rotate(180deg); }
.chapter-tree { flex-shrink: 0; }
.chapter-tree.collapsed .panel-body { display: none; }
.tree-node { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; font-size: 0.82rem; color: var(--text-regular); cursor: pointer; transition: all var(--transition); }
.tree-node:hover { color: var(--text-primary); background: rgba(255,255,255,0.04); }
.node-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); opacity: 0.5; flex-shrink: 0; }
.empty-hint { font-size: 0.8rem; color: var(--text-disabled); padding: 12px 0; text-align: center; }
.session-bar { flex-shrink: 0; max-height: 170px; }
.btn-new { margin-left: auto; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 8px; background: rgba(255,255,255,0.06); color: var(--text-secondary); }
.btn-new:hover { background: var(--primary-bg); color: var(--primary-light); }
.btn-new:disabled { opacity: 0.3; }
.session-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; cursor: pointer; font-size: 0.8rem; color: var(--text-secondary); transition: all var(--transition); margin-bottom: 2px; }
.session-item:hover, .session-item.active { background: rgba(255,255,255,0.06); color: var(--text-primary); }
.s-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.s-actions { display: flex; gap: 4px; }
.s-btn { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 6px; background: transparent; color: var(--text-disabled); }
.s-btn:hover { background: rgba(255,255,255,0.06); color: var(--text-primary); }
.s-btn.danger:hover { color: var(--danger); }
.chat-area { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.messages { flex: 1; overflow-y: auto; padding: 16px; }
.msg { max-width: 85%; padding: 10px 14px; border-radius: 14px; margin-bottom: 10px; font-size: 0.85rem; line-height: 1.55; white-space: pre-wrap; word-break: break-word; }
.msg.user { background: var(--gradient-brand); color: #fff; margin-left: auto; }
.msg.ai { background: rgba(255,255,255,0.04); color: var(--text-primary); }
.welcome-msg { background: transparent !important; }
.welcome { text-align: center; padding: 20px 0; }
.welcome-icon { margin-bottom: 12px; }
.welcome p { font-size: 0.9rem; }
.welcome .hint { margin-top: 6px; font-size: 0.8rem; color: var(--text-secondary); }
.typing { display: flex; gap: 4px; padding: 10px 14px; }
.typing span { width: 6px; height: 6px; border-radius: 50%; background: var(--text-disabled); animation: bounce 1.4s infinite; }
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,80%,100%{transform:scale(0.6)} 40%{transform:scale(1)} }
.gen-card { margin-top: 10px; padding: 12px; background: rgba(91,127,255,0.08); border: 1px solid rgba(91,127,255,0.15); border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.gen-info { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; color: var(--text-primary); flex: 1; }
.btn-gen { padding: 6px 16px; background: var(--gradient-brand); color: #fff; border: none; border-radius: 8px; font-size: 0.78rem; font-weight: 500; white-space: nowrap; flex-shrink: 0; }
.btn-gen:hover { box-shadow: var(--shadow-glow); transform: translateY(-1px); }
.btn-gen:disabled { opacity: 0.5; cursor: not-allowed; }
.input-row { display: flex; gap: 8px; padding: 12px; border-top: 1px solid var(--border-light); }
.input-row input { flex: 1; height: 40px; background: rgba(10,16,40,0.5); border: 1px solid var(--border); border-radius: 20px; padding: 0 16px; font-size: 0.85rem; color: var(--text-primary); outline: none; }
.input-row input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); }
.input-row input::placeholder { color: var(--text-disabled); }
.btn-send { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: var(--gradient-brand); color: #fff; border-radius: 50%; flex-shrink: 0; }
.btn-send:hover { box-shadow: var(--shadow-glow); transform: scale(1.05); }
.btn-send:disabled { opacity: 0.3; cursor: not-allowed; }
.right-panel { flex: 1; min-width: 0; border-radius: var(--radius); overflow: hidden; }
.preview-panel { height: 100%; display: flex; flex-direction: column; }
.preview-tabs { display: flex; gap: 4px; padding: 14px 16px 0; }
.preview-tabs button { padding: 6px 16px; background: transparent; color: var(--text-secondary); border: none; border-radius: 8px; font-size: 0.82rem; font-weight: 500; }
.preview-tabs button.active { background: var(--primary-bg); color: var(--primary-light); }
.preview-tabs button:hover { color: var(--text-primary); }
.preview-body { flex: 1; overflow-y: auto; padding: 16px 20px 20px; }
.preview-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-disabled); gap: 12px; }
.preview-empty p { font-size: 0.9rem; }
.history-item { display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: var(--radius-sm); cursor: pointer; transition: all var(--transition); margin-bottom: 4px; }
.history-item:hover, .history-item.active { background: rgba(255,255,255,0.04); }
.h-icon { color: var(--text-disabled); flex-shrink: 0; }
.h-info { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.h-title { font-size: 0.85rem; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.h-time { font-size: 0.72rem; color: var(--text-disabled); margin-top: 2px; }
.h-status { font-size: 0.9rem; flex-shrink: 0; }
.h-export { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: transparent; color: var(--text-disabled); border-radius: 6px; flex-shrink: 0; }
.h-export:hover { color: var(--success); background: var(--success-bg); }
.h-delete { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: transparent; color: var(--text-disabled); border-radius: 6px; flex-shrink: 0; }
.h-delete:hover { color: var(--danger); background: var(--danger-bg); }
.doc-content { font-size: 0.9rem; line-height: 1.8; color: var(--text-primary); }
.doc-content :deep(h1) { font-size: 1.5rem; margin: 24px 0 12px; color: var(--text-primary); font-weight: 700; }
.doc-content :deep(h2) { font-size: 1.2rem; margin: 20px 0 10px; color: var(--text-primary); font-weight: 600; }
.doc-content :deep(h3) { font-size: 1.05rem; margin: 16px 0 8px; }
.doc-content :deep(p) { margin: 8px 0; }
.doc-content :deep(pre) { background: rgba(10,16,40,0.6); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 16px; overflow-x: auto; font-size: 0.82rem; }
.doc-content :deep(code) { background: rgba(10,16,40,0.5); padding: 2px 6px; border-radius: 4px; font-size: 0.82rem; }
.doc-content :deep(blockquote) { border-left: 3px solid var(--primary); padding-left: 14px; margin: 12px 0; color: var(--text-secondary); }
.doc-content :deep(table) { width: 100%; border-collapse: collapse; margin: 12px 0; }
.doc-content :deep(th), .doc-content :deep(td) { padding: 8px 12px; border: 1px solid var(--border); text-align: left; font-size: 0.85rem; }
.doc-content :deep(th) { background: rgba(255,255,255,0.03); font-weight: 600; }
.doc-content :deep(a) { color: var(--primary-light); }
.mindmap-btn { margin-left: auto; width: 26px; height: 26px; display: none; align-items: center; justify-content: center; border-radius: 6px; background: transparent; font-size: 14px; cursor: pointer; flex-shrink: 0; }
.tree-node:hover .mindmap-btn { display: flex; }
.mindmap-btn:hover { background: var(--primary-bg); }
.mindmap-container-wrap { position: relative; width: 100%; height: 100%; overflow: hidden; }
.mindmap-zoom-bar { position: absolute; top: 10px; right: 10px; z-index: 10; display: flex; align-items: center; gap: 6px; background: var(--surface); backdrop-filter: blur(10px); border: 1px solid var(--border); border-radius: 10px; padding: 6px 12px; }
.mindmap-zoom-bar button { width: 28px; height: 28px; border-radius: 6px; background: rgba(255,255,255,0.06); color: var(--text-primary); font-size: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; border: none; }
.mindmap-zoom-bar button:hover { background: var(--primary-bg); color: var(--primary-light); }
.mindmap-zoom-bar span { font-size: 12px; color: var(--text-secondary); min-width: 40px; text-align: center; font-variant-numeric: tabular-nums; }
.mindmap-container { width: 100%; height: calc(100% - 50px); overflow: auto; display: flex; align-items: flex-start; justify-content: flex-start; padding: 20px; cursor: grab; }
.mindmap-container:active { cursor: grabbing; }
.mindmap-container :deep(svg) { transition: transform 0.2s ease; }
.history-toolbar { display: flex; align-items: center; gap: 8px; padding: 0 0 10px; }
.batch-toggle { padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; background: rgba(255,255,255,0.04); color: var(--text-secondary); border: 1px solid var(--border); cursor: pointer; }
.batch-toggle:hover { color: var(--text-primary); }
.batch-toggle.active { background: var(--primary-bg); color: var(--primary-light); border-color: rgba(91,127,255,0.2); }
.batch-btn { padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; background: rgba(255,255,255,0.04); color: var(--text-secondary); border: 1px solid var(--border); cursor: pointer; }
.batch-btn:hover { color: var(--text-primary); }
.batch-btn.danger { color: var(--danger); border-color: rgba(239,68,68,0.2); }
.batch-btn.danger:hover { background: var(--danger-bg); }
.batch-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.h-checkbox { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; border-radius: 6px; }
.h-checkbox:hover { background: rgba(255,255,255,0.04); }
.h-badge { font-size: 0.65rem; padding: 1px 8px; border-radius: 4px; font-weight: 500; flex-shrink: 0; }
.h-badge.mindmap { background: rgba(155,109,255,0.15); color: #b892ff; }
.h-badge.doc { background: rgba(91,127,255,0.12); color: var(--primary-light); }
.h-badge.quiz { background: rgba(34,197,94,0.12); color: var(--success); }
.export-bar { display: flex; justify-content: flex-end; padding: 0 0 8px; }
.export-btn { display: flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 8px; font-size: 0.8rem; font-weight: 500; background: rgba(34,197,94,0.1); color: var(--success); border: 1px solid rgba(34,197,94,0.2); cursor: pointer; }
.export-btn:hover { background: rgba(34,197,94,0.2); }
@media (max-width: 900px) { .layout { flex-direction: column; } .left-panel { width: 100%; } }
.quiz-select { padding: 8px 14px; border-radius: 8px; background: var(--surface); color: var(--text-primary); border: 1px solid var(--border); font-size: 0.85rem; cursor: pointer; outline: none; }
.quiz-select:focus { border-color: var(--primary); }
.quiz-input { width: 70px; padding: 8px 12px; border-radius: 8px; background: var(--surface); color: var(--text-primary); border: 1px solid var(--border); font-size: 0.85rem; text-align: center; outline: none; }
.quiz-input:focus { border-color: var(--primary); }
.quiz-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 0 0 12px; }
.quiz-meta { font-size: 0.8rem; color: var(--text-secondary); }
.quiz-score-bar { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-radius: 10px; background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.15); margin-bottom: 16px; }
.quiz-score { font-size: 1.4rem; font-weight: 700; color: var(--success); }
.quiz-pct { font-size: 0.85rem; color: var(--text-secondary); }
.quiz-list { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; flex: 1; padding-right: 4px; }
.quiz-item { background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 10px; padding: 16px; transition: border-color 0.2s; }
.quiz-item.correct { border-color: rgba(34,197,94,0.3); background: rgba(34,197,94,0.04); }
.quiz-item.wrong { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.04); }
.quiz-q-header { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; }
.quiz-q-num { color: var(--primary-light); font-weight: 600; min-width: 24px; }
.quiz-q-type { font-size: 0.65rem; padding: 2px 8px; border-radius: 4px; background: rgba(255,255,255,0.05); color: var(--text-secondary); white-space: nowrap; margin-top: 2px; }
.quiz-q-text { font-size: 0.9rem; color: var(--text-primary); line-height: 1.5; }
.quiz-options { display: flex; flex-direction: column; gap: 6px; margin-left: 32px; }
.quiz-opt { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; background: rgba(255,255,255,0.02); border: 1px solid transparent; cursor: pointer; font-size: 0.85rem; color: var(--text-primary); transition: all 0.15s; }
.quiz-opt:hover { background: rgba(255,255,255,0.05); }
.quiz-opt.selected { border-color: var(--primary); background: var(--primary-bg); }
.quiz-opt.showCorrect { border-color: rgba(34,197,94,0.3); background: rgba(34,197,94,0.06); color: var(--success); }
.quiz-opt.showWrong { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.06); color: var(--danger); }
.quiz-opt input { accent-color: var(--primary); }
.quiz-fill { margin-left: 32px; margin-top: 8px; }
.quiz-fill-input { width: 100%; padding: 8px 12px; border-radius: 8px; background: var(--surface); color: var(--text-primary); border: 1px solid var(--border); font-size: 0.85rem; outline: none; }
.quiz-fill-input:focus { border-color: var(--primary); }
.quiz-fill-textarea { width: 100%; padding: 8px 12px; border-radius: 8px; background: var(--surface); color: var(--text-primary); border: 1px solid var(--border); font-size: 0.85rem; outline: none; resize: vertical; }
.quiz-fill-textarea:focus { border-color: var(--primary); }
.quiz-fill-result { display: block; margin-top: 6px; font-size: 0.8rem; color: var(--text-secondary); }
.quiz-fill-result.correct { color: var(--success); }
.quiz-reference { margin-top: 6px; padding: 8px 12px; border-radius: 6px; background: rgba(91,127,255,0.06); font-size: 0.82rem; color: var(--text-secondary); border-left: 3px solid var(--primary); }
.quiz-explanation { margin-top: 10px; margin-left: 32px; padding: 8px 12px; border-radius: 6px; background: rgba(255,255,255,0.03); font-size: 0.82rem; color: var(--text-secondary); line-height: 1.6; }
.btn-sm { padding: 6px 14px; font-size: 0.8rem; border-radius: 6px; }
.quiz-select-sm { padding: 4px 8px; font-size: 0.75rem; border-radius: 6px; }

.quiz-panel { padding: 16px 20px; }
.quiz-settings { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.quiz-q-card { background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 12px; }
.quiz-q-card.correct { border-color: rgba(34,197,94,0.3); background: rgba(34,197,94,0.04); }
.quiz-q-card.wrong { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.04); }
.quiz-q-header { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; }
.quiz-q-num { color: var(--primary-light); font-weight: 600; min-width: 24px; }
.quiz-q-type { font-size: 0.65rem; padding: 2px 8px; border-radius: 4px; background: rgba(255,255,255,0.05); color: var(--text-secondary); white-space: nowrap; margin-top: 2px; }
.quiz-q-text { font-size: 0.9rem; color: var(--text-primary); line-height: 1.5; }
.quiz-options { display: flex; flex-direction: column; gap: 6px; margin-left: 32px; }
.quiz-opt { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; background: rgba(255,255,255,0.02); border: 1px solid transparent; cursor: pointer; font-size: 0.85rem; color: var(--text-primary); transition: all 0.15s; }
.quiz-opt:hover { background: rgba(255,255,255,0.05); }
.quiz-opt.selected { border-color: var(--primary); background: var(--primary-bg); }
.quiz-opt.showCorrect { border-color: rgba(34,197,94,0.3); background: rgba(34,197,94,0.06); color: var(--success); }
.quiz-opt.showWrong { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.06); color: var(--danger); }
.quiz-opt input { accent-color: var(--primary); }
.quiz-fill { margin-left: 32px; margin-top: 8px; }
.quiz-fill-input { width: 100%; padding: 8px 12px; border-radius: 8px; background: var(--surface); color: var(--text-primary); border: 1px solid var(--border); font-size: 0.85rem; outline: none; }
.quiz-fill-input:focus { border-color: var(--primary); }
.quiz-fill-textarea { width: 100%; padding: 8px 12px; border-radius: 8px; background: var(--surface); color: var(--text-primary); border: 1px solid var(--border); font-size: 0.85rem; outline: none; resize: vertical; }
.quiz-fill-textarea:focus { border-color: var(--primary); }
.quiz-fill-result { display: block; margin-top: 6px; font-size: 0.8rem; color: var(--text-secondary); }
.quiz-fill-result.correct { color: var(--success); }
.quiz-reference { margin-top: 6px; padding: 8px 12px; border-radius: 6px; background: rgba(91,127,255,0.06); font-size: 0.82rem; color: var(--text-secondary); border-left: 3px solid var(--primary); }
.quiz-explanation { margin-top: 10px; margin-left: 32px; padding: 8px 12px; border-radius: 6px; background: rgba(255,255,255,0.03); font-size: 0.82rem; color: var(--text-secondary); line-height: 1.6; }
.btn-sm { padding: 6px 14px; font-size: 0.8rem; border-radius: 6px; }
.quiz-select-sm { padding: 4px 8px; font-size: 0.75rem; border-radius: 6px; }
.quiz-input-sm { width: 50px; padding: 4px 6px; font-size: 0.75rem; border-radius: 6px; }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); border-radius: 8px; padding: 8px 18px; cursor: pointer; font-size: 0.85rem; }
.btn-outline:hover { border-color: var(--primary); color: var(--primary-light); }

.h-badge.video { background: rgba(249,115,22,0.12); color: #f97316; }
.h-badge.video-link { background: rgba(249,115,22,0.12); color: #f97316; }
.h-badge.code-badge { background: rgba(34,197,94,0.12); color: var(--success); }
.ppt-badge { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }

/* Video Link Cards */
.vl-list { display: flex; flex-direction: column; gap: 8px; }
.vl-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; margin-bottom: 4px; font-size: 0.78rem; }
.vl-keyword { color: var(--primary-light); font-weight: 500; }
.vl-source { color: var(--text-secondary); font-size: 0.72rem; }
.vl-card { display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 10px; cursor: pointer; transition: all 0.2s; }
.vl-card:hover { transform: translateY(-2px); border-color: var(--primary); box-shadow: 0 4px 16px rgba(91,127,255,0.15); background: rgba(255,255,255,0.05); }
.vl-rank { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: rgba(249,115,22,0.12); color: #f97316; font-weight: 700; font-size: 0.85rem; flex-shrink: 0; }
.vl-info { flex: 1; min-width: 0; }
.vl-title { font-size: 0.85rem; color: var(--text-primary); line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 4px; }
.vl-meta { display: flex; gap: 12px; font-size: 0.7rem; color: var(--text-secondary); flex-wrap: wrap; }
.vl-author { color: var(--text-secondary); }
.vl-play { color: var(--primary-light); }
.vl-duration { color: var(--text-secondary); }
.vl-arrow { flex-shrink: 0; opacity: 0.4; transition: opacity 0.2s; }
.vl-card:hover .vl-arrow { opacity: 0.8; }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); border-radius: 8px; padding: 8px 18px; cursor: pointer; font-size: 0.85rem; }
.btn-outline:hover { border-color: var(--primary); color: var(--primary-light); }
</style>

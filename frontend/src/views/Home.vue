<template>
  <div class="home">
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>

    <nav class="navbar glass-panel">
      <div class="nav-inner">
        <div class="nav-brand">
          <span class="brand-icon">✦</span>
          <span class="brand-text">AI 学习平台</span>
        </div>
        <div class="nav-links">
          <router-link to="/profile" class="nav-link">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M6 21v-2a4 4 0 014-4h4a4 4 0 014 4v2"/></svg>
            学习画像
          </router-link>
          <router-link to="/resources" class="nav-link">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
            资源中心
          </router-link>
          <router-link to="/learning-path" class="nav-link">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
            学习路径
          </router-link>
        </div>
        <div class="nav-actions">
          <button class="btn-logout" @click="exitLogin">退出</button>
        </div>
      </div>
    </nav>

    <section class="hero">
      <div class="hero-badge">
        <span class="badge-dot"></span>
        AI 驱动 · 个性化学习
      </div>
      <h1 class="hero-title">
        让每一次学习<br/>
        <span class="gradient-text">都精准有效</span>
      </h1>
      <p class="hero-desc">
        基于大语言模型的智能学习平台，深度理解你的知识结构，<br/>
        个性化推荐学习资源，让进步看得见。
      </p>
      <div class="hero-actions">
        <router-link to="/resources" class="btn-primary btn-lg">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
          开始学习
        </router-link>
        <router-link to="/profile" class="btn-ghost btn-lg">
          构建学习画像 →
        </router-link>
      </div>

      <div class="hero-stats">
        <div class="stat-item">
          <span class="stat-value">AI</span>
          <span class="stat-label">智能分析</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">6D</span>
          <span class="stat-label">多维画像</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value">∞</span>
          <span class="stat-label">个性化路径</span>
        </div>
      </div>
    </section>

    <section class="modules">
      <div class="section-header">
        <h2>核心能力</h2>
        <p>三大智能模块，覆盖学习全流程</p>
      </div>
      <div class="module-grid">
        <router-link to="/profile" class="module-card">
          <div class="card-glow"></div>
          <div class="card-icon-wrap">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#grad1)" stroke-width="1.5">
              <defs><linearGradient id="grad1" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#5B7FFF"/><stop offset="1" stop-color="#9B6DFF"/></linearGradient></defs>
              <circle cx="12" cy="8" r="5"/><path d="M3 21v-2a7 7 0 017-7h4a7 7 0 017 7v2"/>
            </svg>
          </div>
          <h3>学习画像</h3>
          <p>AI 对话构建你的六维学习画像，精准定位知识短板与兴趣方向</p>
        </router-link>

        <router-link to="/resources" class="module-card">
          <div class="card-glow"></div>
          <div class="card-icon-wrap">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#grad2)" stroke-width="1.5">
              <defs><linearGradient id="grad2" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#5B7FFF"/><stop offset="1" stop-color="#9B6DFF"/></linearGradient></defs>
              <path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>
            </svg>
          </div>
          <h3>资源中心</h3>
          <p>智能对话推荐 + 一键生成课程文档，流式渲染 Markdown 实时预览</p>
        </router-link>

        <router-link to="/learning-path" class="module-card">
          <div class="card-glow"></div>
          <div class="card-icon-wrap">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#grad3)" stroke-width="1.5">
              <defs><linearGradient id="grad3" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#5B7FFF"/><stop offset="1" stop-color="#9B6DFF"/></linearGradient></defs>
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </div>
          <h3>学习路径</h3>
          <p>基于画像生成个性化学习路线图，循序渐进达成学习目标</p>
        </router-link>
      </div>
    </section>

    <footer class="footer">
      <p>Powered by Qwen-Max &amp; Spark-X · 个性化学习平台 © 2026</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
const username = ref('')
onMounted(() => {
  const u = JSON.parse(localStorage.getItem('user') || '{}')
  username.value = u.username || '同学'
})
function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.home { position: relative; min-height: 100vh; overflow-x: hidden; }
.bg-orb { position: fixed; border-radius: 50%; pointer-events: none; z-index: 0; }
.orb-1 { width: 600px; height: 600px; top: -200px; left: -150px; background: radial-gradient(circle, rgba(91,127,255,0.08) 0%, transparent 70%); animation: float 20s ease-in-out infinite; }
.orb-2 { width: 500px; height: 500px; bottom: -100px; right: -100px; background: radial-gradient(circle, rgba(155,109,255,0.06) 0%, transparent 70%); animation: float 24s ease-in-out infinite reverse; }
@keyframes float { 0%, 100% { transform: translate(0, 0); } 33% { transform: translate(30px, -20px); } 66% { transform: translate(-20px, 15px); } }
.navbar { position: sticky; top: 16px; z-index: 100; margin: 16px auto 0; max-width: 1100px; border-radius: 20px; }
.nav-inner { display: flex; align-items: center; padding: 12px 24px; gap: 32px; }
.nav-brand { display: flex; align-items: center; gap: 10px; }
.brand-icon { font-size: 22px; background: var(--gradient-brand); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.brand-text { font-size: 17px; font-weight: 700; letter-spacing: -0.02em; }
.nav-links { display: flex; gap: 6px; flex: 1; }
.nav-link { display: flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 10px; font-size: 14px; color: var(--text-regular); text-decoration: none; transition: all var(--transition); }
.nav-link:hover, .nav-link.router-link-active { color: var(--text-primary); background: rgba(255,255,255,0.05); }
.nav-link svg { opacity: 0.6; transition: opacity var(--transition); }
.nav-link:hover svg, .nav-link.router-link-active svg { opacity: 1; }
.nav-actions { display: flex; align-items: center; }
.btn-logout { padding: 8px 18px; border-radius: 8px; font-size: 13px; color: var(--text-secondary); background: rgba(255,255,255,0.04); border: 1px solid var(--border); cursor: pointer; transition: all var(--transition); }
.btn-logout:hover { color: var(--danger); border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.08); }
.hero { text-align: center; padding: 80px 20px 60px; position: relative; z-index: 1; }
.hero-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 18px; border-radius: 50px; font-size: 13px; color: var(--primary-light); background: var(--primary-bg); border: 1px solid rgba(91,127,255,0.15); margin-bottom: 28px; }
.badge-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--primary); box-shadow: 0 0 8px var(--primary-glow); animation: pulse-dot 2s ease-in-out infinite; }
@keyframes pulse-dot { 0%, 100% { box-shadow: 0 0 8px var(--primary-glow); } 50% { box-shadow: 0 0 16px var(--primary-glow), 0 0 24px rgba(91,127,255,0.3); } }
.hero-title { font-size: 52px; font-weight: 700; line-height: 1.2; letter-spacing: -0.03em; margin-bottom: 20px; }
.hero-desc { font-size: 17px; color: var(--text-regular); line-height: 1.7; margin-bottom: 36px; }
.hero-actions { display: flex; justify-content: center; gap: 16px; }
.btn-lg { padding: 14px 32px; font-size: 16px; border-radius: 14px; display: inline-flex; align-items: center; gap: 8px; text-decoration: none; font-weight: 600; }
.btn-ghost { padding: 14px 32px; font-size: 16px; border-radius: 14px; color: var(--text-primary); background: rgba(255,255,255,0.04); border: 1px solid var(--border); text-decoration: none; transition: all var(--transition); }
.btn-ghost:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.15); transform: translateY(-1px); }
.hero-stats { display: inline-flex; align-items: center; gap: 32px; margin-top: 56px; padding: 20px 40px; border-radius: 20px; background: var(--surface); backdrop-filter: blur(var(--glass-blur)); border: 1px solid var(--glass-border); }
.stat-item { text-align: center; min-width: 80px; }
.stat-value { display: block; font-size: 24px; font-weight: 700; background: var(--gradient-brand); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stat-label { font-size: 12px; color: var(--text-secondary); }
.stat-divider { width: 1px; height: 32px; background: var(--border); }
.modules { max-width: 1100px; margin: 0 auto; padding: 20px 20px 80px; position: relative; z-index: 1; }
.section-header { text-align: center; margin-bottom: 40px; }
.section-header h2 { font-size: 30px; margin-bottom: 8px; }
.section-header p { color: var(--text-secondary); font-size: 15px; }
.module-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.module-card { position: relative; padding: 32px 24px; border-radius: 20px; background: var(--glass-bg); backdrop-filter: blur(var(--glass-blur)); -webkit-backdrop-filter: blur(var(--glass-blur)); border: 1px solid var(--glass-border); text-decoration: none; transition: all var(--transition-slow); overflow: hidden; }
.card-glow { position: absolute; inset: 0; background: var(--gradient-card); opacity: 0; transition: opacity var(--transition-slow); }
.module-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg), var(--shadow-glow); border-color: rgba(91,127,255,0.2); }
.module-card:hover .card-glow { opacity: 1; }
.card-icon-wrap { width: 52px; height: 52px; display: flex; align-items: center; justify-content: center; border-radius: 14px; background: var(--primary-bg); border: 1px solid rgba(91,127,255,0.12); margin-bottom: 20px; position: relative; z-index: 1; }
.module-card h3 { font-size: 18px; margin-bottom: 10px; position: relative; z-index: 1; }
.module-card p { font-size: 14px; color: var(--text-secondary); line-height: 1.6; position: relative; z-index: 1; }
.footer { text-align: center; padding: 32px 20px; color: var(--text-disabled); font-size: 13px; position: relative; z-index: 1; }
.footer p { margin: 0; }
@media (max-width: 768px) {
  .hero-title { font-size: 32px; }
  .module-grid { grid-template-columns: 1fr; }
  .nav-inner { flex-wrap: wrap; gap: 12px; }
  .hero-stats { gap: 20px; padding: 16px 24px; }
}
</style>

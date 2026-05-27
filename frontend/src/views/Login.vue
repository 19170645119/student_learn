<template>
  <div class="login-page">
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>
    <div class="auth-card glass-panel-glow">
      <div class="card-header">
        <div class="logo-icon">
          <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="url(#loginGrad)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <defs><linearGradient id="loginGrad" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#5B7FFF"/><stop offset="1" stop-color="#9B6DFF"/></linearGradient></defs>
            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 1.1 2.7 2 6 2s6-.9 6-2v-5"/>
          </svg>
        </div>
        <h2 class="gradient-text">AI 学习平台</h2>
        <p>登录你的学习空间</p>
      </div>
      <div class="form">
        <div class="field">
          <label>邮箱地址</label>
          <div class="input-wrap">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
            <input v-model="email" type="email" placeholder="your@email.com" />
          </div>
        </div>
        <div class="field">
          <label>密码</label>
          <div class="input-wrap">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input v-model="password" type="password" placeholder="••••••••" @keyup.enter="handleLogin" />
          </div>
        </div>
        <button class="btn-login" @click="handleLogin" :disabled="loading">
          <span v-if="!loading">登 录</span>
          <span v-else class="loading-dots">验证中<span class="dots"></span></span>
        </button>
        <p class="link">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../http/http.js'

const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!email.value || !password.value) return alert('请填写完整信息')
  loading.value = true
  try {
    const res = await login(email.value, password.value)
    localStorage.setItem('token', res.token)
    localStorage.setItem('user', JSON.stringify(res.user))
    router.push('/home')
  } catch (e) {
    alert(e.message || '登录失败')
  }
  loading.value = false
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.bg-orb { position: fixed; border-radius: 50%; pointer-events: none; z-index: 0; }
.orb-1 { width: 550px; height: 550px; top: -180px; right: -120px; background: radial-gradient(circle, rgba(91,127,255,0.1) 0%, transparent 70%); }
.orb-2 { width: 450px; height: 450px; bottom: -150px; left: -100px; background: radial-gradient(circle, rgba(155,109,255,0.08) 0%, transparent 70%); }
.auth-card { position: relative; z-index: 1; width: 420px; padding: 48px 40px; }
.card-header { text-align: center; margin-bottom: 36px; }
.logo-icon { margin-bottom: 16px; display: inline-block; }
.card-header h2 { font-size: 1.6rem; font-weight: 700; margin-bottom: 6px; }
.card-header p { font-size: 0.9rem; color: var(--text-secondary); }
.field { margin-bottom: 20px; }
.field label { display: block; font-size: 0.82rem; color: var(--text-regular); font-weight: 500; margin-bottom: 8px; }
.input-wrap { display: flex; align-items: center; gap: 10px; background: rgba(10,16,40,0.5); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0 14px; transition: all var(--transition); }
.input-wrap:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); }
.input-wrap svg { color: var(--text-secondary); flex-shrink: 0; }
.input-wrap input { flex: 1; height: 44px; background: transparent; border: none; color: var(--text-primary); font-size: 0.9rem; outline: none; }
.input-wrap input::placeholder { color: var(--text-disabled); }
.btn-login { width: 100%; height: 46px; background: var(--gradient-brand); color: #fff; border: none; border-radius: var(--radius-sm); font-size: 0.95rem; font-weight: 600; margin-top: 8px; letter-spacing: 0.04em; position: relative; overflow: hidden; }
.btn-login::after { content: ""; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent); opacity: 0; transition: opacity var(--transition); }
.btn-login:hover::after { opacity: 1; }
.btn-login:hover { transform: translateY(-1px); box-shadow: var(--shadow-glow); }
.btn-login:disabled { opacity: 0.5; cursor: not-allowed; }
.loading-dots .dots::after { content: ""; animation: dots 1.5s steps(4, end) infinite; }
@keyframes dots { 0% { content: ""; } 25% { content: "."; } 50% { content: ".."; } 75% { content: "..."; } }
.link { text-align: center; margin-top: 24px; font-size: 0.85rem; color: var(--text-secondary); }
.link a { color: var(--primary-light); text-decoration: none; font-weight: 500; }
.link a:hover { text-decoration: underline; }
</style>

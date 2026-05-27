<template>
  <div class="reg-page">
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>
    <div class="auth-card glass-panel-glow">
      <div class="card-header">
        <div class="logo-icon">
          <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="url(#regGrad)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <defs><linearGradient id="regGrad" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#5B7FFF"/><stop offset="1" stop-color="#9B6DFF"/></linearGradient></defs>
            <circle cx="12" cy="8" r="5"/><path d="M3 21v-2a7 7 0 017-7h4a7 7 0 017 7v2"/>
          </svg>
        </div>
        <h2 class="gradient-text">创建账号</h2>
        <p>开启你的AI学习之旅</p>
      </div>
      <div class="form">
        <div class="field">
          <label>邮箱</label>
          <div class="row">
            <div class="input-wrap flex">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
              <input v-model="form.email" type="email" placeholder="your@email.com" />
            </div>
            <button class="code-btn" @click="sendCode" :disabled="countdown > 0">
              {{ countdown > 0 ? countdown + 's' : '发送验证码' }}
            </button>
          </div>
        </div>
        <div class="field">
          <label>验证码</label>
          <div class="input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input v-model="form.code" type="text" placeholder="4位验证码" maxlength="4" />
          </div>
        </div>
        <div class="field">
          <label>用户名</label>
          <div class="input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M6 21v-2a4 4 0 014-4h4a4 4 0 014 4v2"/></svg>
            <input v-model="form.username" type="text" placeholder="设置用户名" />
          </div>
        </div>
        <div class="field">
          <label>密码</label>
          <div class="input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input v-model="form.password" type="password" placeholder="••••••••" />
          </div>
        </div>
        <div class="field">
          <label>确认密码</label>
          <div class="input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input v-model="form.confirmPassword" type="password" placeholder="••••••••" @keyup.enter="handleRegister" />
          </div>
        </div>
        <button class="btn-register" @click="handleRegister" :disabled="loading">
          {{ loading ? '注册中...' : '注 册' }}
        </button>
        <p class="link">已有账号？<router-link to="/login">去登录</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { register, getEmailCode } from '../http/http.js'

const router = useRouter()
const form = reactive({ email: '', code: '', username: '', password: '', confirmPassword: '' })
const loading = ref(false)
const countdown = ref(0)

async function sendCode() {
  if (!form.email) return alert('请输入邮箱')
  try {
    await getEmailCode(form.email)
    alert('验证码已发送')
    countdown.value = 60
    const t = setInterval(() => { countdown.value--; if (countdown.value <= 0) clearInterval(t) }, 1000)
  } catch (e) { alert('发送失败') }
}

async function handleRegister() {
  if (form.password !== form.confirmPassword) return alert('两次密码不一致')
  loading.value = true
  try {
    await register({ ...form, confirm_password: form.confirmPassword })
    alert('注册成功')
    router.push('/login')
  } catch (e) { alert(e.message || '注册失败') }
  loading.value = false
}
</script>

<style scoped>
.reg-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.bg-orb { position: fixed; border-radius: 50%; pointer-events: none; z-index: 0; }
.orb-1 { width: 500px; height: 500px; top: -150px; left: -100px; background: radial-gradient(circle, rgba(155,109,255,0.1) 0%, transparent 70%); }
.orb-2 { width: 450px; height: 450px; bottom: -120px; right: -80px; background: radial-gradient(circle, rgba(91,127,255,0.08) 0%, transparent 70%); }
.auth-card { position: relative; z-index: 1; width: 440px; padding: 40px; max-height: 90vh; overflow-y: auto; }
.card-header { text-align: center; margin-bottom: 30px; }
.logo-icon { margin-bottom: 14px; display: inline-block; }
.card-header h2 { font-size: 1.5rem; font-weight: 700; margin-bottom: 4px; }
.card-header p { font-size: 0.85rem; color: var(--text-secondary); }
.form { text-align: left; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 0.8rem; color: var(--text-regular); font-weight: 500; margin-bottom: 6px; }
.input-wrap { display: flex; align-items: center; gap: 8px; background: rgba(10,16,40,0.5); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0 12px; transition: all var(--transition); }
.input-wrap:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); }
.input-wrap svg { color: var(--text-secondary); flex-shrink: 0; }
.input-wrap input { flex: 1; height: 40px; background: transparent; border: none; color: var(--text-primary); font-size: 0.88rem; outline: none; width: 100%; }
.input-wrap input::placeholder { color: var(--text-disabled); }
.row { display: flex; gap: 10px; }
.flex { flex: 1; }
.code-btn { height: 42px; padding: 0 18px; background: rgba(91,127,255,0.12); color: var(--primary-light); border: 1px solid rgba(91,127,255,0.2); border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; white-space: nowrap; font-weight: 500; transition: all var(--transition); }
.code-btn:hover { background: rgba(91,127,255,0.2); border-color: rgba(91,127,255,0.35); }
.code-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-register { width: 100%; height: 46px; background: var(--gradient-brand); color: #fff; border: none; border-radius: var(--radius-sm); font-size: 0.95rem; font-weight: 600; margin-top: 12px; letter-spacing: 0.04em; position: relative; overflow: hidden; }
.btn-register::after { content: ""; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent); opacity: 0; transition: opacity var(--transition); }
.btn-register:hover::after { opacity: 1; }
.btn-register:hover { transform: translateY(-1px); box-shadow: var(--shadow-glow); }
.btn-register:disabled { opacity: 0.5; cursor: not-allowed; }
.link { text-align: center; margin-top: 20px; font-size: 0.85rem; color: var(--text-secondary); }
.link a { color: var(--primary-light); text-decoration: none; font-weight: 500; }
.link a:hover { text-decoration: underline; }
</style>

<template>
  <div class="page">
    <div class="card">
      <div class="logo">🎓</div>
      <h2>个性化学习平台</h2>
      <p class="desc">高等教育智能学习助手</p>

      <div class="form">
        <label>邮箱</label>
        <input v-model="email" type="email" placeholder="请输入邮箱" />

        <label>密码</label>
        <input v-model="password" type="password" placeholder="请输入密码" @keyup.enter="handleLogin" />

        <button class="btn" @click="handleLogin" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>
        <p class="link">还没有账号？<router-link to="/register">立即注册</router-link></p>
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
.page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #e8f0fe 0%, #d4e4fc 100%); }
.card { background: #fff; border-radius: 20px; padding: 50px 40px; width: 400px; box-shadow: 0 8px 30px rgba(0,0,0,0.12); text-align: center; }
.logo { font-size: 60px; margin-bottom: 10px; }
h2 { font-size: 24px; color: #303133; margin-bottom: 6px; }
.desc { font-size: 14px; color: #909399; margin-bottom: 30px; }
.form { text-align: left; }
label { display: block; font-size: 14px; color: #606266; margin-bottom: 6px; margin-top: 16px; }
input { width: 100%; height: 44px; border: 1px solid #dcdfe6; border-radius: 8px; padding: 0 14px; font-size: 14px; outline: none; box-sizing: border-box; }
input:focus { border-color: #4A90D9; }
.btn { width: 100%; height: 44px; background: #4A90D9; color: #fff; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin-top: 24px; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.link { text-align: center; margin-top: 20px; font-size: 14px; color: #909399; }
.link a { color: #4A90D9; text-decoration: none; }
</style>
<template>
  <div class="page">
    <div class="card">
      <div class="logo">🎓</div>
      <h2>注册账号</h2>

      <div class="form">
        <label>邮箱</label>
        <div class="row">
          <input v-model="form.email" type="email" placeholder="请输入邮箱" class="flex" />
          <button class="code-btn" @click="sendCode" :disabled="countdown > 0">
            {{ countdown > 0 ? countdown + 's' : '发送验证码' }}
          </button>
        </div>

        <label>验证码</label>
        <input v-model="form.code" type="text" placeholder="请输入验证码" maxlength="4" />

        <label>用户名</label>
        <input v-model="form.username" type="text" placeholder="请输入用户名" />

        <label>密码</label>
        <input v-model="form.password" type="password" placeholder="请输入密码" />

        <label>确认密码</label>
        <input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" />

        <button class="btn" @click="handleRegister" :disabled="loading">
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
.page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #e8f0fe 0%, #d4e4fc 100%); }
.card { background: #fff; border-radius: 20px; padding: 40px; width: 420px; box-shadow: 0 8px 30px rgba(0,0,0,0.12); text-align: center; }
.logo { font-size: 50px; margin-bottom: 6px; }
h2 { font-size: 22px; color: #303133; margin-bottom: 20px; }
.form { text-align: left; }
label { display: block; font-size: 14px; color: #606266; margin-bottom: 6px; margin-top: 14px; }
input { width: 100%; height: 42px; border: 1px solid #dcdfe6; border-radius: 8px; padding: 0 12px; font-size: 14px; outline: none; box-sizing: border-box; }
input:focus { border-color: #4A90D9; }
.row { display: flex; gap: 10px; }
.flex { flex: 1; }
.code-btn { height: 42px; padding: 0 16px; background: #e6f0fa; color: #4A90D9; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; white-space: nowrap; }
.code-btn:disabled { opacity: 0.6; }
.btn { width: 100%; height: 44px; background: #4A90D9; color: #fff; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin-top: 20px; }
.btn:disabled { opacity: 0.6; }
.link { text-align: center; margin-top: 18px; font-size: 14px; color: #909399; }
.link a { color: #4A90D9; text-decoration: none; }
</style>
<template>
  <div class="page">
    <header class="topbar">
      <h1>🎓 个性化学习平台</h1>
      <div class="topbar-right">
        <span class="user">你好，{{ username }}</span>
        <button class="logout-btn" @click="logout">退出登录</button>
      </div>
    </header>

    <div class="grid">
      <div class="card" @click="router.push('/profile')">
        <span class="icon">📊</span>
        <h3>学习画像</h3>
        <p>AI对话构建专属画像</p>
      </div>
      <div class="card" @click="router.push('/resources')">
        <span class="icon">📚</span>
        <h3>资源中心</h3>
        <p>AI生成课程文档</p>
      </div>
      <div class="card" @click="router.push('/learning-path')">
        <span class="icon">🗺️</span>
        <h3>学习路径</h3>
        <p>个性化路径规划</p>
      </div>
    </div>

    <div class="section">
      <h2>⚡ 快速操作</h2>
      <button class="btn" @click="router.push('/resources')">生成学习资源</button>
      <button class="btn outline" @click="router.push('/learning-path')">查看学习路径</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('同学')

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
.page { max-width: 800px; margin: 0 auto; padding: 20px; }
.topbar { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; }
.topbar h1 { font-size: 24px; color: #303133; }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.user { font-size: 14px; color: #909399; }
.logout-btn { padding: 6px 16px; background: #f56c6c; color: #fff; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
.logout-btn:hover { background: #e04040; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.card { background: #fff; border-radius: 14px; padding: 24px 18px; text-align: center; cursor: pointer; box-shadow: var(--shadow); transition: transform 0.2s; }
.card:hover { transform: translateY(-2px); }
.icon { font-size: 40px; display: block; margin-bottom: 10px; }
h3 { font-size: 16px; color: #303133; margin-bottom: 4px; }
.card p { font-size: 12px; color: #909399; }
.section { background: #fff; border-radius: 14px; padding: 20px; margin-bottom: 20px; box-shadow: var(--shadow); }
.section h2 { font-size: 18px; margin-bottom: 14px; }
.btn { width: 100%; height: 44px; background: #4A90D9; color: #fff; border: none; border-radius: 10px; font-size: 15px; cursor: pointer; margin-bottom: 10px; }
.btn.outline { background: #e6f0fa; color: #4A90D9; }
</style>
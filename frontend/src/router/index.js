import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/home', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/profile', name: 'Profile', component: () => import('../views/Profile.vue') },
  { path: '/learning-path', name: 'LearningPath', component: () => import('../views/LearningPath.vue') },
  { path: '/resources', name: 'Resources', component: () => import('../views/Resources.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Â·ÓÉÊØÎÀ£ºÎ´µÇÂ¼Ìø×ªµÇÂ¼Ò³

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && to.path !== '/register' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
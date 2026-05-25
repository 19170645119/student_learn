const BASE_URL = 'http://127.0.0.1:8000'

const request = async (url, options = {}) => {
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = 'Bearer ' + token

  const res = await fetch(BASE_URL + url, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '请求失败')
  }
  return res.json()
}

const get = (url, params) => {
  const query = params ? '?' + new URLSearchParams(params).toString() : ''
  return request(url + query)
}
const post = (url, data) => request(url, { method: 'POST', body: JSON.stringify(data) })
const put = (url, data) => request(url, { method: 'PUT', body: JSON.stringify(data) })

// Auth
export const login = (email, password) => post('/auth/login', { email, password })
export const register = (data) => post('/auth/register', data)
export const getEmailCode = (email) => get('/auth/code', { email })

// Profile
export const getProfile = () => get('/profile/')
export const updateProfile = (data) => put('/profile/', data)
export const chatProfile = (message) => post('/profile/chat', { message })

// Resources
export const getResources = (type) => get('/resource/', type ? { resource_type: type } : {})
export const getResourceDetail = (id) => get('/resource/' + id)
export const generateResources = (data) => post('/resource/generate', data)
export const getChapters = () => get('/resource/chapters/list')

// Learning Path
export const getLearningPath = () => get('/learning-path/')
export const generateLearningPath = () => post('/learning-path/generate')
export const getRecommendResources = () => get('/learning-path/recommend')
const BASE_URL = 'http://127.0.0.1:8000'

const request = async (url, options = {}) => {
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = 'Bearer ' + token

  const res = await fetch(BASE_URL + url, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const msg = Array.isArray(err.detail) ? err.detail.map(d => d.msg || JSON.stringify(d)).join('; ') : (err.detail || '请求失败')
    throw new Error(msg)
  }
  return res.json()
}

const get = (url, params) => {
  const query = params ? '?' + new URLSearchParams(params).toString() : ''
  return request(url + query)
}
const post = (url, data) => request(url, { method: 'POST', body: JSON.stringify(data) })
const put = (url, data) => request(url, { method: 'PUT', body: JSON.stringify(data) })
const del = (url) => request(url, { method: 'DELETE' })

// Auth
export const login = (email, password) => post('/auth/login', { email, password })
export const register = (data) => post('/auth/register', data)
export const getEmailCode = (email) => get('/auth/code', { email })

// Profile
export const getProfile = () => get('/profile/')
export const updateProfile = (data) => put('/profile/', data)
export const chatProfile = (message) => post('/profile/chat', { message })

// Resources
export const getDocs = () => get('/resource/', { resource_type: 'doc' })
export const getChapters = () => get('/resource/chapters/list')
export const generateDoc = (chapterId, userQuery = null) => {
  const body = { chapter_id: chapterId, resource_types: ['doc'] }
  if (userQuery) body.user_query = userQuery
  return post('/resource/generate', body)
}

export const resourcePing = async (message) => {
  const token = localStorage.getItem("token")
  const res = await fetch(BASE_URL + "/resource/ping", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
    body: JSON.stringify({ message, session_id: 1 }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export const resourceChat = async (message, sessionId = null) => {
  const token = localStorage.getItem('token')
  const body = { message }
  if (sessionId) body.session_id = sessionId
  const res = await fetch(BASE_URL + '/resource/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token,
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const msg = Array.isArray(err.detail) ? err.detail.map(d => d.msg || JSON.stringify(d)).join('; ') : (err.detail || '请求失败')
    throw new Error(msg)
  }
  return res.json()
}

export const generateDocStream = async (chapterId, userQuery, onChunk, onDone, onError) => {
  const token = localStorage.getItem('token')
  const body = { chapter_id: chapterId, resource_types: ['doc'] }
  if (userQuery) body.user_query = userQuery

  try {
    const res = await fetch(BASE_URL + '/resource/generate/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
      },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || '请求失败')
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.done) onDone(data)
            else if (data.text) onChunk(data.text)
          } catch (e) {}
        }
      }
    }
  } catch (e) {
    if (onError) onError(e)
    else console.error('Stream error:', e)
  }
}

// Resource Sessions
export const getResourceSessions = () => get('/resource/sessions')
export const createResourceSession = (title) => post('/resource/sessions', { title })
export const deleteResourceSession = (id) => del('/resource/sessions/' + id)
export const renameResourceSession = (id, title) => put('/resource/sessions/' + id + '/rename', { title })
export const getResourceSession = (id) => get('/resource/sessions/' + id)

// Learning Path
export const getLearningPath = () => get('/learning-path/')
export const generateLearningPath = () => post('/learning-path/generate')
export const getRecommendResources = () => get('/learning-path/recommend')
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
export const getDocs = () => get('/resource/')
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

export const generateDocStream = async (chapterId, userQuery, onChunk, onDone, onError, resourceTypes = ['doc']) => {
  const token = localStorage.getItem('token')
  const body = { chapter_id: chapterId, resource_types: resourceTypes }
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

// Quiz
export const generateQuiz = (chapterId, userQuery = null, difficulty = "medium", count = 5, questionType = null) => {
  const body = { chapter_id: chapterId, resource_types: ["quiz"] }
  if (userQuery) body.user_query = userQuery
  body.extra = { difficulty, count }
  if (questionType) body.extra.question_type = questionType
  return post("/resource/generate", body)
}
export const gradeQuiz = (resourceId, score, total, answers = []) =>
  request("/resource/" + resourceId + "/grade", {
    method: "PATCH",
    body: JSON.stringify({ score, total, answers }),
  })

// Resource Docs
export const deleteDoc = (id) => del("/resource/" + id)

// Resource Sessions
export const getResourceSessions = () => get('/resource/sessions')
export const createResourceSession = (title) => post('/resource/sessions', { title })
export const deleteResourceSession = (id) => del('/resource/sessions/' + id)
export const renameResourceSession = (id, title) => put('/resource/sessions/' + id + '/rename', { title })
export const getResourceSession = (id) => get('/resource/sessions/' + id)

// Learning Path
export const getLearningPath = () => get('/learning-path/')
export const generateLearningPath = () => post('/learning-path/generate')
export const reviewCode = (resourceId, code, language) =>
  request("/resource/" + resourceId + "/review-code", {
    method: "POST",
    body: JSON.stringify({ code, language }),
  })

export const generateCode = (chapterId, userQuery, language = null) => {
  const body = { chapter_id: chapterId, resource_types: ["code"] }
  if (userQuery) body.user_query = userQuery
  if (language) body.extra = { language }
  return post("/resource/generate", body)
}

export const generateVideoLink = (chapterId, userQuery) =>
  post("/resource/generate", { chapter_id: chapterId, resource_types: ["video_link"], user_query: userQuery })

export const generateVideo = (chapterId, userQuery) =>
  post("/resource/generate", { chapter_id: chapterId, resource_types: ["video"], user_query: userQuery })

// PPT
export const generatePpt = (chapterId, userQuery) => {
  const body = { chapter_id: chapterId, resource_types: ["ppt"] }
  if (userQuery) body.user_query = userQuery
  return post("/resource/generate", body)
}

export const downloadPptx = async (resourceId) => {
  const token = localStorage.getItem('token')
  const res = await fetch(BASE_URL + "/resource/" + resourceId + "/export/pptx", {
    headers: { Authorization: "Bearer " + token },
  })
  if (!res.ok) throw new Error("下载失败")
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "ppt_" + resourceId + ".pptx"
  a.click()
  URL.revokeObjectURL(url)
}

export const getRecommendResources = () => get('/learning-path/recommend')
import axios from 'axios'

const API_BASE_URL = ''
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true // 开启跨域凭证支持
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    config.headers = config.headers || {}

    const adminToken = sessionStorage.getItem('adminToken')
    const userToken = sessionStorage.getItem('token')
    const token = adminToken || userToken

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 打印请求日志
    if (process.env.NODE_ENV === 'development') {
      console.log(`[请求] ${config.method.toUpperCase()} ${config.url}`, config.data || config.params)
    }

    return config
  },
  (error) => {
    console.error('[请求错误]', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 打印响应日志
    if (process.env.NODE_ENV === 'development') {
      console.log(`[响应] ${response.config.url}`, response.data)
    }
    return response
  },
  (error) => {
    console.error('[响应错误]', error)
    // 处理网络错误
    if (!error.response) {
      console.error('网络连接失败，请检查后端服务是否启动或网络是否正常')
      return Promise.reject(new Error('网络连接失败'))
    }
    const status = error.response.status
    // 区分不同角色的401跳转
    if (status === 401) {
      const isAdminPage = window.location.pathname.startsWith('/admin')
      sessionStorage.clear()

      if (isAdminPage) {
        console.error('管理员登录已过期，请重新登录')
        window.location.href = '/admin/login'
      } else {
        console.error('登录已过期，请重新登录')
        window.location.href = '/login'
      }
    }
    // 403权限不足统一处理
    else if (status === 403) {
      const msg = error.response.data?.msg || '您没有权限执行此操作'
      console.error(msg)
    }
    // 500+服务器错误处理
    else if (status >= 500) {
      console.error('服务器内部错误，请稍后重试')
    }
    return Promise.reject(error)
  }
)

export default api

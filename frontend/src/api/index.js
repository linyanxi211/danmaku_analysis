// frontend/src/api/index.js
import axios from 'axios'
//import * as mock from '@/mock'

// 判断是否使用Mock数据
const useMock = false

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    if (useMock) {
      console.log('使用Mock模式，请求:', config.url)
      // 如果是Mock模式，不发送真实请求
      return Promise.reject({ mock: true, config })
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 处理Mock模式
    if (error.mock) {
      // 根据请求URL返回对应的Mock数据
      return handleMockRequest(error.config)
    }
    
    console.error('API错误:', error)
    
    return Promise.reject(error)
  }
)

// 处理Mock请求
const handleMockRequest = (config) => {
  const url = config.url
  const method = config.method
  
  console.log('返回Mock数据:', url)
  
  // 视频相关
  if (url.includes('/video/') && method === 'get') {
    const bvid = url.split('/').pop()
    return Promise.resolve(mock.mockVideoInfo)
  }
  
  // 弹幕相关
  if (url.includes('/danmaku/') && method === 'get') {
    return Promise.resolve({ danmakus: mock.mockDanmakus(), total: 200 })
  }
  
  // 热力图数据
  if (url.includes('/analysis/heatmap/') && method === 'get') {
    return Promise.resolve({ data: mock.mockHeatmapData() })
  }
  
  // 情感曲线
  if (url.includes('/analysis/curve/') && method === 'get') {
    return Promise.resolve({ data: mock.mockCurveData() })
  }
  
  // 高潮时刻
  if (url.includes('/analysis/peaks/') && method === 'get') {
    return Promise.resolve({ peaks: mock.mockPeaks })
  }
  
  // 模型列表
  if (url.includes('/model/list') && method === 'get') {
    return Promise.resolve(mock.mockModelCompare)
  }
  
  // 报告数据
  if (url.includes('/report/') && method === 'get') {
    return Promise.resolve({
      videoInfo: mock.mockVideoInfo,
      summary: mock.mockStats,
      distribution: {
        positive: { count: 15542, ratio: 65 },
        neutral: { count: 5342, ratio: 22 },
        negative: { count: 2963, ratio: 13 }
      },
      peaks: mock.mockPeaks,
      keywords: mock.mockKeywords,
      timeSegments: mock.mockTimeSegments
    })
  }
  
  // 对比数据
  if (url.includes('/compare') && method === 'post') {
    return Promise.resolve({
      a: {
        heatmap: mock.mockHeatmapData(),
        curve: mock.mockCurveData(),
        stats: { positive: 65, neutral: 22, negative: 13, avgSentiment: 0.76, totalDanmaku: 23847 }
      },
      b: {
        heatmap: mock.mockHeatmapData(),
        curve: mock.mockCurveData(),
        stats: { positive: 58, neutral: 25, negative: 17, avgSentiment: 0.68, totalDanmaku: 18734 }
      }
    })
  }
  
  // 默认返回空对象
  return Promise.resolve({})
}

export default api
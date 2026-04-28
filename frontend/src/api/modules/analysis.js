import api from '@/api'

// 开始分析
export const analyzeVideo = (bvid, options = {}) => {
  return api.post('/analyze', { bvid, ...options })
}

// 获取热力图数据
export const getHeatmapData = (bvid) => {
  return api.get(`/analysis/heatmap/${bvid}`)
}

// 获取高潮时刻
export const getPeakMoments = (bvid) => {
  return api.get(`/analysis/peaks/${bvid}`)
}

// 获取情感曲线
export const getSentimentCurve = (bvid) => {
  return api.get(`/analysis/curve/${bvid}`)
}


// 获取对比曲线数据
export function getCompareCurve(bvid) {
  return request.get(`/compare/curve/${bvid}`)
}

// 对比模式分析接口
export function analyzeCompare(url) {
  return request.post('/analyze/compare', { url })
}
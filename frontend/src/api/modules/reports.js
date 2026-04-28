import api from '@/api'

// 获取报告数据
export const getReportData = (bvid) => {
  return api.get(`history/report/${bvid}`)
}

// 导出报告
export const exportReport = (bvid, format) => {
  return api.get(`/report/export/${bvid}`, {
    params: { format },
    responseType: 'blob'
  })
}

// 获取报告历史
export const getReportHistory = () => {
  return api.get('/report/history')
}

// 保存报告
export const saveReport = (data) => {
  return api.post('/report/save', data)
}

// 分享报告
export const shareReport = (reportId) => {
  return api.post(`/report/share/${reportId}`)
}
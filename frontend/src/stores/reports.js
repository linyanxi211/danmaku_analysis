import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getReportData, exportReport } from '@/api/modules/reports'

export const useReportStore = defineStore('report', () => {
  // 状态
  const reportData = ref(null)
  const loading = ref(false)
  const historyList = ref([])
  
  // 获取报告数据
  const fetchReportData = async (bvid) => {
    loading.value = true
    try {
      const data = await getReportData(bvid)
      reportData.value = data
      return data
    } catch (error) {
      console.error('获取报告数据失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 导出报告
  const exportReportFile = async (bvid, format) => {
    try {
      const blob = await exportReport(bvid, format)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `report_${bvid}.${format}`
      link.click()
      window.URL.revokeObjectURL(url)
      return true
    } catch (error) {
      console.error('导出报告失败:', error)
      throw error
    }
  }
  
  // 添加到历史
  const addToHistory = (item) => {
    historyList.value.unshift({
      id: Date.now(),
      ...item,
      time: new Date().toLocaleString()
    })
    if (historyList.value.length > 20) {
      historyList.value.pop()
    }
  }
  
  // 清除报告
  const clearReport = () => {
    reportData.value = null
  }
  
  return {
    reportData,
    loading,
    historyList,
    fetchReportData,
    exportReportFile,
    addToHistory,
    clearReport
  }
})
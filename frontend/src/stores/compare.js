import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getCompareData } from '@/api/modules/compare'

export const useCompareStore = defineStore('compare', () => {
  // 状态
  const videoA = ref(null)
  const videoB = ref(null)
  const compareResult = ref(null)
  const loading = ref(false)
  const historyList = ref([])
  
  // 获取对比数据
  const fetchCompareData = async (bvidA, bvidB) => {
    loading.value = true
    try {
      const result = await getCompareData(bvidA, bvidB)
      compareResult.value = result
      return result
    } catch (error) {
      console.error('获取对比数据失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 设置视频
  const setVideoA = (video) => {
    videoA.value = video
  }
  
  const setVideoB = (video) => {
    videoB.value = video
  }
  
  // 添加对比历史
  const addToHistory = (item) => {
    historyList.value.unshift({
      id: Date.now(),
      ...item,
      time: new Date().toLocaleString()
    })
    if (historyList.value.length > 10) {
      historyList.value.pop()
    }
  }
  
  // 清除对比
  const clearCompare = () => {
    videoA.value = null
    videoB.value = null
    compareResult.value = null
  }
  
  return {
    videoA,
    videoB,
    compareResult,
    loading,
    historyList,
    fetchCompareData,
    setVideoA,
    setVideoB,
    addToHistory,
    clearCompare
  }
})
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAnalysisStore = defineStore('analysis', () => {
  const currentBvid = ref('')
  const heatmapData = ref([])
  const sentimentCurveData = ref([])
  const peaks = ref({
    positive: { time: 0, value: 0, description: '' },
    negative: { time: 0, value: 0, description: '' },
    density: { time: 0, count: 0 }
  })
  const videoInfo = ref(null)
  const totalDanmakus = ref(0)
  const isAnalyzed = ref(false)

  function setAnalysisResult(data) {
    currentBvid.value = data.bvid || ''
    heatmapData.value = data.heatmapData || []
    sentimentCurveData.value = data.curveData || []
    peaks.value = data.peaks || {}
    videoInfo.value = data.videoInfo || null
    totalDanmakus.value = data.totalDanmakus || 0
    isAnalyzed.value = true
  }

  function clearResult() {
    currentBvid.value = ''
    heatmapData.value = []
    sentimentCurveData.value = []
    peaks.value = {
      positive: { time: 0, value: 0, description: '' },
      negative: { time: 0, value: 0, description: '' },
      density: { time: 0, count: 0 }
    }
    videoInfo.value = null
    totalDanmakus.value = 0
    isAnalyzed.value = false
  }

  return {
    currentBvid,
    heatmapData,
    sentimentCurveData,
    peaks,
    videoInfo,
    totalDanmakus,
    isAnalyzed,
    setAnalysisResult,
    clearResult
  }
})
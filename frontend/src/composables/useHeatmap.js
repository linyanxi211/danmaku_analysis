import { ref } from 'vue'

export function useHeatmap() {
  const heatmapData = ref([])
  
  // 处理热力图数据（分桶）
  const processHeatmapData = (danmakus, bucketSize = 10) => {
    const buckets = new Map()
    
    danmakus.forEach(dm => {
      // 时间分桶（每bucketSize秒）
      const timeBucket = Math.floor(dm.time / bucketSize) * bucketSize
      // 情感分层（5层）
      const sentimentLevel = Math.floor(dm.sentiment * 5)
      
      const key = `${timeBucket}-${sentimentLevel}`
      const current = buckets.get(key) || { count: 0, sum: 0 }
      
      current.count += 1
      current.sum += dm.sentiment
      buckets.set(key, current)
    })
    
    // 转换为ECharts格式 [time, sentimentLevel, count]
    const result = []
    buckets.forEach((value, key) => {
      const [time, level] = key.split('-').map(Number)
      result.push([time, level, value.count])
    })
    
    return result
  }
  
  // 增量更新（用于实时弹幕）
  const updateHeatmapIncremental = (danmaku, currentData, bucketSize = 10) => {
    const timeBucket = Math.floor(danmaku.time / bucketSize) * bucketSize
    const sentimentLevel = Math.floor(danmaku.sentiment * 5)
    
    const existing = currentData.find(
      d => d[0] === timeBucket && d[1] === sentimentLevel
    )
    
    if (existing) {
      existing[2] += 1
    } else {
      currentData.push([timeBucket, sentimentLevel, 1])
    }
    
    return currentData
  }
  
  return {
    heatmapData,
    processHeatmapData,
    updateHeatmapIncremental
  }
}
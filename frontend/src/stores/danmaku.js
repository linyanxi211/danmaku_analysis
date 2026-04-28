import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getSegmentDanmakus, getDanmakuStats, searchDanmakus } from '@/api/modules/danmaku'

export const useDanmakuStore = defineStore('danmaku', () => {
  // ==================== 状态 ====================
  
  /** 当前视频的弹幕列表 */
  const danmakus = ref([])
  
  /** 当前选中的时间段弹幕 */
  const segmentDanmakus = ref([])
  
  /** 弹幕统计信息 */
  const stats = ref({
    total_count: 0,
    time_range: { min: 0, max: 0 },
    sentiment_distribution: { positive: 0, neutral: 0, negative: 0 },
    avg_sentiment: 0,
    top_keywords: []
  })
  
  /** 当前选中的时间段 */
  const currentSegment = ref({ start: 0, end: 0 })
  
  /** 加载状态 */
  const loading = ref(false)
  
  /** 当前页码 */
  const currentPage = ref(1)
  
  /** 每页数量 */
  const pageSize = ref(100)
  
  /** 总弹幕数 */
  const total = ref(0)
  
  /** 当前搜索关键词 */
  const searchKeyword = ref('')
  
  /** 当前情感筛选 */
  const sentimentFilter = ref('all')

  // ==================== 计算属性 ====================
  
  /** 过滤后的弹幕（根据情感和搜索） */
  const filteredDanmakus = computed(() => {
    let filtered = [...danmakus.value]
    
    // 情感筛选
    if (sentimentFilter.value !== 'all') {
      filtered = filtered.filter(dm => {
        if (sentimentFilter.value === 'positive') return dm.sentiment_tag === 'positive'
        if (sentimentFilter.value === 'neutral') return dm.sentiment_tag === 'neutral'
        if (sentimentFilter.value === 'negative') return dm.sentiment_tag === 'negative'
        return true
      })
    }
    
    // 搜索筛选
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      filtered = filtered.filter(dm => 
        dm.content.toLowerCase().includes(keyword)
      )
    }
    
    return filtered
  })
  
  /** 情感分布统计 */
  const sentimentStats = computed(() => {
    const pos = danmakus.value.filter(d => d.sentiment_tag === 'positive').length
    const neu = danmakus.value.filter(d => d.sentiment_tag === 'neutral').length
    const neg = danmakus.value.filter(d => d.sentiment_tag === 'negative').length
    const total = danmakus.value.length
    
    return {
      positive: pos,
      neutral: neu,
      negative: neg,
      positive_ratio: total ? (pos / total * 100).toFixed(1) : 0,
      neutral_ratio: total ? (neu / total * 100).toFixed(1) : 0,
      negative_ratio: total ? (neg / total * 100).toFixed(1) : 0
    }
  })

  // ==================== 方法 ====================
  
  /**
   * 加载指定时间段的弹幕
   * @param {string} bvid - 视频BV号
   * @param {number} start - 开始时间
   * @param {number} end - 结束时间
   */
  const loadSegmentDanmakus = async (bvid, start, end) => {
    loading.value = true
    currentSegment.value = { start, end }
    
    try {
      const res = await getSegmentDanmakus(bvid, start, end, 100)
      segmentDanmakus.value = res.data.danmakus || []
      console.log(`加载时段弹幕成功: ${start}-${end}, ${segmentDanmakus.value.length}条`)
    } catch (error) {
      console.error('加载时段弹幕失败:', error)
      segmentDanmakus.value = []
      ElMessage.error('获取弹幕失败')
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 加载弹幕统计信息
   * @param {string} bvid - 视频BV号
   */
  const loadStats = async (bvid) => {
    try {
      const res = await getDanmakuStats(bvid)
      stats.value = res.data
    } catch (error) {
      console.error('加载统计信息失败:', error)
    }
  }
  
  /**
   * 搜索弹幕
   * @param {string} bvid - 视频BV号
   * @param {string} keyword - 搜索关键词
   */
  const search = async (bvid, keyword) => {
    if (!keyword.trim()) {
      searchKeyword.value = ''
      return
    }
    
    loading.value = true
    searchKeyword.value = keyword
    
    try {
      const res = await searchDanmakus(bvid, keyword, currentPage.value, pageSize.value)
      danmakus.value = res.data.results || []
      total.value = res.data.total || 0
    } catch (error) {
      console.error('搜索弹幕失败:', error)
      ElMessage.error('搜索失败')
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 清除搜索
   */
  const clearSearch = () => {
    searchKeyword.value = ''
  }
  
  /**
   * 设置情感筛选
   * @param {string} filter - 'all'/'positive'/'neutral'/'negative'
   */
  const setSentimentFilter = (filter) => {
    sentimentFilter.value = filter
  }
  
  /**
   * 清除当前时段弹幕
   */
  const clearSegment = () => {
    segmentDanmakus.value = []
    currentSegment.value = { start: 0, end: 0 }
  }
  
  /**
   * 清除所有数据
   */
  const clearAll = () => {
    danmakus.value = []
    segmentDanmakus.value = []
    stats.value = {
      total_count: 0,
      time_range: { min: 0, max: 0 },
      sentiment_distribution: { positive: 0, neutral: 0, negative: 0 },
      avg_sentiment: 0,
      top_keywords: []
    }
    currentSegment.value = { start: 0, end: 0 }
    searchKeyword.value = ''
    sentimentFilter.value = 'all'
  }

  return {
    // 状态
    danmakus,
    segmentDanmakus,
    stats,
    currentSegment,
    loading,
    currentPage,
    pageSize,
    total,
    searchKeyword,
    sentimentFilter,
    
    // 计算属性
    filteredDanmakus,
    sentimentStats,
    
    // 方法
    loadSegmentDanmakus,
    loadStats,
    search,
    clearSearch,
    setSentimentFilter,
    clearSegment,
    clearAll
  }
})
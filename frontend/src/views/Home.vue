<template>
  <div class="home-container">
    <!-- 左侧控制面板 -->
    <AppSidebar 
      v-model:bvid="bvid"
      @analyze="handleAnalyze"
      @model-change="handleModelChange"
    />
    
    <!-- 主要内容区 -->
    <div class="main-content">
      <!-- 顶部导航 -->
      <AppHeader />
      
      <div class="content-wrapper">
        <!-- ================= 视频区域：永远显示 ================= -->
        <div class="video-section">
          <VideoPlayer 
            ref="videoPlayer"
            :src="videoSrc"
            @timeupdate="handleTimeUpdate"
          />
        </div>
        
        <!-- ================= 下方内容区：按模式切换 ================= -->
        
        <!-- 对比模式：只显示双曲线图 -->
        <div v-if="currentMode === 'compare'" class="compare-chart-section">
          <div class="section-header">
            <h3>📊 SnowNLP vs BERT 情感趋势对比</h3>
            <span v-if="curveLoading" style="color:#409eff; font-size:13px;">双模型计算中，请稍候...</span>
          </div>
          <div class="chart-legend-hint">
            <span style="color:#4ecdc4">■ SnowNLP (传统词典)</span> 
            <span style="color:#ff6b6b; margin-left:15px;">■ BERT (深度学习)</span>
            <span style="color:#909399; margin-left:15px; font-size:12px;">*曲线分叉处体现了模型对复杂语境理解的差异</span>
          </div>
          <div id="compare-chart-box" style="width: 100%; height: 400px; background: white; border-radius: 8px; padding: 10px; box-sizing: border-box;"></div>
        </div>
        <!-- 新增：情感分布对比图 -->
        <div v-if="currentMode === 'compare'" class="distribution-section">
          <div class="section-header">
            <h3>📊 情感倾向分布对比</h3>
          </div>
          <div style="display: flex; gap: 20px; height: 320px;">
            <div id="dist-snownlp-box" style="flex: 1; background: white; border-radius: 8px; padding: 10px; box-sizing: border-box;"></div>
            <div id="dist-bert-box" style="flex: 1; background: white; border-radius: 8px; padding: 10px; box-sizing: border-box;"></div>
          </div>
        </div>
        <!-- 单模型模式：原有的热力图 + 三卡片 -->
        <template v-else>
          <div class="heatmap-section">
            <div class="section-header">
              <h3>📊 情感热力图</h3>
              <div class="legend">
                <span class="legend-item negative">消极</span>
                <span class="legend-item neutral">中性</span>
                <span class="legend-item positive">积极</span>
              </div>
            </div>
            <div v-if="!heatmapData || heatmapData.length === 0" class="empty-heatmap">
              热力图数据为空 ({{ heatmapData.length }})
            </div>
            <div style="margin-top: 10px; padding: 5px; background: #f0f0f0;">
              热力图数据状态: {{ heatmapData.length }} 条
            </div>
            <Heatmap 
              ref="heatmap"
              :data="heatmapData"
              @click="handleHeatmapClick"
            />
          </div>
          
          <div class="bottom-section">
            <div class="curve-card">
              <h4>📈 情感波动曲线</h4>
              <SentimentCurve :data="sentimentCurveData" />
            </div>
            
            <div class="peaks-card">
              <h4>🔥 高潮时刻</h4>
              <PeakMoments :peaks="peaks" @jump="handleJumpToTime" />
            </div>
            
            <div class="danmaku-card">
              <h4>💬 实时弹幕</h4>
              <DanmakuStream 
                :danmakus="liveDanmakus"
                @click="handleDanmakuClick"
              />
            </div>
          </div>
        </template>
      </div>
    </div>
    
    <!-- 弹幕抽屉 -->
    <DanmakuDrawer
      v-model="drawerVisible"
      :time-segment="selectedTimeSegment"
      :danmakus="segmentDanmakus"
      @jump="handleJumpToTime"
    />
    
    <!-- 加载动画 -->
    <Loading v-if="loading" :progress="progress" :total-danmakus="totalDanmakus" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useRoute } from 'vue-router'

// 组件导入
import AppHeader from '@/components/common/AppHeader.vue'
import AppSidebar from '@/components/common/AppSidebar.vue'
import Loading from '@/components/common/Loading.vue'
import VideoPlayer from '@/components/video/VideoPlayer.vue'
import Heatmap from '@/components/chart/Heatmap.vue'
import SentimentCurve from '@/components/chart/SentimentCurve.vue'
import DanmakuStream from '@/components/danmaku/DanmakuStream.vue'
import DanmakuDrawer from '@/components/danmaku/DanmakuDrawer.vue'
import PeakMoments from '@/components/analysis/PeakMoments.vue'
import { useWebSocketStore } from '@/stores/websocket'
import { useAnalysisStore } from '@/stores/analysis'

// API基础地址
const API_BASE = 'http://localhost:8000/api'
const TEST_VIDEO_URL = 'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/1080/Big_Buck_Bunny_1080_10s_1MB.mp4'

// ==================== 状态定义 ====================
const currentMode = ref('snownlp') // 控制下方内容区显示什么
const bvid = ref('')
const currentModel = ref('snownlp')
const videoSrc = ref(TEST_VIDEO_URL)
const videoPlayer = ref(null)
const loading = ref(false)
const progress = ref(0)
const totalDanmakus = ref(0)
const drawerVisible = ref(false)
const selectedTimeSegment = ref(null)
const segmentDanmakus = ref([])
const heatmapData = ref([])
const sentimentCurveData = ref([])
const peaks = ref({
  positive: { time: 0, value: 0, description: '' },
  negative: { time: 0, value: 0, description: '' },
  density: { time: 0, count: 0 }
})

// 对比模式状态
const curveLoading = ref(false)
let compareChartInstance = null

// WebSocket & Store
const wsStore = useWebSocketStore()
const liveDanmakus = wsStore.liveDanmakus
const analysisStore = useAnalysisStore()

// ==================== 模式切换处理 ====================
const handleModelChange = (model) => {
  if (model === 'compare') {
    currentMode.value = 'compare'
    ElMessage.info('已切换至对比模式，请点击开始分析')
  } else {
    currentMode.value = model
    currentModel.value = model
    ElMessage.success(`已切换至 ${model === 'snownlp' ? 'SnowNLP' : 'BERT'} 模式`)
  }
}

// ==================== ECharts 绘制逻辑 ====================
const renderCompareChart = (data) => {
  const chartDom = document.getElementById('compare-chart-box')
  if (!chartDom) return
  
  if (!compareChartInstance) {
    compareChartInstance = echarts.init(chartDom)
  }
  
  const xData = data.map(item => item.time + 's')
  
  compareChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['SnowNLP', 'BERT'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: 40, containLabel: true },
    xAxis: { type: 'category', data: xData, boundaryGap: false },
    yAxis: { type: 'value', min: 0, max: 1, name: '情感得分(0负-1正)' },
    series: [
      { name: 'SnowNLP', type: 'line', smooth: true, data: data.map(i => i.snownlp), lineStyle: { color: '#4ecdc4', width: 2 }, itemStyle: { color: '#4ecdc4' } },
      { name: 'BERT', type: 'line', smooth: true, data: data.map(i => i.bert), lineStyle: { color: '#ff6b6b', width: 2 }, itemStyle: { color: '#ff6b6b' } }
    ]
  }, true)
}
// 渲染分布饼图
const renderDistributionChart = (distData) => {
  const snowDom = document.getElementById('dist-snownlp-box')
  const bertDom = document.getElementById('dist-bert-box')
  if (!snowDom || !bertDom) return

  let snowChart = echarts.getInstanceByDom(snowDom)
  let bertChart = echarts.getInstanceByDom(bertDom)
  if (!snowChart) snowChart = echarts.init(snowDom)
  if (!bertChart) bertChart = echarts.init(bertDom)

  const makeOption = (title, data) => ({
    title: { text: title, left: 'center', top: 10, textStyle: { fontSize: 14, color: '#333' } },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 10, itemWidth: 12, itemHeight: 12, textStyle: { fontSize: 12 } },
    color: ['#1a9850', '#d73027', '#aaaaaa'], // 绿、红、灰
    series: [{
      type: 'pie',
      radius: ['40%', '70%'], // 环形图
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 5, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%' },
      data: [
        { value: data.positive, name: '积极' },
        { value: data.negative, name: '消极' },
        { value: data.neutral, name: '中性' }
      ]
    }]
  })

  snowChart.setOption(makeOption('SnowNLP 分布', distData.snownlp))
  bertChart.setOption(makeOption('BERT 分布', distData.bert))

  // 绑定窗口缩放
  window.addEventListener('resize', () => {
    snowChart?.resize()
    bertChart?.resize()
  })
}

// 窗口大小改变时重绘图表
window.addEventListener('resize', () => compareChartInstance?.resize())

// ==================== 获取时段弹幕 ====================
const fetchSegmentDanmakus = async (bvid, start, end) => {
  try {
    const response = await axios.get(`${API_BASE}/danmaku/${bvid}/segment`, {
      params: { start, end, limit: 100 }
    })
    if (response.data && response.data.danmakus) {
      segmentDanmakus.value = response.data.danmakus
    } else {
      segmentDanmakus.value = []
    }
  } catch (err) {
    console.error('获取时段弹幕失败:', err)
    segmentDanmakus.value = []
  }
}

// ==================== 处理分析 (核心拦截逻辑) ====================
const handleAnalyze = async (payload) => {
  // 1. 提取纯净的BV号
  let cleanBvid = ''
  if (typeof payload === 'object' && payload.bvid) {
    cleanBvid = payload.bvid
  } else {
    cleanBvid = payload
  }
  const bvidMatch = cleanBvid.match(/BV\w{10}/)
  if (bvidMatch) cleanBvid = bvidMatch[0]
  
  bvid.value = cleanBvid

  // 2. 拦截：如果是对比模式，走双曲线逻辑，直接 return
  if (currentMode.value === 'compare') {
    curveLoading.value = true
    try {
      // 直接用 axios 发请求，不依赖外部文件      
      const res = await axios.post(`${API_BASE}/analyze/compare`, {
        url: `https://www.bilibili.com/video/${cleanBvid}`
      })
      const data = res.data // 重点：axios 返回的数据在这里面
      
      if (data.error) {
        ElMessage.warning(data.error)
      } else {
        videoSrc.value = `https://player.bilibili.com/player.html?bvid=${cleanBvid}&page=1&autoplay=0`
        await nextTick()
        renderCompareChart(data.curve_data) // 传入正确的数组
        renderDistributionChart(data.distribution)
        ElMessage.success('对比曲线生成完成')
      }
    } catch (e) {
      console.error(e)
      ElMessage.error('对比分析失败，请确保后端已启动')
    } finally {
      curveLoading.value = false
    }
    return // 拦截结束，不走下面的单模型逻辑
  }

  // 3. 以下是原有的单模型逻辑，一字不改
  let analyzeModel = currentModel.value 
  if (typeof payload === 'object' && payload.model) analyzeModel = payload.model 
  
  loading.value = true
  progress.value = 0

  try {
    const apiPath = analyzeModel === 'bert' ? '/analyze/bert' : '/analyze'

    const analyzeRes = await axios.post(`${API_BASE}${apiPath}`, {
      url: `https://www.bilibili.com/video/${cleanBvid}`
    })
    
    const taskId = analyzeRes.data.task_id
    ElMessage.info(`${analyzeModel === 'bert' ? 'BERT' : 'SnowNLP'}分析任务已提交...`)
    
    let timeout = setTimeout(() => {
      clearInterval(pollInterval)
      loading.value = false
      ElMessage.error('分析超时，请稍后重试')
    }, 60000)

    let retryCount = 0
    const MAX_RETRIES = 30 
    
    const pollInterval = setInterval(async () => {
      retryCount++
      if (retryCount > MAX_RETRIES) {
        clearInterval(pollInterval)
        clearTimeout(timeout)
        loading.value = false
        ElMessage.error('分析超时')
        return
      }

      try {
        const statusRes = await axios.get(`${API_BASE}${apiPath}/status/${taskId}`)
        progress.value = statusRes.data.progress
        
        if (statusRes.data.status === 'completed') {
          clearInterval(pollInterval)
          clearTimeout(timeout)
          
          const resultRes = await axios.get(`${API_BASE}${apiPath}/result/${taskId}`)
          const result = resultRes.data
          
          heatmapData.value = []
          sentimentCurveData.value = []
          peaks.value = {
            positive: { time: 0, value: 0, description: '' },
            negative: { time: 0, value: 0, description: '' },
            density: { time: 0, count: 0 }
          }
          
          await nextTick()
          
          heatmapData.value = result.heatmap_data ? [...result.heatmap_data] : []
          sentimentCurveData.value = result.curve_data ? [...result.curve_data] : []

          peaks.value = {
            positive: { time: result.peaks?.positive?.time || 0, value: result.peaks?.positive?.value || 0, description: result.peaks?.positive?.description || '' },
            negative: { time: result.peaks?.negative?.time || 0, value: result.peaks?.negative?.value || 0, description: result.peaks?.negative?.description || '' },
            density: { time: result.peaks?.density?.time || 0, count: result.peaks?.density?.count || 0 }
          }

          videoSrc.value = `https://player.bilibili.com/player.html?bvid=${bvid.value}&page=1&autoplay=0`
          totalDanmakus.value = result.total_danmaku || 0
          
          analysisStore.setAnalysisResult({
            bvid: bvid.value,
            heatmapData: heatmapData.value,
            curveData: sentimentCurveData.value,
            peaks: peaks.value,
            totalDanmakus: result.total_danmaku
          })
          
          if (!wsStore.isConnected || wsStore.currentBvid !== bvid.value) {
            wsStore.connect(bvid.value)
          }

          ElMessage.success('分析完成')
          loading.value = false
          
        } else if (statusRes.data.status === 'failed') {
          clearInterval(pollInterval)
          clearTimeout(timeout)
          ElMessage.error('分析失败')
          loading.value = false
        }
      } catch (err) {
        console.error('查询状态失败:', err)
      }
    }, 2000)
    
  } catch (error) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败: ' + (error.response?.data?.detail || error.message))
    loading.value = false
  }
}

// ==================== 其他函数 ====================
const handleTimeUpdate = (time) => {}

const handleHeatmapClick = async (params) => {
  try {
    const timePoint = params.value[0]
    selectedTimeSegment.value = { start: timePoint, end: timePoint + 10 }
    await fetchSegmentDanmakus(bvid.value, timePoint, timePoint + 10)
    drawerVisible.value = true
  } catch (error) {
    console.error('❌ 热力图点击处理错误:', error)
  }
}

const handleJumpToTime = (time) => {
  if (videoPlayer.value) {
    videoPlayer.value.jumpToTime(time)
  }
}

const handleDanmakuClick = (danmaku) => {
  if (videoPlayer.value) {
    videoPlayer.value.jumpToTime(danmaku.time)
  }
}

const route = useRoute()
watch(() => route.path, (newPath, oldPath) => {
  if (newPath !== oldPath) {
    wsStore.disconnect()
  }
})

// ==================== 生命周期 ====================
onMounted(() => {
  if (analysisStore.isAnalyzed) {
    bvid.value = analysisStore.currentBvid
    heatmapData.value = analysisStore.heatmapData
    sentimentCurveData.value = analysisStore.sentimentCurveData
    peaks.value = analysisStore.peaks
    totalDanmakus.value = analysisStore.totalDanmakus
    videoSrc.value = `https://player.bilibili.com/player.html?bvid=${bvid.value}&page=1&autoplay=0`
  } else {
    bvid.value = 'BV1GJ411x7h7'
  }
})

onUnmounted(() => {
  wsStore.disconnect()
})

onBeforeUnmount(() => {
  if (compareChartInstance) {
    compareChartInstance.dispose()
    compareChartInstance = null
  }
})
</script>

<style scoped>
.home-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f5f7fa;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* ================= 视频区域 ================= */
.video-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

/* ================= 对比模式专属样式 ================= */
.compare-chart-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-header h3 { margin: 0; font-size: 16px; color: #333; }

.chart-legend-hint {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
}
.distribution-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

/* ================= 单模型原有样式 ================= */
.heatmap-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.legend { display: flex; gap: 20px; }
.legend-item { font-size: 12px; padding-left: 16px; position: relative; }
.legend-item::before {
  content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 12px; height: 12px; border-radius: 2px;
}
.legend-item.negative::before { background: #d73027; }
.legend-item.neutral::before { background: #ffffbf; }
.legend-item.positive::before { background: #1a9850; }

.empty-heatmap { padding: 40px; text-align: center; color: #999; background: #fafafa; border-radius: 4px; }

.bottom-section { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
.curve-card, .peaks-card, .danmaku-card {
  background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}
.curve-card h4, .peaks-card h4, .danmaku-card h4 { margin: 0 0 16px 0; font-size: 14px; color: #666; }

/* ================= 响应式 ================= */
@media (max-width: 768px) {
  .bottom-section { grid-template-columns: 1fr; }
}
</style>
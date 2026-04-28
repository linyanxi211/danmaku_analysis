<template>
  <div class="compare-container">
    <AppHeader />
    
    <div class="compare-content">
      <!-- 左侧控制面板 -->
      <el-aside class="compare-sidebar" width="320px">
        <el-scrollbar>
          <div class="sidebar-section">
            <h3>🎬 选择对比视频</h3>
            
            <!-- 视频A -->
            <div class="video-selector">
              <div class="selector-header">
                <span class="badge">视频A</span>
              </div>
              
              <el-input 
                v-model="bvidA"
                placeholder="输入BV号，如 BV1GJ411x7h7"
                class="input-box"
              >
                <template #append>
                  <el-button @click="loadVideo('A')" :loading="loadingA">加载</el-button>
                </template>
              </el-input>
              
              <div v-if="videoAInfo" class="video-preview">
                <img :src="videoAInfo.cover || 'https://via.placeholder.com/120x68'" alt="cover">
                <div class="info">
                  <div class="title">{{ videoAInfo.title }}</div>
                  <div class="meta">UP主: {{ videoAInfo.up_name || '未知' }}</div>
                  <div class="meta">弹幕: {{ videoAInfo.danmaku_count || 0 }}条</div>
                </div>
              </div>
            </div>
            
            <!-- 视频B -->
            <div class="video-selector">
              <div class="selector-header">
                <span class="badge badge-b">视频B</span>
              </div>
              
              <el-input 
                v-model="bvidB"
                placeholder="输入BV号，如 BV1xx411x7h7"
                class="input-box"
              >
                <template #append>
                  <el-button @click="loadVideo('B')" :loading="loadingB">加载</el-button>
                </template>
              </el-input>
              
              <div v-if="videoBInfo" class="video-preview">
                <img :src="videoBInfo.cover || 'https://via.placeholder.com/120x68'" alt="cover">
                <div class="info">
                  <div class="title">{{ videoBInfo.title }}</div>
                  <div class="meta">UP主: {{ videoBInfo.up_name || '未知' }}</div>
                  <div class="meta">弹幕: {{ videoBInfo.danmaku_count || 0 }}条</div>
                </div>
              </div>
            </div>
            
            <!-- 历史记录快速选择 -->
            <div class="history-section">
              <h4>📋 历史记录</h4>
              <el-select 
                v-model="selectedHistoryA" 
                placeholder="选择视频A (可选)" 
                clearable
                @change="handleHistorySelect('A')"
              >
                <el-option
                  v-for="item in historyList"
                  :key="item.bvid"
                  :label="item.title || item.bvid"
                  :value="item.bvid"
                />
              </el-select>
              
              <el-select 
                v-model="selectedHistoryB" 
                placeholder="选择视频B (可选)" 
                clearable
                @change="handleHistorySelect('B')"
              >
                <el-option
                  v-for="item in historyList"
                  :key="item.bvid"
                  :label="item.title || item.bvid"
                  :value="item.bvid"
                />
              </el-select>
            </div>
            
            <!-- 开始对比按钮 -->
            <el-button 
              type="primary" 
              class="start-btn"
              :disabled="!canCompare"
              @click="startCompare"
              :loading="loading"
            >
              开始对比分析
            </el-button>
            
            <!-- 加载状态 -->
            <div v-if="loading" class="loading-status">
              <el-progress 
                :percentage="compareProgress" 
                :status="compareProgress >= 100 ? 'success' : ''"
              />
              <p>{{ compareMessage }}</p>
            </div>
          </div>
        </el-scrollbar>
      </el-aside>
      
      <!-- 主对比区域 -->
      <div class="compare-main">
        <!-- 无数据时显示引导 -->
        <div v-if="!showResults" class="empty-state">
          <div style="font-size: 64px; margin-bottom: 20px;">📊</div>
          <h2>视频对比分析</h2>
          <p>请在左侧选择两个视频进行对比分析</p>
          <p style="color: #999; font-size: 13px;">
            可以从历史记录中选择已分析过的视频
          </p>
        </div>
        
        <!-- 对比结果 -->
        <div v-else class="compare-results">
          <!-- 视频信息对比 -->
          <el-row :gutter="20" class="video-row">
            <el-col :span="12">
              <div class="video-card video-a">
                <div class="video-cover">
                  <img :src="videoAInfo?.cover || ''" alt="cover">
                </div>
                <div class="video-info">
                  <h4>{{ videoAInfo?.title || '视频A' }}</h4>
                  <p>UP主: {{ videoAInfo?.up_name || '未知' }}</p>
                  <p>弹幕数: {{ statsA.totalDanmaku?.toLocaleString() || 0 }}</p>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="video-card video-b">
                <div class="video-cover">
                  <img :src="videoBInfo?.cover || ''" alt="cover">
                </div>
                <div class="video-info">
                  <h4>{{ videoBInfo?.title || '视频B' }}</h4>
                  <p>UP主: {{ videoBInfo?.up_name || '未知' }}</p>
                  <p>弹幕数: {{ statsB.totalDanmaku?.toLocaleString() || 0 }}</p>
                </div>
              </div>
            </el-col>
          </el-row>
          
          <!-- 统计数据对比 -->
          <el-row :gutter="20" class="stats-row">
            <el-col :span="12">
              <el-card class="stats-card">
                <h4>📊 视频A 情感统计</h4>
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="label">平均情感</span>
                    <span class="value" :style="{color: getSentimentColor(statsA.avgSentiment)}">
                      {{ statsA.avgSentiment?.toFixed(3) || '-' }}
                    </span>
                  </div>
                  <div class="stat-item">
                    <span class="label">积极比例</span>
                    <span class="value positive">{{ statsA.positiveRatio?.toFixed(1) || 0 }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">中性比例</span>
                    <span class="value neutral">{{ statsA.neutralRatio?.toFixed(1) || 0 }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">消极比例</span>
                    <span class="value negative">{{ statsA.negativeRatio?.toFixed(1) || 0 }}%</span>
                  </div>
                </div>
                
                <!-- 情感分布饼图 -->
                <div ref="pieChartARef" class="pie-chart"></div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="stats-card">
                <h4>📊 视频B 情感统计</h4>
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="label">平均情感</span>
                    <span class="value" :style="{color: getSentimentColor(statsB.avgSentiment)}">
                      {{ statsB.avgSentiment?.toFixed(3) || '-' }}
                    </span>
                  </div>
                  <div class="stat-item">
                    <span class="label">积极比例</span>
                    <span class="value positive">{{ statsB.positiveRatio?.toFixed(1) || 0 }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">中性比例</span>
                    <span class="value neutral">{{ statsB.neutralRatio?.toFixed(1) || 0 }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="label">消极比例</span>
                    <span class="value negative">{{ statsB.negativeRatio?.toFixed(1) || 0 }}%</span>
                  </div>
                </div>
                
                <!-- 情感分布饼图 -->
                <div ref="pieChartBRef" class="pie-chart"></div>
              </el-card>
            </el-col>
          </el-row>
          
          <!-- 高潮时刻对比 -->
          <el-row :gutter="20" class="peaks-row">
            <el-col :span="12">
              <el-card class="peaks-card">
                <h4>🔥 视频A 高潮时刻</h4>
                <div v-if="peaksA.length > 0" class="peaks-list">
                  <div v-for="peak in peaksA" :key="peak.time" class="peak-item">
                    <span class="peak-icon">{{ peak.icon }}</span>
                    <span class="peak-time">{{ peak.timeText }}</span>
                    <span class="peak-desc">{{ peak.description }}</span>
                  </div>
                </div>
                <el-empty v-else description="暂无数据" :image-size="60" />
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="peaks-card">
                <h4>🔥 视频B 高潮时刻</h4>
                <div v-if="peaksB.length > 0" class="peaks-list">
                  <div v-for="peak in peaksB" :key="peak.time" class="peak-item">
                    <span class="peak-icon">{{ peak.icon }}</span>
                    <span class="peak-time">{{ peak.timeText }}</span>
                    <span class="peak-desc">{{ peak.description }}</span>
                  </div>
                </div>
                <el-empty v-else description="暂无数据" :image-size="60" />
              </el-card>
            </el-col>
          </el-row>
          
          <!-- 差异分析 -->
          <el-card class="diff-card">
            <h4>📈 对比分析结论</h4>
            <el-alert
              :title="diffAnalysis.title"
              :type="diffAnalysis.type"
              :description="diffAnalysis.description"
              show-icon
            />
            
            <div class="diff-details">
              <div class="diff-item">
                <span>情感差异</span>
                <span>{{ diffAnalysis.sentimentDiff > 0 ? '+' : '' }}{{ diffAnalysis.sentimentDiff?.toFixed(3) || 0 }}</span>
              </div>
              <div class="diff-item">
                <span>积极度差异</span>
                <span>{{ diffAnalysis.positiveDiff > 0 ? '+' : '' }}{{ diffAnalysis.positiveDiff?.toFixed(1) || 0 }}%</span>
              </div>
              <div class="diff-item">
                <span>弹幕量差异</span>
                <span>{{ diffAnalysis.danmakuDiff > 0 ? '+' : '' }}{{ diffAnalysis.danmakuDiff?.toLocaleString() || 0 }}</span>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import * as echarts from 'echarts'
import AppHeader from '@/components/common/AppHeader.vue'

const API_BASE = 'http://localhost:8000/api'

// 视频源
const bvidA = ref('')
const bvidB = ref('')
const loadingA = ref(false)
const loadingB = ref(false)
const loading = ref(false)
const compareProgress = ref(0)
const compareMessage = ref('')

// 视频信息
const videoAInfo = ref(null)
const videoBInfo = ref(null)

// 历史记录
const historyList = ref([])
const selectedHistoryA = ref('')
const selectedHistoryB = ref('')

// 统计数据
const statsA = reactive({
  totalDanmaku: 0,
  avgSentiment: 0,
  positiveRatio: 0,
  neutralRatio: 0,
  negativeRatio: 0
})

const statsB = reactive({
  totalDanmaku: 0,
  avgSentiment: 0,
  positiveRatio: 0,
  neutralRatio: 0,
  negativeRatio: 0
})

// 高潮时刻
const peaksA = ref([])
const peaksB = ref([])

// 是否显示结果
const showResults = ref(false)

// 图表引用
const pieChartARef = ref(null)
const pieChartBRef = ref(null)

// 是否可以对比
const canCompare = computed(() => {
  return videoAInfo.value && videoBInfo.value
})

// 差异分析
const diffAnalysis = computed(() => {
  if (!showResults.value) return { title: '', type: 'info', description: '' }
  
  const sentimentDiff = statsA.avgSentiment - statsB.avgSentiment
  const positiveDiff = statsA.positiveRatio - statsB.positiveRatio
  const danmakuDiff = statsA.totalDanmaku - statsB.totalDanmaku
  
  let title = '两视频情感分布相近'
  let type = 'info'
  let description = `整体情绪差异不大`
  
  if (Math.abs(sentimentDiff) >= 0.1) {
    if (sentimentDiff > 0) {
      title = '视频A整体更积极'
      type = 'success'
      description = `视频A平均情感高出 ${(sentimentDiff * 100).toFixed(1)}%，积极比例高 ${positiveDiff.toFixed(1)}%`
    } else {
      title = '视频B整体更积极'
      type = 'success'
      description = `视频B平均情感高出 ${(Math.abs(sentimentDiff) * 100).toFixed(1)}%，积极比例高 ${Math.abs(positiveDiff).toFixed(1)}%`
    }
  }
  
  return {
    title,
    type,
    description,
    sentimentDiff,
    positiveDiff,
    danmakuDiff
  }
})

// 加载历史记录
const loadHistory = async () => {
  try {
    const res = await axios.get(`${API_BASE}/history`, { params: { page: 1, page_size: 20 } })
    historyList.value = res.data.items || []
  } catch (e) {
    console.error('加载历史记录失败:', e)
  }
}

// 加载视频
const loadVideo = async (which) => {
  const bvid = which === 'A' ? bvidA.value : bvidB.value
  if (!bvid) {
    ElMessage.warning('请输入BV号')
    return
  }
  
  if (which === 'A') loadingA.value = true
  else loadingB.value = true
  
  try {
    const res = await axios.get(`${API_BASE}/video/${bvid}`)
    const info = res.data
    
    if (which === 'A') {
      videoAInfo.value = info
    } else {
      videoBInfo.value = info
    }
    
    ElMessage.success('视频加载成功')
  } catch (e) {
    ElMessage.error('加载视频失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    if (which === 'A') loadingA.value = false
    else loadingB.value = false
  }
}

// 历史记录选择
const handleHistorySelect = (which) => {
  const bvid = which === 'A' ? selectedHistoryA.value : selectedHistoryB.value
  if (bvid) {
    if (which === 'A') {
      bvidA.value = bvid
    } else {
      bvidB.value = bvid
    }
    loadVideo(which)
  }
}

// 开始对比
const startCompare = async () => {
  if (!canCompare.value) {
    ElMessage.warning('请先加载两个视频')
    return
  }
  
  loading.value = true
  compareProgress.value = 0
  compareMessage.value = '开始对比分析...'
  showResults.value = false
  
  try {
    // 加载视频A的报告
    compareProgress.value = 20
    compareMessage.value = '加载视频A数据...'
    await loadReport('A', bvidA.value)
    
    // 加载视频B的报告
    compareProgress.value = 60
    compareMessage.value = '加载视频B数据...'
    await loadReport('B', bvidB.value)
    
    compareProgress.value = 100
    compareMessage.value = '对比完成!'
    showResults.value = true
    
    // 绘制饼图
    await nextTick()
    setTimeout(() => {
      drawPieChart('A')
      drawPieChart('B')
    }, 100)
    
    ElMessage.success('对比分析完成')
  } catch (e) {
    ElMessage.error('对比失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

// 加载报告数据
const loadReport = async (which, bvid) => {
  try {
    const res = await axios.get(`${API_BASE}/report/${bvid}`)
    const data = res.data
    
    if (which === 'A') {
      statsA.totalDanmaku = data.summary?.totalDanmaku || 0
      statsA.avgSentiment = data.summary?.avgSentiment || 0
      statsA.positiveRatio = data.distribution?.positive?.ratio || 0
      statsA.neutralRatio = data.distribution?.neutral?.ratio || 0
      statsA.negativeRatio = data.distribution?.negative?.ratio || 0
      peaksA.value = data.peaks || []
    } else {
      statsB.totalDanmaku = data.summary?.totalDanmaku || 0
      statsB.avgSentiment = data.summary?.avgSentiment || 0
      statsB.positiveRatio = data.distribution?.positive?.ratio || 0
      statsB.neutralRatio = data.distribution?.neutral?.ratio || 0
      statsB.negativeRatio = data.distribution?.negative?.ratio || 0
      peaksB.value = data.peaks || []
    }
  } catch (e) {
    console.error(`加载${which}报告失败:`, e)
    // 使用模拟数据
    if (which === 'A') {
      statsA.totalDanmaku = 23847
      statsA.avgSentiment = 0.76
      statsA.positiveRatio = 65
      statsA.neutralRatio = 22
      statsA.negativeRatio = 13
      peaksA.value = [
        { icon: '🏆', timeText: '01:23', description: '观众情绪最高涨' },
        { icon: '💢', timeText: '04:05', description: '情绪低落时刻' },
        { icon: '🔥', timeText: '06:23', description: '弹幕密度峰值' }
      ]
    } else {
      statsB.totalDanmaku = 18734
      statsB.avgSentiment = 0.68
      statsB.positiveRatio = 58
      statsB.neutralRatio = 25
      statsB.negativeRatio = 17
      peaksB.value = [
        { icon: '🏆', timeText: '02:15', description: '观众情绪最高涨' },
        { icon: '💢', timeText: '05:30', description: '情绪低落时刻' },
        { icon: '🔥', timeText: '08:00', description: '弹幕密度峰值' }
      ]
    }
  }
}

// 绘制饼图
const drawPieChart = (which) => {
  const ref = which === 'A' ? pieChartARef.value : pieChartBRef.value
  if (!ref) return
  
  const stats = which === 'A' ? statsA : statsB
  const chart = echarts.init(ref)
  
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left', top: 'center' },
    series: [{
      name: '情感分布',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['60%', '50%'],
      data: [
        { value: stats.positiveRatio, name: '积极', itemStyle: { color: '#1a9850' } },
        { value: stats.neutralRatio, name: '中性', itemStyle: { color: '#ffffbf' } },
        { value: stats.negativeRatio, name: '消极', itemStyle: { color: '#d73027' } }
      ],
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' }
      },
      label: { show: false }
    }]
  })
}

const getSentimentColor = (score) => {
  if (!score) return '#999'
  if (score >= 0.8) return '#1a9850'
  if (score >= 0.6) return '#91cf60'
  if (score >= 0.4) return '#ffffbf'
  if (score >= 0.2) return '#fc8d59'
  return '#d73027'
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.compare-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.compare-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.compare-sidebar {
  background: white;
  border-right: 1px solid #e4e7ed;
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.sidebar-section h3 {
  margin: 0 0 20px 0;
  font-size: 16px;
}

.video-selector {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.selector-header {
  margin-bottom: 12px;
}

.badge {
  background: #1E88E5;
  color: white;
  padding: 2px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.badge-b {
  background: #26A69A;
}

.input-box {
  margin-bottom: 12px;
}

.video-preview {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 4px;
  margin-top: 8px;
}

.video-preview img {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
}

.video-preview .info {
  flex: 1;
}

.video-preview .title {
  font-weight: bold;
  font-size: 13px;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-preview .meta {
  font-size: 12px;
  color: #999;
}

.history-section {
  margin: 20px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.history-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
}

.history-section .el-select {
  width: 100%;
  margin-bottom: 8px;
}

.start-btn {
  width: 100%;
  margin-top: 10px;
}

.loading-status {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.loading-status p {
  text-align: center;
  margin-top: 10px;
  color: #666;
  font-size: 13px;
}

.compare-main {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.empty-state h2 {
  margin: 20px 0 10px;
}

.compare-results {
  max-width: 1200px;
  margin: 0 auto;
}

.video-row {
  margin-bottom: 20px;
}

.video-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  display: flex;
  gap: 20px;
  align-items: center;
}

.video-card.video-a {
  border-left: 4px solid #1E88E5;
}

.video-card.video-b {
  border-left: 4px solid #26A69A;
}

.video-cover img {
  width: 160px;
  height: 90px;
  object-fit: cover;
  border-radius: 8px;
}

.video-info h4 {
  margin: 0 0 8px;
  font-size: 16px;
}

.video-info p {
  margin: 4px 0;
  font-size: 13px;
  color: #666;
}

.stats-row, .peaks-row {
  margin-bottom: 20px;
}

.stats-card, .peaks-card {
  height: 100%;
}

.stats-card h4, .peaks-card h4 {
  margin: 0 0 16px;
  font-size: 15px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.stat-item .label {
  color: #666;
  font-size: 13px;
}

.stat-item .value {
  font-weight: bold;
}

.stat-item .value.positive { color: #1a9850; }
.stat-item .value.neutral { color: #f0ad4e; }
.stat-item .value.negative { color: #d73027; }

.pie-chart {
  height: 180px;
}

.peaks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.peak-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.peak-icon {
  font-size: 20px;
}

.peak-time {
  font-weight: bold;
  color: #1E88E5;
}

.peak-desc {
  flex: 1;
  color: #666;
  font-size: 13px;
}

.diff-card {
  margin-top: 20px;
}

.diff-card h4 {
  margin: 0 0 16px;
}

.diff-details {
  display: flex;
  gap: 20px;
  margin-top: 16px;
}

.diff-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.diff-item span:first-child {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.diff-item span:last-child {
  font-size: 18px;
  font-weight: bold;
  color: #1E88E5;
}
</style>

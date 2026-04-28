<template>
  <div class="report-page">
    <!-- 顶部操作栏 -->
    <div class="report-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h2>情感分析报告</h2>
      </div>
      <div class="header-right">
        <ExportButton :bvid="bvid" />
        <el-button :icon="Share" @click="shareReport">分享</el-button>
        <el-button type="primary" :icon="Printer" @click="printReport">打印</el-button>
        <!-- <el-button type="success" :icon="Download" @click="downloadPDF">下载PDF</el-button> -->
      </div>
    </div>
    
    <!-- 报告内容（可打印区域） -->
    <div class="report-content" ref="reportContent" id="report-content">
      <!-- 封面 -->
      <div class="report-cover">
        <h1>短视频弹幕情感分析报告</h1>
        <div class="video-info">
          <!--<img :src="videoInfo.cover || 'https://placeholder.pics/300x169/EEEEEE/999999?text=No+Cover'" alt="cover" class="cover-img">-->
          <div class="info">
            <div class="title">{{ videoInfo.title }}</div>
            <div class="meta">
              <span>UP主: {{ videoInfo.up }}</span>
              <span>分析时间: {{ reportTime }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 摘要 -->
      <div class="report-section">
        <h3>📋 分析摘要</h3>
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-card">
              <div class="number">{{ summary.totalDanmaku.toLocaleString() }}</div>
              <div class="label">总弹幕数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-card">
              <div class="number">{{ summary.avgSentiment.toFixed(2) }}</div>
              <div class="label">平均情感</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-card">
              <div class="number">{{ summary.positiveRatio }}%</div>
              <div class="label">积极比例</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-card">
              <div class="number">{{ summary.peakCount }}</div>
              <div class="label">高潮时刻</div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 情感分布 -->
      <div class="report-section">
        <h3>📊 情感分布</h3>
        <el-row :gutter="20">
          <el-col :span="12">
            <div ref="pieChartRef" class="chart pie-chart"></div>
          </el-col>
          <el-col :span="12">
            <div class="distribution-table">
              <div class="table-row header">
                <span>情感类别</span>
                <span>数量</span>
                <span>比例</span>
              </div>
              <div class="table-row">
                <span><span class="dot positive"></span>积极</span>
                <span>{{ distribution.positive.count.toLocaleString() }}</span>
                <span>{{ distribution.positive.ratio }}%</span>
              </div>
              <div class="table-row">
                <span><span class="dot neutral"></span>中性</span>
                <span>{{ distribution.neutral.count.toLocaleString() }}</span>
                <span>{{ distribution.neutral.ratio }}%</span>
              </div>
              <div class="table-row">
                <span><span class="dot negative"></span>消极</span>
                <span>{{ distribution.negative.count.toLocaleString() }}</span>
                <span>{{ distribution.negative.ratio }}%</span>
              </div>
              <div class="table-row total">
                <span>总计</span>
                <span>{{ totalCount.toLocaleString() }}</span>
                <span>100%</span>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 情感热力图 -->
      <div class="report-section">
        <h3>🔥 情感热力图</h3>
        <Heatmap :data="heatmapData" />
        <p class="chart-desc">
          热力图展示了视频播放过程中观众情绪的变化，颜色越深表示该时段弹幕密度越大。
        </p>
      </div>
      
      <!-- 高潮时刻 -->
      <div class="report-section">
        <h3>⏰ 高潮时刻</h3>
        <el-row :gutter="20">
          <el-col :span="8" v-for="peak in peaks" :key="peak.time">
            <div class="peak-card" :class="peak.type">
              <div class="peak-icon">{{ peak.icon }}</div>
              <div class="peak-time">{{ peak.timeText }}</div>
              <div class="peak-value">{{ peak.value }}</div>
              <div class="peak-desc">{{ peak.description }}</div>
              <div class="peak-samples">
                <div v-for="sample in peak.samples" :key="sample" class="sample">
                  "{{ sample }}"
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 关键词云 -->
      <div class="report-section">
        <h3>☁️ 关键词云</h3>
        <el-row :gutter="20">
          <el-col :span="12">
            <div ref="wordcloudRef" class="chart wordcloud-chart"></div>
          </el-col>
          <el-col :span="12">
            <div class="keyword-tables">
              <div class="keyword-table">
                <h4>积极关键词</h4>
                <div class="keyword-list">
                  <el-tag v-for="kw in keywords.positive" :key="kw" type="success" class="keyword-tag">
                    {{ kw }}
                  </el-tag>
                </div>
              </div>
              <div class="keyword-table">
                <h4>消极关键词</h4>
                <div class="keyword-list">
                  <el-tag v-for="kw in keywords.negative" :key="kw" type="danger" class="keyword-tag">
                    {{ kw }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 情感曲线 -->
      <div class="report-section">
        <h3>📈 情感波动曲线</h3>
        <div ref="curveRef" class="chart curve-chart"></div>
        <p class="chart-desc">
          折线图展示了整个视频过程中情感值的连续变化，峰值代表观众情绪高涨的时刻，谷值代表情绪低落的时刻。
        </p>
      </div>
      
      <!-- 模型对比 -->
      <div class="report-section" v-if="modelCompare.length">
        <h3>🧠 模型对比</h3>
        <el-table :data="modelCompare" stripe border class="model-table">
          <el-table-column prop="model" label="模型" />
          <el-table-column prop="accuracy" label="准确率" />
          <el-table-column prop="speed" label="速度(条/秒)" />
          <el-table-column prop="size" label="模型大小" />
        </el-table>
      </div>
      
      <!-- 时间分段分析 -->
      <div class="report-section">
        <h3>⏱️ 时间分段分析</h3>
        <el-table :data="timeSegments" stripe border>
          <el-table-column prop="segment" label="时间段" width="120" />
          <el-table-column prop="sentiment" label="平均情感">
            <template #default="{ row }">
              <span :style="{color: getSentimentColor(row.sentiment)}">
                {{ row.sentiment.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="count" label="弹幕数量" />
        </el-table>
      </div>
      
      <!-- 数据附录 -->
      <div class="report-section appendix">
        <h3>📎 附录</h3>
        <p>完整弹幕数据已导出为CSV文件，包含每条弹幕的时间、内容、情感得分。</p>
        <!--<div class="appendix-links">
          <el-button type="primary" link @click="downloadCSV">
            <el-icon><Download /></el-icon> 下载弹幕数据CSV
          </el-button>
          <el-button type="primary" link @click="downloadExcel">
            <el-icon><Grid /></el-icon> 下载Excel完整报告
          </el-button>
        </div> -->
        <div class="appendix-note">
          <p>生成时间: {{ reportTime }}</p>
          <p>报告ID: {{ reportId }}</p>
          <p>分析引擎: {{ modelUsed }}</p>
        </div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <Loading v-if="loading" :progress="loadProgress" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Share, Printer} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import Heatmap from '@/components/chart/Heatmap.vue'
import AppHeader from '@/components/common/AppHeader.vue'
import Loading from '@/components/common/Loading.vue'
import ExportButton from '@/components/export/ExportButton.vue'
import { useReportStore } from '@/stores/reports'
//import { generatePDF } from '@/utils/pdfGenerators'

const route = useRoute()
const router = useRouter()
const reportStore = useReportStore()

// 状态
const loading = ref(false)
const loadProgress = ref(0)
const reportContent = ref(null)

// 图表引用 (不需要 heatmapRef 和 curveRef 了，因为用了组件和单独变量)
const pieChartRef = ref(null)
const wordcloudRef = ref(null)
const curveRef = ref(null)

// 【关键补充】供组件使用的数据变量
const heatmapData = ref([])
const curveData = ref([])

// 报告信息
const bvid = computed(() => route.params.id || route.query.bvid || 'BV1xx')
const reportId = ref('RPT-' + Date.now().toString(36).toUpperCase())
const reportTime = ref(new Date().toLocaleString())
const modelUsed = ref('BERT微调模型 v2.3')

// 视频信息
const videoInfo = reactive({ title: '', up: '', cover: '', publishTime: '' })

// 摘要数据
const summary = reactive({ totalDanmaku: 0, avgSentiment: 0, positiveRatio: 0, peakCount: 0 })

// 分布数据
const distribution = reactive({
  positive: { count: 0, ratio: 0 },
  neutral: { count: 0, ratio: 0 },
  negative: { count: 0, ratio: 0 }
})

const totalCount = computed(() => {
  return distribution.positive.count + distribution.neutral.count + distribution.negative.count
})

// 高潮时刻
const peaks = ref([])

// 关键词
const keywords = ref({ positive: [], negative: [] })

// 模型对比
const modelCompare = ref([])

// 时间分段分析
const timeSegments = ref([])

// 初始化所有图表
const initCharts = () => {
  nextTick(() => {
    initPieChart()
    initWordcloud()
    initCurveChart()
  })
}

// 饼图
const initPieChart = () => {
  if (!pieChartRef.value) return
  const chart = echarts.init(pieChartRef.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      name: '情感分布',
      type: 'pie',
      radius: '50%',
      data: [
        { value: distribution.positive.count, name: '积极', itemStyle: { color: '#1a9850' } },
        { value: distribution.neutral.count, name: '中性', itemStyle: { color: '#ffffbf' } },
        { value: distribution.negative.count, name: '消极', itemStyle: { color: '#d73027' } }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  })
}

// 词云图
const initWordcloud = () => {
  if (!wordcloudRef.value) return
  
  const wordData = [
    ...keywords.value.positive.map(kw => ({ name: kw, value: Math.random() * 50 + 30 })),
    ...keywords.value.negative.map(kw => ({ name: kw, value: Math.random() * 30 + 10 }))
  ]
  
  const chart = echarts.init(wordcloudRef.value)
  chart.setOption({
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      width: '100%',
      height: '100%',
      sizeRange: [12, 50],
      rotationRange: [-90, 90],
      rotationStep: 45,
      gridSize: 8,
      textStyle: {
        fontFamily: '微软雅黑',
        fontWeight: 'bold',
        color: function(params) {
          const colors = ['#1a9850', '#91cf60', '#ffffbf', '#fc8d59', '#d73027']
          return colors[Math.floor(Math.random() * colors.length)]
        }
      },
      data: wordData
    }]
  })
}

// 情感曲线
const initCurveChart = () => {
  if (!curveRef.value) return
  
  let chartData = []
  if (curveData.value && curveData.value.length > 0) {
    chartData = curveData.value
  } else {
    const times = Array.from({ length: 90 }, (_, i) => i * 10)
    chartData = times.map(t => [t, Math.random() * 0.5 + 0.3])
  }
  
  const chart = echarts.init(curveRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '5%', right: '5%', bottom: '8%', top: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      data: chartData.map(d => {
        const t = d[0]
        const min = Math.floor(t / 60)
        const sec = t % 60
        return `${min}:${sec.toString().padStart(2, '0')}`
      }),
      axisLabel: { rotate: 45, interval: Math.floor(chartData.length / 10) }
    },
    yAxis: { type: 'value', min: 0, max: 1 },
    series: [{
      data: chartData.map(d => d[1]),
      type: 'line',
      smooth: true,
      lineStyle: { color: '#1E88E5', width: 3 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(30,136,229,0.3)' },
        { offset: 1, color: 'rgba(30,136,229,0.01)' }
      ])},
      markPoint: {
        data: [
          { type: 'max', name: '峰值' },
          { type: 'min', name: '谷值' }
        ]
      }
    }]
  })
}

// 工具函数
const getSentimentColor = (score) => {
  if (score >= 0.8) return '#1a9850'
  if (score >= 0.6) return '#91cf60'
  if (score >= 0.4) return '#ffffbf'
  if (score >= 0.2) return '#fc8d59'
  return '#d73027'
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 分享报告
const shareReport = () => {
  navigator.clipboard.writeText(window.location.href)
  ElMessage.success('报告链接已复制到剪贴板')
}

// 打印报告
const printReport = () => {
  window.print()
}

// 下载PDF
// const downloadPDF = async () => {
//   loading.value = true
//   loadProgress.value = 0
  
//   try {
//     const interval = setInterval(() => {
//       if (loadProgress.value >= 90) {
//         clearInterval(interval)
//       } else {
//         loadProgress.value += 10
//       }
//     }, 200)
    
//     await generatePDF('report-content', `情感分析报告_${bvid.value}.pdf`)
    
//     loadProgress.value = 100
//     setTimeout(() => {
//       loading.value = false
//       ElMessage.success('PDF下载成功')
//     }, 500)
//   } catch (error) {
//     loading.value = false
//     ElMessage.error('PDF生成失败')
//   }
// }

// 下载CSV
const downloadCSV = () => {
  const headers = ['时间(秒)', '时间格式化', '弹幕内容', '情感得分', '情感分类']
  const rows = []
  for (let i = 0; i < 100; i++) {
    const time = i * 10
    const sentiment = Math.random()
    const category = sentiment >= 0.6 ? '积极' : sentiment >= 0.4 ? '中性' : '消极'
    rows.push([
      time,
      `${Math.floor(time/60)}:${(time%60).toString().padStart(2,'0')}`,
      `示例弹幕${i}`,
      sentiment.toFixed(3),
      category
    ])
  }
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')
  
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `danmaku_${bvid.value}_${Date.now()}.csv`
  link.click()
  ElMessage.success('CSV文件下载成功')
}

// 下载Excel
const downloadExcel = () => {
  ElMessage.success('Excel报告生成中...')
}

// 加载报告数据
const loadReportData = async () => {
  loading.value = true
  loadProgress.value = 10
  try {
    const data = await reportStore.fetchReportData(bvid.value)
    loadProgress.value = 50
    
    if (data) {
      Object.assign(videoInfo, data.videoInfo || {})
      Object.assign(summary, data.summary || {})
      Object.assign(distribution, data.distribution || {})
      
      if (data.peaks) peaks.value = data.peaks
      if (data.keywords) keywords.value = data.keywords
      if (data.timeSegments) timeSegments.value = data.timeSegments
      
      // 赋值给图表组件
      if (data.heatmapData) heatmapData.value = data.heatmapData
      if (data.curveData) curveData.value = data.curveData
      
      loadProgress.value = 80
    }
    
    // 必须先关闭 Loading，等 DOM 挂载，再画图
    loading.value = false     
    await nextTick() 
    initCharts() 
    
    loadProgress.value = 100
  } catch (error) {
    console.error("❌ 加载报告失败:", error)
    ElMessage.error('加载报告失败')
  } finally {
    loading.value = false 
  }
}

onMounted(() => {
  loadReportData()
  window.addEventListener('resize', () => {
    setTimeout(initCharts, 100)
  })
})
</script>

<style scoped>
.report-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.report-header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.header-right {
  display: flex;
  gap: 12px;
}

.report-content {
  max-width: 1200px;
  margin: 40px auto;
  padding: 40px;
  background: white;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  border-radius: 16px;
}

/* 封面 */
.report-cover {
  text-align: center;
  margin-bottom: 60px;
  padding: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
}

.report-cover h1 {
  font-size: 32px;
  margin-bottom: 30px;
}

.video-info {
  display: flex;
  gap: 30px;
  align-items: center;
  text-align: left;
  background: rgba(255,255,255,0.1);
  padding: 20px;
  border-radius: 12px;
}

.cover-img {
  width: 200px;
  height: 112px;
  object-fit: cover;
  border-radius: 8px;
  border: 2px solid white;
}

.video-info .title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 12px;
}

.video-info .meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
  opacity: 0.9;
}

/* 报告章节 */
.report-section {
  margin: 50px 0;
  page-break-inside: avoid;
}

.report-section h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 24px;
  padding-bottom: 8px;
  border-bottom: 2px solid #1E88E5;
}

/* 摘要卡片 */
.summary-card {
  text-align: center;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 12px;
  transition: transform 0.2s;
}

.summary-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.summary-card .number {
  font-size: 32px;
  font-weight: bold;
  color: #1E88E5;
  margin-bottom: 8px;
}

.summary-card .label {
  font-size: 14px;
  color: #666;
}

/* 分布表格 */
.distribution-table {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row.header {
  background: #f5f5f5;
  font-weight: bold;
  color: #333;
}

.table-row.total {
  background: #f0f7ff;
  font-weight: bold;
}

.dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}

.dot.positive { background: #1a9850; }
.dot.neutral { background: #ffffbf; }
.dot.negative { background: #d73027; }

/* 图表 */
.chart {
  width: 100%;
  height: 300px;
  margin: 20px 0;
}

.pie-chart {
  height: 250px;
}

/*
.heatmap-chart {
  height: 350px;
}
*/
.wordcloud-chart {
  height: 300px;
}

.curve-chart {
  height: 300px;
}

.chart-desc {
  color: #999;
  font-size: 13px;
  margin-top: 8px;
  font-style: italic;
}

/* 高潮卡片 */
.peak-card {
  padding: 20px;
  border-radius: 12px;
  height: 100%;
  transition: transform 0.2s;
}

.peak-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
}

.peak-card.positive {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border-left: 4px solid #1a9850;
}

.peak-card.negative {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  border-left: 4px solid #d73027;
}

.peak-card.density {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-left: 4px solid #1E88E5;
}

.peak-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.peak-time {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.peak-value {
  font-size: 16px;
  color: #666;
  margin-bottom: 12px;
}

.peak-desc {
  font-size: 14px;
  margin-bottom: 16px;
  line-height: 1.5;
}

.peak-samples {
  background: rgba(255,255,255,0.5);
  padding: 12px;
  border-radius: 8px;
}

.sample {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
  font-style: italic;
}

/* 关键词 */
.keyword-tables {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.keyword-table h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  font-size: 13px;
  padding: 4px 12px;
}

/* 模型表格 */
.model-table {
  margin: 20px 0;
}

/* 附录 */
.appendix {
  background: #f8f9fa;
  padding: 30px;
  border-radius: 12px;
  margin-top: 60px;
}

.appendix h3 {
  border-bottom-color: #999;
}

.appendix-links {
  display: flex;
  gap: 20px;
  margin: 20px 0;
}

.appendix-note {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px dashed #ddd;
  color: #999;
  font-size: 12px;
}

/* 打印样式 */
@media print {
  .report-header {
    display: none;
  }
  
  .report-content {
    box-shadow: none;
    padding: 20px;
  }
  
  .peak-card {
    break-inside: avoid;
  }
  
  .chart {
    break-inside: avoid;
  }
}
</style>
<template>
  <div class="training-monitor">
    <h4>📈 训练监控</h4>
    
    <!-- 进度条 -->
    <div class="progress-section">
      <div class="progress-label">
        <span>训练进度</span>
        <span>{{ progress }}%</span>
      </div>
      <el-progress 
        :percentage="progress" 
        :color="progressColors"
        :stroke-width="12"
        striped
        striped-flow
      />
    </div>
    
    <!-- Loss曲线 -->
    <div class="chart-section">
      <div class="chart-label">
        <span>Loss曲线</span>
        <span class="current-value">当前: {{ currentLoss }}</span>
      </div>
      <div ref="lossChartRef" class="mini-chart"></div>
    </div>
    
    <!-- Accuracy曲线 -->
    <div class="chart-section">
      <div class="chart-label">
        <span>准确率曲线</span>
        <span class="current-value">当前: {{ currentAccuracy }}%</span>
      </div>
      <div ref="accChartRef" class="mini-chart"></div>
    </div>
    
    <!-- 训练信息 -->
    <div class="info-grid">
      <div class="info-item">
        <span class="label">当前轮次</span>
        <span class="value">{{ currentEpoch }}/{{ totalEpochs }}</span>
      </div>
      <div class="info-item">
        <span class="label">剩余时间</span>
        <span class="value">{{ remainingTime }}</span>
      </div>
      <div class="info-item">
        <span class="label">学习率</span>
        <span class="value">{{ learningRate }}</span>
      </div>
      <div class="info-item">
        <span class="label">批次</span>
        <span class="value">{{ currentBatch }}/{{ totalBatches }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  progress: {
    type: Number,
    default: 0
  },
  loss: {
    type: Array,
    default: () => []
  },
  accuracy: {
    type: Array,
    default: () => []
  }
})

const lossChartRef = ref(null)
const accChartRef = ref(null)
let lossChart = null
let accChart = null

// 模拟数据
const currentLoss = ref('0.234')
const currentAccuracy = ref('94.2')
const currentEpoch = ref(2)
const totalEpochs = ref(3)
const remainingTime = ref('2m 30s')
const learningRate = ref('2e-5')
const currentBatch = ref(128)
const totalBatches = ref(512)

const progressColors = [
  { color: '#f56c6c', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#5cb87a', percentage: 60 },
  { color: '#1989fa', percentage: 80 },
  { color: '#6f7ad3', percentage: 100 }
]

// 初始化Loss图表
const initLossChart = () => {
  if (!lossChartRef.value) return
  lossChart = echarts.init(lossChartRef.value)
  lossChart.setOption({
    grid: { left: '5%', right: '5%', top: 10, bottom: 10 },
    xAxis: { show: false, type: 'category' },
    yAxis: { show: false, min: 0 },
    series: [{
      data: props.loss.length ? props.loss : [0.8, 0.6, 0.4, 0.35, 0.3, 0.28, 0.25, 0.23],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#f56c6c', width: 2 },
      areaStyle: { color: 'rgba(245,108,108,0.1)' },
      symbol: 'none'
    }]
  })
}

// 初始化准确率图表
const initAccChart = () => {
  if (!accChartRef.value) return
  accChart = echarts.init(accChartRef.value)
  accChart.setOption({
    grid: { left: '5%', right: '5%', top: 10, bottom: 10 },
    xAxis: { show: false, type: 'category' },
    yAxis: { show: false, min: 0, max: 100 },
    series: [{
      data: props.accuracy.length ? props.accuracy : [65, 72, 78, 82, 86, 89, 92, 94],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#67c23a', width: 2 },
      areaStyle: { color: 'rgba(103,194,58,0.1)' },
      symbol: 'none'
    }]
  })
}

onMounted(() => {
  initLossChart()
  initAccChart()
  window.addEventListener('resize', () => {
    lossChart?.resize()
    accChart?.resize()
  })
})

watch(() => props.loss, () => {
  if (lossChart) {
    lossChart.setOption({ series: [{ data: props.loss }] })
  }
})

watch(() => props.accuracy, () => {
  if (accChart) {
    accChart.setOption({ series: [{ data: props.accuracy }] })
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', () => {
    lossChart?.resize()
    accChart?.resize()
  })
  lossChart?.dispose()
  accChart?.dispose()
})
</script>

<style scoped>
.training-monitor {
  margin-top: 20px;
}

.training-monitor h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #666;
}

.progress-section {
  margin-bottom: 20px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
  color: #666;
}

.chart-section {
  margin-bottom: 16px;
}

.chart-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
  color: #666;
}

.current-value {
  color: #1E88E5;
  font-weight: bold;
}

.mini-chart {
  height: 60px;
  width: 100%;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 11px;
  color: #999;
}

.info-item .value {
  font-size: 14px;
  font-weight: bold;
  color: #333;
}
</style>
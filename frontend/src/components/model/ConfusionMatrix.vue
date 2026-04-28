<template>
  <div class="confusion-matrix">
    <!-- 矩阵热力图 -->
    <div ref="matrixRef" class="matrix-chart"></div>
    
    <!-- 指标 -->
    <div class="metrics">
      <div class="metric-item">
        <span class="label">准确率</span>
        <span class="value">{{ metrics.accuracy }}%</span>
      </div>
      <div class="metric-item">
        <span class="label">精确率</span>
        <span class="value">{{ metrics.precision }}%</span>
      </div>
      <div class="metric-item">
        <span class="label">召回率</span>
        <span class="value">{{ metrics.recall }}%</span>
      </div>
      <div class="metric-item">
        <span class="label">F1值</span>
        <span class="value">{{ metrics.f1 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => [
      [85, 8, 7],
      [6, 78, 16],
      [4, 12, 84]
    ]
  }
})

const matrixRef = ref(null)
let chart = null

const metrics = {
  accuracy: 94.2,
  precision: 93.8,
  recall: 94.1,
  f1: 0.939
}

const categories = ['积极', '中性', '消极']

onMounted(() => {
  if (!matrixRef.value) return
  
  chart = echarts.init(matrixRef.value)
  
  const option = {
    tooltip: {
      position: 'top',
      formatter: (params) => {
        return `
          <div>
            <div>真实: ${categories[params.value[1]]}</div>
            <div>预测: ${categories[params.value[0]]}</div>
            <div>数量: ${params.value[2]}</div>
          </div>
        `
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      top: '10%',
      bottom: '10%'
    },
    xAxis: {
      type: 'category',
      data: categories,
      name: '预测类别',
      nameLocation: 'middle',
      nameGap: 25
    },
    yAxis: {
      type: 'category',
      data: categories,
      name: '真实类别',
      nameLocation: 'middle',
      nameGap: 25
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: true,
      inRange: {
        color: ['#ffffff', '#1E88E5']
      }
    },
    series: [{
      name: '混淆矩阵',
      type: 'heatmap',
      data: props.data.flatMap((row, i) => 
        row.map((value, j) => [j, i, value])
      ),
      label: {
        show: true,
        formatter: (params) => params.value[2]
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0,0,0,0.5)'
        }
      }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  window.removeEventListener('resize', () => chart?.resize())
  chart?.dispose()
})
</script>

<style scoped>
.confusion-matrix {
  padding: 8px;
}

.matrix-chart {
  width: 100%;
  height: 200px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-item .label {
  font-size: 11px;
  color: #999;
}

.metric-item .value {
  font-size: 14px;
  font-weight: bold;
  color: #1E88E5;
}
</style>
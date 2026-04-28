<template>
  <div class="curve-container">
    <h4>📈 情感波动曲线</h4>
    <div ref="chartRef" class="curve-chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chart = null

const getOption = () => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const data = params[0]
      return `
        <div>
          <div>时间: ${formatTime(data.value[0])}</div>
          <div>情感值: ${data.value[1].toFixed(2)}</div>
        </div>
      `
    }
  },
  grid: {
    left: '5%',
    right: '5%',
    top: '15%',
    bottom: '15%'
  },
  xAxis: {
    type: 'category',
    data: props.data.map(item => formatTime(item[0])),
    axisLabel: {
      rotate: 30,
      interval: Math.max(0, Math.floor(props.data.length / 15)),       
      color: '#666',      
      fontSize: 11
    }
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 1,
    splitLine: {
      lineStyle: {
        type: 'dashed'
      }
    }
  },
  series: [{
    data: props.data.map(item => item[1]),
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: {
      width: 3,
      color: '#1E88E5'
    },
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(30,136,229,0.3)' },
        { offset: 1, color: 'rgba(30,136,229,0.01)' }
      ])
    },
    markPoint: {
      data: [
        { type: 'max', name: '峰值' },
        { type: 'min', name: '谷值' }
      ]
    }
  }]
})

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onMounted(() => {
  chart = echarts.init(chartRef.value)
  chart.setOption(getOption())
  
  window.addEventListener('resize', () => chart.resize())
})

// 在 SentimentCurve.vue 中
watch(() => props.data, (newData) => {
  console.log('曲线收到新数据:', newData)
  if (chart && newData && newData.length > 0) {
    // 同时更新X轴和Y轴数据
    chart.setOption({
      xAxis: {
        data: newData.map(item => formatTime(item[0]))  // 更新X轴
      },
      series: [{
        data: newData.map(item => item[1])  // 更新Y轴数据
      }]
    })
    console.log('曲线更新完成')
  }
}, { deep: true, immediate: true })

onUnmounted(() => {
  window.removeEventListener('resize', () => chart.resize())
  chart?.dispose()
})
</script>

<style scoped>
.curve-container {
  margin-top: 20px;
}

.curve-container h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #666;
}

.curve-chart {
  width: 100%;
  height: 150px;
}
</style>
<template>
  <div class="heatmap-container">
    <div class="heatmap-header">
      <h3>📊 情感热力图</h3>
      <div class="legend">
        <span class="legend-item negative">消极</span>
        <span class="legend-item neutral">中性</span>
        <span class="legend-item positive">积极</span>
      </div>
    </div>
    <div ref="chartRef" class="heatmap-chart"></div>
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
console.log('📦 Heatmap 组件初始化, 初始数据:', props.data)
console.log('📦 初始数据长度:', props.data?.length)

const emit = defineEmits(['click'])

const chartRef = ref(null)
let chart = null

const formatTime = (seconds) => {
   // 如果 seconds 不是数字或无效，返回默认值
  if (seconds === undefined || seconds === null || isNaN(seconds)) {
    return '0:00'
  }
  
  // 确保是数字
  const totalSeconds = Number(seconds)
  if (isNaN(totalSeconds)) {
    return '0:00'
  }
  

  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const handleResize = () => {
  chart?.resize()
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  
  const baseOption = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const time = params.value[0]
        const level = params.value[1]
        const count = params.value[2]
        return `
          <div>
            <div>时间: ${formatTime(time)}</div>
            <div>情感层级: ${level}</div>
            <div>弹幕数: ${count}条</div>
          </div>
        `
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      top: '10%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      name: '视频时间',
      nameLocation: 'middle',
      nameGap: 30,
      data: [],
      axisLabel: {
        formatter: (value) => formatTime(parseInt(value))
      }
    },
    yAxis: {
      type: 'category',
      name: '情感强度',
      data: ['消极', '偏消极', '中性', '偏积极', '积极'],
      axisLabel: {
        fontSize: 12
      }
    },

    // grid: {
    //       top: 30,           // 距离顶部的距离
    //       bottom: 60,        // 距离底部的距离（给 X 轴标签留位置）
    //       left: 80,          // 距离左侧距离（给 Y 轴标签留位置）
    //       right: 100,        // 距离右侧距离（给 visualMap 图例留位置）
    //       containLabel: false // 设为 false，严格按上面的像素值控制边界
    //     },

    visualMap: {
      min: 0,
      max: 4,         // ✅ 改成 4！因为后端传过来的 Y 轴数据最大就是 4
      calculable: true,
      inRange: {
        // 顺序：对应 0(消极)->1->2(中性)->3->4(积极)
        color: ['#d73027', '#fc8d59', '#ffffbf', '#91cf60', '#1a9850'] 
      },
      text: ['积极', '消极'] // 加上左右提示，体验更好
    },
    series: [{
      name: '情感热力图',
      type: 'heatmap',
      data: props.data || [],
      label: { show: false }
    }]
  }
  
  chart.setOption(baseOption)
  
  chart.on('click', (params) => {
    emit('click', params)
  })
}

// 监听数据变化
watch(() => props.data, (newData) => {
  console.log('🔥 watch 触发, 数据长度:', newData?.length)
  
  if (!chart || !newData || newData.length === 0) return

  // 1. 获取时间点
  const timePoints = [...new Set(newData.map(item => item[0]))].sort((a, b) => a - b)
  
  // 2. 创建映射
  const timeIndexMap = {}
  timePoints.forEach((time, index) => { timeIndexMap[time] = index })
  
  // 3. 映射数据
  const mappedData = newData.map(item => [
    timeIndexMap[item[0]],
    item[1],
    item[2]
  ])
  
  // 4. 计算数据范围
  const values = mappedData.map(item => item[2])
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  
  // 5. 格式化时间
  const formattedTimes = timePoints.map(t => {
    const mins = Math.floor(t / 60)
    const secs = Math.floor(t % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  })
  
  // 6. 设置完整配置
  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const time = params.value[0]
        const level = params.value[1]
        const count = params.value[2]
        return `
          <div>
            <div>时间: ${formattedTimes[time]}</div>
            <div>情感层级: ${level}</div>
            <div>弹幕数: ${count}条</div>
          </div>
        `
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      top: '10%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: formattedTimes,
      axisLabel: { rotate: 30 }
    },
    yAxis: {
      type: 'category',
      data: ['消极', '偏消极', '中性', '偏积极', '积极'],
    },
    visualMap: {
      min: minValue,
      max: maxValue,
      calculable: true,
      inRange: {
        color: ['#d73027', '#fc8d59', '#ffffbf', '#91cf60', '#1a9850']
      }
    },
    series: [{
      type: 'heatmap',
      data: mappedData,
      label: { show: false }
    }]
  }, { notMerge: true })
  
  // 7. 重新绑定点击事件
  chart.off('click')
  chart.on('click', (params) => {
    const originalTime = timePoints[params.value[0]]
    emit('click', {
      ...params,
      value: [originalTime, params.value[1], params.value[2]]
    })
  })
  
  console.log('✅ 图表更新完成')
}, { deep: true })
onMounted(() => {
  console.log('Heatmap组件挂载')
  console.log('📊 挂载时数据:', props.data)
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.off('click')
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.heatmap-container {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.heatmap-chart {
  width: 100%;
  height: 300px;
  min-height: 300px;
}

.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.heatmap-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.legend {
  display: flex;
  gap: 20px;
}

.legend-item {
  font-size: 12px;
  padding-left: 16px;
  position: relative;
}

.legend-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-item.negative::before {
  background: #d73027;
}

.legend-item.neutral::before {
  background: #ffffbf;
}

.legend-item.positive::before {
  background: #1a9850;
}

.heatmap-chart {
  width: 100%;
  height: 300px;
}
</style>
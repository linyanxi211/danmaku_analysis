<template>
  <el-drawer
    v-model="visible"
    :title="drawerTitle"
    size="40%"
    direction="rtl"
    @open="handleOpen"
  >
    <div class="drawer-content">
      <!-- 情感筛选 -->
      <div class="filter-bar">
        <el-radio-group v-model="sentimentFilter" size="small">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="positive">积极</el-radio-button>
          <el-radio-button value="neutral">中性</el-radio-button>
          <el-radio-button value="negative">消极</el-radio-button>
        </el-radio-group>
        
        <el-input
          v-model="searchText"
          placeholder="搜索弹幕"
          :prefix-icon="Search"
          clearable
          size="small"
          style="width: 200px"
        />
      </div>
      
      <!-- 弹幕列表 -->
      <el-table
        :data="filteredDanmakus"
        height="calc(100vh - 250px)"
        stripe
        border
        @row-click="handleRowClick"
        v-loading="loading"
      >
        <el-table-column prop="time_point" label="时间" width="80">
          <template #default="{ row }">
            {{ formatTime(row.time_point) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="content" label="弹幕内容" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="sentiment_score" label="情感" width="80">
          <template #default="{ row }">
            <el-tag :type="getSentimentType(row.sentiment_score)" size="small">
              {{ (row.sentiment_score * 100).toFixed(0) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="60" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              link 
              size="small"
              @click.stop="handleJump(row)"
            >
              跳转
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 空状态 - 当没有数据时显示 -->
      <el-empty v-if="!filteredDanmakus.length" description="暂无弹幕数据" />
      
      <!-- 时段统计 -->
      <div class="segment-stats">
        <div class="stat-item">
          <span class="label">总弹幕</span>
          <span class="value">{{ danmakus.length }}条</span>
        </div>
        <div class="stat-item">
          <span class="label">平均情感</span>
          <span class="value">{{ avgSentiment }}</span>
        </div>
        <div class="stat-item">
          <span class="label">时间段</span>
          <span class="value">{{ timeRange }}</span>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  timeSegment: {
    type: Object,
    default: () => ({ start: 0, end: 0 })
  },
  danmakus: {
    type: Array,
    default: () => []
  }
})

// 在 props 定义后添加
//watch(() => props.danmakus, (newVal) => {
 // if (newVal && newVal.length > 0) {
  //  console.log('📝 第一条弹幕完整数据:', newVal[0])
   // console.log('📝 time_point 值:', newVal[0].time_point)
   // console.log('📝 time_point 类型:', typeof newVal[0].time_point)
 // }
//}, { immediate: true })

const emit = defineEmits(['update:modelValue', 'jump'])

// 状态
const loading = ref(false)
const sentimentFilter = ref('all')
const searchText = ref('')

// 抽屉可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 抽屉标题
const drawerTitle = computed(() => {
  return `⏱️ ${formatTime(props.timeSegment?.start || 0)} - ${formatTime(props.timeSegment?.end || 0)} 时段弹幕`
})

// 时间范围显示
const timeRange = computed(() => {
  return `${formatTime(props.timeSegment?.start || 0)} - ${formatTime(props.timeSegment?.end || 0)}`
})

// 筛选后的弹幕
const filteredDanmakus = computed(() => {
  console.log('📊 计算过滤后的弹幕, 原始数据:', props.danmakus)


  if (props.danmakus && props.danmakus.length > 0) {
  console.log('📝 第一条数据完整结构:', props.danmakus[0])
}

  if (!props.danmakus || !props.danmakus.length){ 
    return []
  }
  
  let filtered = [...props.danmakus]
  
  // 情感筛选
  if (sentimentFilter.value !== 'all') {
    filtered = filtered.filter(dm => {
    const tag = dm.sentiment_tag
    if (sentimentFilter.value === 'positive') return tag === 'positive'
    if (sentimentFilter.value === 'neutral') return tag === 'neutral'
    if (sentimentFilter.value === 'negative') return tag === 'negative'
      return true
    })
  }
  
  // 文本搜索
  if (searchText.value) {
    const searchLower = searchText.value.toLowerCase()
    filtered = filtered.filter(dm => 
      dm.content.toLowerCase().includes(searchLower)
    )
  }
  
  return filtered
})

// 平均情感
const avgSentiment = computed(() => {
  if (!props.danmakus || !props.danmakus.length) return '0.00'
  const sum = props.danmakus.reduce((acc, dm) => acc + (dm.sentiment || 0), 0)
  return (sum / props.danmakus.length).toFixed(2)
})

// 格式化时间
const formatTime = (seconds) => {
  if (seconds === undefined || seconds === null) return '00:00'
  if (typeof seconds === 'string') seconds = parseFloat(seconds)
  if (isNaN(seconds)) return '0:00'
  
  // 如果是字符串，尝试转换
  //if (typeof seconds === 'string') {
   // seconds = parseFloat(seconds)
  //}
  
  // 如果不是数字或无效
  //if (isNaN(seconds)) {
  //  console.warn('⚠️ 无效的时间值:', seconds)
   // return '0:00'
 // }

  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 获取情感类型
const getSentimentType = (score) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'info'
  if (score >= 0.4) return 'warning'
  return 'danger'
}

// 行点击
const handleRowClick = (row) => {
  ElMessage.info(`跳转到 ${formatTime(row.time)}`)
}

// 跳转
const handleJump = (row) => {
  console.log('1️⃣ 抽屉发出跳转, 时间:', row.time_point)
  emit('jump', row.time_point)
}

// 抽屉打开事件

const handleOpen = () => {
  console.log('抽屉打开', props.timeSegment)
  console.log('弹幕数据:', props.danmakus)
}

</script>

<style scoped>
.drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0 4px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 8px 0;
}

.segment-stats {
  margin-top: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-item .label {
  color: #999;
  font-size: 13px;
}

.stat-item .value {
  color: #333;
  font-weight: bold;
}

:deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-drawer__body) {
  padding: 16px 20px;
}
</style>
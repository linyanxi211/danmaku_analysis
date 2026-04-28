<template>
  <div class="danmaku-stream">
    <div class="stream-header">
      <span class="live-badge">🔴 LIVE</span>
      <span class="stream-title">实时弹幕流</span>
      <span class="stream-count">{{ liveCount }}条/分钟</span>
      <el-switch v-model="autoScroll" size="small" active-text="自动滚动" />
    </div>
    
    <div class="stream-list" ref="listRef">
      <transition-group name="danmaku">
        <div 
          v-for="dm in displayedDanmakus" 
          :key="dm.id" 
          class="stream-item"
          @click="handleClick(dm)"
        >
          <span class="time">[{{ formatTime(dm.time) }}]</span>
          <span class="text">{{ dm.text }}</span>
          <el-tag :type="getSentimentType(dm.sentiment)" size="small" effect="light">
            {{ formatSentiment(dm.sentiment_score) }}
          </el-tag>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useWebSocketStore } from '@/stores/websocket'

const props = defineProps({
  danmakus: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['click'])

const wsStore = useWebSocketStore()
const { liveCount } = storeToRefs(wsStore)

const autoScroll = ref(true)
const listRef = ref(null)
const displayedDanmakus = ref([])

// ⭐ 新增：格式化情感值，处理 NaN 和 undefined
const formatSentiment = (score) => {
  if (score === undefined || score === null || isNaN(score)) {
    return 'N/A'
  }
  return (score * 100).toFixed(0)
}

const getSentimentType = (score) => {
  if (score === undefined || score === null || isNaN(score)) {
    return 'info'  // 使用灰色标签
  }
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'info'
  if (score >= 0.4) return 'warning'
  return 'danger'
}

// 显示最近50条
watch(() => props.danmakus, (newVal) => {
  displayedDanmakus.value = newVal.slice(-50)
  
  if (autoScroll.value) {
    nextTick(() => {
      const list = listRef.value
      list.scrollTop = list.scrollHeight
    })
  }
}, { deep: true })

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}


const handleClick = (danmaku) => {
  emit('click', danmaku)
}
</script>

<style scoped>
.danmaku-stream {
  background: white;
  border-radius: 8px;
  padding: 16px;
  height: 300px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.stream-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.live-badge {
  background: #f56c6c;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

.stream-title {
  font-weight: bold;
  color: #333;
}

.stream-count {
  color: #999;
  font-size: 12px;
  margin-left: auto;
}

.stream-list {
  flex: 1;
  overflow-y: auto;
  font-size: 13px;
}

.stream-item {
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.stream-item:hover {
  background: #f5f7fa;
}

.time {
  color: #999;
  font-family: monospace;
}

.text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 动画 */
.danmaku-enter-active,
.danmaku-leave-active {
  transition: all 0.3s ease;
}

.danmaku-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.danmaku-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.danmaku-move {
  transition: transform 0.3s;
}
</style>
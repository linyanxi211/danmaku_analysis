<template>
  <div class="peak-moments">
    <h3>🔥 高潮时刻</h3>
    
    <div class="peaks-list">
      <!-- 最积极 -->
      <div class="peak-card positive">
        <div class="peak-icon">🏆</div>
        <div class="peak-content">
          <div class="peak-time" @click="jumpTo(positivePeak.time)">
            {{ formatTime(positivePeak.time) }}
          </div>
          <div class="peak-value">情感 {{ (positivePeak.value * 100).toFixed(0) }}</div>
          <div class="peak-desc">{{ positivePeak.description }}</div>
        </div>
      </div>
      
      <!-- 最消极 -->
      <div class="peak-card negative">
        <div class="peak-icon">💢</div>
        <div class="peak-content">
          <div class="peak-time" @click="jumpTo(negativePeak.time)">
            {{ formatTime(negativePeak.time) }}
          </div>
          <div class="peak-value">情感 {{ (negativePeak.value * 100).toFixed(0) }}</div>
          <div class="peak-desc">{{ negativePeak.description }}</div>
        </div>
      </div>
      
      <!-- 弹幕峰值 -->
      <div class="peak-card density">
        <div class="peak-icon">📊</div>
        <div class="peak-content">
          <div class="peak-time" @click="jumpTo(densityPeak.time)">
            {{ formatTime(densityPeak.time) }}
          </div>
          <div class="peak-value">{{ densityPeak.count }}条弹幕</div>
          <div class="peak-desc">弹幕峰值时刻</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useVideoStore } from '@/stores/video'

const props = defineProps({
  peaks: {
    type: Object,
    default: () => ({
      positive: { time: 0, value: 0, description: '' },
      negative: { time: 0, value: 0, description: '' },
      density: { time: 0, count: 0 }
    })
  }
})

const emit = defineEmits(['jump'])
const videoStore = useVideoStore()

const positivePeak = computed(() => props.peaks.positive)
const negativePeak = computed(() => props.peaks.negative)
const densityPeak = computed(() => props.peaks.density)

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const jumpTo = (time) => {
  videoStore.jumpToTime(time)
  emit('jump', time)
}
</script>

<style scoped>
.peak-moments {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.peak-moments h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #333;
}

.peaks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.peak-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  transition: transform 0.2s;
  cursor: pointer;
}

.peak-card:hover {
  transform: translateX(5px);
}

.peak-card.positive {
  background: rgba(26, 152, 80, 0.1);
  border-left: 4px solid #1a9850;
}

.peak-card.negative {
  background: rgba(215, 48, 39, 0.1);
  border-left: 4px solid #d73027;
}

.peak-card.density {
  background: rgba(30, 136, 229, 0.1);
  border-left: 4px solid #1E88E5;
}

.peak-icon {
  font-size: 24px;
  min-width: 40px;
  text-align: center;
}

.peak-content {
  flex: 1;
}

.peak-time {
  font-weight: bold;
  font-size: 16px;
  color: #333;
  cursor: pointer;
}

.peak-time:hover {
  color: #1E88E5;
  text-decoration: underline;
}

.peak-value {
  font-size: 13px;
  color: #666;
  margin: 2px 0;
}

.peak-desc {
  font-size: 12px;
  color: #999;
}
</style>
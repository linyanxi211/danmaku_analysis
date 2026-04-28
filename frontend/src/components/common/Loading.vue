<template>
  <div class="loading-overlay">
    <div class="loading-content">
      <el-progress 
        type="circle" 
        :percentage="progress" 
        :width="80"
        :stroke-width="6"
        color="#1E88E5"
      />
      <p class="loading-text">分析中... {{ progress }}%</p>
      <p class="loading-tip">正在处理 {{ totalDanmakus }} 条弹幕</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  progress: {
    type: Number,
    default: 0
  },
  totalDanmakus: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-content {
  text-align: center;
  background: white;
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.1);
}

.loading-text {
  margin-top: 20px;
  font-size: 16px;
  font-weight: bold;
  color: #1E88E5;
}

.loading-tip {
  margin-top: 8px;
  font-size: 13px;
  color: #999;
}
</style>
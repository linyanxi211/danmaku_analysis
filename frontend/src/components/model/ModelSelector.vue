<template>
  <div class="model-selector">
    <el-radio-group v-model="selectedModel" @change="handleChange" size="default">
      <el-radio-button value="snownlp">
        <span>SnowNLP (快速)</span>
      </el-radio-button>
      
      <el-radio-button value="bert">
        <span>BERT (精准)</span>
      </el-radio-button>
      
      <el-radio-button value="compare">
        <span>对比模式</span>
      </el-radio-button>
    </el-radio-group>
    
    <!-- 简单的模型说明 -->
    <div class="model-tip">
      <span v-if="selectedModel === 'snownlp'" class="tip-text info">基于词典匹配，速度快</span>
      <span v-else-if="selectedModel === 'bert'" class="tip-text success">基于深度学习，准确率 88.5%，支持反讽识别</span>
      <span v-else class="tip-text warning">将同时运行两种模型并排展示差异</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['change'])

// 默认使用 SnowNLP 保持向后兼容
const selectedModel = ref('snownlp')

const handleChange = (val) => {
  // 将用户选择的模型类型传递给父组件
  emit('change', val)
}

// 暴露给父组件的方法，方便父组件主动获取当前选中的模型
defineExpose({
  getSelectedModel: () => selectedModel.value
})
</script>

<style scoped>
.model-selector {
  width: 100%;
}

.model-tip {
  margin-top: 8px;
  height: 20px;
}

.tip-text {
  font-size: 12px;
}

.tip-text.info {
  color: #909399;
}

.tip-text.success {
  color: #67c23a;
  font-weight: 500;
}

.tip-text.warning {
  color: #e6a23c;
  font-weight: 500;
}
</style>
<template>
  <el-aside class="app-sidebar" :width="isCollapse ? '64px' : '280px'">
    <div class="sidebar-header">
      <el-button 
        :icon="isCollapse ? Expand : Fold" 
        @click="toggleCollapse"
        text
      />
    </div>
    
    <el-scrollbar>
      <!-- 数据源 -->
      <div class="sidebar-section" >
        <h3>📁 数据源</h3>
        <el-radio-group v-model="dataSource" size="small">
          <el-radio-button value="bvid">B站URL</el-radio-button>
          <el-radio-button value="upload" v-if = false>上传文件</el-radio-button>
          <el-radio-button value="kaggle" v-if = false>Kaggle</el-radio-button>
        </el-radio-group>
        
        <div v-if="dataSource === 'bvid'" class="input-wrapper">
          <el-input 
            :model-value="localBvid"
            @update:model-value="handleBvidInput"
            placeholder="输入BV号或视频链接"
            :disabled="loading"
            clearable
          >
            <template #append>
              <el-button :loading="loading" @click="handleAnalyze">
                {{ loading ? '分析中' : '分析' }}
              </el-button>
            </template>
          </el-input>
        </div>
        
        <div v-if="dataSource === 'upload'" class="upload-wrapper">
          <el-upload
            class="upload-box"
            drag
            action="#"
            :before-upload="handleUpload"
            :show-file-list="false"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="upload-text">
              拖拽文件或点击上传
            </div>
            <template #tip>
              <div class="upload-tip">
                支持 .xml .csv 格式的弹幕文件
              </div>
            </template>
          </el-upload>
        </div>
      </div>
      
      <!-- 模型选择 -->
      <div class="sidebar-section">
        <h3>🧠 情感模型</h3>
        <el-select v-model="selectedModel" placeholder="选择模型" @change="handleModelChange" class="model-select">
          <el-option label="SnowNLP (快速)" value="snownlp" />
          <el-option label="BERT (精准)" value="bert" />
          <el-option label="对比模式" value="compare" />
        </el-select>
      </div>
      
      <!-- 分析设置 -->
      <div class="sidebar-section" v-if = false>
        <h3>⚙️ 分析设置</h3>
        <div class="setting-item">
          <span class="setting-label">时间粒度</span>
          <el-radio-group v-model="timeGranularity" size="small">
            <el-radio-button value="5">5s</el-radio-button>
            <el-radio-button value="10">10s</el-radio-button>
            <el-radio-button value="30">30s</el-radio-button>
          </el-radio-group>
        </div>
        
        <div class="setting-item">
          <el-checkbox v-model="options.peak">高潮时刻识别</el-checkbox>
        </div>
        <div class="setting-item">
          <el-checkbox v-model="options.compare">情感对比</el-checkbox>
        </div>
        <div class="setting-item">
          <el-checkbox v-model="options.keyword">关键词提取</el-checkbox>
        </div>
      </div>
      
      <!-- 实时控制 -->
      <div class="sidebar-section" v-if = false>
        <h3>🔴 实时演示</h3>
        <div class="live-control">
          <el-switch v-model="liveMode" size="small" />
          <span class="live-text">{{ liveMode ? '开启' : '关闭' }}</span>
        </div>
        <div v-if="liveMode" class="speed-control">
          <span class="speed-label">速率</span>
          <el-slider v-model="speed" :min="0.5" :max="3" :step="0.5" size="small" />
          <span class="speed-value">{{ speed }}x</span>
        </div>
      </div>
      
      <!-- 导出按钮 -->
      <div class="sidebar-footer" v-if = false>
        <el-button type="primary" :icon="Download" @click="handleExport" class="export-btn">
          导出报告
        </el-button>
      </div>
    </el-scrollbar>
  </el-aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Fold, Expand, UploadFilled, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  bvid: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['analyze', 'model-change', 'update:bvid'])

// 侧边栏折叠状态
const isCollapse = ref(false)

// 数据源
const dataSource = ref('bvid')

// BV号输入
const localBvid = ref(props.bvid)
const loading = ref(false)

// 模型选择
const selectedModel = ref('snownlp')

// 分析设置
const timeGranularity = ref('10')
const options = ref({
  peak: true,
  compare: false,
  keyword: true
})

// 实时控制
const liveMode = ref(false)
const speed = ref(1)

// 监听props变化
watch(() => props.bvid, (newVal) => {
  localBvid.value = newVal
})

// 切换折叠
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 处理BV号输入
const handleBvidInput = (val) => {
  localBvid.value = val
  emit('update:bvid', val)
}

// 处理分析
const handleAnalyze = () => {
  if (!localBvid.value) {
    ElMessage.warning('请输入BV号')
    return
  }
  
  loading.value = true
  emit('analyze', {
    bvid: localBvid.value,
    model: selectedModel.value
  })
  
  // 模拟加载
  setTimeout(() => {
    loading.value = false
    ElMessage.success('分析完成')
  }, 2000)
}

// 处理文件上传
const handleUpload = (file) => {
  ElMessage.success(`文件 ${file.name} 上传成功`)
  return false
}

// 处理模型切换
const handleModelChange = (val) => {
  emit('model-change', val)
  ElMessage.info(`已切换至 ${val === 'snownlp' ? 'SnowNLP' : val === 'bert' ? 'BERT' : '对比模式'}`)
}

// 处理导出
const handleExport = () => {
  ElMessage.info('导出功能开发中')
}
</script>

<style scoped>
.app-sidebar {
  background: white;
  border-right: 1px solid #e4e7ed;
  transition: width 0.3s;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.sidebar-section {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.sidebar-section h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.input-wrapper {
  margin-top: 12px;
}

.upload-wrapper {
  margin-top: 12px;
}

.upload-box {
  width: 100%;
}

.upload-text {
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}

.upload-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.model-select {
  width: 100%;
  margin-top: 8px;
}

.setting-item {
  margin-bottom: 12px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
}

.live-control {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.live-text {
  font-size: 13px;
  color: #666;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.speed-label {
  font-size: 12px;
  color: #999;
  min-width: 40px;
}

.speed-value {
  font-size: 12px;
  color: #1E88E5;
  font-weight: 500;
  min-width: 40px;
}

.sidebar-footer {
  padding: 20px;
  margin-top: auto;
}

.export-btn {
  width: 100%;
}

:deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

:deep(.el-radio-button__inner) {
  padding: 8px 12px;
  font-size: 12px;
}

:deep(.el-checkbox) {
  margin-right: 12px;
}

:deep(.el-slider) {
  flex: 1;
}
</style>
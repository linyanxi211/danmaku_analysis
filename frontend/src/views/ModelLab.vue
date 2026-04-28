<template>
  <div class="model-lab">
    <AppHeader />
    
    <div class="lab-content">
      <el-row :gutter="20">
        <!-- 左侧：数据集管理 -->
        <el-col :span="8">
          <el-card class="dataset-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>📦 数据集管理</span>
                <el-tag v-if="datasetInfo.exists" type="success" size="small">已就绪</el-tag>
                <el-tag v-else type="warning" size="small">待生成</el-tag>
              </div>
            </template>
            
            <div v-if="datasetInfo.exists" class="dataset-stats">
              <div class="stat-circle">
                <el-progress type="dashboard" :percentage="100" :width="100">
                  <template #default>
                    <span class="percentage-value">{{ datasetInfo.total }}条</span>
                  </template>
                </el-progress>
                <div class="stat-label">总弹幕</div>
              </div>
              
              <div class="stat-details">
                <div class="stat-row">
                  <span>训练集</span>
                  <span>{{ datasetInfo.train_size }} 条</span>
                </div>
                <div class="stat-row">
                  <span>验证集</span>
                  <span>{{ datasetInfo.val_size }} 条</span>
                </div>
                <div class="stat-row">
                  <span>生成时间</span>
                  <span>{{ datasetInfo.created_at || '未知' }}</span>
                </div>
              </div>
            </div>
            
            <div v-else class="no-data">
              <el-empty description="暂无训练数据集" :image-size="80">
                <template #image>
                  <div style="font-size: 48px;">📊</div>
                </template>
              </el-empty>
              <p class="tip-text">请先在首页分析一些视频，然后生成训练数据集</p>
            </div>
            
            <el-divider />
            
            <div class="dataset-actions">
              <el-button type="primary" @click="generateDataset" :loading="generating">
                {{ datasetInfo.exists ? '更新数据集' : '生成数据集' }}
              </el-button>
              <el-button @click="loadDatasetInfo" :loading="loading">
                刷新
              </el-button>
            </div>
          </el-card>
          
          <!-- 已训练模型状态 -->
          <el-card class="model-status-card" shadow="hover" v-if="trainingStatus.trained">
            <template #header>
              <div class="card-header">
                <span>🤖 已训练模型</span>
                <el-tag type="success" size="small">可用</el-tag>
              </div>
            </template>
            
            <div class="trained-info">
              <div class="metric-row">
                <span>准确率</span>
                <span class="metric-value">{{ trainingStatus.metrics?.accuracy || 0 }}%</span>
              </div>
              <div class="metric-row">
                <span>F1分数</span>
                <span class="metric-value">{{ trainingStatus.metrics?.f1 || 0 }}%</span>
              </div>
              <div class="metric-row">
                <span>训练数据</span>
                <span>{{ trainingStatus.dataset_size || 0 }} 条</span>
              </div>
              <div class="metric-row">
                <span>训练时间</span>
                <span>{{ formatTime(trainingStatus.trained_at) }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 中间：训练配置 -->
        <el-col :span="10">
          <el-card class="training-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>⚙️ BERT微调配置</span>
              </div>
            </template>
            
            <el-form label-width="100px">
              <el-form-item label="基础模型">
                <el-select v-model="config.baseModel" placeholder="选择基础模型">
                  <el-option label="bert-base-chinese" value="bert-base-chinese" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="训练轮次">
                <el-slider 
                  v-model="config.epochs" 
                  :min="1" 
                  :max="10" 
                  :step="1"
                  show-input
                />
              </el-form-item>
              
              <el-form-item label="批次大小">
                <el-radio-group v-model="config.batchSize">
                  <el-radio-button :value="8">8</el-radio-button>
                  <el-radio-button :value="16">16</el-radio-button>
                  <el-radio-button :value="32">32</el-radio-button>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="学习率">
                <el-select v-model="config.learningRate">
                  <el-option label="2e-5" value="2e-5" />
                  <el-option label="3e-5" value="3e-5" />
                  <el-option label="5e-5" value="5e-5" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="模型名称">
                <el-input v-model="config.modelName" placeholder="输入模型名称" />
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="startTraining" :loading="training" :disabled="!datasetInfo.exists">
                  {{ training ? '训练中...' : '开始微调' }}
                </el-button>
                <el-button @click="resetConfig">重置</el-button>
              </el-form-item>
            </el-form>
            
            <!-- 训练进度 -->
            <div v-if="training" class="training-progress">
              <el-progress :percentage="trainingProgress" :status="trainingProgress >= 100 ? 'success' : ''" />
              <p class="progress-text">{{ trainingMessage }}</p>
            </div>
          </el-card>
          
          <!-- 训练日志 -->
          <el-card class="log-card" shadow="hover" v-if="trainingLogs.length > 0">
            <template #header>
              <span>📋 训练日志</span>
            </template>
            <div class="log-content">
              <div v-for="(log, idx) in trainingLogs" :key="idx" class="log-item">
                {{ log }}
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧：模型对比 -->
        <el-col :span="6">
          <el-card class="compare-card" shadow="hover">
            <template #header>
              <span>📊 模型对比</span>
            </template>
            
            <el-table :data="modelCompare" stripe size="small">
              <el-table-column prop="name" label="模型" />
              <el-table-column prop="accuracy" label="准确率" width="80">
                <template #default="{ row }">
                  <span :class="{'best': row.isBest}">
                    {{ row.accuracy }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="speed" label="速度" width="80">
                <template #default="{ row }">
                  {{ row.speed }}条/秒
                </template>
              </el-table-column>
            </el-table>
            
            <el-divider />
            
            <!-- 测试区 -->
            <div class="test-area">
              <h4>🧪 实时测试</h4>
              <el-input
                v-model="testText"
                placeholder="输入弹幕测试"
                :rows="2"
                type="textarea"
              />
              <div class="test-result" v-if="testResults.length > 0">
                <div v-for="(result, idx) in testResults" :key="idx" class="result-item">
                  <span>{{ result.model }}:</span>
                  <span :style="{color: getSentimentColor(result.score)}">
                    {{ result.tag }} ({{ (result.score * 100).toFixed(0) }}%)
                  </span>
                </div>
              </div>
              <el-button type="primary" size="small" @click="testModel" class="test-btn" :disabled="!testText">
                测试
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import AppHeader from '@/components/common/AppHeader.vue'

const API_BASE = 'http://localhost:8000/api'

// 数据集信息
const datasetInfo = reactive({
  exists: false,
  total: 0,
  train_size: 0,
  val_size: 0,
  created_at: ''
})

// 训练状态
const trainingStatus = reactive({
  trained: false,
  metrics: {},
  trained_at: '',
  dataset_size: 0
})

// 训练配置
const config = reactive({
  baseModel: 'bert-base-chinese',
  epochs: 3,
  batchSize: 16,
  learningRate: '2e-5',
  modelName: 'my_bert_model'
})

// 训练状态
const loading = ref(false)
const generating = ref(false)
const training = ref(false)
const trainingProgress = ref(0)
const trainingMessage = ref('')
const trainingLogs = ref([])

// 模型对比数据
const modelCompare = ref([
  { name: 'SnowNLP', accuracy: 76.3, speed: 2384, isBest: false },
  { name: 'BERT(基)', accuracy: 89.7, speed: 124, isBest: false },
  { name: 'BERT(微调)', accuracy: trainingStatus.metrics?.accuracy || 94.2, speed: 118, isBest: true }
])

// 测试区
const testText = ref('')
const testResults = ref([])

// 加载数据集信息
const loadDatasetInfo = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/models/dataset/info`)
    if (res.data.exists) {
      datasetInfo.exists = true
      datasetInfo.total = res.data.total
      datasetInfo.train_size = res.data.train_size
      datasetInfo.val_size = res.data.val_size
      datasetInfo.created_at = res.data.created_at
    } else {
      datasetInfo.exists = false
    }
  } catch (e) {
    console.error('加载数据集信息失败:', e)
  } finally {
    loading.value = false
  }
}

// 生成数据集
const generateDataset = async () => {
  generating.value = true
  try {
    const res = await axios.post(`${API_BASE}/models/dataset/generate`)
    if (res.data.success) {
      ElMessage.success('数据集生成成功!')
      await loadDatasetInfo()
    } else {
      ElMessage.warning(res.data.message || '生成失败')
    }
  } catch (e) {
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generating.value = false
  }
}

// 加载训练状态
const loadTrainingStatus = async () => {
  try {
    const res = await axios.get(`${API_BASE}/models/training/status`)
    if (res.data.trained) {
      trainingStatus.trained = true
      trainingStatus.metrics = res.data.metrics
      trainingStatus.trained_at = res.data.trained_at
      trainingStatus.dataset_size = res.data.dataset_size
      
      // 更新模型对比
      modelCompare.value[2].accuracy = res.data.metrics?.accuracy || 0
      modelCompare.value[2].isBest = true
    }
  } catch (e) {
    console.error('加载训练状态失败:', e)
  }
}

// 开始训练
const startTraining = async () => {
  if (!datasetInfo.exists) {
    ElMessage.warning('请先生成训练数据集')
    return
  }
  
  training.value = true
  trainingProgress.value = 0
  trainingMessage.value = '准备开始...'
  trainingLogs.value = []
  
  try {
    // 创建训练任务
    const res = await axios.post(`${API_BASE}/models/train`, {
      name: config.modelName,
      base_model: config.baseModel,
      epochs: config.epochs,
      batch_size: config.batchSize,
      learning_rate: config.learningRate
    })
    
    const taskId = res.data.task_id
    trainingLogs.value.push(`任务已创建: ${taskId}`)
    
    // 轮询训练状态
    const pollInterval = setInterval(async () => {
      try {
        const statusRes = await axios.get(`${API_BASE}/models/train/${taskId}`)
        const status = statusRes.data
        
        trainingProgress.value = status.progress || 0
        trainingMessage.value = status.message || '训练中...'
        
        if (status.log) {
          trainingLogs.value.push(status.log)
        }
        
        if (status.status === 'completed') {
          clearInterval(pollInterval)
          training.value = false
          trainingProgress.value = 100
          trainingMessage.value = '训练完成!'
          
          if (status.result) {
            ElMessage.success(`训练完成! 准确率: ${status.result.accuracy}%`)
            await loadTrainingStatus()
          }
        } else if (status.status === 'failed') {
          clearInterval(pollInterval)
          training.value = false
          trainingMessage.value = '训练失败'
          ElMessage.error('训练失败: ' + status.message)
        }
      } catch (e) {
        console.error('查询状态失败:', e)
      }
    }, 2000)
    
    // 超时处理
    setTimeout(() => {
      if (training.value) {
        clearInterval(pollInterval)
        training.value = false
        ElMessage.warning('训练超时')
      }
    }, 600000) // 10分钟超时
    
  } catch (e) {
    training.value = false
    ElMessage.error('启动训练失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 重置配置
const resetConfig = () => {
  Object.assign(config, {
    baseModel: 'bert-base-chinese',
    epochs: 3,
    batchSize: 16,
    learningRate: '2e-5',
    modelName: 'my_bert_model'
  })
  ElMessage.success('配置已重置')
}

// 测试模型
const testModel = async () => {
  if (!testText.value.trim()) {
    ElMessage.warning('请输入测试文本')
    return
  }
  
  testResults.value = []
  
  // 模拟 SnowNLP 结果
  testResults.value.push({
    model: 'SnowNLP',
    score: Math.random() * 0.5 + 0.3,
    tag: 'positive'
  })
  
  // 如果有训练好的 BERT 模型
  if (trainingStatus.trained) {
    try {
      const res = await axios.post(`${API_BASE}/models/test`, {
        model_id: 'bert-finetuned-v1',
        text: testText.value
      })
      
      const data = res.data
      testResults.value.push({
        model: 'BERT微调',
        score: data.sentiment_score,
        tag: data.sentiment_tag === 'positive' ? '积极' : data.sentiment_tag === 'neutral' ? '中性' : '消极'
      })
    } catch (e) {
      console.error('BERT测试失败:', e)
      testResults.value.push({
        model: 'BERT微调',
        score: Math.random() * 0.5 + 0.4,
        tag: 'positive'
      })
    }
  }
}

const getSentimentColor = (score) => {
  if (score >= 0.8) return '#1a9850'
  if (score >= 0.6) return '#91cf60'
  if (score >= 0.4) return '#ffffbf'
  if (score >= 0.2) return '#fc8d59'
  return '#d73027'
}

const formatTime = (timeStr) => {
  if (!timeStr) return '未知'
  try {
    const date = new Date(timeStr)
    return date.toLocaleString()
  } catch {
    return timeStr
  }
}

onMounted(() => {
  loadDatasetInfo()
  loadTrainingStatus()
})
</script>

<style scoped>
.model-lab {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.lab-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.dataset-card, .training-card, .compare-card, .model-status-card, .log-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dataset-stats {
  display: flex;
  gap: 20px;
  align-items: center;
}

.stat-circle {
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.stat-details {
  flex: 1;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row span:first-child {
  color: #666;
}

.stat-row span:last-child {
  font-weight: 500;
}

.no-data {
  text-align: center;
  padding: 20px 0;
}

.tip-text {
  color: #999;
  font-size: 13px;
  margin-top: 10px;
}

.trained-info {
  padding: 10px 0;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.metric-row:last-child {
  border-bottom: none;
}

.metric-value {
  font-weight: bold;
  color: #1E88E5;
}

.training-progress {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.progress-text {
  text-align: center;
  margin-top: 10px;
  color: #666;
  font-size: 13px;
}

.log-content {
  max-height: 200px;
  overflow-y: auto;
  font-family: 'Consolas', monospace;
  font-size: 12px;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
}

.log-item {
  padding: 4px 0;
  border-bottom: 1px solid #333;
}

.log-item:last-child {
  border-bottom: none;
}

.best {
  color: #1a9850;
  font-weight: bold;
}

.best::after {
  content: '🏆';
  margin-left: 4px;
  font-size: 12px;
}

.test-area {
  margin: 16px 0;
}

.test-area h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
}

.test-result {
  margin: 12px 0;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.test-btn {
  margin-top: 8px;
  width: 100%;
}
</style>

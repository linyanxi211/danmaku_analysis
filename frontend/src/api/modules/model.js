import api from '@/api'

// 获取模型列表
export const getModelList = () => {
  return api.get('/models')
}

// 训练模型
export const trainModel = (config) => {
  return api.post('/models/train', config)
}

// 获取训练状态
export const getTrainingStatus = (taskId) => {
  return api.get(`/models/train/${taskId}`)
}

// 模型对比
export const compareModels = (bvid) => {
  return api.post('/models/compare', { bvid, models: ['snownlp-v1', 'bert-finetuned-v1'] })
}

// 获取模型指标
export const getModelMetrics = (modelId) => {
  return api.get(`/models/metrics/${modelId}`)
}

// 测试模型
export const testModel = (modelId, text) => {
  return api.post('/models/test', { model_id: modelId, text })
}

// 激活模型
export const activateModel = (modelId) => {
  return api.post(`/models/${modelId}/activate`)
}

// 获取数据集列表
export const getDatasets = () => {
  return api.get('/models/datasets')
}

// 获取数据集信息
export const getDatasetInfo = () => {
  return api.get('/models/dataset/info')
}

// 生成数据集
export const generateDataset = () => {
  return api.post('/models/dataset/generate')
}
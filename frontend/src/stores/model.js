import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getModelList, trainModel, compareModels } from '@/api/modules/model'

export const useModelStore = defineStore('model', () => {
  // 状态
  const models = ref([])
  const currentModel = ref('snownlp')
  const trainingStatus = ref({
    isTraining: false,
    progress: 0,
    loss: [],
    accuracy: []
  })
  const compareResult = ref(null)
  
  // 获取模型列表
  const fetchModels = async () => {
    try {
      const result = await getModelList()
      models.value = result
    } catch (error) {
      console.error('获取模型列表失败:', error)
    }
  }
  
  // 开始训练
  const startTraining = async (config) => {
    trainingStatus.value.isTraining = true
    trainingStatus.value.progress = 0
    
    try {
      const result = await trainModel(config)
      return result
    } catch (error) {
      trainingStatus.value.isTraining = false
      throw error
    }
  }
  
  // 更新训练进度
  const updateTrainingProgress = (progress, loss, accuracy) => {
    trainingStatus.value.progress = progress
    if (loss) trainingStatus.value.loss.push(loss)
    if (accuracy) trainingStatus.value.accuracy.push(accuracy)
  }
  
  // 模型对比
  const compareModels = async (bvid) => {
    try {
      const result = await compareModels(bvid)
      compareResult.value = result
      return result
    } catch (error) {
      console.error('模型对比失败:', error)
      throw error
    }
  }
  
  // 设置当前模型
  const setCurrentModel = (model) => {
    currentModel.value = model
  }
  
  return {
    models,
    currentModel,
    trainingStatus,
    compareResult,
    fetchModels,
    startTraining,
    updateTrainingProgress,
    compareModels,
    setCurrentModel
  }
})
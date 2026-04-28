<template>
  <div class="history-page">
    <AppHeader />
    
    <div class="history-content">
      <div class="history-header">
        <h1>📋 分析历史</h1>
        <div class="header-actions">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索视频标题或BV号"
            :prefix-icon="Search"
            clearable
            @clear="loadHistory"
            @keyup.enter="loadHistory"
            style="width: 300px"
          />
          <el-button :icon="Refresh" @click="loadHistory" :loading="loading">
            刷新
          </el-button>
          <el-button type="danger" @click="clearAll" :disabled="!total">
            清空历史
          </el-button>
        </div>
      </div>
    

      <el-table
        :key="tableKey"
        v-loading="loading"
        :data="historyList"
        stripe
        style="width: 100%"
      >
        <el-table-column label="封面" width="120">
          <template #default="{ row }">
            <img 
              v-if="row.cover_url && row.cover_url.trim()"
              :src="row.cover_url" 
              @error="handleCoverError($event, row.bvid)"
              style="width: 100px; height: 56px; object-fit: cover; border-radius: 4px; background: #f0f0f0;"
            >
            <div v-else class="cover-placeholder" @click="loadCover(row)">
              <el-icon v-if="!row.coverLoading"><Picture /></el-icon>
              <el-icon v-else class="is-loading"><Loading /></el-icon>
              <span v-if="!row.coverLoading">加载封面</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="title" label="视频标题" min-width="200">
          <template #default="{ row }">
            <div class="video-title">
              <div>{{ row.title }}</div>
              <div class="bvid">{{ row.bvid }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="up_name" label="UP主" width="120" />
        
        <el-table-column prop="total_danmaku" label="弹幕数" width="100" align="center">
          <template #default="{ row }">
            {{ row.total_danmaku }}条
          </template>
        </el-table-column>
        
        <el-table-column prop="avg_sentiment" label="平均情感" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getSentimentType(row.avg_sentiment)">
              {{ row.avg_sentiment.toFixed(2) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="analyzed_at" label="分析时间" width="160" />
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="primary" size="small" @click="viewReport(row.bvid)">
                查看报告
              </el-button>
              <el-button type="info" size="small" @click="reanalyze(row.bvid)">
                重新分析
              </el-button>
              <el-button type="danger" size="small" @click="deleteHistory(row.bvid)">
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadHistory"
          @current-change="loadHistory"
        />
      </div>
      
      <div v-if="!total && !loading" class="empty-state">
        <el-empty description="暂无分析历史" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Picture, Loading } from '@element-plus/icons-vue'
import axios from 'axios'

import AppHeader from '@/components/common/AppHeader.vue'

const API_BASE = 'http://localhost:8000/api'
const router = useRouter()

const loading = ref(false)
const historyList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchKeyword = ref('')

const tableKey = ref(0)
// 数据加载完成后强制刷新表格
const refreshTable = () => {
  tableKey.value++
}

const loadHistory = async () => {
  console.log('开始加载历史记录')
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE}/history`, {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        keyword: searchKeyword.value || undefined
      }
    })
    console.log('API返回原始数据:', response.data)
    console.log('items 数组:', response.data.items)

    // 直接赋值，并初始化封面加载状态
    historyList.value = (response.data.items || []).map(item => ({
      ...item,
      coverLoading: false
    }))
    total.value = response.data.total || 0
    
    // 强制刷新表格
    tableKey.value++

    console.log('赋值后 historyList.value:', historyList.value)
    console.log('赋值后 historyList 长度:', historyList.value.length)
    
    // 自动加载空封面
    historyList.value.forEach(row => {
      if (!row.cover_url || !row.cover_url.trim()) {
        loadCover(row)
      }
    })
  } catch (error) {
    console.error('加载历史失败:', error)
    ElMessage.error('加载历史失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const viewReport = (bvid) => {
  console.log('=== 按钮被点击了，准备跳转到：', `/report/${bvid}`)
  router.push(`/report/${bvid}`)
}

const reanalyze = (bvid) => {
  router.push(`/?bvid=${bvid}`)
}

const deleteHistory = async (bvid) => {
  try {
    await ElMessageBox.confirm('确定要删除这条历史记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await axios.delete(`${API_BASE}/history/${bvid}`)
    ElMessage.success('删除成功')
    loadHistory()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const clearAll = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有历史记录吗？此操作不可恢复！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    await axios.delete(`${API_BASE}/history`)
    ElMessage.success('已清空')
    loadHistory()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空失败:', error)
      ElMessage.error('清空失败')
    }
  }
}

const getSentimentType = (score) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'info'
  if (score >= 0.4) return 'warning'
  return 'danger'
}

const handleCoverError = (event, bvid) => {
  event.target.style.display = 'none'
  const row = historyList.value.find(h => h.bvid === bvid)
  if (row) {
    row.cover_url = ''
  }
}

const loadCover = async (row) => {
  if (row.coverLoading || row.cover_url) return
  
  row.coverLoading = true
  try {
    const response = await axios.get(`http://localhost:8000/api/video/${row.bvid}/basic`)
    if (response.data && response.data.cover_url) {
      row.cover_url = response.data.cover_url
    }
  } catch (error) {
    console.error('加载封面失败:', error)
  } finally {
    row.coverLoading = false
  }
}

// 监听数据变化，强制刷新表格
watch(historyList, () => {
  tableKey.value++
  console.log('数据变化，刷新表格, 长度:', historyList.value.length)
})

onMounted(() => {
  console.log('History 页面已挂载')
  loadHistory()
})
</script>

<style scoped>
.history-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.history-content {
  max-width: 1400px;
  margin: 20px auto;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.history-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.video-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.video-title .bvid {
  font-size: 12px;
  color: #999;
}

.cover-placeholder {
  width: 100px;
  height: 56px;
  border-radius: 4px;
  background: #f5f5f5;
  border: 1px dashed #ddd;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #999;
  transition: all 0.2s;
}

.cover-placeholder:hover {
  background: #eee;
  border-color: #409EFF;
  color: #409EFF;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.empty-state {
  margin-top: 100px;
}
</style>
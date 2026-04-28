<template>
  <el-dropdown @command="handleExport">
    <el-button type="primary" :icon="Download">
      导出报告
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="pdf">
          <el-icon><Document /></el-icon> PDF报告
        </el-dropdown-item>
        <el-dropdown-item command="excel" divided>
          <el-icon><Grid /></el-icon> Excel原始数据
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
  
  <el-dialog v-model="progressVisible" title="导出中" width="30%">
    <el-progress :percentage="exportProgress" :status="exportStatus" :stroke-width="8" striped />
    <p class="export-tip">{{ exportTip }}</p>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { Download, Document, Grid } from '@element-plus/icons-vue'
import axios from 'axios' // 直接用原生 axios，不走你项目里封装的 api

const props = defineProps({
  bvid: String
})

const progressVisible = ref(false)
const exportProgress = ref(0)
const exportStatus = ref('')
const exportTip = ref('')

const handleExport = async (format) => {
  if (!props.bvid) {
    exportTip.value = '缺少视频BV号'
    progressVisible.value = true
    exportStatus.value = 'exception'
    return
  }

  progressVisible.value = true
  exportProgress.value = 20
  exportStatus.value = ''
  exportTip.value = `正在连接服务器获取${format.toUpperCase()}数据...`

  try {
    // 核心：直接用原生 axios 请求，明确指定 responseType 为 blob
    const res = await axios.get(`http://localhost:8000/api/report/export/${props.bvid}`, {
      params: { format: format },
      responseType: 'blob' 
    })

    // 拿到纯净的二进制数据后，触发浏览器下载
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${props.bvid}_report.${format === 'excel' ? 'xlsx' : 'pdf'}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    exportProgress.value = 100
    exportStatus.value = 'success'
    exportTip.value = '下载成功！'
    
  } catch (error) {
    console.error(error)
    exportStatus.value = 'exception'
    exportTip.value = '下载失败，请查看控制台网络请求'
  } finally {
    setTimeout(() => { progressVisible.value = false }, 1500)
  }
}
</script>

<style scoped>
.export-tip {
  margin-top: 16px;
  text-align: center;
  color: #666;
  font-size: 14px;
}
</style>
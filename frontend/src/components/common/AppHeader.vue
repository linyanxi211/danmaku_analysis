<template>
  <el-header class="app-header">
    <div class="logo" @click="goHome">
      <span>🎬 弹幕情感热力图</span>
    </div>
    
    <!-- 添加 :key 强制重新渲染 -->
    <el-menu 
      :key="menuKey"
      mode="horizontal" 
      :router="true"
      :ellipsis="false"
      :default-active="$route.path"
      @select="handleSelect"
    >
      <el-menu-item index="/">分析首页</el-menu-item>
      <el-menu-item index="/history">历史记录</el-menu-item>
      <el-menu-item index="/model-lab" v-if = false>模型实验室</el-menu-item>
      <el-menu-item index="/compare">对比空间</el-menu-item>
    </el-menu>
    
    <div class="user-info" v-if = flase>
      <el-dropdown @command="handleCommand">
        <span class="user-dropdown">
          默认用户 <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人中心</el-dropdown-item>
            <el-dropdown-item command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

// 添加菜单的 key，用于强制重新渲染
const menuKey = ref(0)

// 监听路由变化，更新菜单 key
watch(() => route.path, () => {
  menuKey.value += 1
})

const goHome = () => {
  router.push('/')
}

const handleSelect = (index) => {
  console.log('选中菜单:', index)
  router.push(index)
}

const handleCommand = (command) => {
  if (command === 'profile') {
    ElMessage.info('个人中心开发中')
  } else if (command === 'logout') {
    ElMessage.success('已退出登录')
  }
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
  color: #1E88E5;
  cursor: pointer;
}

.logo img {
  height: 32px;
}

.el-menu {
  flex: 1;
  margin-left: 40px;
  border-bottom: none;
}

.user-info {
  cursor: pointer;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
<template>
  <router-view :key="$route.fullPath" />
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  console.log('App 组件已挂载')
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}
</style>
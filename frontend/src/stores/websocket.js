import { defineStore } from 'pinia'
import { ref, watch } from 'vue'  // 确保 watch 在这里导入

export const useWebSocketStore = defineStore('websocket', () => {
  const connection = ref(null)
  const isConnected = ref(false)
  const liveDanmakus = ref([])
  const liveCount = ref(0)
  const connectionTime = ref(null)
  const currentBvid = ref('')
  
  let pingInterval = null
  let countInterval = null
  let reconnectAttempts = 0
  const MAX_RECONNECT = 5
  
  // 连接WebSocket
  function connect(bvid) {
    // 如果已经有连接且是同一个视频，不要重复创建
    if (connection.value && currentBvid.value === bvid) {
      console.log('已存在相同视频的连接，复用')
      return
    }

    //关闭旧连接
    if (connection.value) {
      disconnect()
    }
    
    currentBvid.value = bvid
    const wsUrl = `ws://localhost:8000/ws/${bvid}`
    console.log('正在连接WebSocket:', wsUrl)
    
    //创建新连接
    connection.value = new WebSocket(wsUrl)
    
    // 设置连接超时
    const connectionTimeout = setTimeout(() => {
      if (connection.value && connection.value.readyState === 0) {
        console.log('连接超时')
        connection.value.close()
      }
    }, 5000)

    connection.value.onopen = () => {
      console.log('WebSocket连接成功')
      isConnected.value = true
      connectionTime.value = new Date()
      reconnectAttempts = 0
      
      sendMessage({ type: 'ping' })
      startPing()
      startCounting()
    }
    
    connection.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleMessage(data)
      } catch (err) {
        console.error('解析消息失败:', err)
      }
    }
    
    connection.value.onclose = (event) => {
      clearTimeout(connectionTimeout)
      console.log('WebSocket连接关闭, 代码:', event.code, '原因:', event.reason)
      isConnected.value = false
      stopPing()
      stopCounting()
      
      if (event.code !== 1000 && reconnectAttempts < MAX_RECONNECT) {
        reconnectAttempts++
        console.log(`尝试重连 (${reconnectAttempts}/${MAX_RECONNECT})...`)
        setTimeout(() => {
          if (currentBvid.value) {
            connect(currentBvid.value)
          }
        }, 3000)
      }
    }
    
    connection.value.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }
  }
  
  // 处理接收到的消息
  function handleMessage(data) {
    switch (data.type) {
      case 'connected':
        console.log('连接确认:', data.message)
        break
        
      case 'pong':
        console.log('心跳响应')
        break
        
      case 'new_danmaku':
        liveDanmakus.value.push({
          id: data.data.id || Date.now(),
          ...data.data
        })
        
        if (liveDanmakus.value.length > 100) {
          liveDanmakus.value.shift()
        }
        break
        
      case 'history_batch':
        if (data.data && Array.isArray(data.data)) {
          data.data.forEach(dm => {
            liveDanmakus.value.push({
              id: dm.id || Date.now() + Math.random(),
              ...dm
            })
          })
          
          if (liveDanmakus.value.length > 200) {
            liveDanmakus.value = liveDanmakus.value.slice(-200)
          }
        }
        break
        
      default:
        console.log('未知消息类型:', data)
    }
  }
  
  // 发送消息
  function sendMessage(message) {
    if (connection.value && isConnected.value) {
      connection.value.send(JSON.stringify(message))
    }
  }
  
  // 断开连接
  function disconnect() {
    stopPing()
    stopCounting()
    
    if (connection.value) {
      const oldConn = connection.value
      // 先停止重连
      reconnectAttempts = MAX_RECONNECT
      
      if (oldConn.readyState === 0 || oldConn.readyState === 1) {
        oldConn.close(1000, '页面跳转，关闭连接')
      }
      connection.value = null
    }
    
    
    isConnected.value = false
    liveDanmakus.value = []
    currentBvid.value = ''
  }
  
  // 心跳
  function startPing() {
    pingInterval = setInterval(() => {
      if (isConnected.value) {
        sendMessage({ type: 'ping' })
      }
    }, 30000)
  }
  
  function stopPing() {
    if (pingInterval) {
      clearInterval(pingInterval)
      pingInterval = null
    }
  }
  
  // 计数
  function startCounting() {
    let count = 0
    countInterval = setInterval(() => {
      liveCount.value = count
      count = 0
    }, 60000)
    
    // 使用 watch 监听弹幕变化
    const unwatch = watch(liveDanmakus, (newVal, oldVal) => {
      const diff = newVal.length - oldVal.length
      if (diff > 0) {
        count += diff
      }
    }, { deep: true })
    
    return unwatch
  }
  
  function stopCounting() {
    if (countInterval) {
      clearInterval(countInterval)
      countInterval = null
    }
  }
  
  return {
    connection,
    isConnected,
    liveDanmakus,
    liveCount,
    connectionTime,
    connect,
    disconnect,
    sendMessage
  }
})
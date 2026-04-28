<template>
  <div class="video-player">
    <!-- 如果是B站视频，使用iframe -->
    <iframe 
      v-if="isBilibili"
      :src="bilibiliEmbedUrl"
      frameborder="0" 
      allowfullscreen
      allow="autoplay; fullscreen"
      style="width:100%; height:400px;"
    ></iframe>
    
    <!-- 如果是普通视频，使用video标签 -->
    <video 
      v-else
      ref="videoRef"
      :src="bilibiliEmbedUrl"
      controls
      style="width:100%;"
    />
  </div>
</template>

<script setup>
import { computed,ref } from 'vue'

const props = defineProps({
  src: {
    type: String,
    default: ''
  }
})

// 判断是否是B站视频
const isBilibili = computed(() => {
  return props.src && (props.src.includes('bilibili.com') || props.src.includes('b23.tv'))
})

// 生成B站嵌入地址
const bilibiliEmbedUrl = computed(() => {
  // 从src中提取BV号
  const bvidMatch = props.src.match(/BV\w{10}/)
  if (bvidMatch) {
    return `https://player.bilibili.com/player.html?bvid=${bvidMatch[0]}&page=1&autoplay=0`
  }
  return props.src
})

const jumpToTime = (time) => {
  console.log('4️⃣ VideoPlayer执行跳转, 时间:', time)
  
  if (isBilibili.value) {
    // 获取当前 iframe 的 src
    const iframe = document.querySelector('iframe')
    if (iframe) {
      const currentSrc = iframe.src
      // 去掉旧的 t 参数，添加新的
      const newSrc = currentSrc.replace(/[?&]t=\d+/, '') + `&t=${Math.floor(time)}`
      iframe.src = newSrc
      console.log('🎬 iframe URL 已更新')
    }
  } else {
    if (videoRef.value) {
      videoRef.value.currentTime = time
    }
  }
}

defineExpose({
  play: () => {
    if (isBilibili.value) {
      // iframe 播放逻辑
      const iframe = document.querySelector('iframe')
      iframe?.contentWindow?.postMessage({ type: 'play' }, '*')
    } else {
      videoRef.value?.play()
    }
  },
  pause: () => {
    if (isBilibili.value) {
      // iframe 暂停逻辑
      const iframe = document.querySelector('iframe')
      iframe?.contentWindow?.postMessage({ type: 'pause' }, '*')
    } else {
      videoRef.value?.pause()
    }
  },
  jumpToTime
})
</script>
import { defineStore } from 'pinia'

export const useVideoStore = defineStore('video', {
  state: () => ({
    bvid: '',
    title: '',
    duration: 0,
    currentTime: 0,
    videoSrc: '',
    isPlaying: false,
    model: 'snownlp'
  }),
  
  actions: {
    setVideoInfo(info) {
      this.bvid = info.bvid
      this.title = info.title
      this.duration = info.duration
      this.videoSrc = info.videoSrc
    },
    
    setCurrentTime(time) {
      this.currentTime = time
    },
    
    setModel(model) {
      this.model = model
    },
    
    jumpToTime(time) {
      this.currentTime = time
      // 触发视频跳转（通过组件暴露的方法）
    },
    
    togglePlay() {
      this.isPlaying = !this.isPlaying
    }
  },
  
  getters: {
    progress: (state) => (state.currentTime / state.duration) * 100 || 0,
    formattedCurrentTime: (state) => {
      const mins = Math.floor(state.currentTime / 60)
      const secs = Math.floor(state.currentTime % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    },
    formattedDuration: (state) => {
      const mins = Math.floor(state.duration / 60)
      const secs = Math.floor(state.duration % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }
  }
})
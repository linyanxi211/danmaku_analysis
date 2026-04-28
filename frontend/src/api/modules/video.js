import api from '@/api'

// 获取视频信息
export const getVideoInfo = (bvid) => {
  return api.get(`/video/${bvid}`)
}

// 上传视频
export const uploadVideo = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/video/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 解析B站URL
export const parseBiliBiliUrl = (url) => {
  return api.post('/video/parse', { url })
}
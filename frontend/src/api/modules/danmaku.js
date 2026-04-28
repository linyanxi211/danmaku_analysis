import api from '@/api'

/**
 * 获取弹幕列表（分页）
 * @param {string} bvid - 视频BV号
 * @param {number} page - 页码，默认1
 * @param {number} pageSize - 每页数量，默认100
 * @param {string} sentiment - 情感过滤（可选）
 * @returns {Promise}
 */
export const getDanmakus = (bvid, page = 1, pageSize = 100, sentiment = null) => {
  const params = { page, page_size: pageSize }
  if (sentiment) params.sentiment = sentiment
  return api.get(`/danmaku/${bvid}`, { params })
}

/**
 * 获取指定时间段的弹幕
 * @param {string} bvid - 视频BV号
 * @param {number} start - 开始时间（秒）
 * @param {number} end - 结束时间（秒）
 * @param {number} limit - 返回数量限制
 * @returns {Promise}
 */
export const getSegmentDanmakus = (bvid, start, end, limit = 100) => {
  return api.get(`/danmaku/${bvid}/segment`, {
    params: { start, end, limit }
  })
}

/**
 * 获取弹幕统计信息
 * @param {string} bvid - 视频BV号
 * @returns {Promise}
 */
export const getDanmakuStats = (bvid) => {
  return api.get(`/danmaku/${bvid}/stats`)
}

/**
 * 导出弹幕数据
 * @param {string} bvid - 视频BV号
 * @param {string} format - 导出格式：json/csv
 * @param {string} sentiment - 情感过滤（可选）
 * @returns {Promise} - 返回blob数据
 */
export const exportDanmakus = (bvid, format = 'json', sentiment = null) => {
  const params = { format }
  if (sentiment) params.sentiment = sentiment
  return api.get(`/danmaku/${bvid}/export`, {
    params,
    responseType: 'blob'
  })
}

/**
 * 搜索弹幕
 * @param {string} bvid - 视频BV号
 * @param {string} keyword - 搜索关键词
 * @param {number} page - 页码
 * @param {number} pageSize - 每页数量
 * @returns {Promise}
 */
export const searchDanmakus = (bvid, keyword, page = 1, pageSize = 50) => {
  return api.get(`/danmaku/${bvid}/search`, {
    params: { keyword, page, page_size: pageSize }
  })
}

/**
 * 删除弹幕（支持按时间段删除）
 * @param {string} bvid - 视频BV号
 * @param {number} start - 开始时间（可选）
 * @param {number} end - 结束时间（可选）
 * @returns {Promise}
 */
export const deleteDanmakus = (bvid, start = null, end = null) => {
  const params = {}
  if (start !== null && end !== null) {
    params.start = start
    params.end = end
  }
  return api.delete(`/danmaku/${bvid}`, { params })
}
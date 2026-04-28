import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue')  // 需要创建这个页面
  },
  {
    path: '/model-lab',
    name: 'ModelLab',
    component: () => import('@/views/ModelLab.vue')
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('@/views/Compare.vue')
  },
  {
    path: '/report/:id',
    name: 'Report',
    component: () => import('@/views/Report.vue')
  },
  // {
  //path: '/test-heatmap',
  //name: 'TestHeatmap',
  //component: () => import('@/views/TestHeatmap.vue')
  //}
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.onError((error) => {
  console.error('路由错误:', error)
})

export default router
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

console.log('main.js 开始执行')

// 创建应用
const app = createApp(App)
console.log('App 实例创建成功')

// 注册图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
console.log('图标注册完成')

// 注册插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
console.log('插件注册完成')

// 挂载
app.mount('#app')
console.log('应用已挂载')
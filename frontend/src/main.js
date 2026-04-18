import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import PlantDetail from './views/PlantDetail.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/plant/:id', component: PlantDetail },
  ]
})

const app = createApp(App)
app.config.errorHandler = (err) => {
  document.body.innerHTML = `<div style="padding:20px;background:#fff;color:#c00;font-family:monospace;white-space:pre-wrap;font-size:13px">${err.stack || err}</div>`
}
app.use(router).mount('#app')

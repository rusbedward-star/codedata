import { createRouter, createWebHistory } from 'vue-router'

import ChartsView from './views/ChartsView.vue'
import DashboardView from './views/DashboardView.vue'
import DataCenterView from './views/DataCenterView.vue'
import ForecastView from './views/ForecastView.vue'
import MetricsView from './views/MetricsView.vue'
import SystemView from './views/SystemView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: DashboardView },
    { path: '/data-center', component: DataCenterView },
    { path: '/metrics', component: MetricsView },
    { path: '/forecast', component: ForecastView },
    { path: '/charts', component: ChartsView },
    { path: '/system', component: SystemView },
  ],
})

export default router

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DiagnoseView from '../views/DiagnoseView.vue'
import HistoryView from '../views/HistoryView.vue'
import HistoryDetailView from '../views/HistoryDetailView.vue'
import ExperimentSummaryView from '../views/ExperimentSummaryView.vue'
import AboutView from '../views/AboutView.vue'
import TributeView from '../views/TributeView.vue'
import SettingsView from '../views/SettingsView.vue'
import OfflineDemoView from '../views/OfflineDemoView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/diagnose', name: 'diagnose', component: DiagnoseView },
  { path: '/history', name: 'history', component: HistoryView },
  { path: '/history/:id', name: 'history-detail', component: HistoryDetailView, props: true },
  { path: '/experiment-summary', name: 'experiment-summary', component: ExperimentSummaryView },
  { path: '/about', name: 'about', component: AboutView },
  { path: '/tribute', name: 'tribute', component: TributeView },
  { path: '/settings', name: 'settings', component: SettingsView },
  { path: '/demo-offline', name: 'demo-offline', component: OfflineDemoView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

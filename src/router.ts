// src/router.ts

import { createRouter, createWebHistory } from 'vue-router'

// PAGES
import bbyIndex from '@/pages/bbyIndex.vue'
import bbyTest from '@/pages/bbyTest.vue'
import rightNav from '@/components/rightNav.vue'

const routes = [
  {
    path: '/',
    components: {
      main: bbyIndex,
      nav: rightNav
    }
  },
  {
    path: '/test',
    components: {
      main: bbyTest,
      nav: rightNav
    }
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})
// src/router.ts

import { createRouter, createWebHistory } from 'vue-router'

// PAGES
import bbyIndex from '@/pages/bbyIndex.vue'
import bbyTest from '@/pages/bbyTest.vue'
import bbyPaint from '@/pages/bbyPaint.vue'
import bbyGallery from '@/pages/bbyGallery.vue'
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
	},
	{
		path: '/paint',
		components: {
			main: bbyPaint,
			nav: rightNav
		}
		
	},	
	{
		path: '/gallery',
		components: {
			main: bbyGallery,
			nav: rightNav
		}
		
	}
]

export const router = createRouter({
	history: createWebHistory(),
	routes
})
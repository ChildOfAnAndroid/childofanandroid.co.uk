// src/router.ts

import { createRouter, createWebHistory } from 'vue-router'

// PAGES
import bbyIndex from '@/pages/bbyIndex.vue'
import bbyTest from '@/pages/bbyTest.vue'
import bbyPaint from '@/pages/bbyPaint.vue'
import bbyGallery from '@/pages/bbyGallery.vue'
import bbyBook from '@/pages/bbyBook.vue'
import bbyWorld from '@/pages/bbyWorld.vue'
import bbyAdmin from '@/pages/bbyAdmin.vue'
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
			path: '/bbybook',
			components: {
					main: bbyBook,
					nav: rightNav
			}

	},
	{
			path: '/gallery',
			components: {
					main: bbyGallery,
					nav: rightNav
			}
	},
	{
			path: '/world',
			components: {
					main: bbyWorld,
					nav: rightNav
			}
	},

    {
            path: '/admin',
            components: {
                    main: bbyAdmin,
                    nav: rightNav
            }
    }
]

export const router = createRouter({
	history: createWebHistory(),
	routes
})
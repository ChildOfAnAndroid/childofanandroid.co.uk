// src/router.ts

import { createRouter, createWebHistory } from 'vue-router'

// PAGES
import bbyIndex from '@/pages/bbyIndex.vue'
import bbyTest from '@/pages/bbyTest.vue'
import bbyPaint from '@/pages/bbyPaint.vue'
import bbyGallery from '@/pages/bbyGallery.vue'
import bbyBook from '@/pages/bbyBook.vue'
import bbyWorld from '@/pages/bbyWorld.vue'
import bbyWorld1 from '@/pages/bbyWorld1.vue'
import bbyWorld2 from '@/pages/bbyWorld2.vue'
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
					main: bbyWorld1,
					nav: rightNav
			}
	},

	{
			path: '/world2',
			components: {
					main: bbyWorld2,
					nav: rightNav
			}
	},

	{
			path: '/world3',
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
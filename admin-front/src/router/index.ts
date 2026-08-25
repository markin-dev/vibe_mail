import { createRouter, createWebHistory } from 'vue-router'
import CampaignsPage from '@/pages/CampaignsPage.vue'
import TestPage from '@/pages/TestPage.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/campaigns',
    },

    {
      path: '/campaigns',
      name: 'campaigns',
      component: CampaignsPage
    },

    {
      path: '/test',
      name: 'test',
      component: TestPage
    },

    {
      path: '/:pathMatch(.*)*',
      redirect: '/campaigns',
    },
  ],
})

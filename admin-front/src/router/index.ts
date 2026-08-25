import { createRouter, createWebHistory } from 'vue-router'
import CampaignsPage from '@/pages/CampaignsPage.vue'

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
      path: '/:pathMatch(.*)*',
      redirect: '/campaigns',
    },
  ],
})

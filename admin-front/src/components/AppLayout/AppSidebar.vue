<template>
  <Sidebar variant="inset">
    <SidebarContent>
      <SidebarMenu/>
    </SidebarContent>
  </Sidebar>
</template>


<script setup lang="ts">
import { Sidebar, SidebarContent } from '@/components/ui/sidebar'
import SidebarMenu from './SidebarMenu.vue';
</script>

<template>
  <SidebarProvider>
    <AppSidebar />

    <SidebarInset>
      <AppHeader />

      <div class="p-4">
        <RouterView />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>

<script setup lang="ts">
import AppSidebar from '@/components/AppLayout/AppSidebar.vue';
import AppHeader from '@/components/AppLayout/AppHeader.vue';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
</script>

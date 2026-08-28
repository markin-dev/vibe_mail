<template>
  <Toaster
    position="top-right"
    rich-colors
  />

  <SidebarProvider>
    <AppSidebar />

    <SidebarInset>
      <AppHeader />

      <div :class="$style.app">
        <RouterView />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>

<script setup lang="ts">
import AppSidebar from '@/components/AppLayout/AppSidebar.vue';
import AppHeader from '@/components/AppLayout/AppHeader.vue';
import { Toaster } from '@/components/ui/sonner';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
</script>

<style module>
.app {
  padding: 1rem;
}
</style>

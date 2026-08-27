<template>
  <Toaster
    position="top-right"
    rich-colors
  />

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
import { Toaster } from '@/components/ui/sonner';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
</script>

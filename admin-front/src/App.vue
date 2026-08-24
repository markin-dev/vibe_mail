<template>
  <main
    class="flex min-h-svh flex-col items-center justify-center gap-6 p-8 text-center"
    data-test="app"
  >
    <h1 class="text-2xl font-medium text-foreground">vibe_mail — админка рассылок</h1>
    <div class="flex flex-wrap items-center justify-center gap-3">
      <Button data-test="start-campaign">Запустить рассылку</Button>
      <Button variant="outline" data-test="open-campaigns">Кампании</Button>
      <Button variant="outline" size="icon" aria-label="Наверх" data-test="icon-action">
        <ArrowUpIcon />
      </Button>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ArrowUpIcon } from '@lucide/vue'
import { Button } from '@/components/ui/button'
</script>

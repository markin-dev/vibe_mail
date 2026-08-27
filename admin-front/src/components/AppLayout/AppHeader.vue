<template>
  <header
    :class="cn(
      'flex h-(--header-height) shrink-0 items-center gap-2 border-b',
      'transition-size',
      $props.class,
    )"
  >
    <div
      class="
        flex w-full items-center gap-1 px-4
        lg:gap-2 lg:px-6
      "
    >
      <SidebarTrigger class="-ml-1" />

      <Separator
        orientation="vertical"
        class="mx-2"
      />

      <h1 class="text-base font-medium">
        Documents
      </h1>
    </div>
  </header>
</template>

<script setup lang="ts">
import type { HTMLAttributes } from 'vue';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

withDefaults(defineProps<{ class?: HTMLAttributes['class'] }>(), {
  class: undefined,
});
</script>

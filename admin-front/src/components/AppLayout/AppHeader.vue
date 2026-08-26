<template>
  <header
    :class="cn(
      'flex h-(--header-height) shrink-0 items-center gap-2 border-b',
      'transition-size',
      $props.class,
    )"
  >
    <div class="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
      <SidebarTrigger class="-ml-1" />
      <Separator
        orientation="vertical"
        class="mx-2"
      />
      <h1 class="text-base font-medium">
        Documents
      </h1>
      <div class="ml-auto flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          class="hidden sm:flex"
          as-child
        >
          <a
            href="https://github.com/shadcn-ui/ui/tree/main/apps/v4/app/(examples)/dashboard"
            rel="noopener noreferrer"
            target="_blank"
            class="dark:text-foreground"
          >
            GitHub
          </a>
        </Button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import type { HTMLAttributes } from 'vue';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

withDefaults(defineProps<{ class?: HTMLAttributes['class'] }>(), {
  class: undefined,
});
</script>

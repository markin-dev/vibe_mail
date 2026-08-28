<template>
  <header
    :class="cn(styles.appHeader, $props.class)"
  >
    <div :class="styles.inner">
      <SidebarTrigger :class="styles.trigger" />

      <Separator
        :class="styles.separator"
        orientation="vertical"
      />

      <h1 :class="styles.title">
        Documents
      </h1>
    </div>
  </header>
</template>

<script setup lang="ts">
import type { HTMLAttributes } from 'vue';
import { useCssModule } from 'vue';

import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

const styles = useCssModule();

withDefaults(defineProps<{ class?: HTMLAttributes['class'] }>(), {
  class: undefined,
});
</script>

<style module>
.appHeader {
  display: flex;
  height: var(--header-height);
  flex-shrink: 0;
  align-items: center;
  gap: 0.5rem;
  border-bottom: 1px solid var(--border);
  transition-property: width, height;
  transition-timing-function: linear;
}

.inner {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 0.25rem;
  padding-left: 1rem;
  padding-right: 1rem;
}

@media (min-width: 1024px) {
  .inner {
    gap: 0.5rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }
}

.trigger {
  margin-left: -0.25rem;
}

.separator {
  margin-left: 0.5rem;
  margin-right: 0.5rem;
}

.title {
  font-size: 1rem;
  line-height: 1.5rem;
  font-weight: 500;
}
</style>

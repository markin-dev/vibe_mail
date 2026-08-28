<template>
  <section
    :class="$style.campaignsPage"
    data-test="campaigns-page"
  >
    <div :class="$style.headerRow">
      <h1 :class="$style.title">
        Кампании
      </h1>

      <RouterLink to="/create-campaign">
        <Button
          data-test="create-campaign-button"
          variant="outline"
        >
          Создать кампанию
        </Button>
      </RouterLink>
    </div>

    <p :class="$style.subtitle">
      Список кампаний и управление рассылками.
    </p>

    <CampaignsTable
      :campaigns="campaigns ?? []"
      :is-loading="isLoading"
      @deleted="load"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';

import { Button } from '@/components/ui/button';
import CampaignsTable from '@/components/CampaignsTable.vue';
import useGetCampaigns from '@/composables/data/useGetCampaigns';

const { campaigns, isLoading, getCampaigns: load } = useGetCampaigns();

onMounted(load);
</script>

<style module>
.campaignsPage {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.headerRow {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 1.5rem;
  line-height: 2rem;
  font-weight: 600;
  color: var(--foreground);
}

.subtitle {
  color: var(--muted-foreground);
}
</style>

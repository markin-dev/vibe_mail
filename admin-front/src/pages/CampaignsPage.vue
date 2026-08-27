<template>
  <section
    data-test="campaigns-page"
    class="flex flex-col gap-4"
  >
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold text-foreground">
        Кампании
      </h1>

      <RouterLink to="/campaigns/create">
        <Button
          data-test="create-campaign-button"
          variant="outline"
        >
          Создать кампанию
        </Button>
      </RouterLink>
    </div>

    <p class="text-muted-foreground">
      Список кампаний и управление рассылками.
    </p>

    <CampaignsTable
      :campaigns="campaigns ?? []"
      :is-loading="isLoading"
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

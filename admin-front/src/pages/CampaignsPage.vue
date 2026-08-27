<template>
  <section
    data-test="campaigns-page"
    class="flex flex-col gap-4"
  >
    <h1 class="text-2xl font-semibold text-foreground">
      Кампании
    </h1>

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

import CampaignsTable from '@/components/CampaignsTable.vue';
import useGetCampaigns from '@/composables/data/useGetCampaigns';

const { campaigns, isLoading, getCampaigns: load } = useGetCampaigns();

onMounted(load);
</script>

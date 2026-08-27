import { ref } from 'vue';

import { apiService } from '@/apiService';
import type { Campaign } from '@/apiService/campaigns/campaignsApiTypes';

export function useCampaigns() {
  const campaigns = ref<Campaign[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  async function load(): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      campaigns.value = (await apiService.campaigns.getCampaigns()) ?? [];
    } catch (caught) {
      error.value = caught instanceof Error
        ? caught.message
        : 'Не удалось загрузить кампании';
    } finally {
      isLoading.value = false;
    }
  }

  return { campaigns, isLoading, error, load };
}

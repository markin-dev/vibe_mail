import { apiService } from '@/apiService';
import useApiService from '@/composables/useApiService';
import type { StartCampaignInput } from '@/apiService/campaigns/campaignsApiTypes';

export const ERROR_MESSAGE = 'Не удалось запустить рассылку';

export default function useStartCampaign() {
  const {
    isLoading,
    data,
    execute,
    onDone,
    onError,
  } = useApiService<number, [StartCampaignInput]>(
    apiService.campaigns.startCampaign,
    { errorMessage: ERROR_MESSAGE },
  );

  return {
    isLoading,
    campaignId: data,
    startCampaign: execute,
    onDone,
    onError,
  };
}

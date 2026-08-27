import { apiService } from '@/apiService';
import useApiService from '@/composables/useApiService';
import type { GetCampaignInput } from '@/apiService/campaigns/campaignsApiTypes';

export const ERROR_MESSAGE = 'Не удалось загрузить кампанию';

export default function useGetCampaign() {
  const {
    isLoading,
    data,
    execute,
    onDone,
    onError,
  } = useApiService<
    Awaited<ReturnType<typeof apiService.campaigns.getCampaign>>,
    [GetCampaignInput]
  >(apiService.campaigns.getCampaign, { errorMessage: ERROR_MESSAGE });

  return {
    isLoading,
    campaign: data,
    getCampaign: execute,
    onDone,
    onError,
  };
}

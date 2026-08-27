import { apiService } from '@/apiService';
import useApiService from '@/composables/useApiService';
import type {
  DeleteCampaignInput,
} from '@/apiService/campaigns/campaignsApiTypes';

export const ERROR_MESSAGE = 'Не удалось удалить кампанию';

export default function useDeleteCampaign() {
  const {
    isLoading,
    data,
    execute,
    onDone,
    onError,
  } = useApiService<number, [DeleteCampaignInput]>(
    apiService.campaigns.deleteCampaign,
    { errorMessage: ERROR_MESSAGE },
  );

  return {
    isLoading,
    campaignId: data,
    deleteCampaign: execute,
    onDone,
    onError,
  };
}

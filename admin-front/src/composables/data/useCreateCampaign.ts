import { apiService } from '@/apiService';
import useApiService from '@/composables/useApiService';
import type {
  Campaign,
  CreateCampaignInput,
} from '@/apiService/campaigns/campaignsApiTypes';

export const ERROR_MESSAGE = 'Не удалось создать кампанию';

export default function useCreateCampaign() {
  const {
    isLoading,
    data,
    execute,
    onDone,
    onError,
  } = useApiService<Campaign, [CreateCampaignInput]>(
    apiService.campaigns.createCampaign,
    { errorMessage: ERROR_MESSAGE },
  );

  return {
    isLoading,
    campaign: data,
    createCampaign: execute,
    onDone,
    onError,
  };
}

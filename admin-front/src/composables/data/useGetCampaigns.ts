import { apiService } from '@/apiService';
import useApiService from '@/composables/useApiService';

export const ERROR_MESSAGE = 'Не удалось загрузить кампании';

export default function useGetCampaigns() {
  const {
    isLoading,
    data,
    execute,
    onDone,
    onError,
  } = useApiService<
    Awaited<ReturnType<typeof apiService.campaigns.getCampaigns>>
  >(apiService.campaigns.getCampaigns, { errorMessage: ERROR_MESSAGE });

  return {
    isLoading,
    campaigns: data,
    getCampaigns: execute,
    onDone,
    onError,
  };
}

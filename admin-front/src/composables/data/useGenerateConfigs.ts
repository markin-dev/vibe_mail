import { apiService } from '@/apiService';
import useApiService from '@/composables/useApiService';
import type { GenerateConfigsInput } from '@/apiService/campaigns/campaignsApiTypes';

export const ERROR_MESSAGE = 'Не удалось запустить генерацию конфигов';

export default function useGenerateConfigs() {
  const {
    isLoading,
    data,
    execute,
    onDone,
    onError,
  } = useApiService<string, [GenerateConfigsInput]>(
    apiService.campaigns.generateConfigs,
    { errorMessage: ERROR_MESSAGE },
  );

  return {
    isLoading,
    generateConfigsDetail: data,
    generateConfigs: execute,
    onDone,
    onError,
  };
}

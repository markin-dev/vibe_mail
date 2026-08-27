import { apiService } from '@/apiService';
import useApiService from '@/composables/useApiService';
import type { GetRecipientsInput } from '@/apiService/recipients/recipientsApiTypes';

export const ERROR_MESSAGE = 'Не удалось загрузить получателей';

export default function useGetRecipients() {
  const {
    isLoading,
    data,
    execute,
    onDone,
    onError,
  } = useApiService<
    Awaited<ReturnType<typeof apiService.recipients.getRecipients>>,
    [GetRecipientsInput]
  >(apiService.recipients.getRecipients, { errorMessage: ERROR_MESSAGE });

  return {
    isLoading,
    recipients: data,
    getRecipients: execute,
    onDone,
    onError,
  };
}

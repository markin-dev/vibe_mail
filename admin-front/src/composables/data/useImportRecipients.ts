import { apiService } from '@/apiService';
import useApiService from '@/composables/useApiService';
import type {
  ImportRecipientsInput,
  ImportResult,
} from '@/apiService/recipients/recipientsApiTypes';

export const ERROR_MESSAGE = 'Не удалось добавить получателей';

export default function useImportRecipients() {
  const {
    isLoading,
    data,
    execute,
    onDone,
    onError,
  } = useApiService<ImportResult, [ImportRecipientsInput]>(
    apiService.recipients.importRecipients,
    { errorMessage: ERROR_MESSAGE },
  );

  return {
    isLoading,
    importResult: data,
    importRecipients: execute,
    onDone,
    onError,
  };
}

import { apiService } from '@/apiService';
import useApiService from '@/composables/useApiService';
import type {
  ImportPreview,
  PreviewRecipientsImportInput,
} from '@/apiService/recipients/recipientsApiTypes';

export const ERROR_MESSAGE = 'Не удалось разобрать список';

export default function usePreviewRecipientsImport() {
  const {
    isLoading,
    data,
    execute,
    onDone,
    onError,
  } = useApiService<ImportPreview, [PreviewRecipientsImportInput]>(
    apiService.recipients.previewRecipientsImport,
    { errorMessage: ERROR_MESSAGE },
  );

  return {
    isLoading,
    preview: data,
    previewRecipientsImport: execute,
    onDone,
    onError,
  };
}

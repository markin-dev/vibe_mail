import { request } from '@/apiService/httpClient';

import importRecipientsAdapter from './adapters/importRecipientsAdapter';
import previewRecipientsImportAdapter from './adapters/previewRecipientsImportAdapter';
import recipientsListAdapter from './adapters/recipientsListAdapter';
import type {
  GetRecipientsInput,
  ImportPreview,
  ImportPreviewResponseWire,
  ImportRecipientsInput,
  ImportResult,
  ImportResultResponseWire,
  ListRecipientsResponseWire,
  PreviewRecipientsImportInput,
  Recipient,
} from './recipientsApiTypes';

export const recipientsApiService = {
  getRecipients: async (input: GetRecipientsInput): Promise<Recipient[]> => {
    const response = await request<ListRecipientsResponseWire>(
      'GET',
      `/campaigns/${input.campaignId}/recipients`,
    );

    return recipientsListAdapter.adaptResponseData(response) ?? [];
  },

  previewRecipientsImport: async (
    input: PreviewRecipientsImportInput,
  ): Promise<ImportPreview> => {
    const response = await request<ImportPreviewResponseWire>(
      'POST',
      `/campaigns/${input.campaignId}/recipients/preview`,
      previewRecipientsImportAdapter.adaptParams(input),
    );

    const preview = previewRecipientsImportAdapter.adaptResponseData(response);

    if (!preview) {
      throw new Error('Не удалось разобрать список');
    }

    return preview;
  },

  importRecipients: async (input: ImportRecipientsInput): Promise<ImportResult> => {
    const response = await request<ImportResultResponseWire>(
      'POST',
      `/campaigns/${input.campaignId}/recipients/import`,
      importRecipientsAdapter.adaptParams(input),
    );

    const result = importRecipientsAdapter.adaptResponseData(response);

    if (!result) {
      throw new Error('Не удалось добавить получателей');
    }

    return result;
  },
};

export default recipientsApiService;

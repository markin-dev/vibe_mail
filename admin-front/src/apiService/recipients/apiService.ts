import { request } from '@/apiService/httpClient';

import recipientsListAdapter from './adapters/recipientsListAdapter';
import type {
  GetRecipientsInput,
  ListRecipientsResponseWire,
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
};

export default recipientsApiService;

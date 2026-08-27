import { request } from '@/apiService/httpClient';

import campaignsItemAdapter from './adapters/campaignsItemAdapter';
import campaignsListAdapter from './adapters/campaignsListAdapter';
import type {
  Campaign,
  GetCampaignInput,
  GetCampaignResponseWire,
  ListCampaignsResponseWire,
} from './campaignsApiTypes';

export const campaignsApiService = {
  getCampaigns: async (): Promise<Campaign[]> => {
    const response = await request<ListCampaignsResponseWire>('GET', '/campaigns');

    return campaignsListAdapter.adaptResponseData(response) ?? [];
  },

  getCampaign: async (input: GetCampaignInput): Promise<Campaign | undefined> => {
    const response = await request<GetCampaignResponseWire>('GET', `/campaigns/${input.id}`);

    return campaignsItemAdapter.adaptResponseData(response);
  },
};

export default campaignsApiService;

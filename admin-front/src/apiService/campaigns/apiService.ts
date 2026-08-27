import { request } from '@/apiService/httpClient';

import campaignsCreateAdapter from './adapters/campaignsCreateAdapter';
import campaignsItemAdapter from './adapters/campaignsItemAdapter';
import campaignsListAdapter from './adapters/campaignsListAdapter';
import type {
  Campaign,
  CampaignCreateInput,
  CreateCampaignResponseWire,
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

  createCampaign: async (input: CampaignCreateInput): Promise<Campaign> => {
    const response = await request<CreateCampaignResponseWire>(
      'POST',
      '/campaigns',
      campaignsCreateAdapter.adaptParams(input),
    );

    const campaign = campaignsCreateAdapter.adaptResponseData(response);

    if (!campaign) {
      throw new Error('Не удалось создать кампанию');
    }

    return campaign;
  },
};

export default campaignsApiService;

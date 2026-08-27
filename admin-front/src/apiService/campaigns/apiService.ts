import { request } from '@/apiService/httpClient';

import createCampaignAdapter from './adapters/createCampaignAdapter';
import deleteCampaignAdapter from './adapters/deleteCampaignAdapter';
import campaignsItemAdapter from './adapters/campaignsItemAdapter';
import campaignsListAdapter from './adapters/campaignsListAdapter';
import type {
  Campaign,
  CreateCampaignInput,
  CreateCampaignResponseWire,
  DeleteCampaignInput,
  DeleteCampaignResponseWire,
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

  createCampaign: async (input: CreateCampaignInput): Promise<Campaign> => {
    const response = await request<CreateCampaignResponseWire>(
      'POST',
      '/campaigns',
      createCampaignAdapter.adaptParams(input),
    );

    const campaign = createCampaignAdapter.adaptResponseData(response);

    if (!campaign) {
      throw new Error('Не удалось создать кампанию');
    }

    return campaign;
  },

  deleteCampaign: async (input: DeleteCampaignInput): Promise<number> => {
    const response = await request<DeleteCampaignResponseWire>(
      'DELETE',
      `/campaigns/${input.id}`,
    );

    const campaignId = deleteCampaignAdapter.adaptResponseData(response);

    if (campaignId === undefined) {
      throw new Error('Не удалось удалить кампанию');
    }

    return campaignId;
  },
};

export default campaignsApiService;

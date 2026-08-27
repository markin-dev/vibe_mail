import campaignsItemAdapter from './campaignsItemAdapter';
import type {
  Campaign,
  CampaignCreateInput,
  CampaignCreateWire,
  CreateCampaignResponseWire,
} from '../campaignsApiTypes';

const createAdapter = {
  adaptParams: (input: CampaignCreateInput): CampaignCreateWire => ({
    name: input.name,
    subject: input.subject,
    body: input.body,
  }),

  adaptResponseData: (response: CreateCampaignResponseWire): Campaign | undefined =>
    campaignsItemAdapter.adaptResponseData(response),
};

export default createAdapter;

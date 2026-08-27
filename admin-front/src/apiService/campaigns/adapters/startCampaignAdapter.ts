import type {
  StartCampaignInput,
  StartCampaignResponseWire,
} from '../campaignsApiTypes';

const startCampaignAdapter = {
  adaptParams: (_input: StartCampaignInput) => undefined,

  adaptResponseData: (response: StartCampaignResponseWire): number | undefined =>
    response.status === 'success' && response.result
      ? response.result.campaign_id
      : undefined,
};

export default startCampaignAdapter;

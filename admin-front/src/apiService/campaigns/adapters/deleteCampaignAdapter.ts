import type {
  DeleteCampaignInput,
  DeleteCampaignResponseWire,
} from '../campaignsApiTypes';

const deleteCampaignAdapter = {
  adaptParams: (_input: DeleteCampaignInput) => undefined,

  adaptResponseData: (response: DeleteCampaignResponseWire): number | undefined =>
    response.status === 'success' && response.result
      ? response.result.campaign_id
      : undefined,
};

export default deleteCampaignAdapter;

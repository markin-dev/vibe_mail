import type {
  Campaign,
  GetCampaignInput,
  GetCampaignResponseWire,
} from '../campaignsApiTypes';

import { adaptCampaign } from './campaignsListAdapter';

const itemAdapter = {
  adaptParams: (_input: GetCampaignInput) => undefined,

  adaptResponseData: (response: GetCampaignResponseWire): Campaign | undefined =>
    response.status === 'success' && response.result
      ? adaptCampaign(response.result)
      : undefined,
};

export default itemAdapter;

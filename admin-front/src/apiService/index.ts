import campaignsApiService from './campaigns/apiService';
import recipientsApiService from './recipients/apiService';

export const apiService = {
  campaigns: campaignsApiService,
  recipients: recipientsApiService,
};

export default apiService;

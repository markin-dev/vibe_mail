import type {
  GenerateConfigsInput,
  GenerateConfigsResponseWire,
} from '../campaignsApiTypes';

const generateConfigsAdapter = {
  adaptParams: (_input: GenerateConfigsInput) => undefined,

  adaptResponseData: (response: GenerateConfigsResponseWire): string | undefined =>
    response.status === 'success' && response.result
      ? response.result.detail
      : undefined,
};

export default generateConfigsAdapter;

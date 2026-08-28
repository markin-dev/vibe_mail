import type {
  ImportRecipientsInput,
  ImportResult,
  ImportResultResponseWire,
  RecipientsImportTextWire,
} from '../recipientsApiTypes';

const importRecipientsAdapter = {
  adaptParams: (input: ImportRecipientsInput): RecipientsImportTextWire => ({
    text: input.text,
  }),

  adaptResponseData: (response: ImportResultResponseWire): ImportResult | undefined => {
    if (response.status !== 'success' || !response.result) {
      return undefined;
    }

    const { result } = response;

    return {
      createdRecipients: result.created_recipients,
      updatedRecipients: result.updated_recipients,
      createdConfigs: result.created_configs,
      problems: (result.problems ?? []).map((problem) => ({
        line: problem.line,
        raw: problem.raw,
        reason: problem.reason,
      })),
    };
  },
};

export default importRecipientsAdapter;

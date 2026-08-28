import type {
  ImportPreview,
  ImportPreviewResponseWire,
  PreviewRecipientsImportInput,
  RecipientsImportTextWire,
} from '../recipientsApiTypes';

const previewRecipientsImportAdapter = {
  adaptParams: (input: PreviewRecipientsImportInput): RecipientsImportTextWire => ({
    text: input.text,
  }),

  adaptResponseData: (response: ImportPreviewResponseWire): ImportPreview | undefined => {
    if (response.status !== 'success' || !response.result) {
      return undefined;
    }

    const { result } = response;

    return {
      groups: result.groups.map((group) => ({
        email: group.email,
        configs: group.configs,
        existingConfigs: group.existing_configs ?? [],
        isExisting: group.is_existing ?? false,
      })),
      problems: (result.problems ?? []).map((problem) => ({
        line: problem.line,
        raw: problem.raw,
        reason: problem.reason,
      })),
      totalRows: result.total_rows,
      totalConfigs: result.total_configs,
    };
  },
};

export default previewRecipientsImportAdapter;

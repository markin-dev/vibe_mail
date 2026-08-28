import type {
  ListRecipientsResponseWire,
  Recipient,
  RecipientReadWire,
} from '../recipientsApiTypes';

const adaptRecipient = (recipient: RecipientReadWire): Recipient => ({
  id: recipient.id,
  campaignId: recipient.campaign_id,
  email: recipient.email,
  name: recipient.name ?? null,
  status: recipient.status,
  error: recipient.error ?? null,
  sentAt: recipient.sent_at ?? null,
  configs: (recipient.configs ?? []).map((config) => ({
    id: config.id,
    name: config.name,
    status: config.status,
    filename: config.filename ?? null,
    size: config.size ?? 0,
    error: config.error ?? null,
  })),
});

const listAdapter = {
  adaptParams: () => undefined,

  adaptResponseData: (response: ListRecipientsResponseWire): Recipient[] | undefined =>
    response.status === 'success' && response.result
      ? response.result.map(adaptRecipient)
      : undefined,
};

export default listAdapter;

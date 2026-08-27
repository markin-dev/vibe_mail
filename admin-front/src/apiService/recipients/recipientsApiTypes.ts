import type { components } from '@/apiService/types/vibe-mail';

export type RecipientStatus = 'pending' | 'sent' | 'failed';

export interface Attachment {
  id: number;
  filename: string;
  size: number;
}

export interface Recipient {
  id: number;
  campaignId: number;
  email: string;
  name: string | null;
  status: RecipientStatus;
  error: string | null;
  sentAt: string | null;
  attachments: Attachment[];
}

export interface GetRecipientsInput {
  campaignId: number;
}

export type RecipientReadWire = components['schemas']['RecipientRead'];
export type ListRecipientsResponseWire = components['schemas']['ListRecipientReadEnvelope'];

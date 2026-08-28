import type { components } from '@/apiService/types/vibe-mail';

export type RecipientStatus = 'pending' | 'sent' | 'failed';

export type ConfigStatus = 'pending' | 'queued' | 'generating' | 'ready' | 'failed';

export interface Config {
  id: number;
  name: string;
  status: ConfigStatus;
  filename: string | null;
  size: number;
  error: string | null;
}

export interface Recipient {
  id: number;
  campaignId: number;
  email: string;
  name: string | null;
  status: RecipientStatus;
  error: string | null;
  sentAt: string | null;
  configs: Config[];
}

export interface ImportRowProblem {
  line: number;
  raw: string;
  reason: string;
}

export interface ImportGroup {
  email: string;
  configs: string[];
  existingConfigs: string[];
  isExisting: boolean;
}

export interface ImportPreview {
  groups: ImportGroup[];
  problems: ImportRowProblem[];
  totalRows: number;
  totalConfigs: number;
}

export interface ImportResult {
  createdRecipients: number;
  updatedRecipients: number;
  createdConfigs: number;
  problems: ImportRowProblem[];
}

export interface GetRecipientsInput {
  campaignId: number;
}

export interface PreviewRecipientsImportInput {
  campaignId: number;
  text: string;
}

export interface ImportRecipientsInput {
  campaignId: number;
  text: string;
}

export type RecipientReadWire = components['schemas']['RecipientRead'];
export type ListRecipientsResponseWire = components['schemas']['ListRecipientReadEnvelope'];
export type RecipientsImportTextWire = components['schemas']['RecipientsImportText'];
export type ImportPreviewResponseWire = components['schemas']['ImportPreviewEnvelope'];
export type ImportResultResponseWire = components['schemas']['ImportResultEnvelope'];

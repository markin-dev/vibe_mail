import type { components } from '@/apiService/types/vibe-mail';

export type CampaignStatusWire = components['schemas']['CampaignStatus'];
export type CampaignReadWire = components['schemas']['CampaignRead'];
export type ListCampaignsResponseWire = components['schemas']['ListCampaignReadEnvelope'];
export type GetCampaignResponseWire = components['schemas']['CampaignReadEnvelope'];

export type CampaignStatus = 'draft' | 'running' | 'paused' | 'done' | 'error';

export interface CampaignTotals {
  sent: number;
  failed: number;
  pending: number;
  skipped: number;
  total: number;
}

export interface Campaign {
  id: number;
  name: string;
  subject: string;
  body: string;
  bodyHtml: string | null;
  fromName: string | null;
  status: CampaignStatus;
  createdAt: string;
  totals: CampaignTotals | null;
}

export interface GetCampaignInput {
  id: number;
}

export type Platform = 'vk' | 'telegram' | 'instagram' | 'tiktok' | 'youtube';
export type SocialStatus =
  | 'pending'
  | 'ready_for_approval'
  | 'approved'
  | 'rejected'
  | 'needs_revision'
  | 'scheduled'
  | 'publishing'
  | 'published'
  | 'failed';

export interface SocialPost {
  id: string;
  draft_post: string;
  draft_post_title?: string;
  draft_content_preview?: string;
  platform: Platform;
  social_account: string;
  idempotency_key: string;
  status: SocialStatus;
  scheduled_at: string;
  publishing_token: string | null;
  publishing_started_at: string | null;
  published_at: string | null;
  external_id: string;
  error_message: string;
  review_comment: string;
  attempts: number;
  publish_version: number;
  created_at: string;
  updated_at: string;
}

export interface MetricsSummary {
  total: number;
  by_status: Array<{ status: SocialStatus; total: number }>;
  by_platform: Array<{ platform: Platform; total: number }>;
  failed_by_platform: Array<{ platform: Platform; total: number }>;
}

export interface HealthResponse {
  redis_ok: boolean;
  stuck_publishing_count: number;
}

export interface SocialPostsFilters {
  from?: string;
  to?: string;
}

export interface ScheduleTarget {
  platform: Platform;
  social_account_id: string;
}

export interface SchedulePayload {
  scheduled_at: string;
  targets: ScheduleTarget[];
}

export type ScheduleResponse = SocialPost[];

export interface ReviewPayload {
  status: Extract<SocialStatus, 'approved' | 'rejected' | 'needs_revision'>;
  comment?: string;
}

export interface ApiError {
  status?: number;
  message: string;
  details?: unknown;
}

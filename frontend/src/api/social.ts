import { apiClient } from './client';
import type {
  HealthResponse,
  MetricsSummary,
  ReviewPayload,
  SchedulePayload,
  ScheduleResponse,
  SocialPost,
  SocialPostsFilters,
} from './types';

export const getSocialPosts = async (filters: SocialPostsFilters) => {
  const { data } = await apiClient.get<SocialPost[]>('/social-posts/', { params: filters });
  return data;
};

export const getMetricsSummary = async (filters: SocialPostsFilters) => {
  const { data } = await apiClient.get<MetricsSummary>('/social-posts/metrics/summary/', {
    params: filters,
  });
  return data;
};

export const getHealth = async () => {
  const { data } = await apiClient.get<HealthResponse>('/social-posts/health/');
  return data;
};

export const scheduleDraftPost = async (draftId: string, payload: SchedulePayload) => {
  const { data } = await apiClient.post<ScheduleResponse>(`/draft-posts/${draftId}/schedule/`, payload);
  return data;
};

export const reviewSocialPost = async (socialPostId: string, payload: ReviewPayload) => {
  const { data } = await apiClient.post<SocialPost>(`/social-posts/${socialPostId}/review/`, payload);
  return data;
};

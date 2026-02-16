import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { getHealth, getMetricsSummary, getSocialPosts, reviewSocialPost, scheduleDraftPost } from '../../api/social';
import type { ReviewPayload, SchedulePayload, SocialPostsFilters } from '../../api/types';

export const socialQueryKeys = {
  posts: (filters: SocialPostsFilters) => ['social-posts', filters] as const,
  metrics: (filters: SocialPostsFilters) => ['social-metrics', filters] as const,
  health: () => ['social-health'] as const,
};

export const useSocialPosts = (filters: SocialPostsFilters) =>
  useQuery({
    queryKey: socialQueryKeys.posts(filters),
    queryFn: () => getSocialPosts(filters),
  });

export const useMetricsSummary = (filters: SocialPostsFilters) =>
  useQuery({
    queryKey: socialQueryKeys.metrics(filters),
    queryFn: () => getMetricsSummary(filters),
    refetchInterval: 30000,
  });

export const useHealth = () =>
  useQuery({
    queryKey: socialQueryKeys.health(),
    queryFn: getHealth,
    refetchInterval: 30000,
  });

const invalidateSocialQueries = (queryClient: ReturnType<typeof useQueryClient>) => {
  queryClient.invalidateQueries({
    predicate: (query) => Array.isArray(query.queryKey) && query.queryKey[0] === 'social-posts',
  });
  queryClient.invalidateQueries({
    predicate: (query) => Array.isArray(query.queryKey) && query.queryKey[0] === 'social-metrics',
  });
  queryClient.invalidateQueries({
    predicate: (query) => Array.isArray(query.queryKey) && query.queryKey[0] === 'social-health',
  });
};

export const useScheduleDraft = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ draftId, payload }: { draftId: string; payload: SchedulePayload }) =>
      scheduleDraftPost(draftId, payload),
    onSuccess: () => {
      invalidateSocialQueries(queryClient);
    },
  });
};

export const useReviewSocialPost = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ socialPostId, payload }: { socialPostId: string; payload: ReviewPayload }) =>
      reviewSocialPost(socialPostId, payload),
    onSuccess: () => {
      invalidateSocialQueries(queryClient);
    },
  });
};

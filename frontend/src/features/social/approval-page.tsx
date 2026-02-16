import { useMemo, useState } from 'react';

import { toApiError } from '../../api/client';
import type { SocialPost, SocialStatus } from '../../api/types';
import { Badge, Button, Card, ErrorBox, Page, Skeleton } from '../../components/ui';
import { formatDateTime } from '../../utils/date';
import { useReviewSocialPost, useSocialPosts } from './hooks';

const statusVariant = (status: SocialStatus) => {
  if (status === 'approved' || status === 'published') return 'success';
  if (status === 'rejected' || status === 'failed') return 'danger';
  if (status === 'needs_revision' || status === 'publishing') return 'warning';
  return 'default';
};

type ReviewAction = Extract<SocialStatus, 'approved' | 'rejected' | 'needs_revision'>;

type ModalState = {
  post: SocialPost;
  action: ReviewAction;
} | null;

const stripHtml = (value?: string) => {
  if (!value) return 'Нет контента';
  const parser = new DOMParser();
  const doc = parser.parseFromString(value, 'text/html');
  return doc.body.textContent?.trim() || 'Нет контента';
};

export const ApprovalPage = () => {
  const query = useSocialPosts({});
  const reviewMutation = useReviewSocialPost();
  const [modal, setModal] = useState<ModalState>(null);
  const [comment, setComment] = useState('');
  const [toast, setToast] = useState<string | null>(null);

  const errorMessage = query.error ? toApiError(query.error).message : null;

  const approvalRows = useMemo(
    () =>
      (query.data ?? []).filter(
        (item) => item.status === 'ready_for_approval' || item.status === 'needs_revision',
      ),
    [query.data],
  );

  const openModal = (post: SocialPost, action: ReviewAction) => {
    if (action === 'approved') {
      reviewMutation
        .mutateAsync({ socialPostId: post.id, payload: { status: action, comment: '' } })
        .then(() => {
          setToast('Статус обновлён: согласовано');
          setTimeout(() => setToast(null), 2500);
        })
        .catch(() => undefined);
      return;
    }
    setComment('');
    setModal({ post, action });
  };

  const submitModal = async () => {
    if (!modal) return;
    if (!comment.trim()) return;

    await reviewMutation.mutateAsync({
      socialPostId: modal.post.id,
      payload: { status: modal.action, comment: comment.trim() },
    });

    setModal(null);
    setComment('');
    setToast(modal.action === 'rejected' ? 'Пост отклонён' : 'Пост отправлен на доработку');
    setTimeout(() => setToast(null), 2500);
  };

  return (
    <Page>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Согласование публикаций</h2>
        <Button onClick={() => query.refetch()}>Обновить</Button>
      </div>

      {toast ? (
        <Card className="border-emerald-200 bg-emerald-50">
          <p className="text-sm text-emerald-700">{toast}</p>
        </Card>
      ) : null}

      {errorMessage ? <ErrorBox message={errorMessage} onRetry={() => query.refetch()} /> : null}
      {reviewMutation.error ? <ErrorBox message={toApiError(reviewMutation.error).message} /> : null}

      {query.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : approvalRows.length === 0 ? (
        <Card>
          <p className="text-sm text-slate-500">Нет постов в статусах ready_for_approval / needs_revision.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {approvalRows.map((post) => (
            <Card key={post.id}>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Badge>{post.platform}</Badge>
                <Badge variant={statusVariant(post.status)}>{post.status}</Badge>
                <span className="text-xs text-slate-600">{formatDateTime(post.scheduled_at)}</span>
              </div>

              <p className="text-sm font-medium">{post.draft_post_title || `Draft ${post.draft_post}`}</p>
              <p className="mt-1 line-clamp-3 text-sm text-slate-700">{stripHtml(post.draft_content_preview)}</p>

              <div className="mt-2 grid gap-1 text-xs text-slate-600">
                <p>Попытки: {post.attempts}</p>
                {post.error_message ? <p>Ошибка: {post.error_message}</p> : null}
                {post.review_comment ? <p>Комментарий: {post.review_comment}</p> : null}
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <Button onClick={() => openModal(post, 'approved')} disabled={reviewMutation.isPending}>
                  ✅ Одобрить
                </Button>
                <Button className="bg-red-600 hover:bg-red-500" onClick={() => openModal(post, 'rejected')} disabled={reviewMutation.isPending}>
                  ❌ Отклонить
                </Button>
                <Button className="bg-amber-600 hover:bg-amber-500" onClick={() => openModal(post, 'needs_revision')} disabled={reviewMutation.isPending}>
                  🔁 На доработку
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {modal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <Card className="w-full max-w-lg">
            <h3 className="mb-2 text-lg font-semibold">
              {modal.action === 'rejected' ? 'Отклонение публикации' : 'Отправка на доработку'}
            </h3>
            <p className="mb-3 text-sm text-slate-600">Комментарий обязателен.</p>
            <textarea
              className="min-h-28 w-full rounded-md border border-slate-300 p-2 text-sm"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Опишите причину..."
            />
            <div className="mt-3 flex justify-end gap-2">
              <Button className="bg-slate-600" onClick={() => setModal(null)}>
                Отмена
              </Button>
              <Button onClick={submitModal} disabled={!comment.trim() || reviewMutation.isPending}>
                Сохранить
              </Button>
            </div>
          </Card>
        </div>
      ) : null}
    </Page>
  );
};

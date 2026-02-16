import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { toApiError } from '../../api/client';
import type { Platform, SocialStatus } from '../../api/types';
import { Badge, Button, Card, ErrorBox, Input, Page, Select, Skeleton } from '../../components/ui';
import { formatDateTime, toDateInput } from '../../utils/date';
import { useSocialPosts } from './hooks';

const statuses: SocialStatus[] = ['pending', 'ready_for_approval', 'approved', 'rejected', 'needs_revision', 'scheduled', 'publishing', 'published', 'failed'];
const platforms: Platform[] = ['vk', 'telegram', 'instagram', 'tiktok', 'youtube'];

const statusBadge = (status: SocialStatus) => {
  if (status === 'published') return 'success';
  if (status === 'failed') return 'danger';
  if (status === 'publishing') return 'warning';
  return 'default';
};

export const PostsPage = () => {
  const [searchParams] = useSearchParams();
  const [from, setFrom] = useState(searchParams.get('from') ?? toDateInput(new Date(Date.now() - 7 * 24 * 3600 * 1000)));
  const [to, setTo] = useState(searchParams.get('to') ?? toDateInput(new Date()));
  const [statusFilter, setStatusFilter] = useState('all');
  const [platformFilter, setPlatformFilter] = useState('all');
  const [onlyFailed, setOnlyFailed] = useState(false);
  const [onlyQueue, setOnlyQueue] = useState(false);

  const query = useSocialPosts({ from, to });
  const errorMessage = query.error ? toApiError(query.error).message : null;

  const rows = useMemo(() => {
    const source = query.data ?? [];
    return source.filter((row) => {
      if (statusFilter !== 'all' && row.status !== statusFilter) return false;
      if (platformFilter !== 'all' && row.platform !== platformFilter) return false;
      if (onlyFailed && row.status !== 'failed') return false;
      if (onlyQueue && !['pending', 'publishing'].includes(row.status)) return false;
      return true;
    });
  }, [query.data, statusFilter, platformFilter, onlyFailed, onlyQueue]);

  return (
    <Page>
      <Card>
        <div className="grid gap-3 md:grid-cols-6">
          <div>
            <p className="mb-1 text-xs text-slate-600">from</p>
            <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          </div>
          <div>
            <p className="mb-1 text-xs text-slate-600">to</p>
            <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
          </div>
          <div>
            <p className="mb-1 text-xs text-slate-600">status</p>
            <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="all">all</option>
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <p className="mb-1 text-xs text-slate-600">platform</p>
            <Select value={platformFilter} onChange={(e) => setPlatformFilter(e.target.value)}>
              <option value="all">all</option>
              {platforms.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={onlyFailed} onChange={(e) => setOnlyFailed(e.target.checked)} />Only failed
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={onlyQueue} onChange={(e) => setOnlyQueue(e.target.checked)} />Only pending/publishing
          </label>
        </div>
      </Card>

      {errorMessage ? <ErrorBox message={errorMessage} onRetry={() => query.refetch()} /> : null}

      <Card>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Публикации</h2>
          <Button onClick={() => query.refetch()}>Refresh</Button>
        </div>

        {query.isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        ) : rows.length === 0 ? (
          <p className="text-sm text-slate-500">Нет данных для выбранных фильтров.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="p-2">scheduled_at</th>
                  <th className="p-2">platform</th>
                  <th className="p-2">status</th>
                  <th className="p-2">attempts</th>
                  <th className="p-2">published_at</th>
                  <th className="p-2">external_id</th>
                  <th className="p-2">draft_post</th>
                  <th className="p-2">error</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className="border-b last:border-none">
                    <td className="p-2">{formatDateTime(row.scheduled_at)}</td>
                    <td className="p-2">{row.platform}</td>
                    <td className="p-2">
                      <Badge variant={statusBadge(row.status)}>{row.status}</Badge>
                    </td>
                    <td className="p-2">{row.attempts}</td>
                    <td className="p-2">{formatDateTime(row.published_at)}</td>
                    <td className="p-2">{row.external_id || '—'}</td>
                    <td className="p-2" title={row.draft_post}>
                      {row.draft_post.slice(0, 8)}...
                    </td>
                    <td className="max-w-xs truncate p-2" title={row.error_message}>
                      {row.error_message || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </Page>
  );
};

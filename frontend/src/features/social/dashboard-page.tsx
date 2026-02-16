import { useMemo, useState } from 'react';

import { toApiError } from '../../api/client';
import { Badge, Button, Card, ErrorBox, Input, Page, Skeleton } from '../../components/ui';
import { toDateInput } from '../../utils/date';
import { useHealth, useMetricsSummary, useSocialPosts } from './hooks';

export const DashboardPage = () => {
  const [from, setFrom] = useState(toDateInput(new Date(Date.now() - 7 * 24 * 3600 * 1000)));
  const [to, setTo] = useState(toDateInput(new Date()));

  const filters = useMemo(() => ({ from, to }), [from, to]);
  const metricsQuery = useMetricsSummary(filters);
  const healthQuery = useHealth();
  const postsQuery = useSocialPosts(filters);

  const metricsError = metricsQuery.error ? toApiError(metricsQuery.error).message : null;
  const healthError = healthQuery.error ? toApiError(healthQuery.error).message : null;
  const postsError = postsQuery.error ? toApiError(postsQuery.error).message : null;

  return (
    <Page>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <p className="mb-1 text-xs text-slate-600">from</p>
          <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </div>
        <div>
          <p className="mb-1 text-xs text-slate-600">to</p>
          <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        </div>
        <Button onClick={() => { metricsQuery.refetch(); healthQuery.refetch(); postsQuery.refetch(); }}>Refresh</Button>
      </div>

      {metricsError ? <ErrorBox message={metricsError} onRetry={() => metricsQuery.refetch()} /> : null}
      {healthError ? <ErrorBox message={healthError} onRetry={() => healthQuery.refetch()} /> : null}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-xs text-slate-500">Всего публикаций</p>
          {metricsQuery.isLoading ? <Skeleton className="mt-2 h-8 w-20" /> : <p className="mt-2 text-2xl font-bold">{metricsQuery.data?.total ?? 0}</p>}
        </Card>
        <Card>
          <p className="text-xs text-slate-500">Redis</p>
          <div className="mt-2">{healthQuery.isLoading ? <Skeleton className="h-6 w-20" /> : <Badge variant={healthQuery.data?.redis_ok ? 'success' : 'danger'}>{healthQuery.data?.redis_ok ? 'OK' : 'DOWN'}</Badge>}</div>
        </Card>
        <Card>
          <p className="text-xs text-slate-500">Stuck publishing</p>
          {healthQuery.isLoading ? <Skeleton className="mt-2 h-8 w-16" /> : <p className="mt-2 text-2xl font-bold">{healthQuery.data?.stuck_publishing_count ?? 0}</p>}
        </Card>
        <Card>
          <p className="text-xs text-slate-500">Превью списка</p>
          {postsQuery.isLoading ? <Skeleton className="mt-2 h-8 w-20" /> : <p className="mt-2 text-2xl font-bold">{postsQuery.data?.length ?? 0}</p>}
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="mb-2 text-sm font-medium">По статусам</h3>
          <div className="space-y-2 text-sm">
            {metricsQuery.data?.by_status.map((item) => (
              <div key={item.status} className="flex justify-between"><span>{item.status}</span><span>{item.total}</span></div>
            ))}
          </div>
        </Card>
        <Card>
          <h3 className="mb-2 text-sm font-medium">По платформам</h3>
          <div className="space-y-2 text-sm">
            {metricsQuery.data?.by_platform.map((item) => (
              <div key={item.platform} className="flex justify-between"><span>{item.platform}</span><span>{item.total}</span></div>
            ))}
          </div>
        </Card>
        <Card>
          <h3 className="mb-2 text-sm font-medium">Ошибки по платформам</h3>
          <div className="space-y-2 text-sm">
            {metricsQuery.data?.failed_by_platform.length ? metricsQuery.data.failed_by_platform.map((item) => (
              <div key={item.platform} className="flex justify-between"><span>{item.platform}</span><span>{item.total}</span></div>
            )) : <p className="text-slate-500">Нет ошибок</p>}
          </div>
        </Card>
      </div>

      {postsError ? <ErrorBox message={postsError} onRetry={() => postsQuery.refetch()} /> : null}
    </Page>
  );
};

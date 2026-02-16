import { addMonths, endOfMonth, format, startOfMonth } from 'date-fns';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { toApiError } from '../../api/client';
import { Button, ErrorBox, Page, Skeleton } from '../../components/ui';
import { MonthGrid } from '../../components/calendar/month-grid';
import { useSocialPosts } from './hooks';

export const CalendarPage = () => {
  const [month, setMonth] = useState(() => new Date());
  const navigate = useNavigate();

  const filters = useMemo(
    () => ({
      from: format(startOfMonth(month), 'yyyy-MM-dd'),
      to: format(endOfMonth(month), 'yyyy-MM-dd'),
    }),
    [month],
  );

  const query = useSocialPosts(filters);
  const errorMessage = query.error ? toApiError(query.error).message : null;

  return (
    <Page>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Календарь публикаций</h2>
        <div className="flex items-center gap-2">
          <Button className="bg-slate-600" onClick={() => setMonth((prev) => addMonths(prev, -1))}>
            ←
          </Button>
          <span className="w-40 text-center text-sm font-medium">{format(month, 'LLLL yyyy')}</span>
          <Button className="bg-slate-600" onClick={() => setMonth((prev) => addMonths(prev, 1))}>
            →
          </Button>
        </div>
      </div>

      {errorMessage ? <ErrorBox message={errorMessage} onRetry={() => query.refetch()} /> : null}

      {query.isLoading ? (
        <Skeleton className="h-[36rem]" />
      ) : (
        <MonthGrid
          month={month}
          posts={query.data ?? []}
          onDayClick={(date) => navigate(`/social/posts?from=${format(date, 'yyyy-MM-dd')}&to=${format(date, 'yyyy-MM-dd')}`)}
        />
      )}
    </Page>
  );
};

import { eachDayOfInterval, endOfMonth, endOfWeek, format, isSameMonth, startOfMonth, startOfWeek } from 'date-fns';

import type { SocialPost } from '../../api/types';
import { Badge, Card } from '../ui';

type Props = {
  month: Date;
  posts: SocialPost[];
  onDayClick?: (date: Date) => void;
};

const statusVariant = (status: SocialPost['status']) => {
  if (status === 'published') return 'success';
  if (status === 'failed') return 'danger';
  if (status === 'publishing') return 'warning';
  return 'default';
};

export const MonthGrid = ({ month, posts, onDayClick }: Props) => {
  const monthStart = startOfMonth(month);
  const intervalStart = startOfWeek(monthStart, { weekStartsOn: 1 });
  const intervalEnd = endOfWeek(endOfMonth(month), { weekStartsOn: 1 });
  const days = eachDayOfInterval({ start: intervalStart, end: intervalEnd });

  const byDate = posts.reduce<Record<string, SocialPost[]>>((acc, item) => {
    const key = format(new Date(item.scheduled_at), 'yyyy-MM-dd');
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});

  return (
    <Card>
      <div className="mb-3 grid grid-cols-7 gap-2 text-xs font-medium text-slate-500">
        {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((d) => (
          <div key={d} className="px-2">
            {d}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-2">
        {days.map((day) => {
          const key = format(day, 'yyyy-MM-dd');
          const entries = byDate[key] ?? [];
          return (
            <button
              key={key}
              type="button"
              onClick={() => onDayClick?.(day)}
              className="min-h-28 rounded-md border border-slate-200 bg-white p-2 text-left hover:border-slate-400"
            >
              <div className="mb-1 flex items-center justify-between">
                <span className={isSameMonth(day, month) ? 'text-sm text-slate-800' : 'text-sm text-slate-400'}>{format(day, 'd')}</span>
                <span className="text-xs text-slate-500">{entries.length || ''}</span>
              </div>
              <div className="space-y-1">
                {entries.slice(0, 3).map((post) => (
                  <div key={post.id} className="truncate text-xs">
                    <Badge variant={statusVariant(post.status)}>{post.platform}</Badge>
                  </div>
                ))}
                {entries.length > 3 ? <p className="text-xs text-slate-500">+{entries.length - 3} ещё</p> : null}
              </div>
            </button>
          );
        })}
      </div>
    </Card>
  );
};

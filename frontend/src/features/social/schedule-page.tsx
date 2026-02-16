import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { toApiError } from '../../api/client';
import type { Platform, SchedulePayload, ScheduleTarget } from '../../api/types';
import { Badge, Button, Card, ErrorBox, Input, Page, Select } from '../../components/ui';
import { formatDateTime } from '../../utils/date';
import { useScheduleDraft } from './hooks';

const platformOptions: Platform[] = ['vk', 'telegram', 'instagram', 'tiktok', 'youtube'];

const createTarget = (): ScheduleTarget => ({ platform: 'telegram', social_account_id: '' });

export const SchedulePage = () => {
  const navigate = useNavigate();
  const mutation = useScheduleDraft();
  const [draftId, setDraftId] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [targets, setTargets] = useState<ScheduleTarget[]>([createTarget()]);
  const [validationError, setValidationError] = useState<string | null>(null);

  const onTargetChange = (index: number, patch: Partial<ScheduleTarget>) => {
    setTargets((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (!draftId.trim()) return setValidationError('Укажите DraftPost ID.');
    if (!scheduledAt) return setValidationError('Укажите дату и время публикации.');
    if (!targets.length) return setValidationError('Нужен хотя бы один target.');

    for (const t of targets) {
      if (!t.platform) return setValidationError('Укажите platform для всех targets.');
      if (!t.social_account_id.trim()) return setValidationError('Укажите social_account_id для всех targets.');
    }

    const localDate = new Date(scheduledAt);
    // Convert datetime-local to timezone-aware ISO string
    const iso = new Date(localDate.getTime() - localDate.getTimezoneOffset() * 60000).toISOString();

    const payload: SchedulePayload = {
      scheduled_at: iso,
      targets: targets.map((t) => ({ platform: t.platform, social_account_id: t.social_account_id.trim() })),
    };

    await mutation.mutateAsync({ draftId: draftId.trim(), payload });
  };

  return (
    <Page>
      <Card>
        <h2 className="mb-4 text-lg font-semibold">Запланировать публикацию</h2>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <p className="mb-1 text-xs text-slate-600">DraftPost ID</p>
            <Input placeholder="UUID draft_post" value={draftId} onChange={(e) => setDraftId(e.target.value)} />
          </div>
          <div>
            <p className="mb-1 text-xs text-slate-600">Datetime (timezone-aware)</p>
            <Input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} />
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">Targets</p>
              <Button type="button" onClick={() => setTargets((prev) => [...prev, createTarget()])}>
                + Добавить target
              </Button>
            </div>
            {targets.map((target, index) => (
              <div key={index} className="grid gap-2 rounded-md border border-slate-200 p-3 md:grid-cols-3">
                <Select value={target.platform} onChange={(e) => onTargetChange(index, { platform: e.target.value as Platform })}>
                  {platformOptions.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </Select>
                <Input
                  placeholder="social_account_id"
                  value={target.social_account_id}
                  onChange={(e) => onTargetChange(index, { social_account_id: e.target.value })}
                />
                <Button
                  type="button"
                  className="bg-slate-600"
                  onClick={() => setTargets((prev) => prev.filter((_, i) => i !== index))}
                  disabled={targets.length === 1}
                >
                  Удалить
                </Button>
              </div>
            ))}
          </div>

          {validationError ? <ErrorBox message={validationError} /> : null}
          {mutation.error ? <ErrorBox message={toApiError(mutation.error).message} /> : null}

          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Отправка...' : 'Schedule'}
          </Button>
        </form>
      </Card>

      {mutation.data ? (
        <Card>
          <h3 className="mb-2 text-sm font-semibold">Результат</h3>
          <div className="space-y-2 text-sm">
            {mutation.data.map((item) => (
              <div key={item.id} className="rounded border border-slate-200 p-2">
                <div className="flex items-center gap-2">
                  <Badge>{item.platform}</Badge>
                  <Badge>{item.status}</Badge>
                </div>
                <p>Scheduled: {formatDateTime(item.scheduled_at)}</p>
                <p>ID: {item.id}</p>
              </div>
            ))}
          </div>
          <Button className="mt-3" onClick={() => navigate('/social/posts')}>
            Перейти к списку публикаций
          </Button>
        </Card>
      ) : null}
    </Page>
  );
};

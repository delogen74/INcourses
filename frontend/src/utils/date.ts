import { format } from 'date-fns';

export const formatDateTime = (value?: string | null) => {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '—';
  return format(d, 'dd.MM.yyyy HH:mm');
};

export const toDateInput = (value: Date) => format(value, 'yyyy-MM-dd');

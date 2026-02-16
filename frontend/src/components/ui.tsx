import type { ButtonHTMLAttributes, InputHTMLAttributes, PropsWithChildren, SelectHTMLAttributes } from 'react';

import { cn } from '../utils/cn';

export const Page = ({ children }: PropsWithChildren) => (
  <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">{children}</div>
);

export const Card = ({ children, className }: PropsWithChildren<{ className?: string }>) => (
  <section className={cn('rounded-xl border border-slate-200 bg-white p-4 shadow-sm', className)}>{children}</section>
);

export const Button = ({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button
    className={cn(
      'rounded-md bg-slate-900 px-3 py-2 text-sm text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50',
      className,
    )}
    {...props}
  />
);

export const Input = ({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) => (
  <input
    className={cn('w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none ring-slate-300 focus:ring', className)}
    {...props}
  />
);

export const Select = ({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) => (
  <select className={cn('w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none ring-slate-300 focus:ring', className)} {...props} />
);

export const Badge = ({ children, variant = 'default' }: PropsWithChildren<{ variant?: 'default' | 'success' | 'danger' | 'warning' }>) => {
  const variants = {
    default: 'bg-slate-100 text-slate-800',
    success: 'bg-emerald-100 text-emerald-800',
    danger: 'bg-red-100 text-red-800',
    warning: 'bg-amber-100 text-amber-800',
  };
  return <span className={cn('inline-flex rounded-full px-2 py-1 text-xs font-medium', variants[variant])}>{children}</span>;
};

export const ErrorBox = ({ message, onRetry }: { message: string; onRetry?: () => void }) => (
  <Card className="border-red-200 bg-red-50">
    <p className="text-sm text-red-700">{message}</p>
    {onRetry && (
      <Button className="mt-3 bg-red-600 hover:bg-red-500" onClick={onRetry}>
        Повторить
      </Button>
    )}
  </Card>
);

export const Skeleton = ({ className }: { className?: string }) => (
  <div className={cn('animate-pulse rounded bg-slate-200', className)} />
);

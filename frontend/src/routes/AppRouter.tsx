import { NavLink, Navigate, Route, Routes } from 'react-router-dom';

import { SettingsPage } from '../features/settings/settings-page';
import { ApprovalPage } from '../features/social/approval-page';
import { CalendarPage } from '../features/social/calendar-page';
import { DashboardPage } from '../features/social/dashboard-page';
import { PostsPage } from '../features/social/posts-page';
import { SchedulePage } from '../features/social/schedule-page';
import { cn } from '../utils/cn';

const navItems = [
  { to: '/social/dashboard', label: 'Dashboard' },
  { to: '/social/approval', label: 'Согласование' },
  { to: '/social/calendar', label: 'Календарь' },
  { to: '/social/posts', label: 'Публикации' },
  { to: '/social/schedule', label: 'Планирование' },
  { to: '/settings', label: 'Настройки' },
];

export const AppRouter = () => (
  <div className="min-h-screen bg-slate-50">
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-7xl items-center gap-3 p-4">
        <h1 className="mr-4 text-lg font-semibold">INcourses Social Console</h1>
        <nav className="flex flex-wrap gap-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100',
                  isActive && 'bg-slate-900 text-white hover:bg-slate-900',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>

    <Routes>
      <Route path="/social/dashboard" element={<DashboardPage />} />
      <Route path="/social/approval" element={<ApprovalPage />} />
      <Route path="/social/calendar" element={<CalendarPage />} />
      <Route path="/social/posts" element={<PostsPage />} />
      <Route path="/social/schedule" element={<SchedulePage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="*" element={<Navigate to="/social/dashboard" replace />} />
    </Routes>
  </div>
);

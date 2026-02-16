# INcourses Frontend

Production-ready frontend for INcourses social pipeline.

## Stack
- Vite + React + TypeScript
- Tailwind CSS
- TanStack Query
- React Router
- Axios
- date-fns

## Environment
Create `.env` from template:

```bash
cp .env.example .env
```

Set:

```env
VITE_API_BASE_URL=http://localhost:8000
```

All requests use `${VITE_API_BASE_URL}/api/...`.

## Run
```bash
npm install
npm run dev
```

## Routes
- `/social/dashboard` — metrics + health + date filter
- `/social/approval` — approval workflow for ready/revision posts
- `/social/calendar` — month calendar with posts grouped by day
- `/social/posts` — social posts table with filters and quick toggles
- `/social/schedule` — schedule form for `/api/draft-posts/{id}/schedule/`
- `/settings` — token management + API base URL

## Authentication behavior
- Token from `/settings` is stored in `localStorage` and sent as `Authorization: Bearer <token>`.
- If token is empty, requests are sent without Authorization header.
- 401/403 errors are normalized as: `Недостаточно прав / требуется вход`.

## Notes
If backend is unavailable, the UI shows retriable error cards on each page.

`datetime-local` value in schedule form is converted to timezone-aware ISO before sending to backend.

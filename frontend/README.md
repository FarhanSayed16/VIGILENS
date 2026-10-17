# Frontend (React + Vite + TypeScript)

Phase **4** scaffold: Daylight Lecture theme, app shell, stub routes.

## Run

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

- Login is a **scaffold gate** (any non-empty password). Real JWT arrives in Phase 6.
- API base URL: `VITE_API_BASE_URL` (see `.env.example`)

## Layout

```text
src/
├── app/           # shell, router, auth gate
├── pages/         # route pages (stubs → filled later)
├── components/    # ui + domain + charts
├── api/           # fetch client
├── styles/        # tokens + global + shell
├── stores/        # scaffold auth flag
├── hooks/, utils/, assets/, features/
└── main.tsx
```

## Theme

**Daylight Lecture** — teal accent, amber for review signals, graphite for weak coverage (tokens in `styles/tokens.css`). Icons: Lucide. Motion: Framer Motion page transitions with `prefers-reduced-motion` respect.

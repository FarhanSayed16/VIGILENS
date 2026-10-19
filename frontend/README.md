# Frontend (React + Vite + TypeScript)

Lecturer UI — Daylight Lecture theme, session subnav, Results charts, Export/Pulse/Settings.

## Run

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API must be on `VITE_API_BASE_URL` (default `http://localhost:8000`).

## Layout

```text
src/
├── app/           # shell, router, auth
├── pages/         # login → sessions → setup → live → analysis → results → export …
├── components/    # ui + domain + charts
├── api/
├── styles/        # tokens + shell
└── main.tsx
```

Motion respects `prefers-reduced-motion`. Full stack: [../README.md](../README.md).

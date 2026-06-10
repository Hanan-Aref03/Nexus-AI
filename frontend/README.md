# Frontend

Next.js dashboard for investigations, findings, incidents, dependency graphs, and copilot interactions.

## Intended Internal Shape

- `app/` - application routes and page shells
- `components/` - reusable UI primitives and composed components
- `lib/` - server-side backend access, derived dashboard logic, and shared types

## Current Phase 3 Routes

- `/` - live dashboard overview
- `/findings` - searchable evidence stream
- `/incidents` - incident room and dependency map
- `/incidents/[incidentId]` - deep incident detail and postmortem draft
- `/graph` - service relationship map
- `/postmortems` - reusable postmortem summary

## Local Run

From the `frontend/` directory:

```bash
npm install
npm run dev
```

From the repository root with Docker:

```bash
docker compose up --build
```

The UI should feel like an operations console, not a generic admin template.

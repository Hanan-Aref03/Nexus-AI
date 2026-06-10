# Phase 3 - Investigation UX

## Purpose

Expose the intelligence created in Phase 2 through a useful dashboard and investigation flow.

## What This Phase Delivers

- Tenant-aware login and signup entry points
- Findings list and incident detail views
- Service impact graph or relationship map
- Postmortem summary generation
- Clear visual prioritization of the most important issues

## Dependencies

- Findings and incidents must already exist
- The data model needs stable identifiers and enough metadata for UI navigation

## Notes

- Keep the UI operational, not decorative
- Show evidence and context first, not just abstract scores
- Make the incident timeline easy to explain in a review or postmortem
- Use a polished, role-aware shell with cards, badges, and panels so the workspace feels focused and easy to scan
- Prefer server-rendered workspace data with a signed session seam, then layer client-side interactivity on top of the live snapshot
- Keep the frontend in the same Docker compose workflow as the backend so `docker compose up --build` brings up the full local stack

## Phase 3 Implementation Slice

- `app/login/page.tsx` and `app/signup/page.tsx` provide tenant-aware entry points
- `app/page.tsx` shows the dashboard overview with findings, incidents, relationship map, and postmortem draft
- `app/findings/page.tsx` exposes the searchable evidence stream
- `app/incidents/page.tsx` and `app/incidents/[incidentId]/page.tsx` expose the incident room and deep investigation view
- `app/graph/page.tsx` presents the service relationship map and blast-radius view
- `app/postmortems/page.tsx` gives the team a structured summary surface for review and handoff

## Local Commands

From the repository root:

```bash
docker compose up --build
```

From the `frontend/` directory:

```bash
npm install
npm run dev
```

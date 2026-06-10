# Frontend App

This directory will hold the Next.js route tree and page-level layouts.

Expected early routes include:

- login and signup
- dashboard overview
- findings
- incidents
- impact map
- summary draft

Keep the route layer thin and push business-specific behavior into feature modules.

## Implemented Routes

- `app/login/page.tsx` - workspace access
- `app/signup/page.tsx` - workspace creation
- `app/page.tsx` - dashboard overview
- `app/findings/page.tsx` - evidence stream
- `app/incidents/page.tsx` - incident room
- `app/incidents/[incidentId]/page.tsx` - incident deep dive
- `app/graph/page.tsx` - impact map
- `app/postmortems/page.tsx` - summary drafting surface

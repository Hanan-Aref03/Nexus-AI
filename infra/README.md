# Infra

Deployment, local development, and environment definitions for the NexusAI platform.

## Intended Internal Shape

- `docker/` - local compose and container definitions
- `k8s/` - Kubernetes manifests or helm charts
- `terraform/` - cloud infrastructure provisioning

## PR1 Runtime

- `docker/docker-compose.yml` boots PostgreSQL with the pgvector extension and the FastAPI backend
- `docker/postgres/init/001_enable_pgvector.sql` enables `vector` on first database start

## Local Start

```bash
docker compose -f infra/docker/docker-compose.yml up --build
```

The first infrastructure PR should make local development predictable before any production automation is added.

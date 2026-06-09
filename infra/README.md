# Infra

Deployment, local development, and environment definitions for the NexusAI platform.

## Intended Internal Shape

- `docker/` - local compose and container definitions
- `k8s/` - Kubernetes manifests or helm charts
- `terraform/` - cloud infrastructure provisioning

The first infrastructure PR should make local development predictable before any production automation is added.

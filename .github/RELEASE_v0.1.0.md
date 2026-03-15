# v0.1.0 — Initial MVP

**ChangeTrail: What changed before this alert?**

Unified change timeline for incident response. Collects infrastructure changes from Kubernetes, GitHub, and AWS into a single timeline so you can answer "what changed?" in seconds.

## Highlights

- **Kubernetes collector** — watches deployments, pod restarts, configmap changes, scaling events
- **GitHub collector** — push events, PR merges, releases via webhooks
- **Timeline API** — query by time range, source, service, namespace
- **React UI** — dark-themed timeline with filters and real-time refresh
- **Slack integration** — `/changetrail last 30m` from any channel
- **Demo mode** — `python3 -m changetrail demo` shows a realistic incident timeline instantly
- **Docker Compose** — `make up` runs the full stack in one command
- **Helm chart** — ready for Kubernetes deployment

## Quick Start

```bash
git clone --branch v0.1.0 https://github.com/cvemula1/ChangeTrail.git
cd ChangeTrail
make up
```

Open http://localhost:3000 to see the UI.

## What's Next

- ArgoCD, Terraform, GitLab collectors
- Alert + change correlation
- Event detail view in UI
- Dark/light theme toggle

See [CONTRIBUTING.md](https://github.com/cvemula1/ChangeTrail/blob/main/CONTRIBUTING.md) to get involved.

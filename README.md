# ChangeTrail

> What changed in my system before this alert?

Open-source tool that gives you a **unified timeline of infrastructure changes** — deployments, config edits, IAM modifications, pod restarts — across all your systems in one place.

During an incident you're jumping between ten dashboards trying to figure out what changed. ChangeTrail collects those events automatically and shows them on a single timeline so you can answer that question in seconds.

```
Alert: API latency spike

Recent system changes (last 30 minutes)
────────────────────────────────────────
12:41  deploy    checkout-service v1.23           (kubernetes)
12:43  update    configmap checkout-config         (kubernetes)
12:45  restart   pod checkout-service-7f8b9 ×3     (kubernetes)
12:48  modify    iam-role checkout-svc-role         (aws)
```

## Try it in 60 seconds

```bash
# No dependencies needed — just see it work
git clone https://github.com/cvemula1/ChangeTrail.git
cd ChangeTrail
python3 -m changetrail demo
```

You'll immediately see:

```
  ChangeTrail — Demo Timeline
  ═══════════════════════════════════════════════════════
  Scenario: API latency spike on checkout-service
  ───────────────────────────────────────────────────────

  11:56  · deployed payment-service → v3.8                       (kubernetes)
  12:06  · release v2.1.0 published for shared-lib               (github)
  12:11  · updated configmap feature-flags                       (kubernetes)
  12:19  · PR #142 merged: Add Redis caching layer               (github)
  12:25  · push to main: 3 commit(s) by alice                   (github)
  12:29  · deployed checkout-service → v1.23                     (kubernetes)
  12:31  · updated configmap checkout-config                     (kubernetes)
  12:35  ▲ restarted pod checkout-service-7f8b9c6d4-x2k9p (×2)  (kubernetes)
  12:37  ▲ restarted pod checkout-service-7f8b9c6d4-m4n5o (×3)  (kubernetes)
  12:39  ▲ modified iam-role checkout-svc-role — policy attached  (aws)
  12:42  · scaled checkout-service (3 → 5 replicas)              (kubernetes)
```

The deployment at 12:29 likely caused the pod restart spike. **That's the value.**

## Install

```bash
# Latest
git clone https://github.com/cvemula1/ChangeTrail.git

# Specific release
git clone --branch v0.1.0 https://github.com/cvemula1/ChangeTrail.git

# Or install as a Python package
pip install git+https://github.com/cvemula1/ChangeTrail.git@v0.1.0
```

## Quick Start (full stack)

```bash
# One command — builds and starts everything in Docker
make up
```

This runs Postgres + API + UI, seeds demo data, and prints the URLs:

| Service | URL |
|---------|-----|
| UI | http://localhost:3000 |
| API | http://localhost:8000/api/v1/changes |
| Swagger docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

To stop: `make down`

## Local Development

```bash
make dev    # DB in Docker + API with hot reload
make ui     # Start UI dev server (separate terminal)
make demo   # Print demo timeline (zero dependencies)
make test   # Run tests
make lint   # Run linter
make help   # Show all commands
```

## Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Kubernetes   │  │    GitHub    │  │     AWS      │
│  Collector    │  │  Collector   │  │  Collector   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────┬────────┴────────┬────────┘
                │                 │
         ┌──────▼───────┐  ┌─────▼────────┐
         │  Normalizer  │  │  Webhook API │
         └──────┬───────┘  └─────┬────────┘
                │                │
         ┌──────▼────────────────▼──┐
         │       Event Store        │
         │      (PostgreSQL)        │
         └──────────┬───────────────┘
                    │
              ┌─────▼─────┐
              │ Timeline   │
              │   API      │
              └─────┬──────┘
                    │
              ┌─────▼─────┐
              │    UI      │
              └────────────┘
```

## Project Structure

```
changetrail/
├── api/              # FastAPI timeline API
├── collectors/       # Event source plugins
│   ├── kubernetes/   # K8s watcher
│   ├── github/       # GitHub webhook + poller
│   └── aws/          # CloudTrail ingestion
├── core/             # Event model, normalizer, store
├── ui/               # React frontend
├── helm/             # Kubernetes Helm chart
├── docker-compose.yml
└── tests/
```

## Supported Sources

| Source | Events | Status |
|--------|--------|--------|
| **Kubernetes** | Deployments, Pod restarts, ConfigMap changes | ✅ MVP |
| **GitHub** | Deployments, Push events | ✅ MVP |
| **AWS CloudTrail** | IAM, EC2, S3 changes | 🔜 Planned |
| **Azure Activity Log** | Resource changes | 🔜 Planned |
| **Terraform** | Plan/apply events | 🔜 Community |
| **ArgoCD** | Sync events | 🔜 Community |

## API

```bash
# Recent changes (last 30 minutes)
GET /api/v1/changes?last=30m

# Changes for a specific service
GET /api/v1/changes?service=checkout-service

# Changes since timestamp
GET /api/v1/changes?since=2026-03-14T12:00:00Z

# Changes by source
GET /api/v1/changes?source=kubernetes
```

## Slack Integration

```
/changetrail last 30m
```

```
🔵 12:29 ☸️ deployed checkout-service → v1.23
🔵 12:31 ☸️ updated configmap checkout-config
🟡 12:35 ☸️ restarted pod checkout-service-7f8b9c6d4-x2k9p (×2)
🟡 12:37 ☸️ restarted pod checkout-service-7f8b9c6d4-m4n5o (×3)
🟡 12:39 ☁️ modified iam-role checkout-svc-role — policy attached
```

Setup: point your Slack slash command to `https://your-domain/api/v1/integrations/slack/command`

## Roadmap

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | Unified change timeline (MVP) | 🔧 In Progress |
| 2 | Alert + change correlation | 🔜 Next |
| 3 | AI incident explanation | 📋 Planned |
| 4 | Remediation suggestions | 📋 Planned |
| 5 | Autonomous DevSecOps agent | 📋 Vision |

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow, branch naming, and how to add a new collector.

Good first contributions:
- Add a new event source collector (ArgoCD, Terraform, GitLab)
- Improve the UI
- Write more tests
- Fix something from the [issue tracker](https://github.com/cvemula1/ChangeTrail/issues)

## Versioning

We use [semantic versioning](https://semver.org/). Releases are tagged on `main`.

```bash
git tag -a v0.1.0 -m "Initial MVP"
git push origin v0.1.0
```

See [Releases](https://github.com/cvemula1/ChangeTrail/releases) for changelog.

## License

MIT — see [LICENSE](LICENSE) for details.

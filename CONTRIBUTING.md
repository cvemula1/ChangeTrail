# Contributing to ChangeTrail

Thanks for your interest. Here's how to get involved.

## Get the code

```bash
# Clone the latest release
git clone https://github.com/cvemula1/ChangeTrail.git
cd ChangeTrail

# Or clone a specific version
git clone --branch v0.1.0 https://github.com/cvemula1/ChangeTrail.git
```

## Set up your dev environment

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make test          # run tests (no Docker needed)
make demo          # see it work instantly
```

To run the full stack locally:

```bash
make up            # Docker Compose: DB + API + UI + seed data
# or, without Docker for the API:
make dev           # DB in Docker, API with hot reload
```

## Making changes

### Branch naming

| Type | Branch name |
|------|------------|
| Feature | `feat/short-description` |
| Bug fix | `fix/short-description` |
| Docs | `docs/short-description` |
| Collector plugin | `plugin/source-name` |

### PR workflow

1. Fork the repo and create your branch from `main`
2. Write your code and add tests
3. Run `make test` and `make lint`
4. Push and open a Pull Request against `main`
5. Fill in the PR description — what changed and why
6. Wait for review; address any feedback

Keep PRs focused. One feature or fix per PR.

### Commit messages

Use clear, descriptive messages:

```
feat: add ArgoCD collector
fix: handle empty namespace in k8s events
docs: update Slack setup instructions
test: add normalizer edge case coverage
```

## Releases and tags

We use [semantic versioning](https://semver.org/):

- **v0.1.0** — initial MVP
- **v0.2.0** — new features (e.g. new collector)
- **v0.1.1** — bug fixes only

Releases are tagged on `main` and published on GitHub Releases.
To install a specific version:

```bash
pip install git+https://github.com/cvemula1/ChangeTrail.git@v0.1.0
```

## Adding a new collector

1. Create `changetrail/collectors/your_source/collector.py`
2. Subclass `BaseCollector` (poll-based) or `WebhookCollector` (push-based)
3. Emit `ChangeEvent` objects — that's the only contract
4. Register it in `changetrail/collectors/registry.py`
5. Add tests under `tests/`
6. Update `README.md` supported sources table

See the Kubernetes and GitHub collectors for working examples.

## Ground rules

- All events normalize to `ChangeEvent` — no source-specific schemas leak out
- Add tests for new code
- Use type hints everywhere
- Run `make lint` before pushing
- Don't commit `.env` files or secrets

## Code style

- **Python**: PEP 8, type hints, `ruff` for linting
- **TypeScript**: follow existing patterns in `ui/src/`
- Line length: 100 chars

## Questions?

Open an [issue](https://github.com/cvemula1/ChangeTrail/issues) or start a discussion. Happy to help.

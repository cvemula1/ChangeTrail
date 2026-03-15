# Good First Issues

Copy-paste these into GitHub Issues (https://github.com/cvemula1/ChangeTrail/issues/new).
Add labels: `good first issue`, `help wanted`, and the relevant label below.

---

## Issue 1: Add ArgoCD collector plugin

**Labels**: `good first issue`, `help wanted`, `plugin`

### Description

Add an ArgoCD collector that watches for sync events and converts them to ChangeTrail's `ChangeEvent` format.

ArgoCD exposes application sync status via its API and can send webhook notifications. Either approach works.

### Events to capture

- Application synced (deployed)
- Sync failed
- Health status changed (healthy → degraded)
- Rollback triggered

### Implementation guide

1. Create `changetrail/collectors/argocd/collector.py`
2. Subclass `BaseCollector` (poll ArgoCD API) or `WebhookCollector` (receive webhooks)
3. Map ArgoCD events → `ChangeEvent` with appropriate `action` and `severity`
4. Register in `changetrail/collectors/registry.py`
5. Add tests in `tests/test_argocd_collector.py`

### References

- [ArgoCD API docs](https://argo-cd.readthedocs.io/en/stable/developer-guide/api-docs/)
- [ArgoCD notifications](https://argo-cd.readthedocs.io/en/stable/operator-manual/notifications/)
- Look at `changetrail/collectors/kubernetes/collector.py` for a working example

---

## Issue 2: Add Terraform Cloud collector

**Labels**: `good first issue`, `help wanted`, `plugin`

### Description

Add a Terraform Cloud/Enterprise collector that captures plan and apply events via webhooks.

### Events to capture

- Plan started / completed
- Apply started / completed / failed
- State changed (resource created/updated/destroyed)
- Run errored

### Implementation guide

1. Create `changetrail/collectors/terraform/collector.py`
2. Subclass `WebhookCollector` (Terraform Cloud sends run notifications)
3. Parse the webhook payload → `ChangeEvent`
4. Register in `changetrail/collectors/registry.py`
5. Add tests

### References

- [Terraform Cloud notifications](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/settings/notifications)
- Look at `changetrail/collectors/github/collector.py` for webhook handling

---

## Issue 3: Add GitLab collector

**Labels**: `good first issue`, `help wanted`, `plugin`

### Description

Add a GitLab webhook collector for push events, merge requests, pipeline completions, and deployments.

### Events to capture

- Push to branch
- Merge request merged
- Pipeline succeeded / failed
- Deployment created

### Implementation guide

1. Create `changetrail/collectors/gitlab/collector.py`
2. Subclass `WebhookCollector`
3. Handle GitLab webhook events (different payload format than GitHub)
4. Register in registry, add tests

### References

- [GitLab webhook events](https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html)
- Look at `changetrail/collectors/github/collector.py` for a similar implementation

---

## Issue 4: Add dark/light theme toggle to UI

**Labels**: `good first issue`, `help wanted`, `ui`

### Description

The UI currently uses a dark theme. Add a toggle button in the header to switch between dark and light modes.

### Acceptance criteria

- Toggle button in the header (sun/moon icon from Lucide)
- Persists preference in `localStorage`
- Defaults to dark mode
- Smooth transition between themes

### Files to modify

- `ui/src/components/Header.tsx` — add toggle button
- `ui/src/App.tsx` — manage theme state
- `ui/src/index.css` — add light theme colors

---

## Issue 5: Add event detail drawer/modal

**Labels**: `good first issue`, `help wanted`, `ui`

### Description

Clicking an event in the timeline should open a side drawer or modal showing the full event details, including raw metadata and labels.

### Acceptance criteria

- Click event row → drawer slides in from right (or modal opens)
- Shows all event fields including `metadata` as formatted JSON
- Close button and click-outside-to-close
- Keyboard accessible (Escape to close)

### Files to modify

- `ui/src/components/Timeline.tsx` — add click handler
- Create `ui/src/components/EventDetail.tsx`

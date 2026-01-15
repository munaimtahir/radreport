# Production logging (stdout/stderr)

Backend logs are emitted to stdout/stderr so they show up in container or systemd
log collectors. Use the commands below based on how the backend is deployed.

## Docker

```bash
docker logs -f <backend_container>
```

## systemd

```bash
journalctl -u <backend_service> -f
```

## What to look for

Workflow transitions emit structured log entries with IDs and actions. Search for
`workflow_transition` and confirm the log includes:

- `service_visit_id`
- `service_visit_item_id`
- `from_status` → `to_status`
- `event=workflow_transition`

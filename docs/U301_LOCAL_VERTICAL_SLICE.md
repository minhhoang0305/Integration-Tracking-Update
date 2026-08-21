# U301 local vertical slice

This test uses a Gmail sender only as a local trigger. It maps `gmail.com` to U301, so do not use this registry in production.

## Configure the local registry

```sh
cp backend/Configuration/provider-integrations.local.example.json backend/Configuration/provider-integrations.local.json
export Templates__RegistryPath="Configuration/provider-integrations.local.json"
```

Start the native backend with that environment variable, alongside the local RabbitMQ, PostgreSQL, and AI worker. The current U301 manifest is in `integrations/u301/actions_manifest.json`; the verified new snapshot remains in `test-fixtures/u301/actions_manifest.new.json`.

## Expected result

Send the U301 notice and trigger Gmail sync. The resulting proposal is `Pending` and contains:

- 8 removed legacy actions;
- 10 added `/v3/shorten` actions;
- top-level changes including `executor` and `provider_config`;
- an impact analysis with overall severity `High`: 8 affected existing actions, 10 new actions, and configuration-change severity;
- generated `actions_manifest.json`, `diff.patch`, `CHANGELOG.md`, `evidence.json`, and `impact.json` below `backend/proposals/<proposal-id>/`.

`GET /api/reviews/{proposal-id}` returns the structured `impact` field. `GET /api/reviews` includes `impactSeverity` for filtering or sorting. The provider-update event also contains `provider: "u301"` and `integrationId: "u301-shortener"` when the local registry resolves the Gmail sender.

Approval records an audit decision only. It never overwrites `integrations/u301/actions_manifest.json`.

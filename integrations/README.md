# Integration action manifests

Each integration owns one `actions_manifest.json`. Register its provider mapping in `backend/Configuration/provider-integrations.json`.

Generated proposals are written below `backend/proposals/` and never modify files in this directory.

For the local U301 vertical slice, the current manifest is `u301/actions_manifest.json`. The verified replacement snapshot lives in `test-fixtures/u301/`; it is copied into a proposal artifact only after an email triggers the workflow.

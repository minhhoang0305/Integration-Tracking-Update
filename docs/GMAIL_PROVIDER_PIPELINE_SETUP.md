# Gmail Provider Pipeline Setup

## Google Cloud

1. Create a Google Cloud project and enable **Gmail API** and **Cloud Pub/Sub API**.
2. Configure the OAuth consent screen and add the Gmail service mailbox as a test user while the app is in testing.
3. Create an OAuth client of type **Desktop app**. Do not commit its client secret.
4. Create a Pub/Sub topic, such as `projects/<project-id>/topics/gmail-provider-updates`.
5. Grant `roles/pubsub.publisher` on that topic to `gmail-api-push@system.gserviceaccount.com`.
6. Create a push subscription targeting `https://<public-host>/api/gmail/push`; configure an authenticated OIDC push token in production.

The backend requests only `https://www.googleapis.com/auth/gmail.readonly`; it never marks, moves, deletes, or sends email.

## Local configuration

Set values in the terminal that starts the backend. Keep secrets out of `appsettings.json`.

```powershell
$env:Gmail__ClientId = "<oauth-client-id>"
$env:Gmail__ClientSecret = "<oauth-client-secret>"
$env:Gmail__ServiceMailbox = "provider-notifications@gmail.com"
$env:Gmail__PubSubTopic = "projects/<project-id>/topics/gmail-provider-updates"
$env:Gmail__AllowedSenderDomains__0 = "stripe.com"
$env:ProposalLlm__ApiKey = "<llm-api-key>"
$env:ProposalLlm__Model = "<structured-json-capable-model>"
```

Run the backend, then bootstrap Gmail OAuth locally:

```powershell
cd backend
dotnet run
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/gmail/oauth/bootstrap"
```

The refresh token is encrypted with Windows DPAPI at `%LOCALAPPDATA%\IntegrationTracking\gmail`.

## Registry and manifests

Copy `backend/Configuration/provider-integrations.example.json` into `provider-integrations.json`, then add real providers and manifest paths.

Each manifest must contain an `actions` array. Generated proposals are stored under `backend/proposals/<proposal-id>/` with `actions_manifest.json`, `CHANGELOG.md`, `diff.patch`, and `evidence.json`. The source manifest is never modified.

## Review API

- `GET /api/reviews`
- `GET /api/reviews/{id}`
- `POST /api/reviews/{id}/approve`
- `POST /api/reviews/{id}/reject`
- `POST /api/reviews/{id}/regenerate`

Approval stores only the audit decision. Applying a proposal remains a manual Git change.

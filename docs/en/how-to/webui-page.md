# Standalone WebUI

## Scope

Sharelife WebUI runs standalone; you do not need AstrBot Dashboard embedding.
This public page documents the public/member experience only:

1. Spotlight-style market search
2. local installation management
3. template upload and profile-pack community submission
4. task/result tracking on the member side

Privileged moderation and operator workflows are intentionally documented in private docs only.

## Config

```json
{
  "webui": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 8106,
    "cors": {
      "allow_origins": ""
    },
    "security_headers": {
      "enabled": true,
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "no-referrer",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
      "Content-Security-Policy": "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; form-action 'self'"
    },
    "auth": {
      "member_password": "",
      "token_ttl_seconds": 7200,
      "allow_query_token": false,
      "allow_anonymous_member": false,
      "anonymous_member_user_id": "webui-user",
      "anonymous_member_allowlist": [
        "POST /api/trial",
        "GET /api/trial/status",
        "POST /api/templates/install",
        "GET /api/member/installations",
        "POST /api/member/installations/refresh",
        "GET /api/preferences",
        "POST /api/preferences/mode",
        "POST /api/preferences/observe"
      ],
      "login_rate_limit_window_seconds": 60,
      "login_rate_limit_max_attempts": 10,
      "api_rate_limit_window_seconds": 60,
      "api_rate_limit_max_requests": 600
    },
    "observability": {
      "metrics_max_paths": 128,
      "metrics_overflow_path_label": "/__other__"
    }
  }
}
```

## Auth behavior

1. Empty auth fields keep the public/member surface available.
2. `member_password` enables login gating for protected member actions.
3. `GET /api/ui/capabilities` stays readable before login so the UI can capability-gate controls.
4. Query token auth is off by default; use `Authorization: Bearer <token>`.
5. Login attempts are rate-limited by `login_rate_limit_*`.
6. API requests are rate-limited by `api_rate_limit_*` (`client + role + path` scope).
7. Default responses include `security_headers`, including `Content-Security-Policy`.
8. If `allow_anonymous_member=true`, only the configured anonymous allowlist can run without login, and requests stay pinned to `anonymous_member_user_id`.
9. Privileged auth procedures, secret material, and backup/restore runbooks stay in private docs.
10. Standalone local AstrBot import is disabled by default for safer host deployments. Enable only when required:
   - CLI: `python3 scripts/run_sharelife_webui_standalone.py --enable-local-astrbot-import`
   - Env: `SHARELIFE_ENABLE_LOCAL_ASTRBOT_IMPORT=1`
   - Optional anonymous local import: `--allow-anonymous-local-astrbot-import` / `SHARELIFE_ALLOW_ANONYMOUS_LOCAL_ASTRBOT_IMPORT=1`
11. Local AstrBot auto-detection accepts optional host hints:
   - `SHARELIFE_ASTRBOT_CONFIG_PATH=/absolute/path/to/cmd_config.json`
   - `SHARELIFE_ASTRBOT_CONFIG_PATH=/path/a:/path/b` (Windows uses `;`)
   - `SHARELIFE_ASTRBOT_SEARCH_ROOTS=/path/root-a:/path/root-b` (Windows uses `;`)
   - `SHARELIFE_ASTRBOT_HOME=/path/to/astrbot`

## Start and routes

1. Plugin startup attempts to launch WebUI automatically.
2. Run `/sharelife_webui` to get the URL.
3. Public/member-facing routes:
   - `/` integrated entry
   - `/member` member-focused console
   - `/market` standalone market page
4. Restricted operator routes exist, but they are intentionally not described in the public docs.

### Container quick start

```bash
docker compose up -d --build
```

Then open `http://127.0.0.1:8106`.
Data is persisted under `./output/docker-data`.
Compose defaults to `state_store.backend=sqlite` with `./output/docker-data/sharelife_state.sqlite3`.

## Member workflows

### 1. Store Search + Trial Status

1. `/member` and `/market` both lead with a spotlight-style search surface.
2. Search feeds catalog cards, detail, and compare.
3. `Trial Status` shows `not_started|active|expired`, plus `ttl_seconds` and `remaining_seconds`.

### 2. Manage Installations

1. Load your local installation list.
2. Use `Refresh Local Installations` to resync the visible state.
3. Per-installation actions include:
   - `Reinstall`
   - `Uninstall`
4. Install controls support:
   - `preflight`
   - `force_reinstall`
   - `source_preference=auto|uploaded_submission|generated`

### 3. Template Upload Chain

1. Open the upload area in `/member`.
2. Select a file or use generated package output.
3. Direct package upload is capped at `20 MiB`.
4. Upload options:
   - `scan_mode=strict|balanced`
   - `visibility=community|private`
   - `replace_existing=true|false`
5. After submit, open `My Submissions` to inspect detail and download your own original package.

### 4. Profile-Pack Community Submission Chain

1. Prepare a profile-pack artifact and copy its `artifact_id`.
2. Submit it from `/member` or `/market`.
3. Submit options:
   - `pack_type`
   - `selected_sections`
   - `redaction_mode`
   - `replace_existing`
4. Open `My Profile-Pack Submissions` to inspect detail and download your own export.

### 5. Capability Gating and Error Model

1. Button-level operations are gated from backend policy via `/api/ui/capabilities`.
2. Auth/rate-limit/internal failures return a unified shape:
   `{"ok": false, "error": {"code": "...", "message": "..."}}`
3. Owner mismatch returns `permission_denied`.
4. Oversized template uploads return `package_too_large`.
5. Risk scan hits such as `prompt_injection_detected` are surfaced as review signals, not silent deletion.

## Public/private boundary

1. Public docs cover search, install, upload, and member-scoped submission management.
2. Public docs do not expose moderation actions, privileged apply/rollback, secret handling, or backup/restore SOP.

## Troubleshooting

1. `401`: auth is enabled and the protected member action requires login.
2. `permission_denied`: the current token cannot access the requested `user_id` or action.
3. `package_too_large`: uploaded template package exceeded the `20 MiB` limit.
4. `prompt_injection_detected`: the package was flagged and escalated for review.
5. Wrong locale after manual browser storage edits: remove `sharelife.uiLocale` and refresh.
6. Wrong developer-mode state after manual browser storage edits: remove `sharelife.developerMode` and refresh.

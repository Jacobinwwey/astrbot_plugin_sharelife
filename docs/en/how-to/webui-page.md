# Standalone WebUI

## Scope

Sharelife WebUI runs standalone; you do not need AstrBot Dashboard embedding.
Use it for trial, moderation, apply/rollback, profile-pack operations, and audit checks.
Core panels include Trial Status and Admin Apply Workflow.

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

Auth behavior:

1. Empty auth fields keep the public/member-only surface available.
2. Any valid WebUI password enables API login gating.
3. Admin API authorization uses token role, not request body `role`.
4. Legacy `auth.password` still works as member-only compatibility.
5. Query token auth is off by default; use `Authorization: Bearer <token>`.
6. Login attempts are rate-limited by `login_rate_limit_*`.
7. Token TTL is controlled by `token_ttl_seconds`.
8. API requests are rate-limited by `api_rate_limit_*` (`client + role + path` scope).
9. Metrics path cardinality is guarded by `observability.metrics_max_paths`; overflow paths are folded into `metrics_overflow_path_label`.
10. `GET /api/ui/capabilities` stays readable before login and returns the effective role + operation list used by UI-level capability gating.
11. Default WebUI responses include security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy`), configurable under `webui.security_headers`.
12. Reviewer/admin auth procedures and secret-backup instructions are intentionally kept out of the public docs surface.
13. If `allow_anonymous_member=true`, selected member endpoints (`trial/install/preferences/installations`) can run without login, but are still pinned to `anonymous_member_user_id` and cannot cross-access other `user_id`s.
14. `anonymous_member_allowlist` lets operators override the anonymous endpoint set explicitly (`"METHOD /api/path"` entries). Missing field falls back to the secure default set above.

## Start and routes

1. Plugin tries to start WebUI on init.
2. Run `/sharelife_webui` to get URL.
3. Open one of these routes:
   - `/` full console
   - `/member` member-focused console
   - `/admin` admin-focused console
   - `/market` standalone market page

### Container quick start

```bash
docker compose up -d --build
```

Then open `http://127.0.0.1:8106`.
Data is persisted under `./output/docker-data`.
Compose defaults to `state_store.backend=sqlite` with `./output/docker-data/sharelife_state.sqlite3`.

## Main capabilities

1. Preference controls: execution mode + task detail observability.
2. Trial Status panel: explicit trial state, TTL, and remaining seconds.
3. Template market: list/submit/install/prompt/package/download.
4. Admin Apply Workflow: dry-run -> apply -> rollback.
5. Risk scan panel: `risk_level`, labels, warning flags, injection matches.
6. Developer Mode toggle (top-right): enables localized risk evidence (`file/path/line/column`) for upload/import scan records.
7. In non-developer mode, risk panel keeps only decision-level signals to reduce noise for regular operators.
8. Admin moderation: review notes, labels, compare, queue lock/decision, audit timeline.
9. Notifications: list notifier events.
10. Server-backed filters for templates/submissions (`template_id`, `category`, `tag`, `source_channel`, `risk_level`, `status`, `review_label`, `warning_flag`).
11. Profile-pack market section: submission/catalog/compare/featured controls plus server-driven catalog insights (`/api/profile-pack/catalog/insights`) for metrics/featured/trending data cards.
12. Plugin install gate in profile-pack flow: plan -> confirm -> execute.
13. Execution evidence cards with grouped failures (`policy_blocked`, `command_failed`, `timed_out`).
14. UI locale (`en-US` / `zh-CN` / `ja-JP`) synced across `/`, `/member`, `/admin`, `/market` via `sharelife.uiLocale`.
15. Top utility bar keeps locale quick-switch and console links always visible for faster mode/language changes.
16. `/member` and `/admin` now use independent information-architecture templates (member-first vs admin-first) instead of a single mixed navigation surface.
17. On role pages, auth-role selection is now page-locked (`/member` => `member`, `/admin` => `admin`) to reduce cross-role operation mistakes.
18. Low-frequency controls are collapsed by default (`Workspace route actions`, `Plugin install execution controls`, `Risk Glossary`) to reduce noise in daily operations.
19. API responses include `X-Request-ID` for traceability, and `/api/metrics` exposes Prometheus text metrics (`sharelife_webui_http_*`, `sharelife_webui_auth_events_total`, `sharelife_webui_rate_limit_total`).
20. Reviewer/admin operations, observability runbooks, and auth-secret backup procedures are maintained in private operator docs, not the public docs site.
21. Auth/rate-limit/internal failures return a unified error payload shape: `{"ok": false, "error": {"code": "...", "message": "..."}}`.
22. Button-level operations are now capability-gated from backend policy (`/api/ui/capabilities`) so member/admin/public surfaces stay aligned with token role.
23. Profile-pack panel now includes a dedicated Compatibility Guidance block (issue list + clickable action shortcuts). Mapped issues/actions can jump to target controls, and shortcuts can prefill `plugin_ids`/recommended sections when hints are available. Developer-only shortcuts can auto-resume after Developer Mode is enabled. Raw `compatibility_issues`/`action_codes` remain Developer Mode only.
24. `/market` now uses a left-facet + top-search IA (Hugging Face-style), with compact card grid and responsive filter drawer on mobile.
25. Market local view state is URL-synced (`q`, `sort`, `facet_*`, `pack_id`), so filtered/selected views are directly shareable.
26. In desktop market layout, `Detail & Compare` is pinned as a dedicated right column; `Operation Log` is collapsed by default and can be expanded from a toggle button inside the profile-pack card.
27. Admin Storage Backup panel now supports full local backup and restore lifecycle: summary, policy read/write, backup job run/list/detail, restore prepare/commit/cancel, and restore job observability.
28. Storage output now defaults to operator-friendly summaries; raw JSON payload is appended only in Developer Mode.

## Troubleshooting

1. `permission_denied`: token is not admin.
2. `review_lock_held`: another admin currently owns the lock.
3. `401`: auth enabled, login required.
4. `prompt_injection_detected`: package is marked high risk; current behavior is labeling + visualization, not auto-delete.
5. Wrong locale after manual storage edits: delete `sharelife.uiLocale` from browser storage and refresh.
6. Wrong developer-mode state after manual storage edits: delete `sharelife.developerMode` and refresh.

# Sharelife API v1 (Public + Member Surface)

This page documents only the public catalog surface and member-scoped mutation surface.
Privileged internal endpoints are intentionally omitted from the public reference.

## Scope

1. Public read APIs: market discovery, detail, compare, health, and capability discovery.
2. Member APIs: login, trial, install, upload, profile-pack import/submission, local-installation management, task recovery, transfer-job visibility, and owner-scoped submission queries/downloads.
3. Owner binding: when auth is enabled, member routes can only act on the authenticated `user_id`.

## Public + Member Application Methods

1. `get_preferences(user_id)`
2. `set_preference_mode(user_id, mode)`
3. `set_preference_observe(user_id, enabled)`
4. `submit_template(user_id, template_id, version)`
5. `submit_template_package(user_id, template_id, version, filename, content_base64)`
6. `list_templates()`
7. `get_template_detail(template_id)`
8. `request_trial(user_id, session_id, template_id)`
9. `get_trial_status(user_id, session_id, template_id)`
10. `install_template(user_id, session_id, template_id)`
11. `generate_prompt_bundle(template_id)`
12. `generate_package(template_id)`
13. `list_member_tasks(user_id, limit=50)`
14. `refresh_member_tasks(user_id, limit=50)`
15. `list_member_transfer_jobs(user_id, direction="", status="", limit=50)`
16. `refresh_member_transfer_jobs(user_id, direction="", status="", limit=50)`
17. `list_profile_pack_catalog(pack_query="", pack_type="", risk_level="", review_label="", warning_flag="", featured="")`
18. `get_profile_pack_catalog_detail(pack_id)`
19. `compare_profile_pack_catalog(pack_id, selected_sections=None)`
20. `member_import_profile_pack(user_id, filename, content_base64)`
21. `member_list_profile_pack_imports(user_id, limit=50)`
22. `submit_profile_pack(user_id, artifact_id, submit_options=None)`
23. `list_member_installations(user_id, limit=50)`
24. `refresh_member_installations(user_id, limit=50)`
25. `uninstall_member_installation(user_id, template_id)`
26. `member_list_submissions(user_id, status="", template_query="", risk_level="", review_label="", warning_flag="")`
27. `member_get_submission_detail(user_id, submission_id)`
28. `member_get_submission_package(user_id, submission_id, idempotency_key="")`
29. `member_list_profile_pack_submissions(user_id, status="", pack_query="", pack_type="", risk_level="", review_label="", warning_flag="")`
30. `member_get_profile_pack_submission_detail(user_id, submission_id)`
31. `member_withdraw_profile_pack_submission(user_id, submission_id)`
32. `member_get_profile_pack_submission_export(user_id, submission_id)`

## Public + Member HTTP Routes

Public routes:

1. `GET /api/auth-info`
2. `POST /api/login`
3. `GET /api/health`
4. `GET /api/ui/capabilities?page_mode=auto|member|market`
5. `GET /api/templates`
6. `GET /api/templates/detail?template_id=...`
7. `GET /api/profile-pack/catalog`
8. `GET /api/profile-pack/catalog/detail?pack_id=...`
9. `GET /api/profile-pack/catalog/compare?pack_id=...&selected_sections=plugins,providers`
10. `GET /api/profile-pack/catalog/insights`

Member routes:

1. `GET /api/preferences?user_id=...`
2. `POST /api/preferences/mode`
3. `POST /api/preferences/observe`
4. `POST /api/trial`
5. `GET /api/trial/status?user_id=...&session_id=...&template_id=...`
6. `POST /api/templates/install`
7. `POST /api/templates/submit`
8. `GET /api/templates/package/download?template_id=...`
9. `POST /api/templates/prompt`
10. `POST /api/templates/package`
11. `GET /api/member/tasks?user_id=...`
12. `POST /api/member/tasks/refresh`
13. `GET /api/member/transfers?user_id=...&direction=download&status=...`
14. `POST /api/member/transfers/refresh`
15. `POST /api/profile-pack/submit`
16. `POST /api/member/profile-pack/imports`
17. `GET /api/member/profile-pack/imports?user_id=...`
18. `GET /api/member/installations?user_id=...`
19. `POST /api/member/installations/refresh`
20. `POST /api/member/installations/uninstall`
21. `GET /api/member/submissions?user_id=...&status=...&template_id=...&risk_level=...`
22. `GET /api/member/submissions/detail?user_id=...&submission_id=...`
23. `GET /api/member/submissions/package/download?user_id=...&submission_id=...`
24. `GET /api/member/profile-pack/submissions?user_id=...&status=...&pack_id=...&pack_type=...`
25. `GET /api/member/profile-pack/submissions/detail?user_id=...&submission_id=...`
26. `POST /api/member/profile-pack/submissions/withdraw`
27. `GET /api/member/profile-pack/submissions/export/download?user_id=...&submission_id=...`

## Public Upload / Install Payload Notes

1. `POST /api/templates/install`
   - `install_options.preflight: bool`
   - `install_options.force_reinstall: bool`
   - `install_options.source_preference: auto|uploaded_submission|generated`
2. `POST /api/templates/submit`
   - `package_name + package_base64` for direct package upload
   - `upload_options.scan_mode: strict|balanced`
   - `upload_options.visibility: community|private`
   - `upload_options.replace_existing: bool`
   - `upload_options.idempotency_key` or `Idempotency-Key` header for safe retry
3. `POST /api/profile-pack/submit`
   - `artifact_id` is required on the current branch
   - `submit_options.pack_type: bot_profile_pack|extension_pack`
   - `submit_options.selected_sections: string[]`
   - `submit_options.redaction_mode: exclude_secrets|exclude_provider|include_provider_no_key|include_encrypted_secrets`
   - `submit_options.replace_existing: bool`
   - `submit_options.idempotency_key` or `Idempotency-Key` header for safe retry
4. `POST /api/member/profile-pack/imports`
   - `filename + content_base64` creates a member-owned import draft before community submission
5. `GET /api/member/submissions/package/download`
   - optional `Idempotency-Key` header de-duplicates repeated download job creation
   - success responses can include `X-Sharelife-Transfer-Job-Id` and `X-Sharelife-Transfer-Status`
6. Direct template package upload is capped at `20 MiB` and returns `package_too_large` if exceeded.

## Auth Badge Matrix (HTTP)

| Route | Required Role | Deny Behavior |
| --- | --- | --- |
| `GET /api/ui/capabilities` | `public` | N/A |
| `POST /api/login` | `public` | `401 invalid_credentials` or `429 rate_limited` |
| `GET /api/templates` | `public` | N/A |
| `GET /api/templates/detail` | `public` | N/A |
| `GET /api/profile-pack/catalog` | `public` | N/A |
| `GET /api/profile-pack/catalog/detail` | `public` | N/A |
| `GET /api/profile-pack/catalog/compare` | `public` | N/A |
| `GET /api/profile-pack/catalog/insights` | `public` | N/A |
| `POST /api/trial` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/templates/install` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/tasks` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/tasks/refresh` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/transfers` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/transfers/refresh` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/templates/submit` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/profile-pack/submit` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/profile-pack/imports` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/imports` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/installations` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/installations/refresh` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/installations/uninstall` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/submissions` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/submissions/detail` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/submissions/package/download` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/submissions` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/submissions/detail` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/profile-pack/submissions/withdraw` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/submissions/export/download` | `member` | `401 unauthorized` or `403 permission_denied` |

All role-deny responses are expected to return `error.code=permission_denied`.

## Error Model

1. `permission_denied`: token role or owner binding blocks the action.
2. `unauthorized` / `invalid_credentials`: login is required or credentials are wrong.
3. `package_too_large`: uploaded package exceeds the `20 MiB` limit.
4. `template_not_installable`: install was requested for a template that is not installable.
5. `profile_pack_source_required`: profile-pack community submit was called without `artifact_id`.
6. `idempotency_key_conflict`: the same idempotency key was reused across a different submission scope.
7. `prompt_injection_detected`: scan flagged risky content; current behavior is labeling and review escalation, not auto-delete.

## Runtime Notes

1. `get_trial_status()` and `GET /api/trial/status` report `not_started|active|expired` plus `ttl_seconds` and `remaining_seconds`.
2. `GET /api/ui/capabilities` is intentionally readable before login so the UI can hide or disable protected controls.
3. If `allow_anonymous_member=true`, only the configured allowlist can run without login, and requests are still pinned to `anonymous_member_user_id`.
4. `GET /api/templates` supports server-side filter/sort on catalog metadata, including `category`, `tag`, `source_channel`, `review_label`, `warning_flag`, `sort_by`, and `sort_order`.
5. Template list/detail payloads now include `category`, `tags`, `maintainer`, `source_channel`, and an aggregated `engagement` object for market ranking cards.
6. Current `engagement` fields include `trial_requests`, `installs`, `prompt_generations`, `package_generations`, `community_submissions`, and `last_activity_at`.
7. `POST /api/templates/submit` and `POST /api/profile-pack/submit` both support idempotent replay through payload options or the `Idempotency-Key` header.
8. Member task routes provide audit-backed upload/download recovery across page reloads.
9. Member transfer routes expose transfer-job history with `attempt_count`, `retry_count`, `failure_reason`, and `metadata` for download troubleshooting.
10. Submission package download can attach transfer-job metadata to the payload and response headers, allowing the UI to replay or poll the same logical download job safely.
11. Member profile-pack imports remain member-owned drafts until they are explicitly submitted to the community queue.
12. `POST /api/member/profile-pack/submissions/withdraw` lets a member revoke a pending profile-pack submission before queue handling begins.
13. Member download surfaces are owner-scoped by design: a member can only download the package/export for their own submission.
14. Privileged approval, apply/rollback, secret rotation, backup/restore, and featured curation flows stay outside the public documentation set.

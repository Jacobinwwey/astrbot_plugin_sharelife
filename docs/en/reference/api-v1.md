# Sharelife API v1 (Command Reuse Layer)

`sharelife/interfaces/api_v1.py` is the unified use-case layer that command handlers call directly, so orchestration logic stays in one place.

## User-facing methods

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
13. `list_profile_pack_catalog(pack_query="", pack_type="", risk_level="", review_label="", warning_flag="", featured="")`
14. `get_profile_pack_catalog_detail(pack_id)`
15. `compare_profile_pack_catalog(pack_id, selected_sections=None)`
16. `member_list_submissions(user_id, status="", template_query="", risk_level="", review_label="", warning_flag="")`
17. `member_get_submission_detail(user_id, submission_id)`
18. `member_get_submission_package(user_id, submission_id)`
19. `member_list_profile_pack_submissions(user_id, status="", pack_query="", pack_type="", risk_level="", review_label="", warning_flag="")`
20. `member_get_profile_pack_submission_detail(user_id, submission_id)`
21. `member_get_profile_pack_submission_export(user_id, submission_id)`

## Admin-facing methods

1. `admin_list_submissions(role, status="")`
2. `admin_get_submission_detail(role, submission_id)`
3. `admin_update_submission_review(role, submission_id, review_note="", review_labels=None)`
4. `admin_decide_submission(role, submission_id, decision, review_note="", review_labels=None)`
5. `admin_list_retry_requests(role)`
6. `admin_acquire_retry_lock(role, request_id, admin_id, force=False, reason="")`
7. `admin_decide_retry_request(role, request_id, decision, admin_id=None, request_version=None, lock_version=None)`
8. `admin_dryrun(role, plan_id, patch)`
9. `admin_apply(role, plan_id)`
10. `admin_rollback(role, plan_id)`
11. `admin_list_audit(role, limit=100)`
12. `admin_export_profile_pack(role, pack_id, version, pack_type="bot_profile_pack", redaction_mode="exclude_secrets", sections=None, mask_paths=None, drop_paths=None)`
13. `admin_get_profile_pack_export(role, artifact_id)`
14. `admin_list_profile_pack_exports(role, limit=50)`
15. `admin_import_profile_pack(role, filename, content_base64)`
16. `admin_import_profile_pack_from_export(role, artifact_id)`
17. `admin_import_profile_pack_and_dryrun(role, plan_id, selected_sections=None, filename="", content_base64="", artifact_id="")`
18. `admin_list_profile_pack_imports(role, limit=50)`
19. `admin_profile_pack_dryrun(role, import_id, plan_id, selected_sections=None)`
20. `admin_profile_pack_plugin_install_plan(role, import_id)`
21. `admin_profile_pack_confirm_plugin_install(role, import_id, plugin_ids=None)`
22. `admin_profile_pack_execute_plugin_install(role, import_id, plugin_ids=None, dry_run=False)`
23. `admin_profile_pack_apply(role, plan_id)`
24. `admin_profile_pack_rollback(role, plan_id)`
25. `admin_set_profile_pack_featured(role, pack_id, featured, note="")`
26. `admin_run_pipeline(role, contract, input_payload, actor_id="admin", run_id="")`
27. `admin_storage_local_summary(role)`
28. `admin_storage_get_policies(role)`
29. `admin_storage_set_policies(role, patch, admin_id="admin")`
30. `admin_storage_run_job(role, admin_id="admin", trigger="manual", note="")`
31. `admin_storage_list_jobs(role, status="", limit=50)`
32. `admin_storage_get_job(role, job_id)`
33. `admin_storage_restore_prepare(role, artifact_ref, admin_id="admin", note="")`
34. `admin_storage_restore_commit(role, restore_id, admin_id="admin")`
35. `admin_storage_restore_cancel(role, restore_id, admin_id="admin")`
36. `admin_storage_list_restore_jobs(role, state="", limit=50)`
37. `admin_storage_get_restore_job(role, restore_id)`

## Reviewer and access-governance methods

1. `admin_create_reviewer_invite(role, admin_id, expires_in_seconds=3600)`
2. `admin_list_reviewer_invites(role, status="")`
3. `admin_revoke_reviewer_invite(role, invite_code, admin_id)`
4. `reviewer_redeem_invite(invite_code, reviewer_id)`
5. `reviewer_register_device(reviewer_id, label="")`
6. `reviewer_list_devices(reviewer_id)`
7. `reviewer_revoke_device(reviewer_id, device_id)`
8. `admin_list_reviewers(role)`
9. `admin_force_reset_reviewer_devices(role, reviewer_id, admin_id)`
10. `admin_list_profile_pack_submissions(role, status="", pack_query="", pack_type="", risk_level="", review_label="", warning_flag="")`
11. `admin_decide_profile_pack_submission(role, submission_id, decision, review_note="", review_labels=None, reviewer_id="")`

## Error code examples

1. `permission_denied`
2. `invite_revoked`
3. `review_lock_held`
4. `takeover_reason_required`
5. `review_lock_required`
6. `review_lock_not_owner`
7. `request_version_conflict`
8. `lock_version_conflict`
9. `template_not_installable`
10. `package_service_unavailable`
11. `package_payload_required`
12. `invalid_package_payload`
13. `plan_not_found`
14. `plan_not_applied`
15. `invalid_pack_type`
16. `profile_pack_plugin_install_confirm_required`
17. `profile_pack_plugin_not_in_plan`
18. `profile_pack_plugin_id_required`
19. `profile_pack_plugin_install_exec_disabled`
20. `profile_pack_plugin_install_exec_required`
21. `profile_pack_plugin_install_exec_failed`
22. `pipeline_service_unavailable`
23. `invalid_pipeline_contract`
24. `pipeline_execution_failed`
25. `storage_service_unavailable`
26. `daily_upload_budget_exceeded`
27. `remote_sync_command_not_found`
28. `remote_sync_failed`
29. `artifact_not_found`
30. `artifact_checksum_mismatch`
31. `remote_encryption_required`
32. `remote_retention_failed`
33. `remote_retention_command_not_found`

## Concurrency governance

1. Review lock TTL is 10 minutes.
2. Force takeover requires reason.
3. Decisions can be protected by `request_version + lock_version`.

## WebUI HTTP Layer

Phase 3 adds `sharelife/interfaces/web_api_v1.py` and `sharelife/interfaces/webui_server.py` for standalone page + HTTP endpoints.

Endpoint prefix: `/api` (inside standalone WebUI server).

User routes:

1. `GET /api/preferences?user_id=...`
2. `POST /api/preferences/mode`
3. `POST /api/preferences/observe`
4. `GET /api/templates`
5. `GET /api/templates/detail?template_id=...`
6. `POST /api/templates/submit`
7. `GET /api/templates/package/download?template_id=...`
8. `POST /api/trial`
9. `GET /api/trial/status?user_id=...&session_id=...&template_id=...`
10. `POST /api/templates/install`
11. `POST /api/templates/prompt`
12. `POST /api/templates/package`
13. `GET /api/profile-pack/catalog`
14. `GET /api/profile-pack/catalog/detail?pack_id=...`
15. `GET /api/profile-pack/catalog/compare?pack_id=...&selected_sections=plugins,providers`
16. `GET /api/profile-pack/catalog/insights`
17. `GET /api/member/submissions?user_id=...&status=...&template_id=...`
18. `GET /api/member/submissions/detail?user_id=...&submission_id=...`
19. `GET /api/member/submissions/package/download?user_id=...&submission_id=...`
20. `GET /api/member/profile-pack/submissions?user_id=...&status=...&pack_id=...`
21. `GET /api/member/profile-pack/submissions/detail?user_id=...&submission_id=...`
22. `GET /api/member/profile-pack/submissions/export/download?user_id=...&submission_id=...`

Reviewer routes:

1. `POST /api/reviewer/invites`
2. `GET /api/reviewer/invites`
3. `POST /api/reviewer/invites/revoke`
4. `POST /api/reviewer/redeem`
5. `POST /api/reviewer/devices/register`
6. `GET /api/reviewer/devices`
7. `DELETE /api/reviewer/devices/{device_id}`
8. `GET /api/reviewer/accounts`
9. `POST /api/reviewer/accounts/reset-devices`
10. `GET /api/reviewer/session`
11. `POST /api/reviewer/session/logout`
12. `GET /api/reviewer/submissions`
13. `POST /api/reviewer/submissions/review`
14. `POST /api/reviewer/submissions/decide`
15. `GET /api/reviewer/submissions/detail?submission_id=...`
16. `GET /api/reviewer/submissions/compare?submission_id=...`
17. `GET /api/reviewer/submissions/package/download?submission_id=...`
18. `GET /api/reviewer/profile-pack/submissions`
19. `POST /api/reviewer/profile-pack/submissions/decide`

Admin routes:

1. `GET /api/admin/submissions?role=admin&status=...`
2. `POST /api/admin/dryrun`
3. `POST /api/admin/apply`
4. `POST /api/admin/rollback`
5. `GET /api/admin/submissions/detail?submission_id=...`
6. `POST /api/admin/submissions/review`
7. `GET /api/admin/submissions/compare?submission_id=...`
8. `GET /api/admin/submissions/package/download?submission_id=...`
9. `POST /api/admin/submissions/decide`
10. `GET /api/admin/retry-requests?role=admin`
11. `POST /api/admin/retry-requests/lock`
12. `POST /api/admin/retry-requests/decide`
13. `GET /api/admin/audit?role=admin&limit=20`
14. `POST /api/admin/profile-pack/export`
15. `GET /api/admin/profile-pack/export/download?artifact_id=...`
16. `GET /api/admin/profile-pack/exports?role=admin&limit=...`
17. `POST /api/admin/profile-pack/import`
18. `POST /api/admin/profile-pack/import/from-export`
19. `POST /api/admin/profile-pack/import-and-dryrun`
20. `GET /api/admin/profile-pack/imports?role=admin&limit=...`
21. `POST /api/admin/profile-pack/dryrun`
22. `GET /api/admin/profile-pack/plugin-install-plan?import_id=...`
23. `POST /api/admin/profile-pack/plugin-install-confirm`
24. `POST /api/admin/profile-pack/plugin-install-execute`
25. `POST /api/admin/profile-pack/apply`
26. `POST /api/admin/profile-pack/rollback`
27. `POST /api/admin/profile-pack/catalog/featured`
28. `POST /api/admin/pipeline/run`
29. `GET /api/admin/storage/local-summary`
30. `GET /api/admin/storage/policies`
31. `POST /api/admin/storage/policies`
32. `POST /api/admin/storage/jobs/run`
33. `GET /api/admin/storage/jobs`
34. `GET /api/admin/storage/jobs/{job_id}`
35. `POST /api/admin/storage/restore/prepare`
36. `POST /api/admin/storage/restore/commit`
37. `POST /api/admin/storage/restore/cancel`
38. `GET /api/admin/storage/restore/jobs`
39. `GET /api/admin/storage/restore/jobs/{restore_id}`

`GET /api/admin/audit` returns both raw `events` and a `summary` block grouped by actor role, actor, action, reviewer, and device.

Utility routes:

1. `GET /api/auth-info`
2. `POST /api/login` (supports split `member/admin` credentials)
3. `GET /api/health`
4. `GET /api/notifications?limit=...`
5. `GET /api/ui/capabilities?page_mode=auto|member|admin` (returns effective role + operation keys for UI gating)

## Auth Badge Matrix (HTTP)

| Route | Required Role | Deny Behavior |
| --- | --- | --- |
| `GET /api/ui/capabilities` | `public` | N/A |
| `POST /api/login` | `public` | `401 invalid_credentials` or `429 rate_limited` |
| `GET /api/templates` | `public` (read-only market surface) | N/A |
| `GET /api/templates/detail` | `public` (read-only market surface) | N/A |
| `GET /api/profile-pack/catalog` | `public` (read-only market surface) | N/A |
| `GET /api/profile-pack/catalog/detail` | `public` (read-only market surface) | N/A |
| `GET /api/profile-pack/catalog/compare` | `public` (read-only market surface) | N/A |
| `GET /api/profile-pack/catalog/insights` | `public` (read-only market surface) | N/A |
| `POST /api/templates/submit` | `member|reviewer|admin` | `401 unauthorized` (no token), `403 permission_denied` (member owner mismatch) |
| `GET /api/member/submissions` | `member|reviewer|admin` | `401 unauthorized` (no token), `403 permission_denied` (member owner mismatch) |
| `GET /api/member/submissions/detail` | `member|reviewer|admin` | `401 unauthorized` (no token), `403 permission_denied` (member owner mismatch) |
| `GET /api/member/submissions/package/download` | `member|reviewer|admin` | `401 unauthorized` (no token), `403 permission_denied` (member owner mismatch) |
| `GET /api/member/profile-pack/submissions` | `member|reviewer|admin` | `401 unauthorized` (no token), `403 permission_denied` (member owner mismatch) |
| `GET /api/member/profile-pack/submissions/detail` | `member|reviewer|admin` | `401 unauthorized` (no token), `403 permission_denied` (member owner mismatch) |
| `GET /api/member/profile-pack/submissions/export/download` | `member|reviewer|admin` | `401 unauthorized` (no token), `403 permission_denied` (member owner mismatch) |
| `POST /api/reviewer/invites/revoke` | `admin` | `403 permission_denied` |
| `POST /api/reviewer/redeem` | `public` (invite-based onboarding) | `400/404/409/410` invite validation errors |
| `GET /api/reviewer/submissions` | `reviewer|admin` | `403 permission_denied` |
| `POST /api/reviewer/submissions/decide` | `reviewer|admin` | `403 permission_denied` |
| `POST /api/admin/apply` | `admin` | `403 permission_denied` |
| `POST /api/admin/profile-pack/apply` | `admin` | `403 permission_denied` |
| `POST /api/admin/pipeline/run` | `admin` | `403 permission_denied` |

All role-deny responses are expected to return `error.code=permission_denied`.

## Phase 4 Notes

1. `get_trial_status()` and `GET /api/trial/status` now report `not_started|active|expired` with `ttl_seconds` and `remaining_seconds`.
2. `admin_dryrun()` and `POST /api/admin/dryrun` prepare a strict-mode patch plan without mutating runtime state yet.
3. `admin_rollback()` and `POST /api/admin/rollback` restore the latest successful snapshot for that plan.
4. `POST /api/templates/submit` now accepts optional `package_name + package_base64` fields for template package upload.
5. Upload responses expose `risk_level`, `review_labels`, `warning_flags`, and `scan_summary.prompt_injection`.
6. `generate_package()` and the download endpoint prefer the approved uploaded artifact when available and return `source=uploaded_submission|generated`.
7. Admins can save `review_note` and manual moderation labels separately through `POST /api/admin/submissions/review`, without deciding immediately.
8. Admins can download the original package from an unapproved submission through `GET /api/admin/submissions/package/download` and compare it with the current published baseline through `GET /api/admin/submissions/compare`.
9. `GET /api/admin/submissions/compare` now returns a `details` object with field-level diffs for version, risk, review note, prompt preview, package metadata, and scan changes.
10. `GET /api/templates` now also supports server-side official-catalog filters for `category`, `tag`, and `source_channel`, in addition to `review_label` and `warning_flag`.
11. `GET /api/templates` additionally supports `sort_by=template_id|recent_activity|trial_requests|installs` and `sort_order=asc|desc`.
12. Template list/detail payloads now expose `category`, `tags`, `maintainer`, `source_channel`, and an aggregate `engagement` object for starter-catalog discovery.
13. `engagement` currently includes `trial_requests`, `installs`, `prompt_generations`, `package_generations`, `community_submissions`, and `last_activity_at`.
14. `GET /api/templates/detail` and `GET /api/admin/submissions/detail` return detail-oriented payloads with prompt preview/length, timestamps, package metadata, catalog metadata, and template engagement data for direct WebUI rendering.
15. WebUI locale switching (`en-US` / `zh-CN` / `ja-JP`) is client-side behavior only; API routes do not accept locale parameters and payload schema does not change by locale.
16. WebUI-localized labels (collection/panel state text, moderation guidance, detail-field labels) are derived from front-end dictionaries; API field keys remain stable (`snake_case` payload keys in English).
17. `GET /api/ui/capabilities` is intentionally readable before login; when auth is enabled and no token is provided, role resolves to `public` with minimal operation scope.
18. With auth enabled, market catalog read routes remain public (`GET /api/templates*`, `GET /api/profile-pack/catalog*`), while mutation routes remain token-protected.
19. If `webui.public_market.auto_publish_profile_pack_approve=true`, approving a profile-pack submission can return `public_market_publish` in decision payload, including publish status and generated artifact paths.
20. Public-market auto-publish runtime knobs: `webui.public_market.auto_publish_profile_pack_approve`, `webui.public_market.root`, and `webui.public_market.rebuild_snapshot_on_publish`.
21. Member download endpoints are owner-scoped by design: both template submission package download and profile-pack submission export download require `user_id` to match the authenticated member subject when auth is enabled.
22. `market.html` login now forwards member `user_id` explicitly, and the market-page member actor binds to the login-returned `user_id` instead of a hardcoded identifier, preventing owner-scope false `403` responses.

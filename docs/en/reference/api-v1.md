# Sharelife API v1 (Public + Member Surface)

This page documents only the public catalog surface and member-scoped mutation surface.
Reviewer/admin/operator endpoints are intentionally omitted from the public reference and moved to private operator docs.

## Scope

1. Public read APIs: market discovery, detail, compare, health, and capability discovery.
2. Member APIs: login, trial, install, upload, profile-pack community submission, local-installation management, and owner-scoped submission queries/downloads.
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
13. `list_profile_pack_catalog(pack_query="", pack_type="", risk_level="", review_label="", warning_flag="", featured="")`
14. `get_profile_pack_catalog_detail(pack_id)`
15. `compare_profile_pack_catalog(pack_id, selected_sections=None)`
16. `submit_profile_pack(user_id, artifact_id, submit_options=None)`
17. `list_member_installations(user_id, limit=50)`
18. `refresh_member_installations(user_id, limit=50)`
19. `uninstall_member_installation(user_id, template_id)`
20. `member_list_submissions(user_id, status="", template_query="", risk_level="", review_label="", warning_flag="")`
21. `member_get_submission_detail(user_id, submission_id)`
22. `member_get_submission_package(user_id, submission_id)`
23. `member_list_profile_pack_submissions(user_id, status="", pack_query="", pack_type="", risk_level="", review_label="", warning_flag="")`
24. `member_get_profile_pack_submission_detail(user_id, submission_id)`
25. `member_get_profile_pack_submission_export(user_id, submission_id)`

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
11. `POST /api/profile-pack/submit`
12. `GET /api/member/installations?user_id=...`
13. `POST /api/member/installations/refresh`
14. `POST /api/member/installations/uninstall`
15. `GET /api/member/submissions?user_id=...`
16. `GET /api/member/submissions/detail?user_id=...&submission_id=...`
17. `GET /api/member/submissions/package/download?user_id=...&submission_id=...`
18. `GET /api/member/profile-pack/submissions?user_id=...`
19. `GET /api/member/profile-pack/submissions/detail?user_id=...&submission_id=...`
20. `GET /api/member/profile-pack/submissions/export/download?user_id=...&submission_id=...`

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
3. `POST /api/profile-pack/submit`
   - `artifact_id` is required on the current branch
   - `submit_options.pack_type: bot_profile_pack|extension_pack`
   - `submit_options.selected_sections: string[]`
   - `submit_options.redaction_mode: exclude_secrets|exclude_provider|include_provider_no_key|include_encrypted_secrets`
   - `submit_options.replace_existing: bool`
4. Direct template package upload is capped at `20 MiB` and returns `package_too_large` if exceeded.

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
| `POST /api/templates/submit` | `member` | `401 unauthorized` or `403 permission_denied` |
| `POST /api/profile-pack/submit` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/installations` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/installations/refresh` | `member` or anonymous allowlist | `401 unauthorized` or `403 permission_denied` |
| `POST /api/member/installations/uninstall` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/submissions` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/submissions/detail` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/submissions` | `member` | `401 unauthorized` or `403 permission_denied` |
| `GET /api/member/profile-pack/submissions/detail` | `member` | `401 unauthorized` or `403 permission_denied` |

All role-deny responses are expected to return `error.code=permission_denied`.

## Error Model

1. `permission_denied`: token role or owner binding blocks the action.
2. `unauthorized` / `invalid_credentials`: login is required or credentials are wrong.
3. `package_too_large`: uploaded package exceeds the `20 MiB` limit.
4. `template_not_installable`: install was requested for a template that is not installable.
5. `profile_pack_source_required`: profile-pack community submit was called without `artifact_id`.
6. `prompt_injection_detected`: scan flagged risky content; current behavior is labeling and review escalation, not auto-delete.

## Runtime Notes

1. `get_trial_status()` and `GET /api/trial/status` report `not_started|active|expired` plus `ttl_seconds` and `remaining_seconds`.
2. `GET /api/ui/capabilities` is intentionally readable before login so the UI can hide or disable protected controls.
3. If `allow_anonymous_member=true`, only the configured allowlist can run without login, and requests are still pinned to `anonymous_member_user_id`.
4. Member download surfaces are owner-scoped by design: a member can only download the package/export for their own submission.
5. Operator flows such as approval, apply/rollback, reviewer lifecycle, secret rotation, backup/restore, and featured curation are documented only in the private operator docs.

# Sharelife API v1

`sharelife/interfaces/api_v1.py` は、チャットコマンド、WebUI、HTTP ルートが共通で使うユースケース層です。

## ユーザー向けメソッド

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

## 管理者向けメソッド

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

## Reviewer と認可運用メソッド

1. `admin_create_reviewer_invite(role, admin_id, expires_in_seconds=3600)`
2. `admin_list_reviewer_invites(role, status="")`
3. `reviewer_redeem_invite(invite_code, reviewer_id)`
4. `reviewer_register_device(reviewer_id, label="")`
5. `reviewer_list_devices(reviewer_id)`
6. `reviewer_revoke_device(reviewer_id, device_id)`
7. `admin_list_reviewers(role)`
8. `admin_force_reset_reviewer_devices(role, reviewer_id, admin_id)`
9. `admin_list_profile_pack_submissions(role, status="", pack_query="", pack_type="", risk_level="", review_label="", warning_flag="")`
10. `admin_decide_profile_pack_submission(role, submission_id, decision, review_note="", review_labels=None, reviewer_id="")`

## 主なエラーコード

1. `permission_denied`
2. `review_lock_held`
3. `takeover_reason_required`
4. `review_lock_required`
5. `review_lock_not_owner`
6. `request_version_conflict`
7. `lock_version_conflict`
8. `template_not_installable`
9. `package_service_unavailable`
10. `invalid_package_payload`
11. `plan_not_found`
12. `plan_not_applied`
13. `invalid_pack_type`
14. `profile_pack_plugin_install_confirm_required`
15. `profile_pack_plugin_not_in_plan`
16. `profile_pack_plugin_id_required`
17. `profile_pack_plugin_install_exec_disabled`
18. `profile_pack_plugin_install_exec_required`
19. `profile_pack_plugin_install_exec_failed`
20. `pipeline_service_unavailable`
21. `invalid_pipeline_contract`
22. `pipeline_execution_failed`
23. `storage_service_unavailable`
24. `daily_upload_budget_exceeded`
25. `remote_sync_command_not_found`
26. `remote_sync_failed`
27. `artifact_not_found`
28. `artifact_checksum_mismatch`

## WebUI / HTTP ルート

ユーザー側:

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

Reviewer 側:

1. `POST /api/reviewer/invites`
2. `GET /api/reviewer/invites`
3. `POST /api/reviewer/redeem`
4. `POST /api/reviewer/devices/register`
5. `GET /api/reviewer/devices`
6. `DELETE /api/reviewer/devices/{device_id}`
7. `GET /api/reviewer/accounts`
8. `POST /api/reviewer/accounts/reset-devices`
9. `GET /api/reviewer/session`
10. `POST /api/reviewer/session/logout`
11. `GET /api/reviewer/submissions`
12. `POST /api/reviewer/submissions/review`
13. `POST /api/reviewer/submissions/decide`
14. `GET /api/reviewer/submissions/detail?submission_id=...`
15. `GET /api/reviewer/submissions/compare?submission_id=...`
16. `GET /api/reviewer/submissions/package/download?submission_id=...`
17. `GET /api/reviewer/profile-pack/submissions`
18. `POST /api/reviewer/profile-pack/submissions/decide`

管理者側:

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

`GET /api/admin/audit` は生の `events` に加えて、actor role / actor / action / reviewer / device 単位の `summary` 集計も返します。

補助ルート:

1. `GET /api/auth-info`
2. `POST /api/login`
3. `GET /api/health`
4. `GET /api/notifications?limit=...`
5. `GET /api/ui/capabilities?page_mode=auto|member|admin`（UI ゲート用の有効ロールと operation key を返却）

## Auth Badge Matrix (HTTP)

| ルート | Required Role | 拒否時の挙動 |
| --- | --- | --- |
| `GET /api/ui/capabilities` | `public` | 該当なし |
| `POST /api/login` | `public` | `401 invalid_credentials` または `429 rate_limited` |
| `GET /api/profile-pack/catalog` | `member|reviewer|admin`（認証無効時は `public`） | デプロイ設定により `401/403` |
| `POST /api/reviewer/redeem` | `public`（招待コード型オンボーディング） | 招待検証エラー `400/404/410` |
| `GET /api/reviewer/submissions` | `reviewer|admin` | `403 permission_denied` |
| `POST /api/reviewer/submissions/decide` | `reviewer|admin` | `403 permission_denied` |
| `POST /api/admin/apply` | `admin` | `403 permission_denied` |
| `POST /api/admin/profile-pack/apply` | `admin` | `403 permission_denied` |
| `POST /api/admin/pipeline/run` | `admin` | `403 permission_denied` |

ロール不足による拒否レスポンスは `error.code=permission_denied` を返す想定です。

## 補足

1. `GET /api/trial/status` は `not_started|active|expired` を返し、TTL と残り秒数も確認できます。
2. `GET /api/templates` は `category`、`tag`、`source_channel`、`review_label`、`warning_flag` を使った catalog フィルタに対応します。
3. `GET /api/templates` は `sort_by=template_id|recent_activity|trial_requests|installs` と `sort_order=asc|desc` にも対応します。
4. テンプレート一覧と詳細 payload は `category`、`tags`、`maintainer`、`source_channel`、aggregate な `engagement` を返します。
5. `engagement` には `trial_requests`、`installs`、`prompt_generations`、`package_generations`、`community_submissions`、`last_activity_at` が含まれます。
6. `POST /api/admin/dryrun` は plan を登録するだけで、まだランタイムには適用しません。
7. `POST /api/admin/rollback` は直近の成功スナップショットを復元します。
8. WebUI では Trial Status パネルと Admin Apply Workflow パネルからこの流れを直接操作できます。
9. WebUI の locale 切替（`en-US` / `zh-CN` / `ja-JP`）はフロントエンド側の挙動であり、API は locale パラメータを受け取りません。レスポンス schema も locale で変化しません。
10. collection/panel 状態文言、moderation ガイダンス、detail フィールドラベルなどの翻訳は WebUI 辞書で実施され、API フィールドキー（英語 `snake_case`）は固定です。
11. `GET /api/ui/capabilities` はログイン前でも参照可能です。認証有効で token が無い場合、role は `public` になり最小 operation のみ返します。

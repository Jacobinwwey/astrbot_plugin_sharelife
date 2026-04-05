# Sharelife API v1（命令复用层）

`sharelife/interfaces/api_v1.py` 提供统一用例入口，命令层直接调用它，编排逻辑只维护一处。

## 用户侧

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

## 管理员侧

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

## 审核员与准入治理方法

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

## 错误码约定（节选）

1. `permission_denied`
2. `review_lock_held`
3. `takeover_reason_required`
4. `review_lock_required`
5. `review_lock_not_owner`
6. `request_version_conflict`
7. `lock_version_conflict`
8. `template_not_installable`
9. `package_service_unavailable`
10. `package_payload_required`
11. `invalid_package_payload`
12. `plan_not_found`
13. `plan_not_applied`
14. `invalid_pack_type`
15. `profile_pack_plugin_install_confirm_required`
16. `profile_pack_plugin_not_in_plan`
17. `profile_pack_plugin_id_required`
18. `profile_pack_plugin_install_exec_disabled`
19. `profile_pack_plugin_install_exec_required`
20. `profile_pack_plugin_install_exec_failed`
21. `pipeline_service_unavailable`
22. `invalid_pipeline_contract`
23. `pipeline_execution_failed`
24. `storage_service_unavailable`
25. `daily_upload_budget_exceeded`
26. `remote_sync_command_not_found`
27. `remote_sync_failed`
28. `artifact_not_found`
29. `artifact_checksum_mismatch`

## 并发治理规则

1. 审核锁默认 10 分钟。
2. 强制接管必须提供理由。
3. 决策可携带 `request_version + lock_version` 做乐观并发保护。

## WebUI HTTP 适配层

Phase 3 新增 `sharelife/interfaces/web_api_v1.py` 与 `sharelife/interfaces/webui_server.py`，提供独立页面和 HTTP 接口。

接口前缀：`/api`（独立 WebUI 服务内）。

用户侧：

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

审核员侧：

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

管理员侧：

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

`GET /api/admin/audit` 除原始 `events` 外，还会返回按 actor role、actor、action、reviewer、device 聚合的 `summary` 摘要块。

辅助接口：

1. `GET /api/auth-info`
2. `POST /api/login`（支持 `member/admin` 分级密码）
3. `GET /api/health`
4. `GET /api/notifications?limit=...`
5. `GET /api/ui/capabilities?page_mode=auto|member|admin`（返回 UI 门控所需的有效角色与操作键）

## Auth Badge Matrix (HTTP)

| 路由 | Required Role | 拒绝语义 |
| --- | --- | --- |
| `GET /api/ui/capabilities` | `public` | 不适用 |
| `POST /api/login` | `public` | `401 invalid_credentials` 或 `429 rate_limited` |
| `GET /api/profile-pack/catalog` | `member|reviewer|admin`（关闭鉴权时可 `public`） | 由部署鉴权模式决定 `401/403` |
| `POST /api/reviewer/redeem` | `public`（邀请码准入） | 邀请码校验失败返回 `400/404/410` |
| `GET /api/reviewer/submissions` | `reviewer|admin` | `403 permission_denied` |
| `POST /api/reviewer/submissions/decide` | `reviewer|admin` | `403 permission_denied` |
| `POST /api/admin/apply` | `admin` | `403 permission_denied` |
| `POST /api/admin/profile-pack/apply` | `admin` | `403 permission_denied` |
| `POST /api/admin/pipeline/run` | `admin` | `403 permission_denied` |

所有基于角色的拒绝响应，应返回 `error.code=permission_denied`。

## Phase 4 补充

1. `get_trial_status()` 与 `GET /api/trial/status` 现在可返回 `not_started|active|expired` 状态，以及 `ttl_seconds` / `remaining_seconds`。
2. `admin_dryrun()` 与 `POST /api/admin/dryrun` 用于预注册严格模式 patch 计划，不直接落配置。
3. `admin_rollback()` 与 `POST /api/admin/rollback` 可在最近一次成功 apply 后恢复快照。
4. `POST /api/templates/submit` 现在支持附带 `package_name + package_base64`，用于上传模板包。
5. 上传后返回 `risk_level`、`review_labels`、`warning_flags` 与 `scan_summary.prompt_injection`。
6. `generate_package()` 和下载接口会优先复用已批准投稿所附带的原始模板包，并返回 `source=uploaded_submission|generated`。
7. 管理员可通过 `POST /api/admin/submissions/review` 单独保存 `review_note` 与人工审核标签，无需立即 approve/reject。
8. 管理员可在投稿尚未批准前，通过 `GET /api/admin/submissions/package/download` 下载原始投稿包，并用 `GET /api/admin/submissions/compare` 对比当前已发布基线。
9. `GET /api/admin/submissions/compare` 现返回 `details` 字段，包含 version/risk/review_note/prompt/package/scan 等字段级 diff。
10. `GET /api/templates` 现在还支持 `category`、`tag`、`source_channel` 等官方目录筛选参数，并继续支持 `review_label`、`warning_flag`。
11. `GET /api/templates` 还支持 `sort_by=template_id|recent_activity|trial_requests|installs` 与 `sort_order=asc|desc`。
12. 模板列表与详情 payload 现在会返回 `category`、`tags`、`maintainer`、`source_channel`，以及聚合后的 `engagement` 对象，便于 starter catalog 浏览。
13. `engagement` 当前包含 `trial_requests`、`installs`、`prompt_generations`、`package_generations`、`community_submissions` 与 `last_activity_at`。
14. `GET /api/templates/detail` 与 `GET /api/admin/submissions/detail` 会返回适合 WebUI 详情卡片的 payload，包括 prompt 预览/长度、时间戳、包元数据、目录元数据与模板 engagement 数据。
15. WebUI 的语言切换（`en-US` / `zh-CN` / `ja-JP`）属于前端行为；API 接口不接收 locale 参数，返回 schema 不随语言变化。
16. WebUI 中的本地化文案（集合状态、面板状态、审核提示、详情字段标签）由前端字典映射生成；API 字段 key 保持稳定（英文 `snake_case`）。
17. `GET /api/ui/capabilities` 设计为登录前可读；开启鉴权但未携带 token 时，角色解析为 `public`，仅返回最小能力集。

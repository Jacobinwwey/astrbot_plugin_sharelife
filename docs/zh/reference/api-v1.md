# Sharelife API v1（公开 + 用户侧接口面）

本页只保留公开目录读取接口与 member 侧可调用的变更接口。
特权内部接口不在公开参考中展开。

## 范围

1. 公开只读接口：市场检索、详情、对比、健康检查、能力发现。
2. 用户接口：登录、试用、安装、上传、profile-pack 导入/投稿、本地安装管理、任务恢复、transfer-job 可视化、本人投稿查询与下载。
3. 属主绑定：开启鉴权后，member 路由只能操作与当前认证 `user_id` 对应的数据。

## 公开 + 用户侧应用方法

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

## 公开 + 用户侧 HTTP 路由

公开路由：

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

用户路由：

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

## 公开上传 / 安装载荷说明

1. `POST /api/templates/install`
   - `install_options.preflight: bool`
   - `install_options.force_reinstall: bool`
   - `install_options.source_preference: auto|uploaded_submission|generated`
2. `POST /api/templates/submit`
   - `package_name + package_base64`：直接上传模板包
   - `upload_options.scan_mode: strict|balanced`
   - `upload_options.visibility: community|private`
   - `upload_options.replace_existing: bool`
   - `upload_options.idempotency_key` 或 `Idempotency-Key` 请求头：安全重试
3. `POST /api/profile-pack/submit`
   - 当前主线必须提供 `artifact_id`
   - `submit_options.pack_type: bot_profile_pack|extension_pack`
   - `submit_options.selected_sections: string[]`
   - `submit_options.redaction_mode: exclude_secrets|exclude_provider|include_provider_no_key|include_encrypted_secrets`
   - `submit_options.replace_existing: bool`
   - `submit_options.idempotency_key` 或 `Idempotency-Key` 请求头：安全重试
4. `POST /api/member/profile-pack/imports`
   - `filename + content_base64`：先创建用户私有 import 草稿，再决定是否投稿
5. `GET /api/member/submissions/package/download`
   - 可选 `Idempotency-Key` 请求头：避免重复创建下载作业
   - 成功响应可能附带 `X-Sharelife-Transfer-Job-Id` 与 `X-Sharelife-Transfer-Status`
6. 模板包直接上传上限为 `20 MiB`，超限返回 `package_too_large`。

## Auth Badge Matrix (HTTP)

| 路由 | 所需角色 | 拒绝行为 |
| --- | --- | --- |
| `GET /api/ui/capabilities` | `public` | N/A |
| `POST /api/login` | `public` | `401 invalid_credentials` 或 `429 rate_limited` |
| `GET /api/templates` | `public` | N/A |
| `GET /api/templates/detail` | `public` | N/A |
| `GET /api/profile-pack/catalog` | `public` | N/A |
| `GET /api/profile-pack/catalog/detail` | `public` | N/A |
| `GET /api/profile-pack/catalog/compare` | `public` | N/A |
| `GET /api/profile-pack/catalog/insights` | `public` | N/A |
| `POST /api/trial` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/templates/install` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/templates/package/download` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/notifications` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/tasks` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/member/tasks/refresh` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/transfers` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/member/transfers/refresh` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/templates/submit` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/profile-pack/submit` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/member/profile-pack/imports` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/profile-pack/imports` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/installations` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/member/installations/refresh` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/member/installations/uninstall` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/submissions` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/submissions/detail` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/submissions/package/download` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/profile-pack/submissions` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/profile-pack/submissions/detail` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/member/profile-pack/submissions/withdraw` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/profile-pack/submissions/export/download` | `member` | `401 unauthorized` 或 `403 permission_denied` |

所有越权拒绝都应返回 `error.code=permission_denied`。

## 错误模型

1. `permission_denied`：角色或属主绑定拒绝当前操作。
2. `unauthorized` / `invalid_credentials`：需要登录或凭证错误。
3. `package_too_large`：上传包超过 `20 MiB` 上限。
4. `template_not_installable`：目标模板当前不可安装。
5. `profile_pack_source_required`：投稿 profile-pack 时未提供 `artifact_id`。
6. `idempotency_key_conflict`：同一幂等键被用于不同提交范围。
7. `prompt_injection_detected`：扫描命中高风险信号；当前行为是标记并升级审查，不会静默删除。

## 运行说明

1. `get_trial_status()` 与 `GET /api/trial/status` 会返回 `not_started|active|expired`，并附带 `ttl_seconds` 与 `remaining_seconds`。
2. `GET /api/ui/capabilities` 在登录前可读，前端据此隐藏或禁用受保护控件。
3. 若启用 `allow_anonymous_member=true`，只有 allowlist 中的接口可匿名访问，且请求仍固定绑定到 `anonymous_member_user_id`。
4. `GET /api/templates` 支持服务端筛选与排序，包括 `category`、`tag`、`source_channel`、`review_label`、`warning_flag`、`sort_by` 与 `sort_order`。
5. 模板列表与详情 payload 会返回 `category`、`tags`、`maintainer`、`source_channel`，以及聚合后的 `engagement` 对象，便于市场卡片排序与展示。
6. 当前 `engagement` 包含 `trial_requests`、`installs`、`prompt_generations`、`package_generations`、`community_submissions` 与 `last_activity_at`。
7. `POST /api/templates/submit` 与 `POST /api/profile-pack/submit` 都支持通过 payload 选项或 `Idempotency-Key` 请求头实现幂等重放。
8. 用户任务队列接口可以通过审计事件恢复上传/下载历史，页面刷新后仍可重建状态。
9. 用户 transfer 接口会返回 `attempt_count`、`retry_count`、`failure_reason`、`metadata`，用于下载链路排障。
10. 投稿包下载会把 transfer-job 信息附加到 payload 与响应头，便于前端安全重放同一逻辑下载任务。
11. 用户 profile-pack import 在正式投稿前始终保持为用户私有草稿。
12. `POST /api/member/profile-pack/submissions/withdraw` 允许用户在队列处理开始前撤回待审投稿。
13. 用户下载接口默认做属主隔离：member 只能下载自己的投稿包或导出产物。
14. 审批、apply/rollback、secret 轮换、备份恢复、精选运营等特权流程不在公开文档集中展开。

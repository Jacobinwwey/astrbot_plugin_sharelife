# Sharelife API v1（公开 + 用户侧接口面）

本页只保留公开目录读取接口与 member 侧可调用的变更接口。
reviewer/admin/operator 相关接口已从公开参考中移除，转入私有运维文档。

## 范围

1. 公开只读接口：市场检索、详情、对比、健康检查、能力发现。
2. 用户接口：登录、试用、安装、上传、profile-pack 投稿、本地安装管理、本人投稿查询与下载。
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
3. `POST /api/profile-pack/submit`
   - 当前主线必须提供 `artifact_id`
   - `submit_options.pack_type: bot_profile_pack|extension_pack`
   - `submit_options.selected_sections: string[]`
   - `submit_options.redaction_mode: exclude_secrets|exclude_provider|include_provider_no_key|include_encrypted_secrets`
   - `submit_options.replace_existing: bool`
4. 模板包直接上传上限为 `20 MiB`，超限返回 `package_too_large`。

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
| `POST /api/templates/submit` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/profile-pack/submit` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/installations` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/member/installations/refresh` | `member` 或匿名白名单 | `401 unauthorized` 或 `403 permission_denied` |
| `POST /api/member/installations/uninstall` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/submissions` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/submissions/detail` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/profile-pack/submissions` | `member` | `401 unauthorized` 或 `403 permission_denied` |
| `GET /api/member/profile-pack/submissions/detail` | `member` | `401 unauthorized` 或 `403 permission_denied` |

所有越权拒绝都应返回 `error.code=permission_denied`。

## 错误模型

1. `permission_denied`：角色或属主绑定拒绝当前操作。
2. `unauthorized` / `invalid_credentials`：需要登录或凭证错误。
3. `package_too_large`：上传包超过 `20 MiB` 上限。
4. `template_not_installable`：目标模板当前不可安装。
5. `profile_pack_source_required`：投稿 profile-pack 时未提供 `artifact_id`。
6. `prompt_injection_detected`：扫描命中高风险信号；当前行为是标记并升级审查，不会静默删除。

## 运行说明

1. `get_trial_status()` 与 `GET /api/trial/status` 会返回 `not_started|active|expired`，并附带 `ttl_seconds` 与 `remaining_seconds`。
2. `GET /api/ui/capabilities` 在登录前可读，前端据此隐藏或禁用受保护控件。
3. 若启用 `allow_anonymous_member=true`，只有 allowlist 中的接口可匿名访问，且请求仍固定绑定到 `anonymous_member_user_id`。
4. 用户下载接口默认做属主隔离：member 只能下载自己的投稿包或导出产物。
5. 审核、apply/rollback、reviewer 生命周期、secret 轮换、备份恢复、精选运营等流程只在私有运维文档中维护。

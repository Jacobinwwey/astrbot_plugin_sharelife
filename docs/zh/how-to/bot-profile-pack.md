# Bot Profile Pack 操作

本页是 `bot_profile_pack` 与 `extension_pack` 的实操手册。

如需先确认“到底会迁移哪些设置”，请先看：
[Bot 配置迁移范围（真值表）](/zh/how-to/profile-pack-migration-scope)

## 你能得到什么

1. 把运行态配置导出为可迁移包。
2. 默认对 secrets 脱敏。
3. 先看分段 diff，再 apply。
4. apply 后支持 rollback。
5. 支持仅扩展能力的共享包（`skills`、`personas`、`mcp_servers`、`plugins`）。

## 官方参考包

Sharelife 现在会自动注入一个已发布示例包，供用户对照：

1. `pack_id`: `profile/official-starter`
2. `pack_type`: `bot_profile_pack`
3. `version`: `1.0.0`
4. `featured`: `true`

可直接用于：

1. 目录筛选（`pack_id=profile/official-starter`）
2. runtime 对比流程演练
3. import + dry-run + apply 全链路预演后再发布你自己的包

仓库内也提供了可直接参考的示例配置包（展开形态）：

1. `examples/profile-packs/official-starter/manifest.json`
2. `examples/profile-packs/official-starter/sections/*.json`

需要本地打包为可导入 zip 时：

```bash
cd examples/profile-packs/official-starter
zip -r profile-official-starter-1.0.0.bot-profile-pack.zip manifest.json sections
```

## 管理员命令链路

```text
/sharelife_profile_export profile/basic 1.0.0 exclude_secrets astrbot_core,providers,plugins providers.openai.base_url sharelife_meta.owner bot_profile_pack
/sharelife_profile_export extension/community-tools 1.0.0 exclude_secrets "" "" "" extension_pack
/sharelife_profile_exports 20
/sharelife_profile_import <artifact_id> --dryrun --plan-id profile-plan-basic --sections plugins,providers
/sharelife_profile_plugins <import_id>
/sharelife_profile_plugins_confirm <import_id> [plugins_csv]
/sharelife_profile_plugins_install <import_id> [plugins_csv] [dry_run]
/sharelife_profile_import_dryrun <artifact_id> profile-plan-basic plugins,providers
/sharelife_profile_import_dryrun_latest profile-plan-basic plugins,providers
/sharelife_profile_imports 20
```

说明：

1. `/sharelife_profile_import` 支持 `artifact_id` 或本地 `.zip` 路径。
2. `--dryrun` 会在导入后自动触发 dry-run。
3. `--plan-id`、`--sections` 是可选参数。
4. 导出位置参数顺序：`pack_id version redaction_mode sections_csv mask_paths_csv drop_paths_csv pack_type`。
5. 如果返回 `profile_pack_plugin_install_confirm_required`，先执行 `/sharelife_profile_plugins` 与 `/sharelife_profile_plugins_confirm`，再重试 dry-run。
6. `/sharelife_profile_plugins_install` 仅在 `profile_pack.plugin_install.enabled=true` 时执行。

## WebUI 操作链路

在 **Bot Profile Pack** 面板中：

1. 导出 `Export Profile Pack`。
2. 通过文件或导出记录导入。
3. 可一键 `Import + Dry-Run`，也可手动选 sections dry-run。
4. 包含插件 section 时，走 `Plugin Install Plan -> Confirm Plugin Install -> Execute Plugin Install`。
5. 用计划按钮执行 apply/rollback。

### 兼容性指引面板（WebUI）

在 import 或 dry-run 后，WebUI 会渲染独立的 **兼容性指引** 区块：

1. `Compatibility` 总结（`compatible` / `degraded` / `blocked`）。
2. 人类可读的问题列表（签名、加密 secrets、运行时环境差异等）。
3. 可执行动作清单：
   容器重配、系统依赖重装、插件二进制重装、知识库存储同步。
4. 动作支持点击跳转：可直接定位到对应操作区（插件安装控制 / section 选择 / 开发者原始载荷）。
5. 已映射的问题项也支持点击，复用同一快捷跳转链路。
6. 快捷动作会自动预填后续输入：
   插件相关动作会基于 `missing_plugins` 回填 `plugin_ids`，知识库同步动作会自动选中 `knowledge_base` section。
7. 如果目标仅在开发者模式可见，系统会提示先开启，并在开启后自动继续该动作。
8. 仅开发者模式可见：
   原始 `compatibility_issues` 与归一化 `action_codes` 载荷。

这个区块用于明确“迁移包已导入，但环境侧仍需后续重配”的边界。

## 脱敏模式

1. `exclude_secrets`（默认）：保留 provider 结构，掩码敏感值。
2. `exclude_provider`：移除 provider section。
3. `include_provider_no_key`：保留 provider，移除 key 类字段。
4. `include_encrypted_secrets`：导出加密 secrets，导入/dry-run/apply 时可自动解密（需配置 `profile_pack.secrets_encryption_key`）。

高级覆盖：

1. `mask_paths`：强制掩码指定路径。
2. `drop_paths`：导出时删除指定路径。

## Pack 类型

1. `bot_profile_pack`：完整运行态（`astrbot_core/providers/plugins/skills/personas/mcp_servers/sharelife_meta/memory_store/conversation_history/knowledge_base/environment_manifest`）。
2. `extension_pack`：扩展能力（`plugins/skills/personas/mcp_servers`）。

## 安全配置键

1. `profile_pack.signing_key_id`
2. `profile_pack.signing_secret`
3. `profile_pack.trusted_signing_keys`
4. `profile_pack.secrets_encryption_key`
5. `profile_pack.plugin_install.enabled`
6. `profile_pack.plugin_install.command_timeout_seconds`
7. `profile_pack.plugin_install.allowed_command_prefixes`
8. `profile_pack.plugin_install.allow_http_source`
9. `profile_pack.plugin_install.require_success_before_apply`

## 发布后治理元数据

1. `capability_summary`
2. `compatibility_matrix`
3. `review_evidence`
4. `featured` 与管理员说明

## HTTP API

1. `POST /api/admin/profile-pack/export`
2. `GET /api/admin/profile-pack/export/download`
3. `GET /api/admin/profile-pack/exports`
4. `POST /api/admin/profile-pack/import`
5. `POST /api/admin/profile-pack/import/from-export`
6. `POST /api/admin/profile-pack/import-and-dryrun`
7. `GET /api/admin/profile-pack/imports`
8. `POST /api/admin/profile-pack/dryrun`
9. `GET /api/admin/profile-pack/plugin-install-plan`
10. `POST /api/admin/profile-pack/plugin-install-confirm`
11. `POST /api/admin/profile-pack/plugin-install-execute`
12. `POST /api/admin/profile-pack/apply`
13. `POST /api/admin/profile-pack/rollback`
14. `POST /api/admin/profile-pack/catalog/featured`

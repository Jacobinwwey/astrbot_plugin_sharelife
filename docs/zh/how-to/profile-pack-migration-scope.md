# Bot 配置迁移范围（真值表）

这份文档只回答一个问题：**Sharelife 现在到底会迁移哪些设置**。

## 基线（截至当前实现）

1. AstrBot 上游基线：`origin/master@9d4472cb2d0108869d688a4ac731e539d41b919e`（2026-04-02）。
2. 分支说明：AstrBot 上游当前主开发分支是 `master`，不是 `main`。
3. Sharelife 基线：`main@7aebf279d074b80df7566c2d957f58d2c3cd6efd`。
4. 迁移模型：**section 级快照/回放**，来源是 Sharelife runtime state（默认 `runtime_state.json`），不是直接改写 AstrBot 全量配置文件。

## 快速结论

1. `bot_profile_pack` 当前可迁移 section：
   `astrbot_core/providers/plugins/skills/personas/mcp_servers/sharelife_meta/memory_store/conversation_history/knowledge_base/environment_manifest`
2. `extension_pack` 当前可迁移 section：
   `plugins/skills/personas/mcp_servers`
3. 迁移是“按 key 原样回放”，不做字段语义翻译。

## 迁移范围矩阵（当前已实现）

| Section | 来源键（runtime snapshot） | 当前迁移行为 | 备注 |
|---|---|---|---|
| `astrbot_core` | `snapshot["astrbot_core"]` | 导出/导入/dry-run/apply/rollback 全链路可用 | 用于承载 bot 核心设置镜像，不等价于 AstrBot 全配置根节点 |
| `providers` | `snapshot["providers"]` | 全链路可用 | 支持 `exclude_secrets` / `exclude_provider` / `include_provider_no_key` / `include_encrypted_secrets` |
| `plugins` | `snapshot["plugins"]` | 全链路可用 | 若包含安装元数据，会触发 `plan -> confirm -> execute` 安装门禁 |
| `skills` | `snapshot["skills"]` | 全链路可用 | 适合能力包共享 |
| `personas` | `snapshot["personas"]` | 全链路可用 | 适合人格模板共享 |
| `mcp_servers` | `snapshot["mcp_servers"]` | 全链路可用 | 可随包迁移 MCP 服务器声明 |
| `sharelife_meta` | `snapshot["sharelife_meta"]` | 全链路可用（仅 `bot_profile_pack`） | 用于 Sharelife 内部元数据，不属于 AstrBot 核心配置 |
| `memory_store` | `snapshot["memory_store"]` | 全链路可用（仅 `bot_profile_pack`） | 可选导出本地记忆状态；建议先 dry-run 评估体积与敏感度 |
| `conversation_history` | `snapshot["conversation_history"]` | 全链路可用（仅 `bot_profile_pack`） | 可选导出会话历史；可能包含高敏感内容，默认仍遵循 redaction 策略 |
| `knowledge_base` | `snapshot["knowledge_base"]` | 全链路可用（仅 `bot_profile_pack`） | 可迁移知识库索引/配置；外部原始文件仍需手动同步 |
| `environment_manifest` | `snapshot["environment_manifest"]` | 可导出并参与兼容提示（仅 `bot_profile_pack`） | 用于声明容器、系统依赖、插件二进制等“重配信息”，不自动执行系统级变更 |

## 当前明确不在迁移闭环内的内容

1. AstrBot `data/cmd_config.json` 中、且**未映射到上述 section** 的键，不会自动迁移。
2. 当前没有“按 AstrBot 配置 schema 的字段级转换器”；适配层是 `section_name -> state_key` 一对一回放。
3. 插件二进制、系统依赖、容器环境、外部数据库/知识库原始文件不会随 profile pack 自动打包；`environment_manifest` 只承载“需要重配”的声明信息。
4. 插件安装默认不执行命令；即使有安装元数据，也必须经过特权确认和执行门禁配置。
5. 跨大版本 AstrBot 的兼容只做声明校验（`astrbot_version` / `plugin_compat`），不做自动语义迁移。
6. 若包内带有 `environment_manifest` 或知识库外部路径信息，导入后会进入 `compatibility_issues`（degraded），用于提醒迁移后需重配容器、依赖与插件二进制。

## 精准性与安全性保证（当前）

1. 每个 section 都有独立哈希，导入会校验 mismatch。
2. 可选 HMAC 签名与受信任 key 验签。
3. `include_encrypted_secrets` 支持导出加密 + 导入/干跑/应用解密闭环（需配置 `profile_pack.secrets_encryption_key`）。
4. apply 走快照回滚路径，失败可回退。
5. 高风险能力和审核证据会进入 `capability_summary` / `review_evidence`。
6. 对 `environment_manifest` 会产出结构化 `compatibility_issues`，避免误以为“系统依赖已自动迁移”。

## 用户如何自检“这次会迁移什么”

1. 导出前先确认 runtime state 中是否有目标 section。
2. 使用：
   `/sharelife_profile_export <pack_id> <version> exclude_secrets <sections_csv>`
3. 导入后先 dry-run：
   `/sharelife_profile_import <artifact_id> --dryrun --plan-id <plan_id> --sections <sections_csv>`
4. 重点看 dry-run 结果中的 `selected_sections`、`changed_sections`、`diff`，再决定 apply。
5. 若看到 `environment_*_reconfigure_required` 或 `knowledge_base_storage_sync_required`，在迁移后应把该提示同步给你的 AI 运维代理，执行容器/依赖/二进制的重配流程。

## 开发维护要求（给开发者）

每次跟进 AstrBot 上游配置变更时，至少做这 5 步：

1. 更新本页“基线提交号”（AstrBot + Sharelife）。
2. 对比 AstrBot 配置字段变化（参考上游配置文档）。
3. 判断新字段应归属哪个 section，必要时扩展 section 适配器。
4. 补测试（导出、导入、dry-run、apply、rollback）。
5. 同步 README 与多语言文档入口，避免“实现和文档漂移”。

## 参考

1. AstrBot 配置文档：<https://github.com/AstrBotDevs/AstrBot/blob/master/docs/zh/dev/astrbot-config.md>
2. Sharelife Bot Profile Pack 操作：[/zh/how-to/bot-profile-pack](/zh/how-to/bot-profile-pack)

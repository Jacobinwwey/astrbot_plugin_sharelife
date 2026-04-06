# Sharelife Stateful Profile-Pack Migration Design (AstrBot master 2026-04-02)

## Baseline

1. AstrBot upstream baseline: `origin/master@9d4472cb2d0108869d688a4ac731e539d41b919e` (2026-04-02).
2. Sharelife baseline when this spec is written: `main@7aebf279d074b80df7566c2d957f58d2c3cd6efd`.
3. Existing invariant stays unchanged:
   `dry-run -> selective apply -> rollback`, plus scan/evidence/audit.
4. Stitch redesign references (for UI implementation mapping):
   project `11867940733077632109`, market screen `e473948159614979a7a942b41a06ca6f`, member screen `300fdde8c7c8466bac5acdd69dff2dfb`, design system asset `dd11b6a1063c4249932d00c1c7724360` (`Emerald Nocturne`).

## 最简版本

1. 扩展 `bot_profile_pack` section 范围：
   `memory_store / conversation_history / knowledge_base / environment_manifest`（均为可选，不强制导出）。
2. 迁移方式保持不变：
   section 级快照回放，不引入字段级语义转换器。
3. 新增“代码级迁移告知”闭环：
   当 `environment_manifest` 或 `knowledge_base` 包含外部依赖线索时，导入结果标记 `compatibility=degraded`，并输出结构化 `compatibility_issues`，明确需要手动重配。
4. WebUI 保持普通用户简洁面板；开发者模式显示证据、路径、原始 payload 与重配告警。

## 架构图（文字）

```text
[Runtime Snapshot]
    |
    v
[ProfileSectionAdapterRegistry]
  - astrbot_core/providers/plugins/...
  - memory_store/conversation_history/knowledge_base/environment_manifest
    |
    v
[ProfilePackService.export]
  -> redaction/signature/hash
  -> sections/*.json + manifest.json
    |
    v
[ProfilePackService.import]
  -> hash/signature/compat scan
  -> compatibility issues (including environment reconfigure notices)
    |
    v
[dry-run diff]
  -> selected sections
  -> changed sections + review evidence
    |
    v
[apply + rollback]
  -> runtime patch replay
  -> audit trail
```

## 核心组件

1. `sharelife/domain/profile_pack_models.py`
   section 白名单、capability 白名单。
2. `sharelife/application/services_profile_section_registry.py`
   section 采集/回放适配器。
3. `sharelife/application/services_profile_pack.py`
   导出、导入、兼容评估、dry-run、apply、rollback、审核证据。
4. `sharelife/webui/*`
   用户态/管理员态界面、开发者模式视图、i18n。
5. `docs/*/profile-pack-migration-scope.md`
   用户与开发者共读的真值表。

## 数据流

1. Export:
   runtime snapshot -> section capture -> redaction -> manifest+hash/signature -> zip artifact。
2. Import:
   zip parse -> hash/signature verify -> scan evidence -> compatibility + issues -> import record。
3. Dry-run:
   selected sections -> target materialize -> runtime current capture -> diff -> patch register。
4. Apply:
   patch apply -> runtime state update -> rollback snapshot retained -> audit record。
5. Code-level notice:
   `environment_manifest` / KB 外部路径 -> compatibility issues -> WebUI/CLI 告知 -> 迁移后 AI/Ops 执行手动重配。

## 技术栈

1. Backend: Python + FastAPI + Pydantic + layered service architecture。
2. Storage: repository abstraction (SQLite default + JSON fallback)。
3. Frontend: standalone vanilla JS modules + shared event bus + i18n bundles。
4. Security: signature verification, encrypted secrets mode, risk scan evidence, rate-limit/security headers。
5. Docs: VitePress multilingual docs + migration truth-table pages。

## 搭建顺序

1. Phase A (already started):
   扩 section model + registry + compatibility issue mapping。
2. Phase B:
   WebUI 表单与记录展示更新（新增 section 说明、重配告警提示、开发者模式定位）。
3. Phase C:
   补齐测试（domain/application/interfaces/meta）与多语言文档同步。
4. Phase D:
   观察真实社区包反馈后，再考虑字段级语义转换器或增量压缩。

## 边界情况

1. 大量会话历史导致包体过大：
   必须支持 section 选择与分段导出建议。
2. 敏感聊天记录泄露风险：
   继续默认 `exclude_secrets`；用户显式选择才导出对应 section。
3. 目标端环境不匹配：
   通过 `environment_*_reconfigure_required` 阻止“误判已完成迁移”。
4. KB 外部文件缺失：
   `knowledge_base_storage_sync_required` 明确提示手动同步。
5. 跨版本字段漂移：
   当前依赖声明校验；不做自动语义迁移。

## 扩展策略

1. 先保证可解释与可回滚，再做自动化：
   所有自动行为先输出 evidence 和 action hints。
2. section-first 扩展，不破坏现有接口：
   新能力优先以新增 section 接入，不改已有 section 语义。
3. 兼容策略可渐进升级：
   先 `degraded + guidance`，后续按稳定性引入 `auto-fix adapters`。
4. 继续维持用户态/管理员态与开发者模式分层，避免认知过载。

## 潜在瓶颈

1. 大包导入时 CPU/IO 压力（hash + diff + scan）。
2. `conversation_history` 规模增长导致 WebUI 渲染和 diff 成本上升。
3. `environment_manifest` 无统一 schema 时可解释性下降。
4. 多语言文档与 UI 文案同步成本。

## v2 优化

1. 增量迁移：
   对 `conversation_history` 和 `memory_store` 提供 delta export/import。
2. 环境重配自动脚本模板：
   从 `environment_manifest` 生成可审阅的 shell/compose patch（默认 dry-run）。
3. KB artifact 可选打包：
   通过白名单路径 + 压缩策略导出小体积知识库快照。
4. 长任务异步化：
   import/scan/diff 任务化并提供进度事件。
5. 签名策略增强：
   支持多 key trust set 与 key rotation 审计。

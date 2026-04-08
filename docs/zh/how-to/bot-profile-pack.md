# Bot Profile Pack 操作

本页只面向公开 / 用户侧，描述 profile-pack 的浏览、对比与投稿链路。
特权审批、精选运营、secret 导出规则与恢复手册均不在公开文档中展开。

如果你先要看迁移边界真值表，请从这里开始：
[Bot 配置迁移范围（真值表）](/zh/how-to/profile-pack-migration-scope)

## 当前用户能做什么

1. 在 `/market` 浏览已发布的 profile-pack。
2. 打开 `详情与对比`，按 section 对比本地运行时状态。
3. 在 member 侧把 profile-pack 产物投稿到社区队列。
4. 只查看自己的 profile-pack 投稿列表。
5. 只下载自己的投稿导出物。

## 官方参考包

Sharelife 会自动提供一个官方 starter pack：

1. `pack_id`: `profile/official-starter`
2. `pack_type`: `bot_profile_pack`
3. `version`: `1.0.0`
4. `featured`: `true`

它适合用于：

1. 作为目录筛选基线（`pack_id=profile/official-starter`）
2. 演练本地对比流程
3. 在投稿前验证 `selected_sections` 是否合理

## 当前用户投稿链路

1. 先准备本地 profile-pack 产物，并拿到对应的 `artifact_id`。
2. 打开本地 WebUI 的 `/member` 或 `/market`。
3. 在 profile-pack 区域把 `artifact_id` 填入 `投稿到社区`。
4. 可选提交参数：
   - `pack_type`
   - `selected_sections`
   - `redaction_mode`
   - `replace_existing`
5. 提交后，到 `我的 Profile-Pack 投稿` 查看状态、详情与自己的导出下载。

## 提交选项

1. `pack_type`
   - `bot_profile_pack`
   - `extension_pack`
2. `selected_sections`
   - 控制本次投稿要公开哪些 section
3. `redaction_mode`
   - `exclude_secrets`
   - `exclude_provider`
   - `include_provider_no_key`
   - `include_encrypted_secrets`
4. `replace_existing`
   - 对同一 member + pack，会把更早的 pending 投稿标记为已替换，仅保留最新 pending 行作为审查对象

## 对比与本地应用的边界

1. 公开 / 用户文档只覆盖对比与投稿。
2. 特权 apply/rollback 不属于公开契约。
3. 当前推荐链路是：
   - 先浏览已发布包
   - 按 section 对比
   - 决定是否本地安装 / 导入
   - 若希望公开，再把自己的产物投稿进入审查队列

## 当前限制

1. 当前主线的社区投稿是 `artifact_id` 模式，不是公开 ZIP 直传模式。
2. `replace_existing` 只会整理 pending 队列，不会覆盖已通过或已拒绝的历史记录。
3. 对比 / 投稿结果不等于“完整恢复点”；它只能辅助判断，不能代表完整环境快照恢复。
4. 带特权 secret 的 operator 导出物不会作为公开 artifact 暴露，也不会在用户文档路径中提供下载。

## 用户可见状态

1. `pending`
2. `approved`
3. `rejected`
4. `replaced`

## 安全边界

1. profile-pack 目录接口是公开只读。
2. 投稿与“我的投稿”接口是 member 专属且带属主隔离。
3. 特权审核、设备/会话治理与高权限存储流程只在私有文档中维护。

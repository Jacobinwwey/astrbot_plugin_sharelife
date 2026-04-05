# Sharelife v1 冻结方案（2026-03-24）

## 1. 背景与目标

`sharelife` 是一个 AstrBot 插件项目，目标是把模板分发、风险预检、会话试用、管理员审批与全局应用统一在一个治理框架下。

v1 目标：

1. 官方标准模板源可用。
2. 严格模式可用。
3. 普通用户可会话级试用（不改全局）。
4. 管理员可安全应用并可回滚。
5. WebUI 独立页可操作。
6. 文档采用 VitePress + Diataxis，支持中英并行并预埋日语。

## 2. 已确认决策（冻结）

1. 模板来源：仅官方源 `Jacobinwwey/astrbot_plugin_sharelife`。
2. 模板范围：`subagent + agent + AstrBot 更广配置（provider/commands 等）`。
3. 执行策略：严格模式。
4. 独立前端页面：采用独立 `Sharelife` 页面。
5. 普通用户能力：允许会话级试用。
6. 试用时长：默认 2 小时。
7. 续期策略：不允许续期，必须向管理员请求。
8. 首次提醒：仅首次试用触发一次双通知（用户 + 管理员）。
9. 二次试用：进入排队并自动提醒管理员。
10. 队列超时：72 小时后转人工待办，不自动关闭。
11. 人工待办处理权限：任意管理员可处理。
12. 并发决策保护：启用 10 分钟短时抢占锁。
13. 强制接管：允许，但必须填写理由（必填）。
14. 通知通道：WebUI 通知中心 + 管理员私信双发。
15. 实时通知路由：仅当前值班管理员。
16. 离线补偿：后上线管理员收到离线窗口摘要日志。
17. 文档语言：中英双语并行，预埋日语扩展。
18. 迁移预期：为 SDK v4 预留 Runtime 兼容层。
19. 路线优先级：`v1 个人用户社区化优先`；企业化机制（on-call、接管锁、离线补偿）保留为后续可启用能力。
20. 个人用户偏好：支持在两种代理执行方案间切换，并支持开启/关闭任务细节观测（默认关闭）。

## 3. 架构总览

采用模块化分层：

1. `domain`：模型、规则、风险分级、状态机。
2. `application`：用例编排（预检、试用、审批、应用、回滚）。
3. `infrastructure`：GitHub 源、存储、运行时适配、通知适配。
4. `interfaces`：命令、API、WebUI DTO。

依赖方向：`interfaces -> application -> domain`，`infrastructure` 仅实现端口，不反向侵入。

## 4. 风险分级与严格模式

1. L1 低风险：描述文案、角色补充等。
2. L2 中风险：路由策略、工具白名单等。
3. L3 高风险：provider 设置、命令权限、可能影响全局安全边界的配置。

严格模式规则：

1. 全局应用必须先 `dry-run`。
2. L3 默认不生效，需管理员显式授权。
3. 普通用户试用态不得激活 L3。

## 5. 会话级试用模型

1. 范围：仅当前会话，采用 overlay，不写全局配置。
2. 生命周期：`preview -> trial_dryrun -> start_trial -> in_trial -> stop/expire`。
3. 默认 TTL：7200 秒。
4. 不可续期：固定策略。
5. 首次试用后如要继续，必须走管理员请求。

## 6. 重试请求与人工待办

重试请求状态机：

`queued -> notified -> reviewing -> approved | rejected | manual_backlog -> closed`

规则：

1. 72h 到期转 `manual_backlog`，不关闭。
2. 管理员可在 `manual_backlog` 继续处理。
3. 相同请求去重，避免重复刷单。

## 7. 并发处理与抢占锁

1. 打开待办详情即尝试获取 10 分钟锁。
2. 其他管理员默认只读。
3. 可强制接管，接管理由必填。
4. 决策提交需带 `request_version + lock_version`。
5. 冲突返回并提示刷新。

## 8. 通知策略

双通道：

1. WebUI 通知中心。
2. 管理员私信。

路由：

1. 实时事件仅发当前 on-call 管理员。
2. 非 on-call 管理员上线后收到离线窗口摘要。

事件：

1. 首次试用。
2. 二次试用入队。
3. 72h 转人工待办。
4. 强制接管。
5. 管理员终态决策。

## 9. API 草案（v1）

用户侧：

1. `GET /api/sharelife/v1/templates`
2. `GET /api/sharelife/v1/templates/{id}`
3. `POST /api/sharelife/v1/trial/dryrun`
4. `POST /api/sharelife/v1/trial/start`
5. `POST /api/sharelife/v1/trial/stop`
6. `POST /api/sharelife/v1/trial/retry-request`
7. `GET /api/sharelife/v1/trial/retry-request/status`
8. `GET /api/sharelife/v1/preferences`
9. `POST /api/sharelife/v1/preferences/mode`
10. `POST /api/sharelife/v1/preferences/observe-details`

管理员侧：

1. `GET /api/sharelife/v1/admin/retry-requests`
2. `POST /api/sharelife/v1/admin/retry-requests/{id}/decision`
3. `POST /api/sharelife/v1/admin/retry-requests/{id}/takeover`
4. `POST /api/sharelife/v1/admin/dryrun`
5. `POST /api/sharelife/v1/admin/apply`
6. `POST /api/sharelife/v1/admin/rollback`
7. `GET /api/sharelife/v1/admin/audit`

## 10. WebUI 独立页信息架构

1. Market：模板浏览与筛选。
2. Detail：模板详情、风险、兼容结论。
3. Preview：配置差异预览。
4. Trial Bar：当前试用状态与剩余时间。
5. Admin Console：审批、dry-run、apply、rollback。
6. Audit：审计日志与操作轨迹。
7. On-call：值班状态与离线补偿摘要。

## 11. i18n 与文档策略

1. 首版语言：`zh-CN + en-US`。
2. 预埋语言：`ja-JP`。
3. 后端返回 `i18n_key + params`，前端渲染。
4. 文档结构遵循 Diataxis：Tutorials / How-to / Reference / Explanation。

## 12. SDK v4 迁移预期

1. 引入 `RuntimePort` 作为唯一运行时端口。
2. 当前实现 `astrbot_runtime_v3`，预留 `astrbot_runtime_v4`。
3. 业务逻辑不直接依赖 SDK 细节。
4. 通过能力探测与 feature flag 实现双栈灰度。

## 13. 开发优先级（个人用户社区化优先）

v1（优先开发）：

1. 官方模板分发与标准模板规范。
2. 严格模式下的会话试用、管理员审批、全局 apply/rollback。
3. 面向个人用户与小规模社区的基础通知与审计能力。
4. 中英文档并行与日语预埋。

后续阶段（备用方向）：

1. on-call 值班轮转。
2. 多管理员接管锁与复杂并发治理。
3. 离线窗口摘要补偿与更细粒度企业化流程。

## 14. 开发里程碑（两周）

1. Sprint 1：规范、扫描、兼容、只读能力、文档骨架。
2. Sprint 2：管理员闭环、回滚、审计、通知、独立页。

## 15. 验收基线

1. 普通用户不可修改全局配置。
2. 所有全局应用都可回滚。
3. L3 默认禁止自动生效。
4. 72h 超时进入人工待办而非丢单。
5. 并发审批不会产生双写冲突。
6. 中英文档可构建，日语入口预留。

## 16. 待进一步拍板事项

1. on-call 来源：手动切换或排班引擎。
2. 离线摘要的频率与上限。
3. 管理员私信失败时是否升级外部告警通道。

---

该文档是当前讨论的冻结快照，后续版本在此基线增量修订。

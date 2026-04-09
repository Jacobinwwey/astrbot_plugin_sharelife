# 2026-04-06 - Permission Boundary Roadmap Revision

Version: internal-2026-04-06  
Audience: maintainers, reviewer operators, admin operators  
Goal: replace the old permission-boundary roadmap with a code-aligned execution direction that matches public/private documentation constraints.

---

## English

### 1. Why the roadmap must be revised

The previous roadmap was directionally right but tactically unstable.

It mixed together:
- a role-isolation strategy that should stay,
- a reviewer device-key model that is already expensive to maintain,
- a contradictory session policy,
- and public documentation exposure that is broader than necessary.

The revision must therefore do two things at once:
1. keep the macro direction,
2. reduce auth and documentation fragility.

### 2. Code-aligned findings

Validated against the current code:

1. `401` vs `403` is **not** the primary problem anymore.
   - Missing or expired token already returns `401`.
   - Authenticated-but-denied admin/reviewer path access already returns `403`.
   - This belongs in regression tests, not as a major roadmap gap.

2. Reviewer device limit is real.
   - `ReviewerAuthService(max_devices=3)` exists.
   - Registration fails with `device_limit_exceeded` at the configured cap.

3. Reviewer-global single active session is also real.
   - `_issue_token()` in the WebUI server revokes the old token for the same reviewer session key.
   - This contradicts the “up to 3 trusted devices” model and must be removed from the target roadmap.

4. `admin -> reviewer` key/session lifecycle is only partially landed.
   - Backend primitives exist: invite, redeem, register/list/revoke device, force reset.
   - Frontend/admin console is still missing a closed reviewer-management surface.
   - Current docs must stop implying this is complete.

5. Owner-aware policy is missing as a first-class runtime rule.
   - Resource identity fields already exist (`user_id`, maintainer/source metadata).
   - Mutation policy is still role-heavy and not uniformly resource-aware.

### 3. Decisions

1. Do **not** add a standalone runtime `Creator` role.
   - Keep runtime roles simple.
   - Introduce owner-aware authorization checks instead.

2. Keep local reviewer invite/device auth as a fallback path.
   - Do not grow it into a full custom IAM platform.
   - External IdP remains future work.

3. Replace reviewer-global single-session with device-granular invalidation.
   - Each trusted device may hold its own session.
   - Revoking a device invalidates only that device’s sessions.
   - Admin may still revoke all reviewer sessions.

4. Treat admin as audit-constrained, not omnipotent.
   - High-risk operations allowed.
   - Audit history must remain immutable.

### 4. Public/private documentation split

#### Public docs must include
- role boundaries,
- auth semantics (`401` vs `403`),
- stable user/reviewer/admin surface behavior,
- owner-aware direction at principle level,
- explicit statement that reviewer/admin operator procedures are private.

#### Public docs must not include
- reviewer invite SOP,
- device-key lifecycle operations,
- secret storage or restore procedures,
- incident recovery details,
- admin reviewer-key issuance mechanics.

#### Private docs remain the truth source for
- reviewer invite/device/session lifecycle,
- admin reviewer management closure,
- local secret backup and recovery,
- incident and rollback guidance,
- critical architecture tradeoffs and rejected alternatives.

### 5. Required next workstreams

1. Public roadmap rewrite
   - remove key issuance detail,
   - remove reviewer-global single-session target,
   - add owner-aware authorization direction,
   - explicitly mark admin reviewer key closure as incomplete.

2. Admin reviewer key-management closure
   - admin invite issue/list/revoke panel,
   - reviewer device visibility and reset,
   - reviewer session revoke endpoint and UI,
   - audit events for invite/device/session lifecycle,
   - consistent `/admin -> /reviewer` bridge semantics.

3. Owner-aware authorization
   - user-facing mutations must become backend-enforced by resource ownership,
   - not only by hidden controls in the UI.

4. Reviewer evidence UX
   - keep technical evidence visible,
   - default to risk summary first and expandable payloads second.

### 6. Acceptance criteria

This revision is complete only when:
1. public roadmap docs are updated in `zh/en/ja`,
2. private plan is added and visible through the private portal,
3. public docs do not leak operator-grade auth/runbook details,
4. no roadmap text treats `Creator` as a standalone runtime role,
5. the roadmap explicitly says admin reviewer key management is not fully landed yet.

---

## 中文

### 1. 为什么必须修订路线图

旧版路线图的宏观方向没有问题，但战术落地已经不稳定。

它把以下几类内容混在了一起：
- 应该保留的角色隔离方向，
- 已经开始变重的 reviewer 设备密钥体系，
- 自相矛盾的会话策略，
- 以及比当前需要更宽的公开文档暴露面。

所以这轮修订要同时完成两件事：
1. 保住大方向，
2. 收缩认证和文档层面的脆弱性。

### 2. 基于代码现实的判断

已对照当前代码确认：

1. `401` 与 `403` 已不再是主要问题。
   - 缺失或过期 token 已返回 `401`。
   - 已登录但越权访问 reviewer/admin 路径时已返回 `403`。
   - 这应该保留在回归测试里，而不应继续写成路线图主缺口。

2. Reviewer 设备上限是真实存在的。
   - `ReviewerAuthService(max_devices=3)` 已实现。
   - 达到上限后会返回 `device_limit_exceeded`。

3. Reviewer 全局单活跃会话也是真实存在的。
   - WebUI server 中 `_issue_token()` 会回收同一 reviewer 的旧 token。
   - 这与“最多 3 台可信设备”模型直接矛盾，必须从目标路线图中移除。

4. `admin -> reviewer` 密钥/会话生命周期只部分落地。
   - 后端 invite、redeem、device register/list/revoke、force reset 已有。
   - 前端 admin 控制台仍缺完整 reviewer 管理台。
   - 文档必须停止把这一块写得像“已经闭环”。

5. 资源属主规则还不是一等运行时授权规则。
   - 当前资源已存在 `user_id`、maintainer/source 等身份字段。
   - 但所有写操作尚未统一按资源归属做后端强校验。

### 3. 决策

1. 不新增独立运行时 `Creator` 角色。
   - 保持角色矩阵简洁。
   - 改为引入 owner-aware 授权规则。

2. 本地 reviewer invite/device 鉴权保留为 fallback 路径。
   - 不再把它继续扩展成一整套自造 IAM。
   - 外部 IdP 作为后续工作。

3. 用“按设备粒度失效”替换“reviewer 全局单活跃会话”。
   - 每台可信设备可拥有自己的 session。
   - 撤销设备时只失效该设备相关会话。
   - admin 仍可选择全量回收某 reviewer 会话。

4. Admin 仍然受审计约束。
   - 可以操作高危流程。
   - 不能篡改审计历史。

### 4. 公开 / 私有文档分层

#### 公开文档必须包含
- 角色边界，
- 鉴权语义（`401` / `403`），
- 稳定的 user/reviewer/admin 可见行为，
- owner-aware 方向原则，
- reviewer/admin 运维流程仅在私有文档中维护的说明。

#### 公开文档不得包含
- reviewer invite SOP，
- device-key 生命周期操作，
- secret 存储或恢复细节，
- 事故恢复流程，
- admin reviewer 密钥发放机制。

#### 私有文档继续作为真值源
- reviewer invite/device/session 生命周期，
- admin reviewer 管理闭环，
- 本地 secret 备份与恢复，
- 事故与回滚 runbook，
- 关键架构权衡与被否决方案。

### 5. 必须进入下一阶段的工作流

1. 公开路线图重写
   - 删除密钥发放细节，
   - 删除 reviewer 全局单活跃会话目标，
   - 加入 owner-aware 授权方向，
   - 明确 admin reviewer key closure 尚未完成。

2. Admin reviewer 密钥管理闭环
   - admin invite 发放/查看/撤销面板，
   - reviewer 设备可视化与重置，
   - reviewer session revoke 接口与 UI，
   - invite/device/session 生命周期审计事件，
   - `/admin -> /reviewer` 联动链路的一致性。

3. Owner-aware 授权实现
   - 用户写操作必须在后端按资源归属强校验，
   - 不能只依赖前端隐藏按钮。

4. Reviewer 证据体验
   - 保留技术证据可见性，
   - 默认先显示风险摘要，再展开底层 payload。

### 6. 验收标准

满足以下条件才算修订完成：
1. `zh/en/ja` 三语公开路线图全部更新。
2. 私有仓新增的内部计划能够通过 private portal 访问。
3. 公开文档不再泄露运维级 auth/runbook 细节。
4. 路线图不再把 `Creator` 当成独立运行时角色。
5. 路线图明确写出：admin reviewer key management 尚未完全落地。  

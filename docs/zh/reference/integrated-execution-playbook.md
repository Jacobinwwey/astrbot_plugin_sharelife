# 集成执行手册（UI 重构 x 存储持久化）

> 日期：`2026-04-04`  
> 受众：maintainer 与 contributor  
> 目标：把用户面板重构与存储冷备落在同一条可执行交付线上

## 1. 当前工程事实

### 1.1 已有优势

1. `member/reviewer/admin` 角色基线已建立，路由权限边界明确。
2. WebUI 已形成模块化（状态、i18n、详情/对比渲染等）。
3. 接口测试与 E2E 已覆盖关键流程和权限边界。
4. 市场页已具备卡片化目录与详情/对比链路。

### 1.2 仍需治理的结构债

1. `app.js` 仍是偏重编排的大文件。
2. 用户核心流程存在但分散在多个混合界面。
3. 安装/上传选项在载荷中部分隐式化，未形成跨页面统一约束。
4. 本地磁盘受限场景下，长期保留与恢复链路仍偏弱。

### 1.3 增量进展（`2026-04-07`）

1. `upload_options.replace_existing` 已具备真实行为：同一用户同一模板的新提交可回收此前仍处于 `pending` 的旧提交。
2. 市场提交通道在 SQLite 下已持久化 `upload_options`，并补齐了旧表缺少 `upload_options_json` 字段时的自动迁移。
3. WebUI 状态词汇已按执行契约补齐并三语化：新增 `queued/running/succeeded/failed/cancelled/stale`，减少 member/reviewer/admin 面板中原始状态值直出。
4. `profile-pack` 提交流程也已支持行为化 `replace_existing`：同一用户同一 pack 的旧 `pending` 提交会被回收为 `replaced`，并返回 `replaced_submission_ids` 与 `replaced_submission_count`，同时写入审计事件。
5. 模板提交流程新增幂等重放能力：支持 `upload_options.idempotency_key`（以及 WebUI 路由层 `Idempotency-Key` header 透传），重试不再重复写入 submission。
6. 同一幂等键跨模板/版本范围复用会触发确定性冲突拒绝（`idempotency_key_conflict`），避免错误重放污染。
7. `profile-pack` 提交也已接入同样的幂等模型（`submit_options.idempotency_key` + header 透传），并补齐重放/冲突审计事件。

### 1.4 增量进展（`2026-04-10`）

1. Member 页已落地硬边界交付：`/member` 优先返回 `member.safe.html`，member 源模板不再携带 admin/reviewer 控件。
2. 运行时仍保留鉴权后的特权 DOM 防御裁剪，形成“模板边界 + 运行时边界”双重保护。
3. WebUI 绑定逻辑进一步拆分到 `app_binding_slices.js` 注册表，`bindButtons()` 收敛为编排壳层。
4. 新增切片表面与路由表面 meta 测试，覆盖脚本装载顺序、member 安全面与边界回归风险。

### 1.5 增量进展（`2026-04-10`，可观测性补强）

1. 公共市场自动发布链路新增确定性流水线追踪元数据：`pipeline_trace_id` 与固定阶段事件 ID（decision/publish/snapshot/backup-handoff）。
2. market entry 载荷与 API 发布返回结果共享同一追踪结构，可用于跨系统链路对齐。
3. 审计链新增 `profile_pack.public_market.snapshot_rebuilt` 与 `profile_pack.public_market.backup_handoff` 事件，便于 operator 追踪全流程状态。
4. 公共市场备份 manifest 新增快照级追踪摘要字段（`pipeline_trace_count`、latest trace 与阶段事件）。

### 1.6 增量进展（`2026-04-10`，可读性守门）

1. 新增 WebUI 关键主题色 token 的对比度守门测试（覆盖 member/market 核心文本与背景配色对）。
2. 关键语义配色的对比度回归现在会直接在 CI 阶段阻断合并。

### 1.7 增量进展（`2026-04-10`，匿名 member 鉴权一致性补强）

1. 匿名 member 的默认 API 白名单已与能力面板对齐，补齐模板包下载与通知读取接口。
2. 接口测试补齐双向约束：默认白名单必须可读；显式覆写白名单时仍会被正确拒绝。

## 2. 两大方案交叉决策

### 2.1 统一状态词汇

安装任务与备份/恢复作业统一状态语义：

`queued | running | succeeded | failed | cancelled | stale`

### 2.2 先契约后实现

避免并行大改引发漂移，执行顺序固定为：

1. 冻结接口与载荷契约  
2. 实现后端兼容层  
3. 绑定前端  
4. 最后替换布局壳

### 2.3 审计不可妥协

所有存储动作和安装选项变更都必须写入审计，包含 request-id 与 actor-role。

## 3. 执行分期

### Phase A - 合约冻结

1. 用户安装接口与选项载荷扩展。  
2. 存储作业与恢复生命周期接口冻结。  
3. 文档先行并增加 meta 测试。  

### Phase B - 后端先行

1. 安装列表与刷新服务。  
2. 选项默认值与严格校验。  
3. 存储策略/作业/恢复状态模型。  
4. 在服务边界后接入 restic+rclone 适配器。  

### Phase C - 前端接入

1. 引入 Stitch 布局，但保持运行时 ID 锚点不变。  
2. 固化顶部主动作：搜索 + 语言 + `导入本机 AstrBot 配置`。  
3. `/member` 与 `/market` 共用上传/安装选项面板行为。  
4. 用新接口回填任务队列与安装态。  

### Phase D - 加固

1. 跑全量 interface/unit/E2E。  
2. 注入失败场景：
   - API `429/403/500`
   - 备份预算命中
   - 恢复 checksum 不一致
3. 校验审计完整性与 i18n 完整性。  

## 4. 权衡结论

1. Vanilla 渐进增强 vs 框架迁移  
   - 结论：先做渐进增强，保住兼容和测试锚点。
2. Google Drive 冷备 vs 对象存储替换  
   - 结论：Drive 仅做冷备，不做热服务。
3. 大一统上线 vs 分层迭代  
   - 结论：分层迭代，降低爆炸半径并简化回滚。

## 5. 必避坑点

1. 用生成片段直接覆盖运行时 ID。  
2. 增加控件却未做 capability 映射。  
3. 直接上传碎片目录到 Drive。  
4. 未做 restore-prepare 就宣布备份成功。  
5. 无磁盘水位保护下并发跑备份作业。  

## 6. 完成门槛

1. 全量测试通过（含 WebUI E2E）。  
2. 受限路由无 RBAC 回归。  
3. `/member` 与 `/market` 选项行为等价。  
4. 备份/恢复链路具备确定状态转移与完整审计记录。  

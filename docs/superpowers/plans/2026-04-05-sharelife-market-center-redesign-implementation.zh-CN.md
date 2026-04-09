# Sharelife 市场中心入口重构实施计划

> **面向代理式执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务顺序实施本计划。步骤继续使用 checkbox（`- [ ]`）语法跟踪。

**当前语言：** 简体中文

**对应文档：** 英文主文件 `docs/superpowers/plans/2026-04-05-sharelife-market-center-redesign-implementation.md`，日文版本 `docs/superpowers/plans/2026-04-05-sharelife-market-center-redesign-implementation.ja-JP.md`

---

## 当前实现状态快照

> 更新日期：`2026-04-07`

当前分支已经完成：

1. `/market` 已按 public-first 基线运行，Spotlight 搜索位于排序行上方。
2. 公开目录刷新按钮已经统一为 `刷新目录` / `Refresh Catalog`。
3. 公开搜索已接入本地化别名，因此 `官方` 这类中文关键词也能命中官方卡片。
4. 公开目录卡片已加入本地点赞控件与点赞数展示。
5. 用户侧本地安装管理已支持刷新、重新安装、卸载。
6. 后端已支持 `member.installations.uninstall`，本地安装可见性按最新 install / uninstall 审计事件决定。

当前验证说明：

1. 源码级测试已通过。
2. 浏览器 E2E 在本环境中仍依赖本机安装 `playwright` Node 模块后才能执行。

---

### 说明

本文件是该 implementation plan 的中文独立版本，用于满足 EN / 中文 / 日本語 分文件维护的 i18n 要求。

为避免执行偏差，命令块、代码块、文件路径和提交命令继续保留英文原文；这里补充完整的中文任务说明、文件职责、步骤意图与验证要求。

### 目标

将 `/market` 重构为公开只读优先的市场入口：

1. 首屏以浏览和搜索为核心
2. 卡片只承载公开信息
3. 成员动作只在点击卡片后的 detail drawer / sheet 中出现
4. 后续 Stitch 生成的 5 个细则层变体，也只挂在 detail layer 上

### 架构摘要

执行原则如下：

1. 保留现有 standalone `/market` 路由
2. 继续使用 vanilla WebUI 结构
3. 不再把更多职责堆到 `market_page.js`
4. 抽出两个小边界：public catalog contract 与 detail-shell contract
5. 尽量保持 runtime ID 稳定
6. 新建 `sharelife/webui/market_detail/`，满足 Stitch 调用前必须存在模块内 `Design.md` 的要求

### 文件结构

#### 新建

- `sharelife/webui/market_catalog_contract.js`
  承载公开卡片 view model、搜索文本和 detail seed payload。
- `sharelife/webui/market_detail/detail_shell.js`
  承载 drawer / sheet 模式、成员动作鉴权边界与默认 detail state。
- `sharelife/webui/market_detail/variant_registry.js`
  承载 variant ID、激活项归一化与 renderer 查找。
- `sharelife/webui/market_detail/Design.md`
  detail layer 的模块内 Stitch source-of-truth。
- `sharelife/webui/market_detail/variants/variant_1.js` 到 `variant_5.js`
  五个细则层变体 renderer。
- `tests/meta/test_market_center_surface.py`
  校验公开优先的市场 HTML 表面。
- `tests/webui/test_market_catalog_contract.js`
  校验 public card / search / detail-seed helper。
- `tests/webui/test_market_detail_shell.js`
  校验 detail shell 与成员动作 gating。
- `tests/webui/test_market_detail_variants.js`
  校验 variant IDs、切换逻辑和 renderer 注册。

#### 修改

- `sharelife/webui/market.html`
  重排为 header -> Spotlight search -> result controls，并补 detail-shell placeholder。
- `sharelife/webui/market_page.js`
  接入新的 public catalog contract，承接 detail shell、成员动作与 variant switching。
- `sharelife/webui/style.css`
  增加 Spotlight 搜索、public-entry 层级与 drawer / sheet 细则层样式。
- `sharelife/webui/webui_i18n.js`
  增加市场入口、detail、variant 的 EN / 中文 / 日本語 文案。
- `docs/superpowers/specs/2026-04-05-market-center-redesign-design.zh-CN.md`
  只有当实现暴露真实 spec 矛盾时才修改。

#### 模块导出规则

本切片新增的任何浏览器 helper 都必须遵守当前 WebUI 已有的双导出模式：

1. `module.exports` 供 `node:test` 使用
2. `globalScope.<Name>` 供浏览器运行时使用

#### 保持不动

- `sharelife/webui/market_cards.js`
  本次不继续扩张，新公开目录逻辑应落到 `market_catalog_contract.js`。

### 任务概览

#### Task 1：锁定公开优先的市场表面

核心目标：

1. 先用 surface test 把公开优先骨架钉住
2. 在 `market.html` 中移除首屏成员操作块
3. 增加 detail shell 容器

关键验证：

1. `marketGlobalSearch` 必须位于 `marketSortBy` 之前
2. 首屏不应再出现 `btnMarketRefreshInstallations`
3. 必须出现 `marketDetailVariantTabs`
4. 必须出现 `marketDetailMemberActions`

#### Task 2：抽出 Public Catalog Contract

核心目标：

1. 把公开卡片 contract 从页面脚本中分离
2. 确保卡片主动作只剩 `open_detail`
3. 让搜索文本和 detail seed 独立可测

关键验证：

1. public card 不显示成员动作
2. 搜索文本覆盖 pack_id、maintainer、review labels、warning flags、summary 等公开元数据
3. detail seed 能稳定回填 pack 上下文

#### Task 3：建立 Detail-Shell 边界与 Stitch Source File

核心目标：

1. 抽出 detail shell 模块边界
2. 先创建模块内 `Design.md`
3. 为后续 Stitch 调用提供 source-of-truth

关键验证：

1. 默认 detail shell 具备 drawer / sheet 模式判断
2. 未触发成员动作前不要求鉴权
3. 变体切换时 pack context 保持稳定

#### Task 4：把成员动作移到 Detail Shell 后面

核心目标：

1. 首屏不再承担 install / upload / trial 动作
2. 只有进入 detail layer 后才显示成员动作
3. 实际执行前继续保留 auth gate

关键验证：

1. 首屏浏览与成员动作边界清晰
2. detail shell 可以承接动作
3. 只有真正执行动作时才要求登录

#### Task 5：落实 Spotlight 层级与三语文案

核心目标：

1. 让 Spotlight 风格搜索框成为首屏最强视觉锚点
2. 调整 result controls 的位置和层级
3. 补齐 EN / 中文 / 日本語 文案

关键验证：

1. 搜索框位于入口头部下方、排序行上方
2. 首屏读起来像公开市场而不是操作台
3. 三语下核心文案都能正确显示

#### Task 6：在 Stitch 输出接入前先完成 Variant Registry

核心目标：

1. 先把 variant registry 做稳定
2. 为 5 个 Stitch 变体准备切换骨架
3. 同一 pack 上下文里支持一键切换

关键验证：

1. `variant_1` 到 `variant_5` 是稳定 ID
2. 非法输入会被归一化
3. renderer 注册机制可扩展

#### Task 7：定稿 `Design.md`、运行 Stitch、接入五个变体

核心目标：

1. 先定稿 detail-layer `Design.md`
2. 再执行 Stitch 调用
3. 至少获取 5 个可比较变体
4. 调用后等待 5 分钟再抓取
5. 将结果接入当前 runtime shell

关键验证：

1. 5 个变体都在同一个 pack 上下文中切换
2. 任一变体都不能破坏 public facts / member actions / auth gate
3. 任一变体都不能漂回旧 market hub 风格

### 最终验证

最终需要执行并通过：

1. 相关 `node --test` WebUI 测试
2. 相关 `pytest` surface 测试
3. 必要时刷新 docs/private 索引
4. 视觉检查，确认 `/market`、detail shell、variant switching、三语文案与 docs portal 都正常

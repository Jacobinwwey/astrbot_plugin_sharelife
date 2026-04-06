# Sharelife GitHub Pages 迁移设计（2026-03-26）

## 1. 背景

`sharelife` 当前文档站基于 VitePress，仓库位于 `Jacobinwwey/astrbot_plugin_sharelife`，并已形成中英日三语导航结构。现有公开发布链路围绕 EdgeOne Pages 构建，但其当前对外访问形态不满足“稳定、可预测、默认固定入口”的要求。

当前确认的迁移动机：

1. 将文档公开入口切换为稳定的 GitHub Pages URL。
2. 继续保持“同仓维护”，不拆分文档仓库。
3. 保留手动回滚能力。
4. 为未来自定义域名迁移预留最小改动路径。

## 2. 目标

本次迁移的目标形态固定为：

1. 公开主站地址：`https://jacobinwwey.github.io/astrbot_plugin_sharelife/`
2. 发布方式：GitHub Actions 自定义工作流
3. 发布源：`main` 分支构建出的 VitePress 静态产物
4. 文档框架：继续使用 `docs/` 下的 VitePress
5. 维护方式：继续同仓维护
6. 回滚方式：通过手动触发 workflow 并指定 `git_ref`

## 3. 非目标

本阶段不包含以下内容：

1. 不接入自定义域名。
2. 不拆分独立文档仓库。
3. 不长期维持 EdgeOne 与 GitHub Pages 双主站。
4. 不引入 PR 预览环境。
5. 不引入 Cloudflare Pages / Vercel 作为主文档发布渠道。

## 4. 已确认决策

1. 第一阶段直接采用 GitHub Pages project site，而不是等待自定义域名。
2. GitHub Pages 作为唯一对外主入口。
3. EdgeOne 从“默认公开渠道”降级为“历史方案 / 手动备用”。
4. `cleanUrls: true` 保持不变。
5. VitePress `base` 需要显式支持 `project site` 子路径。
6. `base` 不写死在未来不可切换的形态里，需为后续自定义域名保留出口。

## 5. 架构方案

### 5.1 站点路径策略

VitePress 配置增加显式 `base`，采用环境变量驱动：

- 默认值：`/astrbot_plugin_sharelife/`
- 构建变量：`DOCS_BASE`

推荐形式：

```ts
const base = process.env.DOCS_BASE || '/astrbot_plugin_sharelife/'
```

这样处理的原因：

1. 当前直接适配 GitHub Pages project site。
2. 未来若切换独立域名，可仅将 `DOCS_BASE=/`，无需再次重构文档目录与导航。
3. 对现有多语言路径 `/zh/`、`/en/`、`/ja/` 的影响最小。

### 5.2 文档路由与多语言

保留当前路由结构：

1. `/zh/`
2. `/en/`
3. `/ja/`

保留当前 VitePress 多语言导航与 sidebar 结构，不重构目录层级。

当前文档中的 Markdown 站内链接主要写成绝对站内路径，如 `/zh/...`、`/en/...`、`/ja/...`。在 VitePress 正确设置 `base` 后，这些链接可以继续工作，无需批量改写为相对路径。

### 5.3 `cleanUrls` 策略

保留 `cleanUrls: true`。

原因：

1. VitePress 官方路由文档说明 GitHub Pages 默认支持无扩展名访问映射到 `.html`。
2. 当前文档产物已经输出为 `*.html`，路由层不需要新增额外 rewrite 配置。
3. 保持无扩展名 URL 有利于文档链接稳定性与可读性。

## 6. 发布工作流设计

### 6.1 采用 GitHub 官方 Pages Actions

新增 GitHub Pages workflow，例如：

- `.github/workflows/deploy-docs-github-pages.yml`

工作流职责：

1. 在 `push` 到 `main` 时自动发布文档。
2. 在 `workflow_dispatch` 时支持手动发布。
3. 支持通过 `git_ref` 指定历史提交、tag 或分支进行回滚重发。
4. 构建完成后上传 Pages artifact 并部署到 `github-pages` environment。

### 6.2 推荐工作流结构

工作流使用 GitHub 官方 Pages actions：

1. `actions/checkout@v6`
2. `actions/setup-node@v6`（Node 24）
3. `actions/configure-pages@v6`
4. `npm ci --prefix docs`
5. `DOCS_BASE=/astrbot_plugin_sharelife/ npm run docs:build --prefix docs`
6. `actions/upload-pages-artifact@v4`
7. `actions/deploy-pages@v5`

必要权限：

1. `contents: read`
2. `pages: write`
3. `id-token: write`

必要参数与运行约束：

1. `fetch-depth: 0`，确保 `lastUpdated: true` 的时间信息准确。
2. 设置 `concurrency`，避免并发部署互相覆盖。
3. 明确使用 `github-pages` environment。
4. `workflow_dispatch` 提供可选 `git_ref` 输入。

## 7. 本地开发与发布职责分离

GitHub Pages 模式下，本地不再承担“正式上线”职责。

职责划分：

1. 本地：构建验证、预览验证。
2. CI：正式上线发布。

建议保留并强化本地命令：

1. `npm run docs:build --prefix docs`
2. `npm run docs:preview --prefix docs`
3. `DOCS_BASE=/astrbot_plugin_sharelife/ npm run docs:build --prefix docs`

不建议引入“本地一键推送 GitHub Pages”的伪直传入口，因为这会重新把上线路径从可审计的 CI 拉回到不可控的本地环境。

## 8. EdgeOne 处理策略

### 8.1 角色调整

EdgeOne 不再作为默认公开主站，仅保留为：

1. 历史发布方案
2. 手动备用通道
3. 紧急情况下的临时兜底

### 8.2 第一阶段处理建议

第一阶段建议：

1. 保留 `scripts/deploy_edgeone_docs.sh`
2. 保留少量 EdgeOne 相关历史测试或文档痕迹，避免一次性大清理带来额外回归风险
3. 从 README 主发布说明和 VitePress 对外导航中移除 EdgeOne 作为默认入口的表述
4. 视实施成本决定是将 `.github/workflows/deploy-docs-edgeone.yml` 降级为手动备用，还是直接移除

推荐优先级：

1. GitHub Pages 成为唯一默认主入口
2. EdgeOne 不再继续暴露为默认公开地址
3. 等 GitHub Pages 稳定后，再决定是否彻底删除 EdgeOne 链路

## 9. 文档信息架构调整

需要调整以下公开文档面：

1. `README.md`
2. `docs/zh/how-to/edgeone-publish.md`
3. `docs/en/how-to/edgeone-publish.md`
4. `docs/ja/how-to/edgeone-publish.md`
5. `docs/.vitepress/config.ts` 中的导航条目文字

调整目标：

1. 将“默认发布入口”统一改为 GitHub Pages。
2. 明确公开主站 URL 为 `https://jacobinwwey.github.io/astrbot_plugin_sharelife/`。
3. 保留一小段“历史说明”，说明 EdgeOne 已不再是默认入口。
4. 回滚文档统一改为 `workflow_dispatch + git_ref` 模型。

## 10. 回滚设计

回滚继续使用 Git 驱动的发布模型：

1. 手动运行 `deploy-docs-github-pages` workflow。
2. 输入 `git_ref`。
3. workflow checkout 对应 ref。
4. 使用同一套 `DOCS_BASE=/astrbot_plugin_sharelife/` 构建参数重新发布。

该方案的优点：

1. 与当前已接受的 EdgeOne rollback 心智模型一致。
2. 每一次回滚都对应明确的 git 历史对象。
3. 不需要额外维护离线包或静态产物仓。

## 11. 测试与验收

### 11.1 需要新增或调整的校验

1. GitHub Pages workflow 存在。
2. workflow 使用 GitHub 官方 Pages actions。
3. workflow 支持 `workflow_dispatch`。
4. workflow 支持 `git_ref`。
5. 构建命令显式注入 `DOCS_BASE=/astrbot_plugin_sharelife/`。
6. VitePress 配置支持可切换 `base`。
7. 构建产物中的静态资源路径与站内路由符合 `project site` 预期。

### 11.2 基线验证命令

1. `pytest -q`
2. `npm run docs:build --prefix docs`

如需增加专项测试，优先新增 repository/meta 层 surface tests，而不是引入重型 E2E 作为首批门槛。

## 12. 迁移顺序

推荐迁移顺序：

1. 修改 VitePress `base` 方案并支持 `DOCS_BASE`。
2. 新增 GitHub Pages workflow。
3. 本地完成一次带 `DOCS_BASE=/astrbot_plugin_sharelife/` 的构建验证。
4. 增加 GitHub Pages surface tests。
5. 替换 README 和多语言 how-to 文档中的默认发布说明。
6. 在 GitHub Actions 中手动触发一次部署验证。
7. 将 GitHub Pages 正式确认为唯一公开主入口。
8. 观察一个短周期后，再决定是否删除 EdgeOne 链路。

## 13. 风险分析

### 13.1 `base` 配置错误

风险：

- 页面可打开，但 CSS / JS / 字体资源路径错误，产生 404。

缓解：

1. 构建时显式传入 `DOCS_BASE`。
2. 在测试中断言构建产物包含正确前缀。
3. 在首次手动发布后检查线上首页与至少一个深层页面。

### 13.2 Pages 仓库设置或权限缺失

风险：

- 工作流存在，但部署卡在 Pages environment 或权限阶段。

缓解：

1. 实施时同步检查仓库 Pages 配置。
2. 使用 GitHub 官方 Pages actions，避免自定义非标准流程。

### 13.3 EdgeOne 历史说明残留

风险：

- 实际主站已切换，但 README、导航、How-to 仍在引导用户使用 EdgeOne。

缓解：

1. 统一替换对外发布说明。
2. 对 EdgeOne 仅保留“历史 / 备用”定位。

### 13.4 仓库改名导致 URL 变化

风险：

- project site URL 与仓库名绑定，未来仓库改名会改变公开文档地址。

缓解：

1. 当前阶段接受该约束。
2. 后续若品牌化需求上升，再接入自定义域名。

### 13.5 双主站带来的索引和入口分裂

风险：

- GitHub Pages 与 EdgeOne 同时作为公开入口，导致外链分裂、文档引用分裂、维护说明冲突。

缓解：

1. GitHub Pages 作为唯一默认公开主入口。
2. EdgeOne 不再长期作为公开主站。

## 14. 未来演进方向

完成本阶段后，未来可按两条路线升级：

1. 品牌化升级：接入自定义域名，将 `DOCS_BASE` 切换为 `/`。
2. 平台能力升级：若将来需要 PR 预览、headers、edge logic 或更强观测，再重新评估 Cloudflare Pages 或 Vercel。

本次迁移的定位不是锁死未来平台，而是在当前项目阶段，以最低复杂度获得稳定文档公开入口。

## 15. 实施冻结结论

当前冻结结论如下：

1. 先上 `https://jacobinwwey.github.io/astrbot_plugin_sharelife/`。
2. GitHub Pages 作为唯一默认主入口。
3. `DOCS_BASE` 可切换，但第一阶段默认值固定为 `/astrbot_plugin_sharelife/`。
4. `cleanUrls: true` 保留。
5. EdgeOne 降级为历史方案 / 手动备用。
6. 回滚通过 `workflow_dispatch + git_ref` 完成。
7. 实施以最小侵入为原则，不做仓库拆分与域名扩展。

---

该文档为当前 GitHub Pages 迁移讨论的冻结设计基线。后续若进入实施，所有实现计划与代码变更均应以本设计为准。

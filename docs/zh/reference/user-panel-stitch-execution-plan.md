# 用户面板与市场页重构执行方案

> 日期：`2026-04-04`  
> 负责人：WebUI Architecture  
> 范围：用户面板与 `/market` 对齐改造

## 0. 当前执行状态

当前代码库已落地：

1. `/member` 已将四个用户工作流前置为一级界面：
   - Spotlight 式商店搜索
   - 已安装管理
   - 支持拖拽的上传中心
   - 任务队列与历史
2. `/market` 已补齐等价的安装/上传控件、本地安装刷新，以及拖拽上传交互。
3. 以下向后兼容 API 扩展已生效：
   - `GET /api/member/installations`
   - `POST /api/member/installations/refresh`
   - `install_options`
   - `upload_options`
   - `submit_options`
4. 验证已覆盖接口测试、WebUI 单测与浏览器 E2E。
5. `/member` 已改为 Spotlight 优先的用户面板：顶部先给语言切换、本地刷新和单一全局搜索入口，成员页结果区不再重复渲染“市场中心”大标题。

当前权衡：

1. `install_options.source_preference=generated` 已真正参与包解析路径选择。
2. 其余选项块当前已完成归一化、持久化与 UI/API 回显，但并非全部都已经深入影响后续治理语义。

## 1. 目标

在不破坏既有契约与权限控制的前提下，将用户侧 WebUI 明确收敛为四个核心流程：

1. 商店搜索  
2. 已安装管理  
3. 上传中心  
4. 下载与任务管理

## 2. 不可破坏的基线

1. 保持现有 Vanilla 模块化运行架构（`app.js`、`market_page.js`、助手模块）。  
2. 保持 `/api/ui/capabilities` 能力门禁机制。  
3. 保持 `webui_i18n.js` 键值体系。  
4. 保持现有 DOM ID 锚点（测试与编排依赖）。

## 3. 信息架构与界面形态

### 3.1 用户面板

1. 顶部控制条：
   - 全局 Spotlight 式搜索
   - 语言切换
   - 始终可见的 `刷新本地已有配置`
2. 主区默认视图：已安装资源列表。
3. 次区能力：
   - 上传拖拽区 + 上传选项
   - 下载/任务队列（进度与历史）
4. 移动端：
   - 侧栏折叠为抽屉
   - 搜索框保留首要位置（单行或堆叠）

### 3.2 市场页对齐

`/market` 必须提供与用户面板一致的上传/安装选项控制，不允许降级为仅展示页。

## 4. API 合约扩展（向后兼容）

### 4.1 用户安装接口

1. `GET /api/member/installations`  
2. `POST /api/member/installations/refresh`

响应 envelope 保持不变：
`{ ok, message, data, error? }`

### 4.2 载荷扩展

1. `POST /api/templates/install`
   - `install_options.preflight: bool`
   - `install_options.force_reinstall: bool`
   - `install_options.source_preference: auto|uploaded_submission|generated`
2. `POST /api/templates/submit`
   - `upload_options.scan_mode: strict|balanced`
   - `upload_options.visibility: community|private`
   - `upload_options.replace_existing: bool`
3. `POST /api/profile-pack/submit`
   - `submit_options.pack_type`
   - `submit_options.selected_sections`
   - `submit_options.redaction_mode`

## 5. Stitch 集成约束

1. 以 `DESIGN.md` 为唯一设计真值。  
2. 用 Stitch 生成用户面板与市场页布局。  
3. 生成代码必须通过适配层落地：
   - 保留运行时 ID
   - 保留 i18n key
   - 保留 capability 绑定
4. 破坏事件绑定或 RBAC 边界的片段直接拒绝合并。

## 6. 验证矩阵

1. 接口测试：
   - 用户安装接口
   - 载荷扩展默认值与校验
2. WebUI 单测：
   - 安装/任务/选项状态映射
   - i18n key 完整性
3. E2E：
   - 卡片点击 -> 详情抽屉
   - 带选项上传
   - 带选项安装
   - 刷新本地配置 -> 安装列表更新
   - `/member` 与 `/market` 行为对齐

## 7. 风险与控制

1. 风险：生成结构破坏既有绑定  
   控制：合并前执行 ID 保留检查。
2. 风险：清爽化 UI 误伤高阶操作  
   控制：高级能力折叠，不删除。
3. 风险：前后端能力映射漂移  
   控制：新增控件必须先纳入 `CONTROL_CAPABILITY_MAP`。

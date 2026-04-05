# 独立 WebUI 使用

## 适用场景

Sharelife WebUI 可以独立运行，不依赖 AstrBot Dashboard 内嵌。  
你可以用它处理试用、审核、apply/rollback、profile-pack 操作和审计查看。
核心面板包括“试用状态（Trial Status）”与“管理员应用流程（Admin Apply Workflow）”。

## 配置

```json
{
  "webui": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 8106,
    "cors": {
      "allow_origins": ""
    },
    "security_headers": {
      "enabled": true,
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "no-referrer",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
      "Content-Security-Policy": "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; form-action 'self'"
    },
    "auth": {
      "member_password": "",
      "token_ttl_seconds": 7200,
      "allow_query_token": false,
      "login_rate_limit_window_seconds": 60,
      "login_rate_limit_max_attempts": 10,
      "api_rate_limit_window_seconds": 60,
      "api_rate_limit_max_requests": 600
    },
    "observability": {
      "metrics_max_paths": 128,
      "metrics_overflow_path_label": "/__other__"
    }
  }
}
```

鉴权规则：

1. 鉴权字段为空时，默认保留公开 / member 导向界面。
2. 任何有效 WebUI 密码都会开启 API 登录门控。
3. 管理接口权限由 token 角色决定，不信任请求体 `role`。
4. 兼容旧配置 `auth.password`，但它只作为 member 兼容字段。
5. 默认关闭 query token，建议 `Authorization: Bearer <token>`。
6. 登录失败受 `login_rate_limit_*` 限流。
7. token 生命周期由 `token_ttl_seconds` 控制。
8. API 请求受 `api_rate_limit_*` 限流（按 `client + role + path` 维度）。
9. 指标 path 基数由 `observability.metrics_max_paths` 控制，超出后折叠到 `metrics_overflow_path_label`。
10. `GET /api/ui/capabilities` 在登录前也可读取，会返回当前有效角色与可执行操作清单，供前端做能力门控。
11. WebUI 默认会附加安全响应头（`X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy`、`Permissions-Policy`、`Content-Security-Policy`），可在 `webui.security_headers` 下调整。
12. Reviewer / Admin 鉴权细节与密钥备份流程不出现在公开文档面。

## 启动与路由

1. 插件初始化时会尝试启动 WebUI。
2. 执行 `/sharelife_webui` 获取 URL。
3. 可访问路由：
   - `/` 完整控制台
   - `/member` 普通用户控制台
   - `/admin` 管理员控制台
   - `/market` 独立市场页

### 容器快速启动

```bash
docker compose up -d --build
```

启动后访问 `http://127.0.0.1:8106`。  
数据目录默认持久化到 `./output/docker-data`。
Compose 默认使用 `state_store.backend=sqlite`，SQLite 文件为 `./output/docker-data/sharelife_state.sqlite3`。

## 主要能力

1. 用户偏好：执行模式切换、任务细节观测开关。
2. 试用状态（Trial Status）面板：明确展示状态、TTL、剩余秒数。
3. 模板市场：列表、投稿、安装、提示词/包生成、下载。
4. 管理员应用流程（Admin Apply Workflow）：dry-run -> apply -> rollback。
5. 风险扫描：`risk_level`、标签、warning flag、注入命中规则。
6. 右上角一键开发者模式：开启后可查看风险定位证据（`file/path/line/column`）。
7. 关闭开发者模式时，风险面板仅保留决策级信息，避免普通用户被低层细节干扰。
8. 审核区：投稿比较、审核备注、队列锁、决策和审计时间线。
9. 通知中心：显示 WebUI 通知事件。
10. 服务端筛选：支持 `template_id`、`category`、`tag`、`source_channel`、`risk_level`、`status`、`review_label`、`warning_flag`。
11. Profile-pack 市场：submission/catalog/compare/featured 全链路，并通过 `/api/profile-pack/catalog/insights` 提供服务端洞察（metrics/featured/trending 数据卡片）。
12. 插件安装门禁：`plan -> confirm -> execute`。
13. 执行证据：失败按 `policy_blocked`、`command_failed`、`timed_out` 分组展示。
14. 语言同步：`en-US` / `zh-CN` / `ja-JP` 在 `/`、`/member`、`/admin`、`/market` 间共享 `sharelife.uiLocale`。
15. 顶部工具条常驻语言快速切换和控制台入口，方便在多语言/多视图间快速跳转。
16. `/member` 与 `/admin` 已切换为独立信息架构模板（用户优先 / 管理优先），不再共用混合导航面板。
17. 角色页登录角色选择已与页面强绑定（`/member` 仅 `member`、`/admin` 仅 `admin`），减少跨角色误操作。
18. 低频操作默认折叠（`工作区路由操作`、`插件安装执行控制`、`风险词汇表`），减少常规使用的认知噪声。
19. API 响应统一包含 `X-Request-ID` 便于追踪，请求指标可通过 `/api/metrics`（Prometheus 文本格式）采集（`sharelife_webui_http_*`、`sharelife_webui_auth_events_total`、`sharelife_webui_rate_limit_total`）。
20. Reviewer / Admin 运维、可观测性值班手册和鉴权密钥备份流程仅保留在私有运维文档中，不出现在公开文档站。
21. 鉴权/限流/内部异常统一返回错误结构：`{"ok": false, "error": {"code": "...", "message": "..."}}`。
22. 按钮级操作会基于后端能力策略（`/api/ui/capabilities`）做显式门控，确保 public/member/admin 视图与 token 角色一致。
23. Profile-pack 面板新增独立“兼容性指引”区（问题列表 + 可点击动作快捷跳转）；已映射的问题/动作可直接跳到目标操作区，且在有提示时会自动回填 `plugin_ids`/推荐 sections，开发者模式专属目标支持“开启后自动续执行”。原始 `compatibility_issues`/`action_codes` 仅在开发者模式展示。
24. `/market` 已切换为左侧 Facet + 顶部搜索排序的信息架构（Hugging Face 风格），并在移动端提供筛选抽屉。
25. 市场页本地视图状态支持 URL 同步（`q`、`sort`、`facet_*`、`pack_id`），筛选结果和选中项可直接分享链接复现。
26. 桌面端 `/market` 中，“详情与对比”固定为右侧独立列；“操作日志”默认折叠，通过 profile-pack 卡片内按钮按需展开。
27. 管理端已新增“存储备份与恢复”面板：支持本地摘要、策略读写、备份任务执行/列表/详情、恢复 prepare/commit/cancel、恢复任务观测全链路。
28. 存储输出默认展示可读摘要；仅在开发者模式下附带原始 JSON 载荷，便于排障且不干扰日常操作。

## 常见问题

1. `permission_denied`：当前 token 非 admin。
2. `review_lock_held`：请求被其他管理员持锁。
3. `401`：已启用鉴权但未登录。
4. `prompt_injection_detected`：命中高风险规则，当前行为是标记和可视化，不自动删除。
5. 手动改浏览器存储后语言异常：删除 `sharelife.uiLocale` 并刷新。
6. 手动改浏览器存储后开发者模式异常：删除 `sharelife.developerMode` 并刷新。

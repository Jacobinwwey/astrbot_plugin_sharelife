# 独立 WebUI 使用

## 适用范围

Sharelife WebUI 可以独立运行，不依赖 AstrBot Dashboard 内嵌。
本页只记录公开 / 用户侧的真实使用链路：

1. Spotlight 风格的市场搜索
2. 本地安装管理
3. 模板上传与 profile-pack 投稿
4. 用户侧任务 / 结果跟踪

特权审核与 operator 流程只保留在私有文档中。

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
      "allow_anonymous_member": false,
      "anonymous_member_user_id": "webui-user",
      "anonymous_member_allowlist": [
        "POST /api/trial",
        "GET /api/trial/status",
        "POST /api/templates/install",
        "GET /api/member/installations",
        "POST /api/member/installations/refresh",
        "GET /api/preferences",
        "POST /api/preferences/mode",
        "POST /api/preferences/observe"
      ],
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

## 鉴权行为

1. 鉴权字段为空时，公开 / 用户侧界面可直接使用。
2. `member_password` 会为受保护的 member 动作开启登录门控。
3. `GET /api/ui/capabilities` 在登录前可读，前端据此做按钮能力控制。
4. 默认关闭 query token，使用 `Authorization: Bearer <token>`。
5. 登录失败受 `login_rate_limit_*` 限流。
6. API 请求受 `api_rate_limit_*` 限流（维度为 `client + role + path`）。
7. 默认响应会带上 `security_headers`，包括 `Content-Security-Policy`。
8. 若设置 `allow_anonymous_member=true`，只有匿名 allowlist 中的接口可以免登录调用，且请求仍固定绑定到 `anonymous_member_user_id`。
9. 特权鉴权、secret 材料与备份恢复手册都保留在私有文档中。
10. standalone 模式下“导入本机 AstrBot 配置”默认关闭（更安全）。如需启用请显式打开：
   - CLI：`python3 scripts/run_sharelife_webui_standalone.py --enable-local-astrbot-import`
   - 环境变量：`SHARELIFE_ENABLE_LOCAL_ASTRBOT_IMPORT=1`
   - 如需允许匿名主体触发本机导入：`--allow-anonymous-local-astrbot-import` / `SHARELIFE_ALLOW_ANONYMOUS_LOCAL_ASTRBOT_IMPORT=1`
11. 本机 AstrBot 自动探测支持可选路径提示：
   - `SHARELIFE_ASTRBOT_CONFIG_PATH=/绝对路径/cmd_config.json`
   - `SHARELIFE_ASTRBOT_CONFIG_PATH=/path/a:/path/b`（Windows 使用 `;`）
   - `SHARELIFE_ASTRBOT_SEARCH_ROOTS=/path/root-a:/path/root-b`（Windows 使用 `;`）
   - `SHARELIFE_ASTRBOT_HOME=/path/to/astrbot`

## 启动与路由

1. 插件启动时会尝试自动拉起 WebUI。
2. 执行 `/sharelife_webui` 获取访问地址。
3. 公开 / 用户侧路由：
   - `/` 统一入口
   - `/member` 用户控制台
   - `/market` 独立市场页
4. 受限 operator 路由仍然存在，但不会在公开文档中描述。

### 容器快速启动

```bash
docker compose up -d --build
```

随后访问 `http://127.0.0.1:8106`。
数据默认持久化到 `./output/docker-data`。
Compose 默认使用 `state_store.backend=sqlite`，文件位于 `./output/docker-data/sharelife_state.sqlite3`。

## 用户工作流

### 1. 市场搜索 + 试用状态

1. `/member` 与 `/market` 都以 Spotlight 风格搜索作为第一入口。
2. 搜索会驱动目录卡片、详情与对比面板。
3. `试用状态（Trial Status）` 会展示 `not_started|active|expired`，以及 `ttl_seconds` 与 `remaining_seconds`。

### 2. 本地安装管理

1. 先加载本地安装列表。
2. 用 `刷新本地已有配置` 同步当前可见状态。
3. 单个安装项支持：
   - `重新安装`
   - `卸载`
4. 安装控件支持：
   - `preflight`
   - `force_reinstall`
   - `source_preference=auto|uploaded_submission|generated`

### 3. 模板上传链路

1. 在 `/member` 打开上传区域。
2. 选择文件，或直接使用生成包输出。
3. 模板包直传上限为 `20 MiB`。
4. 上传选项：
   - `scan_mode=strict|balanced`
   - `visibility=community|private`
   - `replace_existing=true|false`
5. 提交后，在 `我的投稿` 中查看详情，并下载自己的原始投稿包。

### 4. Profile-Pack 投稿链路

1. 先准备 profile-pack 产物，并复制 `artifact_id`。
2. 在 `/member` 的“本地安装管理”中，导入草稿卡片可直接打开“上传细则”进行审阅后投稿。
3. “上传细则”会按草稿记忆审阅状态（`selected unit/node`、section 勾选、`replace_existing`），同一浏览器会话内关闭重开与页面刷新都不会丢失。
4. 从 `/member` 或 `/market` 发起投稿。
3. 提交选项包括：
   - `pack_type`
   - `selected_sections`
   - `redaction_mode`
   - `replace_existing`
5. 提交后，在 `我的 Profile-Pack 投稿` 查看详情并下载自己的导出物。

### 5. 能力门控与错误模型

1. 所有按钮级动作都通过 `/api/ui/capabilities` 做后端能力门控。
2. 鉴权 / 限流 / 内部错误统一返回：
   `{"ok": false, "error": {"code": "...", "message": "..."}}`
3. 属主不匹配会返回 `permission_denied`。
4. 模板上传超限会返回 `package_too_large`。
5. 类似 `prompt_injection_detected` 的风险命中会作为审查信号展示，不会静默删除。

## 公开 / 私有边界

1. 公开文档只覆盖搜索、安装、上传、以及用户自己的投稿管理。
2. 公开文档不暴露审核动作、特权 apply/rollback、secret 处理、备份恢复 SOP。

## 常见问题

1. `401`：已开启鉴权，当前 member 动作需要先登录。
2. `permission_denied`：当前 token 不能访问指定 `user_id` 或目标动作。
3. `package_too_large`：模板上传超过 `20 MiB`。
4. `prompt_injection_detected`：包已被标记并升级审查。
5. 手动修改浏览器存储后语言异常：删除 `sharelife.uiLocale` 后刷新。
6. 手动修改浏览器存储后开发者模式异常：删除 `sharelife.developerMode` 后刷新。

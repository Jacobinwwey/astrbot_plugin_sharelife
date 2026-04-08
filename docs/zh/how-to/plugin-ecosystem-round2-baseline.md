# 插件生态 Round 2 基线方案（v0.3.13）

该基线把 `sharelife` 从“单功能插件”推进为“可治理插件平台”。

## MVP 边界

最小可用平台包含：

1. `plugin.manifest.v2.json` 协议
2. `astr-agent.yaml` 组合协议
3. 能力网关（网络/文件/命令/provider/MCP）
4. `create-astrbot-plugin` 脚手架
5. 热重载开发流程
6. 市场治理闭环（风险标签、兼容性检查、安装确认、审计）

## 实施状态（M1-M5）

1. `M1` 完成：schema + 示例 + CI 校验脚本（`scripts/validate_protocol_examples.py`）
2. `M2` 完成：能力网关（`sharelife/application/services_capability_gateway.py`），未声明高风险能力默认拒绝
3. `M3` 完成：DX 命令（`scripts/create-astrbot-plugin`、`scripts/sharelife-hot-reload`）和 SDK 契约（`sharelife/sdk/contracts.py`）
4. `M4` 完成：流水线编排（`sharelife/application/services_pipeline.py`），支持 A->B 串联和 `retry/skip/abort`
5. `M5` 完成：治理元数据（`capability_summary`、`compatibility_matrix`、`review_evidence`）和私有精选门禁

后续扩展：

1. `M6` 完成：插件安装执行闭环（`plan -> confirm -> execute`）已落地，含默认关闭执行、命令前缀白名单、超时守卫、执行证据持久化、可选 `require_success_before_apply`

## 架构图（文字）

```text
Plugin Lifecycle -> Capability Gateway -> Runtime Adapters
        |                  |                    |
        v                  v                    v
     Event Bus <-> Pipeline Orchestrator <-> Risk/Audit Engine
        |                  |                    |
        +---------- WebUI/CLI + Registry + Package Storage
```

## 核心组件

1. 生命周期管理器
2. 能力网关
3. manifest/schema 校验器
4. 流水线编排器
5. 风险与审计引擎
6. 注册表服务
7. 开发者工具链

## 关键数据流

1. 发布：校验 -> 打包 -> 扫描 -> 标注 -> 入目录
2. 安装：浏览 -> 兼容性检查 -> 权限确认 -> 安装 -> 审计
3. 运行：触发 -> 能力校验 -> 插件调用 -> 审计
4. 配置迁移：导出 -> 导入 -> dry-run -> apply/rollback

## 技术栈

1. Python 3.12 + FastAPI + Pydantic
2. `application/domain/interfaces/infrastructure` 分层
3. WebUI + VitePress + GitHub Actions + GitHub Pages + GitHub Releases

## 搭建顺序

1. 冻结协议 schema
2. 接入能力网关
3. 交付脚手架与热重载
4. 交付可组合流水线
5. 补齐市场治理证据可视化

## 边界情况

1. 缺失权限声明
2. 版本不兼容（`astrbot_version` / `plugin_compat`）
3. 热重载状态污染
4. 流水线中途失败
5. 未确认的高风险插件安装

## 扩展策略

1. 多源 registry 聚合（官方/社区/私有）
2. 从软隔离逐步升级到强隔离
3. 从静态精选升级到信誉系统
4. 预留 SDK v4 兼容位（`sdk_compat`）

## 潜在瓶颈

1. DX 工具不足导致开发者增长慢
2. 权限声明与运行拦截不一致
3. 审核吞吐被人工流程卡住
4. 插件输入输出协议漂移

## v2 优化

1. 分级沙箱
2. 资源预算与限速
3. 场景化推荐
4. 插件级可观测性
5. 统一 Astr UI Kit
6. 网页到本地的深链一键安装

# Sharelife 文档（简体中文）

这是 `sharelife` 中文文档入口。

## 愿景

我们很难定义记忆与怀念，也许它们就是生命的印迹。  
Sharelife 希望陪伴你体验每一段珍贵的生命，消融所有界限的枷锁。（无损接入任意 bot 与设置）

## 快速安装入口

1. 人类：执行 `pip install -r requirements.txt && bash scripts/sharelife-init-wizard --yes --output config.generated.yaml`，再执行 `pytest -q && node --test tests/webui/*.js`。
2. AI：直接复制 [3 分钟快速跑通](/zh/tutorials/3-minute-quickstart) 里的一键安装 Prompt。

## 为什么它适合做“配置复刻”

1. 复刻按 section 采集，配合哈希校验与 dry-run diff，避免“看起来成功、实际跑偏”。
2. 默认不导出明文密钥，支持加密 secrets 的导出与导入闭环。
3. 高风险能力采用声明校验 + 默认拒绝，避免隐式越权。
4. 插件安装执行默认关闭，必须经过特权确认并通过命令前缀白名单。
5. CI 覆盖协议校验、Python/WebUI 测试和文档构建，发布门槛稳定。

## 推荐阅读顺序

1. [3 分钟快速跑通](/zh/tutorials/3-minute-quickstart)
2. [快速开始](/zh/tutorials/get-started)
3. [初始化向导与配置模板](/zh/how-to/init-wizard-and-config-template)
4. [Bot Profile Pack 操作](/zh/how-to/bot-profile-pack)
5. [Bot 配置迁移范围（真值表）](/zh/how-to/profile-pack-migration-scope)
6. [独立 WebUI 使用](/zh/how-to/webui-page)
7. [市场只读公开页](/zh/how-to/market-public-hub)
8. [市场目录原型页](/zh/how-to/market-catalog-prototype)
9. [权限边界与职责解耦路线图](/zh/reference/permission-boundary-roadmap)
10. [开发完成归档（公开）](/zh/reference/development-completed-archive)
11. [开发进行中推进清单](/zh/reference/development-active-workstreams)
12. [用户面板与市场页重构执行方案](/zh/reference/user-panel-stitch-execution-plan)
13. [存储持久化与冷备执行方案](/zh/reference/storage-cold-backup-execution-plan)
14. [集成执行手册（UI x 存储）](/zh/reference/integrated-execution-playbook)
15. [Sharelife v1 冻结方案](/zh/reference/sharelife-v1-freeze)
16. [API v1 参考](/zh/reference/api-v1)
17. [为什么社区优先](/zh/explanation/community-first)

## 私有运维边界

邀请制审核准入、特权运维 Runbook、可观测性值班手册、本地鉴权备份流程不再出现在公开文档站点。
这些内容应仅保存在本地 `docs-private/` 或独立内网仓库中。若你需要邀请制审核权限，请联系 `Jacobinwwey`。

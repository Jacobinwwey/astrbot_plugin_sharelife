# 市场只读公开页

本页明确公开市场与本地高权限操作的边界。

## 目标

1. 对外提供可用的市场目录。
2. 把管理员操作保留在本地。

## 关联页面

[市场目录原型页](/zh/how-to/market-catalog-prototype)

## 发布基线

主路径：

1. 分支：`main`
2. 发布：GitHub Actions -> GitHub Pages
3. 地址：`https://jacobinwwey.github.io/astrbot_plugin_sharelife/`

可选备用：

1. 用归档分支保存历史快照。
2. 归档分支不作为主站来源。

## 公开页面允许内容

1. 模板与 profile-pack 元数据
2. 风险标签和兼容性说明
3. 下载入口与导入指引
4. 多语言文案（`en` / `zh` / `ja`）
5. 仅限脱敏后的官方/社区 profile-pack 产物

## 公开页面禁止内容

1. 审核决策按钮
2. apply/rollback 操作
3. 管理员 token 或鉴权管理入口
4. 硬编码导致的多语言混用

## 语言基线

1. 文档页以路由 locale 作为唯一来源。
2. 不绑定独立 WebUI 的 `sharelife.uiLocale`。
3. 保持 `/en`、`/zh`、`/ja` 语义一致。

## 与本地 WebUI 的衔接

1. 公网页浏览并下载。
2. 本地 WebUI 导入。
3. 本地执行 dry-run 与 selective apply。

## 运行时说明（更新于 2026-04-07）

1. 当 WebUI 关闭鉴权时，`/member` 与 `/market` 的登录面板默认保持隐藏。
2. 用户面板中的本地安装操作按钮保持可点击；是否允许执行由后端鉴权最终判定。
3. 公开页仍保持只读，Reviewer/Admin 的执行链路仍仅在本地开放。

## 已审核社区包发布

1. 公开市场只接收脱敏后的 profile-pack 压缩包。
2. 审核通过后可执行：

```bash
python3 scripts/publish_public_market_pack.py \
  --artifact /abs/path/to/sanitized-pack.zip \
  --pack-id profile/community-example \
  --version 1.0.0 \
  --title "Community Example" \
  --description "Approved community pack" \
  --maintainer community \
  --review-label approved \
  --review-label risk_low
```

3. 脚本会写入 `docs/public/market/entries/*.json`，并自动重建 `catalog.snapshot.json`。

## 可选：审核通过后自动发布

1. 如需在 reviewer/admin 通过审核后自动发布到公开市场，可开启：
   - `sharelife.webui.public_market.auto_publish_profile_pack_approve=true`
   - `sharelife.webui.public_market.root=/abs/path/to/docs/public`（可选覆盖）
   - `sharelife.webui.public_market.rebuild_snapshot_on_publish=true`
2. 自动发布执行时，决策 API 响应会带 `public_market_publish` 字段。
3. 自动发布采用 fail-safe：即便公开发布失败，审核通过结果仍保留。

## 冷备与定时同步

1. 冷备范围仅限 `docs/public/market/`。
2. 本地或运维机可执行：

```bash
python3 scripts/backup_public_market.py \
  --archive-output-dir output/public-market-backups \
  --remote gdrive:/sharelife/public-market
```

3. 若仓库已配置 rclone secrets，GitHub Actions 的 `public-market-backup.yml` 会按计划归档并同步这些脱敏产物。

## Reviewer 权限

1. Reviewer 的执行权限不会在公开页开放。
2. 如果你想成为 reviewer，请先联系 `Jacobinwwey` 获取邀请。

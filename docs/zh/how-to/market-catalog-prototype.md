# 市场目录原型页

本页用于验证市场浏览体验，定位是只读原型。

## 范围

1. 面向公开 profile-pack 的筛选：pack type、risk、featured、review label。
2. 紧凑卡片展示：`source_channel`、`compatibility`、`maintainer`、下载入口等字段。
3. 下载链接只指向脱敏后的公开 profile-pack 产物。
4. 数据源优先读取 `/market/catalog.snapshot.json`，失败时回退内置示例。

## 原型

<MarketCatalogPrototype locale="zh" />

## 说明

1. 当前页面只读，不提供审核、导入、apply 操作。
2. 快照文件路径：`docs/public/market/catalog.snapshot.json`。
3. 本地高权限流程仍在 Sharelife WebUI 执行。
4. 运行时对比卡片在本地 WebUI（`/` 与 `/market`）实现，不在公开原型页。
5. 页面语言由路由 locale 决定，不读取 `sharelife.uiLocale`。
6. 快照由官方示例包与已发布的公开 entry 共同生成，可通过以下命令刷新：

```bash
npm run docs:prepare:market --prefix docs
```

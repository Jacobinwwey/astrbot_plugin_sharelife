# 市场只读公开页

本页定义市场公开面的边界。

## 目标

1. 提供可用的公开目录。
2. 把高权限执行留在本地。
3. 把用户平滑引导到本地 WebUI 完成安装或投稿。

## 相关页面

[市场目录原型页](/zh/how-to/market-catalog-prototype)

## 公开页可以包含什么

1. template/profile-pack 元数据
2. 风险标签与兼容性说明
3. 详情与对比视图
4. 下载 / 导入引导
5. 多语言文案（`zh` / `en` / `ja`）
6. 已脱敏的官方 / 社区产物

## 公开页不能包含什么

1. 审核决策动作
2. 特权 apply/rollback 动作
3. 高权限鉴权或 secret 管理
4. operator 级备份 / 恢复流程
5. 精选运营控件

## 当前公开面

截至 `2026-04-07`，公开市场页应满足：

1. Spotlight 风格搜索是第一入口。
2. 目录卡片保持公开只读。
3. `详情与对比` 可用于选包与 section 级判断。
4. 受保护的 member 动作必须留在本地 `/member` 或 `/market`，不能回流到公开首屏。

## 向本地 WebUI 交接

1. 先在公开页浏览。
2. 再打开本地 Sharelife WebUI。
3. 进入 `/member` 或 `/market` 执行受保护动作。
4. 若开启鉴权，则以 `member` 身份登录。
5. 本地继续以下链路之一：
   - 带 `preflight` / `force_reinstall` / `source_preference` 的安装
   - 带 `scan_mode` / `visibility` / `replace_existing` 的模板上传
   - 基于 `artifact_id` 与 `submit_options` 的 profile-pack 投稿
6. 通过用户自己的投稿列表跟踪结果。

## 上传链路说明

1. 模板包上传上限为 `20 MiB`。
2. 当前主线的 profile-pack 投稿仍是 `artifact_id` 模式。
3. 公开页可以解释交接方式，但不能暴露高权限 operator 动作。

## 语言基线

1. 公开文档以当前路由语言为准。
2. 不把公开页绑定到本地 operator 状态。
3. `/zh`、`/en`、`/ja` 必须保持同一套边界语义。

## 邀请制角色

1. 公开页不暴露审核或运维控制面。
2. 若你需要邀请制的审核权限，请联系 `Jacobinwwey`。

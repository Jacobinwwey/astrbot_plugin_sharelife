# 发布文档到 GitHub Pages

## 公开地址

`https://jacobinwwey.github.io/astrbot_plugin_sharelife/`

## 自动部署

主工作流：

1. 文件：`.github/workflows/deploy-docs-github-pages.yml`
2. 名称：`deploy-docs-github-pages`

默认行为：

1. `main` 上满足条件的 push 会触发构建发布。
2. 路径过滤包含 `docs/**`、`README.md` 和工作流文件。
3. 构建使用 `DOCS_BASE=/astrbot_plugin_sharelife/`。

前置条件：

1. `Settings -> Pages -> Build and deployment -> Source = GitHub Actions`
2. 可选引导 secret：`PAGES_ENABLEMENT_TOKEN`（管理员 PAT）

## 手动发布

1. 打开 `deploy-docs-github-pages`。
2. 运行 `workflow_dispatch`。
3. 可选设置 `git_ref` 指定提交、标签或分支。

如果出现 `Get Pages site failed`，先在仓库设置启用 Pages，再重跑。

## 回滚

1. 手动运行工作流。
2. `git_ref` 指向已知正常版本。
3. 重新发布。

## 本地验证

```bash
make docs-build-github-pages
```

该命令与生产环境使用相同的 `DOCS_BASE`。

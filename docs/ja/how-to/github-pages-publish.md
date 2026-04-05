# GitHub Pages 公開

## 公開 URL

Sharelife ドキュメントの既定公開先は GitHub Pages に移行しました。

- `https://jacobinwwey.github.io/astrbot_plugin_sharelife/`

## 自動デプロイ

主ワークフロー:

1. `.github/workflows/deploy-docs-github-pages.yml`
2. ワークフロー名: `deploy-docs-github-pages`

既定の動作:

1. `main` への対象 push で docs サイトが自動ビルド・自動デプロイされます。
2. 現在の対象は `docs/**`、`README.md`、`.github/workflows/deploy-docs-github-pages.yml` です。
3. ビルドは `DOCS_BASE=/astrbot_plugin_sharelife/` を使い、GitHub Pages のプロジェクト URL に合わせます。

前提条件:

1. リポジトリの `Settings -> Pages -> Build and deployment -> Source` を `GitHub Actions` に設定してください。
2. 任意の初期化シークレット: `PAGES_ENABLEMENT_TOKEN`（リポジトリ管理者 PAT）。設定されている場合、ワークフローは初回の Pages 有効化を自動で試行します。

## 手動公開

再実行や特定 ref の公開が必要な場合:

1. `deploy-docs-github-pages` ワークフローを開きます。
2. `workflow_dispatch` で手動実行します。
3. `git_ref` を空にすると、その実行コンテキストの ref を公開します。

ログに `Get Pages site failed` が出る場合は、先にリポジトリ設定で Pages を有効化してから再実行してください。

## ロールバック

推奨手順:

1. `deploy-docs-github-pages` をもう一度手動実行します。
2. `git_ref` に正常だった commit、tag、または branch を入れます。
3. その ref を checkout して GitHub Pages サイトを再公開します。

## ローカル確認

push 前に同じ条件でビルドを確認できます。

```bash
make docs-build-github-pages
```

このコマンドは GitHub Pages ワークフローと同じ `DOCS_BASE` を使います。

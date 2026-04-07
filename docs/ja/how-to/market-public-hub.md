# 公開マーケット（読み取り専用）

このページでは、Sharelife の公開マーケットを提供しつつ、特権操作をローカルに限定する運用方針を定義します。

## 目的

1. 公開カタログを読み取り専用で提供する。
2. import/review/apply/rollback はローカル Sharelife WebUI のみに限定する。

## 関連ページ

1. インタラクティブな読み取り専用カタログ: [マーケットカタログ試作ページ](/ja/how-to/market-catalog-prototype)

## デプロイ基準

主要経路：

1. ソース: `main`
2. 配信: GitHub Actions + GitHub Pages
3. 公開 URL: `https://jacobinwwey.github.io/astrbot_plugin_sharelife/`

補助経路（任意）：

1. ビルド成果物をアーカイブ用ブランチに保存する。
2. そのブランチは本番配信元にはしない。

## 公開ページの範囲（読み取り専用）

公開してよいもの：

1. テンプレート / bot profile pack のメタデータ
2. リスクラベルと互換性情報
3. ダウンロードリンクと導入ガイド
4. `en` / `zh` / `ja` 辞書に基づく locale 別 UI 文言
5. 秘密情報を除外した公式 / コミュニティ profile-pack 成果物

公開してはいけないもの：

1. 管理者レビュー操作
2. apply/rollback 実行操作
3. トークン管理などの特権 UI
4. ハードコード由来の混在言語 UI 文言

## locale 運用基準

1. 公開ハブはルート/ページ locale を正準値として扱います。
2. 公開ドキュメントをスタンドアロン WebUI の保存キー `sharelife.uiLocale` に結び付けません。
3. `/en`、`/zh`、`/ja` の辞書内容は意味レベルで整合させます。

## ローカル WebUI への導線

推奨フロー：

1. 公開ページでパッケージを選択しダウンロード
2. ローカル Sharelife WebUI でインポート
3. dry-run と選択適用をローカルで実行

## 実行時メモ（2026-04-07 更新）

1. WebUI 認証が無効な場合、`/member` と `/market` のログインパネルはデフォルトで非表示のままです。
2. ユーザーパネルのローカルインストール操作ボタンはクリック可能なままにし、最終的な許可/拒否はサーバー側認証で判定します。
3. 公開ページは引き続き読み取り専用で、Reviewer/Admin の実行フローはローカル限定です。

## 承認済みコミュニティ pack の公開

1. 公開マーケットへ載せられるのは、secret を除外した profile-pack zip のみです。
2. 承認後は次の CLI で公開面へ昇格します。

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

3. このスクリプトは `docs/public/market/entries/*.json` を書き込み、`catalog.snapshot.json` を再生成します。

## 任意: 承認直後の自動公開

1. reviewer/admin の承認後に自動公開する場合は以下を有効化します。
   - `sharelife.webui.public_market.auto_publish_profile_pack_approve=true`
   - `sharelife.webui.public_market.root=/abs/path/to/docs/public`（任意上書き）
   - `sharelife.webui.public_market.rebuild_snapshot_on_publish=true`
2. 自動公開が実行されると、決定 API のレスポンスに `public_market_publish` が含まれます。
3. 自動公開は fail-safe 設計で、公開失敗時も承認結果自体は維持されます。

## コールドバックアップ

1. バックアップ対象は `docs/public/market/` のみです。
2. ローカルまたは運用機で次を実行します。

```bash
python3 scripts/backup_public_market.py \
  --archive-output-dir output/public-market-backups \
  --remote gdrive:/sharelife/public-market
```

3. rclone secrets を GitHub Actions に設定すれば、`public-market-backup.yml` が定期的に脱敏済み成果物をアーカイブ / 同期します。

## Reviewer 権限

1. Reviewer の実行権限は公開ページでは提供しません。
2. Reviewer になりたい場合は、先に `Jacobinwwey` へ連絡して招待を受けてください。

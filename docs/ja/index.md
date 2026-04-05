# Sharelife ドキュメント (Beta)

日本語ドキュメントは段階的に拡充中です。

## ビジョン

記憶や追想を定義するのは難しい。もしかすると、それは生命の軌跡そのものです。  
sharelife は、かけがえのない生の体験に寄り添い、あらゆる境界の制約を解きほぐすことを目指します。任意の bot と設定へ無損失で接続できます。

## クイック導入入口

1. 人間向け: `pip install -r requirements.txt && bash scripts/sharelife-init-wizard --yes --output config.generated.yaml` 実行後、`pytest -q && node --test tests/webui/*.js` を実行。
2. AI 向け: [3分クイックスタート](/ja/tutorials/3-minute-quickstart) のワンコピー Prompt をそのまま利用。

## コア強み（高精度再現 + 安全デリバリー）

1. 高精度再現: section 単位の取得、hash 検証、署名検証、dry-run diff、rollback。
2. 秘密情報保護: 既定で平文 secrets を出力せず、必要時は暗号化 secrets 往復運用。
3. 実行安全: 未宣言の高リスク capability は deny-by-default で監査証跡を保持。
4. インストール安全: プラグイン install 実行は既定で無効。管理者確認、コマンド接頭辞 allowlist、timeout で制御。
5. 配布安全: プロトコル検証、Python/WebUI テスト、docs build 検証を通過してから公開。

1. [3分クイックスタート](/ja/tutorials/3-minute-quickstart)
2. [クイックスタート](/ja/tutorials/get-started)
3. [初期化ウィザードと設定テンプレート](/ja/how-to/init-wizard-and-config-template)
4. [Bot Profile Pack 運用](/ja/how-to/bot-profile-pack)
5. [Bot 設定移行スコープ](/ja/how-to/profile-pack-migration-scope)
6. [スタンドアロン WebUI](/ja/how-to/webui-page)
7. [公開マーケット（読み取り専用）](/ja/how-to/market-public-hub)
8. [マーケットカタログ試作ページ](/ja/how-to/market-catalog-prototype)
9. [権限制御境界ロードマップ](/ja/reference/permission-boundary-roadmap)
10. [ユーザーパネル + マーケット再設計 実行計画](/ja/reference/user-panel-stitch-execution-plan)
11. [ストレージ永続化 + 冷備 実行計画](/ja/reference/storage-cold-backup-execution-plan)
12. [統合実行プレイブック](/ja/reference/integrated-execution-playbook)
13. [API v1 リファレンス](/ja/reference/api-v1)
14. [コミュニティ優先の理由](/ja/explanation/community-first)

## 非公開運用境界

Reviewer 登録手順、Admin 運用 Runbook、可観測性当番手順、ローカル認証バックアップ手順は公開ドキュメントから除外しています。
これらは `docs-private/` または内部リポジトリでのみ管理してください。

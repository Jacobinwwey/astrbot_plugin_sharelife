# Bot Profile Pack 運用ガイド

このページは profile pack の現行運用ループを説明します。
対象は `bot_profile_pack` + `extension_pack` で、Phase 4 の一部強化（署名検証 + 暗号化 secrets の import 復元）を含みます。

「実際にどの設定が移行対象か」を先に確認する場合:
[Bot 設定移行スコープ（グラウンドトゥルース）](/ja/how-to/profile-pack-migration-scope)

## 目的

1. Bot のランタイム設定を移植可能なパックとして保存する。
2. 機密値をデフォルトでマスクする。
3. section 単位の dry-run で差分確認してから apply する。
4. apply 後に rollback できる状態を維持する。
5. `extension_pack` により `skills/personas/mcp_servers/plugins` の能力セットを配布できる。

## 公式リファレンスパック

Sharelife は参照用に 1 つの公開済み starter pack を自動投入します。

1. `pack_id`: `profile/official-starter`
2. `pack_type`: `bot_profile_pack`
3. `version`: `1.0.0`
4. `featured`: `true`

最初の導線として、次をこの pack で確認してください。

1. catalog フィルタ（`pack_id=profile/official-starter`）
2. compare-with-runtime の差分確認
3. import + dry-run + apply の事前リハーサル

リポジトリには参照用サンプル pack（展開形）も同梱しています。

1. `examples/profile-packs/official-starter/manifest.json`
2. `examples/profile-packs/official-starter/sections/*.json`

import 可能な zip をローカル生成する場合:

```bash
cd examples/profile-packs/official-starter
zip -r profile-official-starter-1.0.0.bot-profile-pack.zip manifest.json sections
```

## コマンドフロー（管理者）

```text
/sharelife_profile_export profile/basic 1.0.0 exclude_secrets astrbot_core,providers,plugins providers.openai.base_url sharelife_meta.owner bot_profile_pack
/sharelife_profile_export extension/community-tools 1.0.0 exclude_secrets "" "" "" extension_pack
/sharelife_profile_exports 20
/sharelife_profile_import <artifact_id> --dryrun --plan-id profile-plan-basic --sections plugins,providers
/sharelife_profile_plugins <import_id>
/sharelife_profile_plugins_confirm <import_id> [plugins_csv]
/sharelife_profile_plugins_install <import_id> [plugins_csv] [dry_run]
/sharelife_profile_import_dryrun <artifact_id> profile-plan-basic plugins,providers
/sharelife_profile_import_dryrun_latest profile-plan-basic plugins,providers
/sharelife_profile_imports 20
```

補足:

1. `/sharelife_profile_import` の `source` は export `artifact_id` またはローカル `.zip` を受け付けます。
2. `--dryrun` を付けると import 後に自動 dry-run します。
3. `--plan-id` と `--sections` は任意です。
4. export の位置引数順序: `pack_id version redaction_mode sections_csv mask_paths_csv drop_paths_csv pack_type`。
5. dry-run が `profile_pack_plugin_install_confirm_required` を返す場合は、先に `/sharelife_profile_plugins` と `/sharelife_profile_plugins_confirm` を実行してから再実行してください。
6. `/sharelife_profile_plugins_install` は `profile_pack.plugin_install.enabled=true` のときのみ install 実行可能です。

## WebUI フロー

Sharelife WebUI の **Bot Profile Pack** パネルで以下を実行できます。

1. `Export Profile Pack`
2. `Import Profile Pack`（ファイル）または `Import From Export Artifact`（エクスポート履歴から直接）
3. `Import + Dry-Run` で import と dry-run を 1 回で実行可能
4. または section 選択後に `Dry-Run Selected Sections` を実行
5. plugin section がある場合は `Plugin Install Plan` -> `Confirm Plugin Install` -> `Execute Plugin Install`
6. `Apply Profile Plan` / `Rollback Profile Plan`

### 互換性ガイダンスパネル（WebUI）

import または dry-run 実行後、WebUI に **互換性ガイダンス** ブロックが表示されます。

1. `Compatibility` サマリー（`compatible` / `degraded` / `blocked`）。
2. 人間可読の issue 一覧（署名、暗号化 secrets、runtime 差分）。
3. 実行アクションチェックリスト：
   container 再設定、system dependency 再インストール、plugin binary 再インストール、KB storage 同期。
4. action はクリック可能で、関連操作エリア（plugin install controls / section 選択 / developer payload）へジャンプできます。
5. 対応済み issue 行もクリック可能で、同じ shortcut パイプラインを利用します。
6. shortcut クリック時に可能な範囲で入力を自動補完します。
   plugin 系 action は `missing_plugins` から `plugin_ids` を補完し、KB 同期 action は `knowledge_base` section を自動選択します。
7. Developer Mode 専用ターゲットの場合は有効化を促し、トグル後に action を自動再開します。
8. Developer Mode のみ:
   生の `compatibility_issues` と正規化済み `action_codes`。

このブロックを「import 自体は成功したが、環境再設定がまだ必要」という判断基準にしてください。

## Redaction モード

1. `exclude_secrets`（既定）: provider 構造は保持し、秘密値はマスク
2. `exclude_provider`: provider section を除外
3. `include_provider_no_key`: provider は含めるが key 類を除外
4. `include_encrypted_secrets`: secrets を暗号化して export。`profile_pack.secrets_encryption_key` 設定時に import/dry-run/apply で復元。

フィールド単位の調整:

1. `mask_paths`: 指定パスを強制マスク
2. `drop_paths`: 指定パスを除外

## Pack タイプ

1. `bot_profile_pack`: Bot 全体設定の移行（`astrbot_core/providers/plugins/skills/personas/mcp_servers/sharelife_meta/memory_store/conversation_history/knowledge_base/environment_manifest`）。
2. `extension_pack`: 拡張機能セット（`plugins/skills/personas/mcp_servers`）共有向け。

## セキュリティ設定

1. `profile_pack.signing_key_id`
2. `profile_pack.signing_secret`
3. `profile_pack.trusted_signing_keys`
4. `profile_pack.secrets_encryption_key`
5. `profile_pack.plugin_install.enabled`
6. `profile_pack.plugin_install.command_timeout_seconds`
7. `profile_pack.plugin_install.allowed_command_prefixes`
8. `profile_pack.plugin_install.allow_http_source`
9. `profile_pack.plugin_install.require_success_before_apply`

## ガバナンスメタデータ

公開済み pack は次を提供します。

1. `capability_summary`（宣言能力/推定能力/高リスク能力/未宣言差分）
2. `compatibility_matrix`（manifest 互換宣言 + runtime 判定）
3. `review_evidence`（リスクラベル、警告フラグ、redaction モード、互換性情報）
4. `featured` 状態と管理者ノート

## HTTP API

1. `POST /api/admin/profile-pack/export`
2. `GET /api/admin/profile-pack/export/download`
3. `GET /api/admin/profile-pack/exports`
4. `POST /api/admin/profile-pack/import`
5. `POST /api/admin/profile-pack/import/from-export`
6. `POST /api/admin/profile-pack/import-and-dryrun`
7. `GET /api/admin/profile-pack/imports`
8. `POST /api/admin/profile-pack/dryrun`
9. `GET /api/admin/profile-pack/plugin-install-plan`
10. `POST /api/admin/profile-pack/plugin-install-confirm`
11. `POST /api/admin/profile-pack/plugin-install-execute`
12. `POST /api/admin/profile-pack/apply`
13. `POST /api/admin/profile-pack/rollback`
14. `POST /api/admin/profile-pack/catalog/featured`

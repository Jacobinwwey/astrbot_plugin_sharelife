# Bot 設定移行スコープ（グラウンドトゥルース）

このページは、**Sharelife が現在どの設定を移行できるか**を明示するための仕様書です。

## 基線（現行実装）

1. AstrBot 上流基線: `origin/master@9d4472cb2d0108869d688a4ac731e539d41b919e`（2026-04-02）。
2. ブランチ注記: AstrBot 上流の主開発ブランチは現時点で `main` ではなく `master`。
3. Sharelife 基線: `main@7aebf279d074b80df7566c2d957f58d2c3cd6efd`。
4. 移行モデル: Sharelife runtime state（既定 `runtime_state.json`）に対する**section 単位の snapshot/patch**。AstrBot 設定ファイル全体を直接書き換える方式ではありません。

## 要点

1. `bot_profile_pack` の移行対象:
   `astrbot_core/providers/plugins/skills/personas/mcp_servers/sharelife_meta/memory_store/conversation_history/knowledge_base/environment_manifest`
2. `extension_pack` の移行対象:
   `plugins/skills/personas/mcp_servers`
3. 移行方式は key を維持した再適用で、意味変換ベースのフィールドマッピングは行いません。

## 生の AstrBot 入力との互換境界

1. Sharelife import は、生の AstrBot backup zip、`cmd_config.json`、`abconf_*.json` を受け付けます。
2. ただしそれらを**直接 apply することはありません**。Sharelife がまず **degraded な Sharelife 標準 pack** に投影してから、通常の import/validation/submit フローへ流します。
3. データベース、添付ファイル、knowledge-base の生ファイル、dashboard secrets、`plugin_set=["*"]` のような完全復元できない情報は対象外のままで、`compatibility_issues` として明示されます。

## 現在の移行範囲マトリクス

| Section | 取得元キー（runtime snapshot） | 現在の移行挙動 | 備考 |
|---|---|---|---|
| `astrbot_core` | `snapshot["astrbot_core"]` | export/import/dry-run/apply/rollback 対応 | Bot コア鏡像用。AstrBot 全 root 設定と同義ではない |
| `providers` | `snapshot["providers"]` | 全ワークフロー対応 | `exclude_secrets` / `exclude_provider` / `include_provider_no_key` / `include_encrypted_secrets` 対応 |
| `plugins` | `snapshot["plugins"]` | 全ワークフロー対応 | install メタデータがある場合 `plan -> confirm -> execute` ガードを通る |
| `skills` | `snapshot["skills"]` | 全ワークフロー対応 | 能力バンドル共有向け |
| `personas` | `snapshot["personas"]` | 全ワークフロー対応 | 人格テンプレート共有向け |
| `mcp_servers` | `snapshot["mcp_servers"]` | 全ワークフロー対応 | MCP サーバ宣言を同梱移行可能 |
| `sharelife_meta` | `snapshot["sharelife_meta"]` | 全ワークフロー対応（`bot_profile_pack` のみ） | Sharelife 内部メタ。AstrBot コア設定ではない |
| `memory_store` | `snapshot["memory_store"]` | 全ワークフロー対応（`bot_profile_pack` のみ） | ローカル記憶の任意移行。サイズ/機微情報を事前確認推奨 |
| `conversation_history` | `snapshot["conversation_history"]` | 全ワークフロー対応（`bot_profile_pack` のみ） | 会話履歴の任意移行。機微情報を含む可能性あり |
| `knowledge_base` | `snapshot["knowledge_base"]` | 全ワークフロー対応（`bot_profile_pack` のみ） | KB の設定/索引メタは移行可。外部生ファイルは手動同期が必要 |
| `environment_manifest` | `snapshot["environment_manifest"]` | export 可 + 互換警告に反映（`bot_profile_pack` のみ） | コンテナ/依存/プラグインバイナリ再構成要件を宣言。自動実行はしない |

## 現時点でスコープ外の項目

1. AstrBot `data/cmd_config.json` のうち、上記 section に鏡像されていないキーは自動移行されません。
2. AstrBot config schema に対する完全な意味変換レイヤーは未実装です。現在の raw AstrBot 互換は、Sharelife section への保守的な投影であって、高忠実度 restore ではありません。
3. プラグイン実体、システム依存、コンテナ状態、外部 DB/KB 生ファイルは profile pack には含まれません。`environment_manifest` は「再構成が必要」という宣言情報のみ保持します。
4. プラグイン install 実行は既定で無効。install メタデータがあっても特権確認と実行ゲート設定が必要です。
5. バージョン跨ぎ互換は宣言検証（`astrbot_version` / `plugin_compat`）中心で、自動意味移行は行いません。
6. `environment_manifest` や KB 外部パス情報が含まれる場合、import 後は `compatibility_issues` に再構成通知を出し、明示的な後処理を必須化します（degraded）。

## 精度と安全性の担保（現行）

1. section ごとのハッシュ検証。
2. 任意 HMAC 署名と trusted key 検証。
3. `include_encrypted_secrets` は暗号化 export と import/dry-run/apply での復号閉ループを提供（`profile_pack.secrets_encryption_key` 必須）。
4. apply は snapshot ベースで rollback 可能。
5. リスク/監査証跡は `capability_summary` と `review_evidence` に保持。
6. `environment_manifest` は `environment_*_reconfigure_required` として明示され、システム側が自動移行されたように誤認しないようにします。

## ユーザー向け事前確認手順

1. runtime state に対象 section が存在することを確認。
2. section 指定で export:
   `/sharelife_profile_export <pack_id> <version> exclude_secrets <sections_csv>`
3. import 後に dry-run:
   `/sharelife_profile_import <artifact_id> --dryrun --plan-id <plan_id> --sections <sections_csv>`
4. `selected_sections` / `changed_sections` / `diff` を確認してから apply。
5. `environment_*_reconfigure_required` または `knowledge_base_storage_sync_required` が出た場合は、移行後にその一覧を自動化フローへ渡し、コンテナ/依存/バイナリ再設定を実行してください。

## 開発者向けメンテナンス手順

AstrBot 上流設定が更新されたら、最低限次を実施:

1. 本ページの基線コミット（AstrBot/Sharelife）を更新。
2. 上流設定キー差分を確認。
3. 新規キーの section 帰属を決め、必要なら section adapter を拡張。
4. export/import/dry-run/apply/rollback のテストを追加。
5. README と多言語ドキュメント導線を同期し、実装と文書のズレを防止。

## 参照

1. AstrBot 設定ドキュメント: <https://github.com/AstrBotDevs/AstrBot/blob/master/docs/zh/dev/astrbot-config.md>
2. Sharelife Bot Profile Pack 運用: [/ja/how-to/bot-profile-pack](/ja/how-to/bot-profile-pack)

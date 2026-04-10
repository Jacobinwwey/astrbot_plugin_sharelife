# 統合実行プレイブック（UI 再設計 x ストレージ永続化）

> 日付: `2026-04-04`  
> 対象: maintainers / contributors  
> 目的: ユーザーパネル再設計とストレージ冷備を単一トラックで実装する

## 1. 現在の工学的事実

### 1.1 既に強い点

1. `member/reviewer/admin` の RBAC 基盤とルートガードが存在。
2. WebUI は state/i18n/detail 比較などでモジュール化済み。
3. Interface + E2E が主要ワークフローと権限境界をカバー。
4. マーケットはカード表示と compare/detail 動線を実装済み。

### 1.2 残る負債

1. `app.js` は依然としてオーケストレーション肥大化。
2. ユーザー主要導線が複数画面に分散。
3. install/upload のオプション契約が画面横断で未正規化。
4. 容量制約下での長期保持・復旧戦略が薄い。

### 1.3 増分進捗（`2026-04-07`）

1. `upload_options.replace_existing` は実動作化され、同一 user/template の既存 `pending` submission を新規 submission で退役できるようになりました。
2. SQLite の market submission 永続化で `upload_options` を保持し、`upload_options_json` 列がない旧テーブルは自動マイグレーションされます。
3. 実行契約に合わせて WebUI の状態語彙を三言語で補完し、`queued/running/succeeded/failed/cancelled/stale` を追加しました。member/reviewer/admin 画面での生ステータス表示を減らします。
4. `profile-pack` の submit フローにも `replace_existing` を実動作で追加しました。同一 user + 同一 pack の既存 `pending` submission は `replaced` に退役され、`replaced_submission_ids` / `replaced_submission_count` と監査イベントが出力されます。
5. template submit には `upload_options.idempotency_key`（および WebUI ルートの `Idempotency-Key` ヘッダー透過）による冪等リプレイを追加し、再送で重複 submission を作らないようにしました。
6. 同一 idempotency key を別 template/version スコープで再利用した場合は、`idempotency_key_conflict` で決定論的に拒否します。
7. `profile-pack` submit も同じ冪等モデル（`submit_options.idempotency_key` + ヘッダー透過）へ拡張し、リプレイ/競合の監査イベントを追加しました。

### 1.4 増分進捗（`2026-04-10`）

1. member ページはハード境界配信に移行し、`/member` は `member.safe.html` を優先して返却、member ソーステンプレートから admin/reviewer 制御を除去しました。
2. 認証後の特権 DOM 削除も継続し、テンプレート境界とランタイム境界の二重防御を維持しています。
3. WebUI の bind ロジックは `app_binding_slices.js` レジストリへさらに分割され、`bindButtons()` はオーケストレーション層へ収束しました。
4. script 順序、member 安全面、境界配信を守る meta テストを追加し、回帰防止を強化しました。

### 1.5 増分進捗（`2026-04-10`、可観測性強化）

1. public-market 自動 publish で、決定的なパイプライントレース（`pipeline_trace_id` と decision/publish/snapshot/backup-handoff の固定イベント ID）を出力するようにしました。
2. market entry と API の publish 応答が同一トレース構造を共有し、相関追跡を安定化しました。
3. 監査イベントに `profile_pack.public_market.snapshot_rebuilt` と `profile_pack.public_market.backup_handoff` を追加し、運用側のライフサイクル可視性を強化しました。
4. public-market backup manifest に snapshot 起点のトレース集計（`pipeline_trace_count`、latest trace / events）を追加しました。

### 1.6 増分進捗（`2026-04-10`、可読性ガード）

1. member/market の主要な文字色と背景色トークンに対するコントラスト検証を meta テストとして追加しました。
2. 重要トークンのコントラスト劣化は CI で fail するようになりました。

### 1.7 増分進捗（`2026-04-10`、匿名 member 認可整合パス）

1. 匿名 member の既定 API allowlist を capability 面と整合させ、テンプレート package download と notifications read を追加しました。
2. interface テストで契約の両面を固定しました。既定 allowlist では read が通り、明示 override 時は拒否されます。

### 1.8 増分進捗（`2026-04-10`、owner binding 強化）

1. auth 有効時の member uninstall ルートで owner binding を強制し、cross-owner uninstall 経路を閉じました。
2. interface テストで両分岐を固定しました。cross-owner uninstall は `403`、own uninstall は成功します。

## 2. 交差分析での決定

### 2.1 状態語彙の統一

installation/task と backup/restore job は同一の状態語彙を使う:

`queued | running | succeeded | failed | cancelled | stale`

### 2.2 契約先行シーケンス

並行改修のドリフトを避けるため順序を固定:

1. 契約凍結  
2. backend 互換層実装  
3. UI バインディング  
4. レイアウト殻置換

### 2.3 監査の必須化

ストレージ操作と install option 更新は request-id + actor-role 付き監査記録を必須とする。

## 3. 実装フェーズ

### Phase A - 契約凍結

1. member installation API + option payload。
2. storage job / restore ライフサイクル API。
3. docs-first の仕様更新 + meta tests。

### Phase B - Backend 先行

1. installation list/refresh service。
2. option payload の既定値/検証。
3. storage policy/job/restore 状態モデル。
4. restic+rclone を service 境界の後ろに統合。

### Phase C - Frontend 統合

1. Stitch 出力を適用しつつ runtime ID を保持。
2. 最上位操作を固定（検索 + 言語 + `ローカル AstrBot 設定をインポート`）。
3. `/member` と `/market` の option panel 挙動を統一。
4. 新 API で task/installation 状態を hydration。

### Phase D - ハードニング

1. interface/unit/E2E 全面実行。
2. 故障注入:
   - API `429/403/500`
   - backup budget 到達
   - restore checksum 不一致
3. audit 完全性と i18n 完全性を検証。

## 4. トレードオフ判断

1. Vanilla 漸進強化 vs フルフレームワーク移行  
   - 採用: 漸進強化（互換性とテスト資産を優先）。
2. Google Drive を cold backup 用途に限定 vs object storage 置換  
   - 採用: cold backup のみ（hot serving はしない）。
3. 一括導入 vs 段階導入  
   - 採用: 段階導入（blast radius 最小化 + rollback 容易化）。

## 5. 回避すべき落とし穴

1. 生成 HTML で runtime ID を直接上書き。
2. capability マップなしで操作追加。
3. Drive へ断片ディレクトリを直接同期。
4. restore-prepare 未検証で backup 成功扱い。
5. ディスク水位ガードなしの backup 競合実行。

## 6. 完了ゲート

1. WebUI E2E を含む全テスト green。
2. 制限ルートで RBAC 回帰なし。
3. member と market の option 挙動が等価。
4. backup/restore が決定論的な状態遷移 + 監査記録を残す。

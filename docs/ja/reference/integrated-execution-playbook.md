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
2. 最上位操作を固定（検索 + 言語 + `刷新本地已有配置`）。
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

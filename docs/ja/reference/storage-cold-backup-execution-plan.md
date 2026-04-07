# ストレージ永続化 + コールドバックアップ 実行計画

> 日付: `2026-04-04`  
> 担当: Backend / Platform  
> 対象: ローカル永続化と Google Drive コールドバックアップ

## 1. 問題定義

1. ローカルディスクは長期保持に不向き（容量制約）。
2. 実行時は低遅延のローカル I/O が必要だが、運用上は遠隔復旧も必要。
3. コールドバックアップ先として Google Drive を採用し、制限を明示的に制御する。

## 2. 運用原則

1. Hot storage と cold storage を分離する。
2. Google Drive を実行時ストレージとして mount しない。
3. 小ファイルを直同期せず、必ずパッケージ化してから送る。
4. オフサイト転送前に暗号化する。
5. バックアップ/リストア作業は監査可能かつ状態遷移を決定論的にする。

## 3. 参照アーキテクチャ

1. Hot plane:
   - ローカル SQLite/Postgres
2. Backup plane:
   - snapshot builder（DB dump + 必須設定エクスポート）
   - package（`tar.zst` / `tar.gz`）
   - encryption + dedup（`restic`）
   - remote sync（`rclone crypt` -> Google Drive）
3. Control plane:
   - policy service
   - scheduler + retention manager
   - restore prepare/commit
   - audit/event log

## 4. 管理者 API

1. `GET /api/admin/storage/local-summary`
2. `GET /api/admin/storage/policies`
3. `POST /api/admin/storage/policies`
4. `POST /api/admin/storage/jobs/run`
5. `GET /api/admin/storage/jobs`
6. `GET /api/admin/storage/jobs/{job_id}`
7. `POST /api/admin/storage/restore/prepare`
8. `POST /api/admin/storage/restore/commit`
9. `POST /api/admin/storage/restore/cancel`

すべて admin 権限必須 + audit 記録必須。

## 5. MVP データモデル

1. `storage_policies`
2. `backup_jobs`
3. `backup_artifacts`
4. `restore_jobs`
5. `storage_audit_events`

## 6. 既定ポリシー

1. RPO: `24h`
2. ローカル保持: `2~3` 世代
3. リモート保持: `30` 日ローリング
4. 帯域制限: 既定で有効
5. 日次アップロード予算ガード: 有効
6. 同時バックアップジョブ: 単一ロック

## 6.1 実装進捗（`2026-04-07`）

1. ストレージ冷備サービスで以下のポリシーガードを実装済み:
   - リモート暗号化必須
   - 日次アップロード予算
   - 任意帯域制限
   - 単一アクティブ backup ロック
2. backup/restore ジョブは永続化され、決定論的な状態遷移で管理者 API から参照可能。
3. template/profile-pack の submit 経路には冪等リプレイと競合拒否を導入し、バックアップ対象に入る前の重複ノイズを抑制。

## 7. Drive 制約への対応

1. 日次アップロード上限ガード。
2. rclone のチャンク/再開転送を利用。
3. 平文 DB/PII のアップロード禁止（暗号化必須）。
4. パッケージ化 + dedup で API 負荷を抑制。

## 8. SRE ガードレール

1. Backup success-rate SLI。
2. Restore-prepare validation success-rate SLI。
3. ストレージ圧力ガード:
   - 高水位で全量バックアップを停止
   - 警告発報 + 重要データのみの縮退運転
4. 定期 canary restore 演習。

## 9. リスクと制御

1. リスク: 鍵管理不備で復旧不能  
   制御: 鍵管理 SOP + リストア演習ゲート。
2. リスク: パッケージ時のローカル容量スパイク  
   制御: staging quota 検証 + 可能な箇所はストリーム処理。
3. リスク: バックアップ成功でも復旧不能  
   制御: リリース前に restore-prepare 検証を必須化。

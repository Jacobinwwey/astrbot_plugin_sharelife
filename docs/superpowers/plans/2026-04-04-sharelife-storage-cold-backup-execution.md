# Sharelife Storage Persistence and Cold-Backup Plan

Date: 2026-04-04  
Owner: Backend/Platform  
Status: Ready for implementation

## 1. Problem statement

- Local disk is capacity-constrained and cannot retain long-tail data safely.
- Runtime requires fast local reads/writes, but persistence requires off-site recovery.
- Target cold-backup backend is Google Drive capacity (5TB), with explicit handling for Drive limits.

## 2. Operating principles

1. Hot storage != cold storage.
2. Never mount Google Drive as business runtime storage.
3. Always package before upload (avoid small-file API collapse).
4. Always encrypt before off-site transfer.
5. Keep API and operations auditable with deterministic job states.

## 3. Reference architecture

- Hot plane:
  - local SQLite/Postgres for runtime state
- Backup plane:
  - snapshot builder (db dump + required config export)
  - package (`tar.zst` or `tar.gz`)
  - encryption/dedup (`restic`)
  - remote sync (`rclone crypt` -> Google Drive)
- Control plane:
  - backup policy service
  - job scheduler and retention manager
  - restore prepare/commit service
  - audit/event log

## 4. API/interface design

### 4.1 Admin operations

1. `GET /api/admin/storage/local-summary`
2. `GET /api/admin/storage/policies`
3. `POST /api/admin/storage/policies`
4. `POST /api/admin/storage/jobs/run`
5. `GET /api/admin/storage/jobs`
6. `GET /api/admin/storage/jobs/{job_id}`
7. `POST /api/admin/storage/restore/prepare`
8. `POST /api/admin/storage/restore/commit`
9. `POST /api/admin/storage/restore/cancel`

All routes require admin capability and emit audit events.

### 4.2 Data model additions

- `storage_policies`
- `backup_jobs`
- `backup_artifacts`
- `restore_jobs`
- `storage_audit_events`

## 5. Policy defaults (MVP)

- RPO: 24h
- local retention: keep last 2~3 snapshots
- remote retention: 30 days rolling
- upload bandwidth cap: default enabled
- daily upload budget guard (Drive hard-limit aware)
- single active backup job lock

## 6. Google Drive constraints handled explicitly

1. Daily upload hard limit guard.
2. Chunking and resumable transfers via rclone.
3. No raw PII/plain DB upload; encrypted path mandatory.
4. API call pressure reduced via packaged artifacts and dedup snapshots.

## 7. Verification and SRE guardrails

1. Backup job success rate SLI.
2. Restore-prepare validation success SLI.
3. Storage pressure guard:
   - high watermark blocks new full backups
   - emit warning events and degrade to critical-only snapshots.
4. Scheduled restore drills (canary restore).

## 8. Risks and controls

1. Risk: key mismanagement makes backups non-restorable  
   Control: key custody SOP + restore drill gate before release.

2. Risk: local disk burst during packaging  
   Control: staging quota checks and stream-based pack pipeline where possible.

3. Risk: backup success without recoverability  
   Control: mandatory restore-prepare checks and checksum/manifest validation.

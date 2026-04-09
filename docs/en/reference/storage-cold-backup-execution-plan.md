# Storage Persistence and Cold-Backup Execution Plan

> Date: `2026-04-04`  
> Owner: Backend / Platform  
> Scope: local runtime persistence + Google Drive cold backup

## 1. Problem

1. Local disk is capacity-constrained for long retention.
2. Runtime needs fast local state, while operations need off-site recoverability.
3. Google Drive is selected as cold backup target, with explicit quota and API-limit handling.

## 2. Operating Principles

1. Hot storage and cold storage must stay separate.
2. Do not mount Google Drive as live runtime storage.
3. Package first, then upload (avoid small-file API collapse).
4. Encrypt before off-site transfer.
5. Keep backup/restore jobs auditable with deterministic state transitions.

## 3. Reference Architecture

1. Hot plane:
   - local SQLite/Postgres for runtime data
2. Backup plane:
   - snapshot builder (DB dump + required config export)
   - package (`tar.zst` / `tar.gz`)
   - encryption + dedup (`restic`)
   - remote sync (`rclone crypt` -> Google Drive)
3. Control plane:
   - policy service
   - job scheduler + retention manager
   - restore prepare/commit
   - audit/event logging

## 4. Private Control Surface

1. Local summary read
2. Policy read/write
3. Backup job run/list/detail
4. Restore prepare/commit/cancel

Exact admin route names stay in the private operator docs. The public plan only documents the capability groups and audit requirements.

## 5. Data Model (MVP)

1. `storage_policies`
2. `backup_jobs`
3. `backup_artifacts`
4. `restore_jobs`
5. `storage_audit_events`

## 6. Default Policy

1. RPO: `24h`
2. Local retention: keep last `2~3` snapshots
3. Remote retention: rolling `30` days
4. Upload bandwidth cap: enabled by default
5. Daily upload budget guard: enabled
6. One active backup job lock: enabled

## 6.1 Current implementation progress (`2026-04-07`)

1. Storage backup service already enforces policy normalization and guards for:
   - remote encryption requirement
   - daily upload budget
   - optional bandwidth cap
   - single active backup lock
2. Backup and restore jobs are persisted with deterministic state transitions, and are available via admin APIs.
3. Upload surfaces (template/profile-pack submit) now include idempotency replay + conflict handling to reduce duplicate submissions before they enter backup scope.

## 7. Drive Constraints (Handled Explicitly)

1. Daily upload hard-limit guard.
2. Chunked + resumable transfer through rclone.
3. Plain DB/PII upload is forbidden; encrypted path required.
4. API pressure reduced by packaged artifacts + dedup snapshots.

## 8. Reliability Guardrails

1. Backup job success-rate SLI.
2. Restore-prepare validation success-rate SLI.
3. Storage pressure controls:
   - high watermark blocks new full backups
   - warning events and critical-only fallback snapshots
4. Scheduled canary restore drills.

## 9. Main Risks and Controls

1. Risk: key custody failure causes unrecoverable backups  
   Control: key SOP + restore drill gate.
2. Risk: packaging bursts local disk usage  
   Control: staging quota checks + stream packaging where possible.
3. Risk: backup marked successful but not restorable  
   Control: restore-prepare validation before release gate.

# Bot Profile Pack Operations

This public guide is for browsing, comparing, and submitting profile packs from the member side.
Privileged moderation, featured curation, secret export rules, and operator recovery steps are intentionally excluded from this page.

Need the exact migration boundary first? Start here:
[Bot Profile Migration Scope (Ground Truth)](/en/how-to/profile-pack-migration-scope)

## What users can do now

1. Browse published profile packs in `/market`.
2. Open `Detail & Compare` and run section-scoped compare against local runtime.
3. Submit a profile-pack artifact to the community queue from the member surface.
4. View only your own profile-pack submissions.
5. Download only your own submission export.

## Official reference pack

Sharelife seeds one published starter pack automatically:

1. `pack_id`: `profile/official-starter`
2. `pack_type`: `bot_profile_pack`
3. `version`: `1.0.0`
4. `featured`: `true`

Use it for:

1. catalog filtering (`pack_id=profile/official-starter`)
2. compare-with-runtime rehearsal
3. validating section selection before you submit your own pack

## Current member submission chain

1. Prepare or select a local profile-pack artifact and copy its `artifact_id`.
2. Open `/member` or `/market` in the local WebUI.
3. In the profile-pack area, paste `artifact_id` into `Submit To Community`.
4. Optional submit controls:
   - `pack_type`
   - `selected_sections`
   - `redaction_mode`
   - `replace_existing`
5. Submit the pack.
6. Open `My Profile-Pack Submissions` to inspect status, detail, and your own export download.

## Submit options

1. `pack_type`
   - `bot_profile_pack`
   - `extension_pack`
2. `selected_sections`
   - section subset for the published artifact payload
3. `redaction_mode`
   - `exclude_secrets`
   - `exclude_provider`
   - `include_provider_no_key`
   - `include_encrypted_secrets`
4. `replace_existing`
   - retires earlier pending submissions for the same member + pack and keeps the latest pending row as the active review candidate

## Compare and local apply handoff

1. Public/member docs cover compare and submission.
2. Privileged apply/rollback is not part of the public contract.
3. The supported handoff is:
   - browse published pack
   - compare selected sections
   - decide whether to install/import locally
   - submit your own artifact for review if you want it published

## Current limitations

1. Community submission on this branch is `artifact_id`-based; direct public ZIP upload is not the contract here.
2. `replace_existing` only normalizes pending rows. It does not overwrite already approved or rejected history.
3. “Perfect restore” is not implied by compare/submission output; compare is advisory, not a full environment snapshot restore.
4. Secret-bearing operator exports are not public artifacts and are not downloadable from member docs surfaces.

## User-visible statuses

1. `pending`
2. `approved`
3. `rejected`
4. `replaced`

## Security boundary

1. Profile-pack catalog routes are public read-only.
2. Submission and “my submissions” routes are member-only and owner-scoped.
3. Privileged moderation, device/session governance, and privileged storage workflows live in private docs only.

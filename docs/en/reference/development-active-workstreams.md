# Development Active Workstreams (Public)

> Last updated: `2026-04-11`  
> Scope: in-progress public-facing engineering tracks

## Stream A: Member upload flow completion

Status: `in progress`

1. Finalize guided upload detail modal parity with market detail UX.
2. Complete deep section introspection for imported AstrBot configuration slices.
3. Ensure rescan refresh behavior is idempotent (no duplicate imported cards).

Public acceptance criteria:

1. Member can import, review, submit, and revoke own submissions with stable UI feedback.
2. Upload detail supports granular section selection and visible effect preview.

## Stream B: AstrBot interoperability hardening

Status: `in progress`

1. Improve compatibility mapping for raw AstrBot exports and profile-pack normalized model.
2. Expand import diagnostics for unsupported or downgraded fields.

Public acceptance criteria:

1. Import results expose deterministic `compatibility_issues`.
2. No silent data loss in declared supported sections.

## Stream C: Docs and visibility governance

Status: `in progress`

1. Keep public docs as interface contract; keep operator procedures private.
2. Maintain trilingual parity for new public docs pages and navigation entries.

Public acceptance criteria:

1. Public docs pass i18n structure and build checks.
2. Promotion gate stays PASS for public-only commits.

## Stream D: CI and e2e stability

Status: `in progress`

1. Continue triage/refactor of flaky webui e2e slices.
2. Preserve deterministic test fixtures across environments.

Public acceptance criteria:

1. `ci` pipeline green on main for repeated pushes.
2. E2E failures are tracked with root-cause labels and mitigation status.


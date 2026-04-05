# Sharelife docs (English)

Use this as the main entry for `sharelife` docs.

## Vision

Memory and longing are hard to define. They may just be traces of life.
Sharelife is built to stay with those moments and make bot setup transfer practical, repeatable, and safe.

## Quick Install Entry

1. Human: run `pip install -r requirements.txt && bash scripts/sharelife-init-wizard --yes --output config.generated.yaml` then `pytest -q && node --test tests/webui/*.js`.
2. AI: copy the one-shot setup prompt in [3-Minute QuickStart](/en/tutorials/3-minute-quickstart).

## Why This Plugin Is Different

1. Replication is section-based, hash-checked, and rollback-safe.
2. Secrets are not exported in plaintext by default.
3. High-risk capabilities are deny-by-default when declarations are missing.
4. Plugin install execution is off by default and requires explicit admin confirmation.
5. CI gates push/deploy with protocol checks, Python/WebUI tests, and docs build verification.

## Suggested Reading Order

1. [3-Minute QuickStart](/en/tutorials/3-minute-quickstart)
2. [Get Started](/en/tutorials/get-started)
3. [Init Wizard + Config Template](/en/how-to/init-wizard-and-config-template)
4. [Bot Profile Pack Operations](/en/how-to/bot-profile-pack)
5. [Bot Profile Migration Scope](/en/how-to/profile-pack-migration-scope)
6. [Standalone WebUI](/en/how-to/webui-page)
7. [Public Market Read-Only Hub](/en/how-to/market-public-hub)
8. [Market Catalog Prototype](/en/how-to/market-catalog-prototype)
9. [Permission Boundary Roadmap](/en/reference/permission-boundary-roadmap)
10. [User Panel + Market Refactor Plan](/en/reference/user-panel-stitch-execution-plan)
11. [Storage Cold Backup Plan](/en/reference/storage-cold-backup-execution-plan)
12. [Integrated Execution Playbook](/en/reference/integrated-execution-playbook)
13. [Sharelife v1 Frozen Plan](/en/reference/sharelife-v1-freeze)
14. [API v1 Reference](/en/reference/api-v1)
15. [Why Community-First](/en/explanation/community-first)

## Private Ops Boundary

Reviewer onboarding, admin runbooks, observability operations, and local auth backup procedures are intentionally excluded from the public docs site and public repo docs surface.
Maintain those materials locally under `docs-private/` or an internal repository.

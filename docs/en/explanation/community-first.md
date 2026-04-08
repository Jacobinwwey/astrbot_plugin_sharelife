# Why community first

`sharelife` v1 is built for personal operators and small communities first. Enterprise staffing, multi-step approval chains, and on-call orchestration are intentionally deferred.

## Practical trade-offs

1. Prioritize trial safety, risk scanning, and the guarded promotion path.
2. Keep enterprise governance hooks available, but not enabled as default workflow.
3. Keep service boundaries clean now so SDK v4 migration is cheaper later.

## What users get today

1. Members can trial templates without mutating global runtime state.
2. Risky changes stay behind guarded, privileged controls.
3. Community packs can be adopted with strict mode and audit evidence.

## Why this scales later

1. Current adapters and governance services are reusable for enterprise mode.
2. zh/en/ja i18n is already part of the baseline, not an afterthought.

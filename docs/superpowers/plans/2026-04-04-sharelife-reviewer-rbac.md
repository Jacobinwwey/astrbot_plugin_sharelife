# Sharelife Reviewer RBAC & Structural Reconfiguration Plan

> **Date:** 2026-04-04
> **Goal:** Establish clear role-based access control (RBAC) separating Users, Reviewers, and Administrators across documentation, API boundaries, and frontend entry points.

## 1. Documentation Persona Architecture
Refactor the VitePress documentation from a flat structure (Tutorial, How-to, Reference) into a persona-driven structure for each supported locale (zh, en, ja).
- **User Guide:** Search, deploy, trial, packaging, and progress tracking.
- **Reviewer SOP:** Moderation operations, queue management, risk marking, and device key handling.
- **Administration:** System deployment, observability, curation, and core configurations.
- **Developer & Architecture:** API specifications, CLI plugins, round-by-round ecosystems.

## 2. Reviewer Device Key Management
A strict limit of 3 devices per Reviewer ensures accountability. Reviewers cannot arbitrarily spawn new sessions if they exceed this limit.
- **Backend Setup:** `_conf_schema.json` dictates `webui.auth.reviewer_password` and `webui.device_keys.max_reviewer_devices` (default 3).
- **State Store:** Introduce a generic `reviewer_device_keys` record linking `{user_id: [key1, key2]}` in `json_state_store.py` and `sqlite_state_store.py`.
- **API Endpoints:**
  - `POST /api/reviewer/devices/register`
  - `GET /api/reviewer/devices`
  - `DELETE /api/reviewer/devices/{device_id}`

## 3. Physical UI Isolation
Deprecate the client-side `data-console-scope` visibility toggles which were inherently insecure.
- **`index.html` (Users):** Cleaned up to solely focus on community browsing and submission interactions.
- **`reviewer.html` (Reviewers):** Explicit standalone entry point for reviewing templates and tracking device bounds.
- **`admin.html` (Administrators):** Restricted control center loaded behind a secure backend file server scope. 

## 4. Middleware & HTTP API Enforcement
Enhance `interfaces/webui_server.py`.
- Define explicit scopes: `_PUBLIC_UI_OPERATIONS`, `_MEMBER_UI_OPERATIONS`, `_REVIEWER_UI_OPERATIONS`, and `_ADMIN_UI_OPERATIONS`.
- Middleware strict HTTP 403 blocks for paths starting with `/api/admin` when the logged-in token is `member` or `reviewer`.
- Test coverages updated in `tests/interfaces/test_webui_server.py`.

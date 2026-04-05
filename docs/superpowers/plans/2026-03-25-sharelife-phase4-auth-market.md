# Sharelife Phase 4 Auth And Market Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add role-separated WebUI authentication, HTTP integration coverage for the standalone server, and the first Phase 4 community package upload/download plus review-label visibility flow.

**Architecture:** Keep the current modular boundary: HTTP session/auth concerns stay in `interfaces/webui_server.py`, HTTP result shaping stays in `interfaces/web_api_v1.py`, business data and moderation metadata live in `application/services_market.py`, and package artifact handling stays in `application/services_package.py`. Phase 4 upload/download is metadata-first and file-system backed, without introducing external storage or enterprise workflow complexity.

**Tech Stack:** Python 3, FastAPI/TestClient, pytest, existing Sharelife application services, VitePress docs, standalone WebUI static assets.

---

### Task 1: Role-Separated WebUI Auth

**Files:**
- Modify: `sharelife/interfaces/webui_server.py`
- Modify: `_conf_schema.json`
- Test: `tests/interfaces/test_webui_server.py`

- [ ] **Step 1: Write the failing auth-tier tests**

```python
def test_webui_login_returns_member_and_admin_tokens():
    ...


def test_member_token_cannot_access_admin_http_routes():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q tests/interfaces/test_webui_server.py -k "login or admin"`
Expected: FAIL because WebUI only supports one password/token and does not bind role to token.

- [ ] **Step 3: Write minimal implementation**

```python
auth = cfg.get("auth", {})
member_password = str(auth.get("member_password", "") or "").strip()
admin_password = str(auth.get("admin_password", "") or "").strip()
```

Add per-role token registry, role-aware request context, and server-side admin-route enforcement that no longer trusts request payload `role`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q tests/interfaces/test_webui_server.py -k "login or admin"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add _conf_schema.json sharelife/interfaces/webui_server.py tests/interfaces/test_webui_server.py
git commit -m "feat: add role-scoped webui auth"
```

### Task 2: WebUI HTTP Integration Coverage

**Files:**
- Create: `tests/interfaces/test_webui_server.py`
- Modify: `sharelife/interfaces/webui_server.py`
- Test: `tests/interfaces/test_webui_server.py`

- [ ] **Step 1: Write failing integration tests for key HTTP flows**

```python
def test_no_auth_mode_supports_health_and_preference_flow():
    ...


def test_admin_flow_can_submit_review_and_package_template():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q tests/interfaces/test_webui_server.py`
Expected: FAIL because endpoints are not fully covered and current auth routing does not preserve actor role safely.

- [ ] **Step 3: Write minimal implementation**

Keep route handlers thin. Add helper(s) that derive `user_id`, `session_id`, `admin_id`, and `role` from the authenticated request context and merge only non-sensitive payload overrides.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q tests/interfaces/test_webui_server.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/interfaces/test_webui_server.py sharelife/interfaces/webui_server.py
git commit -m "test: cover standalone webui http flows"
```

### Task 3: Phase 4 Submission Package Upload And Download

**Files:**
- Modify: `sharelife/application/services_market.py`
- Modify: `sharelife/application/services_package.py`
- Modify: `sharelife/interfaces/api_v1.py`
- Modify: `sharelife/interfaces/web_api_v1.py`
- Modify: `sharelife/interfaces/webui_server.py`
- Test: `tests/application/test_market_service.py`
- Test: `tests/application/test_package_service.py`
- Test: `tests/interfaces/test_api_v1.py`
- Test: `tests/interfaces/test_web_api_v1.py`
- Test: `tests/interfaces/test_webui_server.py`

- [ ] **Step 1: Write failing tests for package upload/download flow**

```python
def test_submit_template_stores_uploaded_package_and_scan_summary(tmp_path):
    ...


def test_download_submission_package_returns_uploaded_artifact(tmp_path):
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q tests/application/test_market_service.py tests/application/test_package_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py tests/interfaces/test_webui_server.py`
Expected: FAIL because submission records do not track uploaded artifacts or download metadata yet.

- [ ] **Step 3: Write minimal implementation**

Introduce submission artifact metadata and file-backed upload ingestion in `PackageService`, then expose the flow through `SharelifeApiV1` and HTTP routes.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q tests/application/test_market_service.py tests/application/test_package_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py tests/interfaces/test_webui_server.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/application/services_market.py sharelife/application/services_package.py sharelife/interfaces/api_v1.py sharelife/interfaces/web_api_v1.py sharelife/interfaces/webui_server.py tests/application/test_market_service.py tests/application/test_package_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py tests/interfaces/test_webui_server.py
git commit -m "feat: add submission package upload and download flow"
```

### Task 4: Review Labels And Injection Scan Visibility

**Files:**
- Modify: `sharelife/application/services_market.py`
- Modify: `sharelife/application/services_scan.py`
- Modify: `sharelife/interfaces/api_v1.py`
- Modify: `sharelife/interfaces/web_api_v1.py`
- Modify: `sharelife/interfaces/webui_server.py`
- Modify: `sharelife/webui/index.html`
- Modify: `sharelife/webui/app.js`
- Modify: `README.md`
- Modify: `docs/zh/how-to/webui-page.md`
- Modify: `docs/en/how-to/webui-page.md`
- Modify: `docs/ja/how-to/webui-page.md`
- Test: `tests/application/test_market_service.py`
- Test: `tests/interfaces/test_api_v1.py`
- Test: `tests/interfaces/test_web_api_v1.py`
- Test: `tests/interfaces/test_webui_server.py`

- [ ] **Step 1: Write failing tests for review labels and scan visibility**

```python
def test_approved_submission_exposes_review_labels_and_scan_findings():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest -q tests/application/test_market_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py tests/interfaces/test_webui_server.py`
Expected: FAIL because submissions and published templates do not expose moderation labels or prompt-injection visualization metadata.

- [ ] **Step 3: Write minimal implementation**

Add:
- label buckets: `risk_level`, `review_labels`, `warning_flags`
- prompt-injection analysis summary with matched rules and severity
- WebUI rendering for upload status, labels, and scan findings

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest -q tests/application/test_market_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py tests/interfaces/test_webui_server.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/application/services_market.py sharelife/application/services_scan.py sharelife/interfaces/api_v1.py sharelife/interfaces/web_api_v1.py sharelife/interfaces/webui_server.py sharelife/webui/index.html sharelife/webui/app.js README.md docs/zh/how-to/webui-page.md docs/en/how-to/webui-page.md docs/ja/how-to/webui-page.md tests/application/test_market_service.py tests/interfaces/test_api_v1.py tests/interfaces/test_web_api_v1.py tests/interfaces/test_webui_server.py
git commit -m "feat: expose phase4 review labels and scan insights"
```

### Task 5: Full Verification

**Files:**
- Verify only

- [ ] **Step 1: Run backend test suite**

Run: `pytest -q`
Expected: PASS with zero failures.

- [ ] **Step 2: Run docs build**

Run: `npm run docs:build --prefix docs`
Expected: PASS

- [ ] **Step 3: Review git diff**

Run: `git status --short && git diff --stat`
Expected: Only intended files changed.

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: advance sharelife phase4 market moderation flow"
```

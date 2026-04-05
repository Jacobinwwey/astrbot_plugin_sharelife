# Sharelife Community-First v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a community-first Sharelife plugin that supports official template distribution, strict-mode session trials, user-switchable execution modes, user-controllable task-detail observability, admin-governed promotion/apply/rollback, and bilingual docs while deferring enterprise scheduling mechanics.

**Architecture:** The plugin uses a modular boundary-first design: `interfaces -> application -> domain`, with `infrastructure` implementing ports only. v1 ships command-first capability and data contracts needed for future WebUI embedding. Enterprise-grade on-call routing/takeover remains behind feature flags as v2-ready code paths, not v1 critical path.

**Tech Stack:** Python 3.12, AstrBot Plugin API (`Star`, `filter.command`), `pytest`, `pydantic`, `PyYAML`, GitHub Actions CI, VitePress docs.

---

## Scope Decomposition

This spec includes multiple concerns, but v1 implementation is intentionally narrowed to one shippable slice:

1. Community-first core workflow (must ship in v1): registry -> scan -> compat -> trial -> retry request -> admin decision -> apply/rollback.
2. User preference controls (must ship in v1): execution mode switch + task-detail observability toggle.
3. Docs and i18n baseline (must ship in v1).
4. Enterprise controls (on-call rotation, takeover lock orchestration) are marked as v2-ready optional paths and not required for v1 release.

## File Structure Plan

### Core Plugin Files

- Create: `metadata.yaml`
- Create: `main.py`
- Create: `_conf_schema.json`
- Create: `requirements.txt`
- Create: `sharelife/__init__.py`

### Domain Layer

- Create: `sharelife/domain/models.py`
- Create: `sharelife/domain/policies.py`
- Create: `sharelife/domain/errors.py`

### Application Layer

- Create: `sharelife/application/ports.py`
- Create: `sharelife/application/services_registry.py`
- Create: `sharelife/application/services_scan.py`
- Create: `sharelife/application/services_trial.py`
- Create: `sharelife/application/services_queue.py`
- Create: `sharelife/application/services_apply.py`
- Create: `sharelife/application/services_preferences.py`

### Infrastructure Layer

- Create: `sharelife/infrastructure/official_registry_source.py`
- Create: `sharelife/infrastructure/local_store.py`
- Create: `sharelife/infrastructure/runtime_bridge.py`
- Create: `sharelife/infrastructure/notifier.py`
- Create: `sharelife/infrastructure/system_clock.py`

### Interface Layer

- Create: `sharelife/interfaces/dto.py`
- Create: `sharelife/interfaces/commands_user.py`
- Create: `sharelife/interfaces/commands_admin.py`

### i18n

- Create: `sharelife/i18n/zh-CN/messages.yaml`
- Create: `sharelife/i18n/en-US/messages.yaml`
- Create: `sharelife/i18n/ja-JP/messages.yaml`

### Tests

- Create: `tests/domain/test_manifest_models.py`
- Create: `tests/domain/test_policies.py`
- Create: `tests/application/test_registry_service.py`
- Create: `tests/application/test_scan_and_compat.py`
- Create: `tests/application/test_trial_service.py`
- Create: `tests/application/test_retry_queue_service.py`
- Create: `tests/application/test_apply_service.py`
- Create: `tests/application/test_preferences_service.py`
- Create: `tests/interfaces/test_command_handlers.py`
- Create: `tests/interfaces/test_preference_commands.py`
- Create: `tests/i18n/test_locale_keys.py`

### Docs and CI

- Modify: `docs/specs/2026-03-24-sharelife-v1-freeze.zh-CN.md`
- Modify: `docs/specs/2026-03-24-sharelife-v1-freeze.en-US.md`
- Create: `docs/zh/how-to/community-first-workflow.md`
- Create: `docs/en/how-to/community-first-workflow.md`
- Create: `.github/workflows/ci.yml`

---

### Task 1: Bootstrap Plugin Skeleton and Test Harness

**Files:**
- Create: `metadata.yaml`, `main.py`, `_conf_schema.json`, `requirements.txt`, `sharelife/__init__.py`
- Test: `tests/domain/test_manifest_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/domain/test_manifest_models.py
from sharelife.domain.models import TemplateManifest


def test_manifest_minimal_fields():
    data = {
        "template_id": "community/basic",
        "version": "1.0.0",
        "title_i18n": {"zh-CN": "示例", "en-US": "Example"},
    }
    manifest = TemplateManifest.model_validate(data)
    assert manifest.template_id == "community/basic"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/domain/test_manifest_models.py::test_manifest_minimal_fields -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sharelife'`

- [ ] **Step 3: Write minimal implementation**

```python
# sharelife/domain/models.py
from pydantic import BaseModel


class TemplateManifest(BaseModel):
    template_id: str
    version: str
    title_i18n: dict[str, str]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/domain/test_manifest_models.py::test_manifest_minimal_fields -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add metadata.yaml main.py _conf_schema.json requirements.txt sharelife tests/domain/test_manifest_models.py
git commit -m "feat: scaffold sharelife plugin and baseline domain model"
```

### Task 2: Implement Manifest Schema and Validation Rules

**Files:**
- Modify: `sharelife/domain/models.py`
- Modify: `sharelife/domain/errors.py`
- Test: `tests/domain/test_manifest_models.py`

- [ ] **Step 1: Write failing tests for required i18n and risk fields**

```python
def test_manifest_requires_zh_and_en_titles():
    data = {
        "template_id": "community/basic",
        "version": "1.0.0",
        "title_i18n": {"zh-CN": "仅中文"},
    }
    with pytest.raises(ValueError):
        TemplateManifest.model_validate(data)
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run: `pytest tests/domain/test_manifest_models.py -v`
Expected: FAIL on missing locale validation

- [ ] **Step 3: Add minimal validators and clear error types**

```python
@field_validator("title_i18n")
@classmethod
def ensure_required_locales(cls, value: dict[str, str]) -> dict[str, str]:
    required = {"zh-CN", "en-US"}
    if not required.issubset(value.keys()):
        raise ValueError("title_i18n must contain zh-CN and en-US")
    return value
```

- [ ] **Step 4: Run tests and ensure pass**

Run: `pytest tests/domain/test_manifest_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/domain/models.py sharelife/domain/errors.py tests/domain/test_manifest_models.py
git commit -m "feat: enforce manifest locale and schema validation"
```

### Task 3: Official Registry Pull + Local Cache

**Files:**
- Create: `sharelife/infrastructure/official_registry_source.py`
- Create: `sharelife/infrastructure/local_store.py`
- Create: `sharelife/application/services_registry.py`
- Test: `tests/application/test_registry_service.py`

- [ ] **Step 1: Write failing tests for index fetch and cache fallback**

```python
def test_registry_service_uses_cache_on_fetch_failure(registry_service, fake_store):
    fake_store.save_json("registry/index.json", {"templates": [{"template_id": "a"}]})
    data = registry_service.refresh_or_load()
    assert data["templates"][0]["template_id"] == "a"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/application/test_registry_service.py -v`
Expected: FAIL with missing service implementation

- [ ] **Step 3: Implement source adapter + cache store + service**

```python
class RegistryService:
    def refresh_or_load(self) -> dict:
        try:
            latest = self.source.fetch_index()
            self.store.save_json("registry/index.json", latest)
            return latest
        except Exception:
            return self.store.load_json("registry/index.json", {"templates": []})
```

- [ ] **Step 4: Run tests and confirm pass**

Run: `pytest tests/application/test_registry_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/infrastructure sharelife/application/services_registry.py tests/application/test_registry_service.py
git commit -m "feat: add official registry pull and local cache fallback"
```

### Task 4: Risk Scan and Compatibility Evaluation

**Files:**
- Create: `sharelife/application/services_scan.py`
- Modify: `sharelife/domain/policies.py`
- Test: `tests/application/test_scan_and_compat.py`

- [ ] **Step 1: Write failing tests for L1/L2/L3 classification**

```python
def test_scan_marks_provider_changes_as_l3(scanner):
    report = scanner.scan({"provider_settings": {"model": "x"}})
    assert "L3" in report.levels
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/application/test_scan_and_compat.py -v`
Expected: FAIL because scanner not implemented

- [ ] **Step 3: Implement minimal scan/compat logic**

```python
if "provider_settings" in payload:
    levels.add("L3")
compat = "compatible" if manifest.astrbot_version else "degraded"
```

- [ ] **Step 4: Run tests and verify pass**

Run: `pytest tests/application/test_scan_and_compat.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/domain/policies.py sharelife/application/services_scan.py tests/application/test_scan_and_compat.py
git commit -m "feat: implement risk scan and compatibility evaluation"
```

### Task 5: Session Trial Service (2h TTL, No Renewal)

**Files:**
- Create: `sharelife/application/services_trial.py`
- Create: `sharelife/infrastructure/system_clock.py`
- Test: `tests/application/test_trial_service.py`

- [ ] **Step 1: Write failing tests for trial TTL and renewal block**

```python
def test_trial_defaults_to_two_hours(service):
    trial = service.start_trial(user_id="u1", session_id="s1", template_id="t1")
    assert trial.ttl_seconds == 7200


def test_trial_renew_is_forbidden(service):
    with pytest.raises(PermissionError):
        service.renew_trial("trial-1")
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/application/test_trial_service.py -v`
Expected: FAIL with missing service methods

- [ ] **Step 3: Implement minimal trial lifecycle**

```python
def renew_trial(self, trial_id: str):
    raise PermissionError("TRIAL_RENEW_FORBIDDEN")
```

- [ ] **Step 4: Run tests and verify pass**

Run: `pytest tests/application/test_trial_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/application/services_trial.py sharelife/infrastructure/system_clock.py tests/application/test_trial_service.py
git commit -m "feat: add trial lifecycle with 2h ttl and renewal prohibition"
```

### Task 6: Retry Queue Service (Community-First Flow)

**Files:**
- Create: `sharelife/application/services_queue.py`
- Test: `tests/application/test_retry_queue_service.py`

- [ ] **Step 1: Write failing tests for queueing and 72h backlog transition**

```python
def test_retry_request_moves_to_manual_backlog_after_72h(service, frozen_clock):
    req = service.enqueue("u1", "t1")
    frozen_clock.shift(hours=73)
    service.reconcile_timeouts()
    assert service.get(req.id).state == "manual_backlog"
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/application/test_retry_queue_service.py -v`
Expected: FAIL for missing queue logic

- [ ] **Step 3: Implement queue state machine with dedup**

```python
if existing and existing.state in {"queued", "reviewing", "manual_backlog"}:
    return existing
```

- [ ] **Step 4: Run tests and verify pass**

Run: `pytest tests/application/test_retry_queue_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/application/services_queue.py tests/application/test_retry_queue_service.py
git commit -m "feat: add retry queue with manual backlog transition"
```

### Task 7: Apply Guard + Snapshot + Rollback Core

**Files:**
- Create: `sharelife/application/services_apply.py`
- Create: `sharelife/application/ports.py`
- Create: `sharelife/infrastructure/runtime_bridge.py`
- Test: `tests/application/test_apply_service.py`

- [ ] **Step 1: Write failing tests for dry-run prerequisite and rollback**

```python
def test_apply_requires_existing_dryrun_plan(service):
    with pytest.raises(ValueError):
        service.apply(plan_id="missing")
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/application/test_apply_service.py -v`
Expected: FAIL due missing apply guard

- [ ] **Step 3: Implement minimal guarded apply flow**

```python
def apply(self, plan_id: str):
    plan = self.plan_store.get(plan_id)
    if not plan:
        raise ValueError("PLAN_NOT_FOUND")
    snap = self.runtime.snapshot()
    try:
        self.runtime.apply_patch(plan.patch)
    except Exception:
        self.runtime.restore_snapshot(snap)
        raise
```

- [ ] **Step 4: Run tests and verify pass**

Run: `pytest tests/application/test_apply_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/application/services_apply.py sharelife/application/ports.py sharelife/infrastructure/runtime_bridge.py tests/application/test_apply_service.py
git commit -m "feat: implement guarded apply with snapshot rollback"
```

### Task 8: Command Interfaces (User + Admin)

**Files:**
- Create: `sharelife/interfaces/dto.py`
- Create: `sharelife/interfaces/commands_user.py`
- Create: `sharelife/interfaces/commands_admin.py`
- Modify: `main.py`
- Test: `tests/interfaces/test_command_handlers.py`

- [ ] **Step 1: Write failing command behavior tests**

```python
def test_user_cannot_call_admin_apply(command_runner):
    resp = command_runner.run(role="member", command="/sharelife apply plan-1")
    assert "permission" in resp.lower()
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/interfaces/test_command_handlers.py -v`
Expected: FAIL because handlers not wired

- [ ] **Step 3: Implement command handlers and role checks**

```python
@filter.command_group("sharelife")
async def sharelife_root(self, event: AstrMessageEvent):
    ...
```

- [ ] **Step 4: Run tests and verify pass**

Run: `pytest tests/interfaces/test_command_handlers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py sharelife/interfaces tests/interfaces/test_command_handlers.py
git commit -m "feat: add community-first sharelife command interfaces"
```

### Task 9: User Preference Switching and Detail Observability Toggle

**Files:**
- Create: `sharelife/application/services_preferences.py`
- Modify: `sharelife/interfaces/commands_user.py`
- Modify: `sharelife/interfaces/dto.py`
- Test: `tests/application/test_preferences_service.py`
- Test: `tests/interfaces/test_preference_commands.py`

- [ ] **Step 1: Write failing tests for mode switching and detail-observe toggle**

```python
def test_user_can_switch_execution_mode(service):
    pref = service.set_execution_mode(user_id="u1", mode="subagent_driven")
    assert pref.execution_mode == "subagent_driven"


def test_user_can_toggle_detail_observability(service):
    pref = service.set_observe_details(user_id="u1", enabled=True)
    assert pref.observe_task_details is True
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/application/test_preferences_service.py tests/interfaces/test_preference_commands.py -v`
Expected: FAIL due missing preference service and command routes

- [ ] **Step 3: Implement minimal preference model and handlers**

```python
class UserPreference(BaseModel):
    user_id: str
    execution_mode: Literal["subagent_driven", "inline_execution"] = "subagent_driven"
    observe_task_details: bool = False
```

- [ ] **Step 4: Run tests and verify pass**

Run: `pytest tests/application/test_preferences_service.py tests/interfaces/test_preference_commands.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/application/services_preferences.py sharelife/interfaces/commands_user.py sharelife/interfaces/dto.py tests/application/test_preferences_service.py tests/interfaces/test_preference_commands.py
git commit -m "feat: add user mode switch and task-detail observability toggle"
```

### Task 10: i18n Packs and Key Parity Checks

**Files:**
- Create: `sharelife/i18n/zh-CN/messages.yaml`
- Create: `sharelife/i18n/en-US/messages.yaml`
- Create: `sharelife/i18n/ja-JP/messages.yaml`
- Test: `tests/i18n/test_locale_keys.py`

- [ ] **Step 1: Write failing test for locale key parity**

```python
def test_zh_and_en_have_same_keys(i18n_loader):
    zh = i18n_loader("zh-CN")
    en = i18n_loader("en-US")
    assert set(zh.keys()) == set(en.keys())
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/i18n/test_locale_keys.py -v`
Expected: FAIL due missing locale files/keys

- [ ] **Step 3: Add locale message packs + fallback behavior**

```yaml
# sharelife/i18n/en-US/messages.yaml
trial_renew_forbidden: "Trial renewal is disabled. Please request admin review."
```

- [ ] **Step 4: Run tests and verify pass**

Run: `pytest tests/i18n/test_locale_keys.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add sharelife/i18n tests/i18n/test_locale_keys.py
git commit -m "feat: add bilingual i18n packs with ja-jp placeholder"
```

### Task 11: Community-First Docs and CI Gate

**Files:**
- Create: `docs/zh/how-to/community-first-workflow.md`
- Create: `docs/en/how-to/community-first-workflow.md`
- Create: `.github/workflows/ci.yml`
- Modify: `docs/specs/2026-03-24-sharelife-v1-freeze.zh-CN.md`
- Modify: `docs/specs/2026-03-24-sharelife-v1-freeze.en-US.md`

- [ ] **Step 1: Write failing docs/ci check command locally**

Run: `pytest -q`
Expected: FAIL before all tasks are complete

- [ ] **Step 2: Add CI workflow for lint + tests + docs build**

```yaml
- run: ruff check .
- run: pytest -q
- run: npm --prefix docs ci && npm --prefix docs run docs:build
```

- [ ] **Step 3: Add how-to docs for personal/community workflow**

```md
# 社区优先工作流
1. 选择模板
2. 试用 2 小时
3. 超出后提交管理员请求
```

- [ ] **Step 4: Run local verification**

Run: `ruff check . && pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs .github/workflows/ci.yml
git commit -m "docs: add community-first how-to and ci verification gates"
```

---

## v1 Done Criteria

1. Personal-user workflow is complete end-to-end via commands.
2. Trial renewal is strictly forbidden and retry requests go through admin path.
3. Global apply requires dry-run and supports rollback.
4. Users can switch between `subagent_driven` and `inline_execution` modes.
5. Users can toggle task-detail observability on/off, default off for privacy-by-default.
6. zh-CN + en-US keys remain in parity; ja-JP placeholder exists.
7. Enterprise mechanics are preserved as non-blocking future extensions.

## v2-Ready (Not Required for v1)

1. On-call rotation routing and scheduling.
2. Advanced takeover lock orchestration and conflict UI.
3. Offline digest routing optimization.

## Plan Self-Review Notes

1. DRY/YAGNI: v1 excludes mandatory enterprise orchestration from critical path.
2. TDD: every task starts with failing tests and verifies pass before commit.
3. Commit discipline: one feature-focused commit per task.

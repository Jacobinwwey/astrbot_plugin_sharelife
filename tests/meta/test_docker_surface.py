from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_standalone_webui_container_files_exist():
    assert (REPO_ROOT / "Dockerfile").exists()
    assert (REPO_ROOT / "docker-compose.yml").exists()
    assert (REPO_ROOT / "scripts" / "run_sharelife_webui_standalone.py").exists()
    assert (REPO_ROOT / "scripts" / "migrate_state_to_sqlite.py").exists()


def test_dockerfile_runs_standalone_webui_with_healthcheck():
    text = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "HEALTHCHECK" in text
    assert "/api/health" in text
    assert "run_sharelife_webui_standalone.py" in text
    assert "SHARELIFE_STATE_BACKEND=sqlite" in text
    assert "PIP_ROOT_USER_ACTION=ignore" in text
    assert "PIP_DISABLE_PIP_VERSION_CHECK=1" in text


def test_compose_exposes_port_volume_and_healthcheck():
    text = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "sharelife-webui" in text
    assert "${SHARELIFE_WEBUI_HOST_PORT:-8106}:8106" in text
    assert "${SHARELIFE_DOCKER_DATA_DIR:-./output/docker-data}:/data" in text
    assert "healthcheck" in text
    assert "SHARELIFE_STATE_BACKEND: \"sqlite\"" in text


def test_webui_docs_include_container_quickstart():
    zh = (REPO_ROOT / "docs" / "zh" / "how-to" / "webui-page.md").read_text(encoding="utf-8")
    en = (REPO_ROOT / "docs" / "en" / "how-to" / "webui-page.md").read_text(encoding="utf-8")
    ja = (REPO_ROOT / "docs" / "ja" / "how-to" / "webui-page.md").read_text(encoding="utf-8")
    for text in (zh, en, ja):
        assert "docker compose up -d --build" in text


def test_standalone_runner_and_docs_surface_private_admin_auth_defaults():
    runner = (REPO_ROOT / "scripts" / "run_sharelife_webui_standalone.py").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    zh = (REPO_ROOT / "docs" / "zh" / "how-to" / "webui-page.md").read_text(encoding="utf-8")
    en = (REPO_ROOT / "docs" / "en" / "how-to" / "webui-page.md").read_text(encoding="utf-8")
    ja = (REPO_ROOT / "docs" / "ja" / "how-to" / "webui-page.md").read_text(encoding="utf-8")

    assert "--allow-config-admin-password" in runner
    assert "SHARELIFE_ALLOW_CONFIG_ADMIN_PASSWORD" in runner

    assert "docs-private/" in readme
    assert "excluded from the public README and docs site" in readme

    for text in (zh, en, ja):
        assert "private" in text.lower() or "私有" in text or "非公開" in text
        assert "SHARELIFE_ADMIN_PASSWORD" not in text
        assert "SHARELIFE_ALLOW_CONFIG_ADMIN_PASSWORD" not in text

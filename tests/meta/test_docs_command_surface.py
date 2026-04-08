from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_readme_lists_public_member_commands_and_private_boundary():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "/sharelife_trial_status" in text
    assert "/sharelife_market" in text
    assert "/sharelife_submit" in text
    assert "/member" in text
    assert "/admin" not in text
    assert "/sharelife_profile_import_dryrun" in text
    assert "/sharelife_profile_import_dryrun_latest" in text
    assert "/sharelife_profile_plugins" in text
    assert "/sharelife_profile_plugins_confirm" in text
    assert "/sharelife_profile_plugins_install" in text


def test_get_started_guides_cover_member_trial_install_and_upload_handoff():
    zh_text = (REPO_ROOT / "docs" / "zh" / "tutorials" / "get-started.md").read_text(encoding="utf-8")
    en_text = (REPO_ROOT / "docs" / "en" / "tutorials" / "get-started.md").read_text(encoding="utf-8")
    ja_text = (REPO_ROOT / "docs" / "ja" / "tutorials" / "get-started.md").read_text(encoding="utf-8")

    for text in (zh_text, en_text, ja_text):
        assert "/sharelife_trial_status" in text
        assert "/sharelife_market" in text
        assert "20 MiB" in text
        assert "artifact_id" in text
        assert "/member" in text
        assert "/sharelife_dryrun" not in text
        assert "/sharelife_rollback" not in text


def test_api_reference_lists_public_member_trial_upload_and_install_routes():
    zh_text = (REPO_ROOT / "docs" / "zh" / "reference" / "api-v1.md").read_text(encoding="utf-8")
    en_text = (REPO_ROOT / "docs" / "en" / "reference" / "api-v1.md").read_text(encoding="utf-8")
    ja_text = (REPO_ROOT / "docs" / "ja" / "reference" / "api-v1.md").read_text(encoding="utf-8")

    for text in (zh_text, en_text, ja_text):
        assert "get_trial_status" in text
        assert "/api/trial/status" in text
        assert "compare_profile_pack_catalog" in text
        assert "/api/profile-pack/catalog/compare" in text
        assert "/api/profile-pack/submit" in text
        assert "/api/member/installations" in text
        assert "/api/admin/" not in text
        assert "/api/reviewer/" not in text


def test_japanese_docs_keep_public_reference_entries_without_private_workflow_links():
    reference_path = REPO_ROOT / "docs" / "ja" / "reference" / "api-v1.md"
    config_text = (REPO_ROOT / "docs" / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    index_text = (REPO_ROOT / "docs" / "ja" / "index.md").read_text(encoding="utf-8")

    assert reference_path.exists()
    assert "/ja/reference/api-v1" in config_text
    assert "/ja/reference/api-v1" in index_text
    assert "/ja/how-to/community-first-workflow" not in config_text
    assert "/ja/how-to/community-first-workflow" not in index_text


def test_webui_guides_mention_trial_status_upload_chain_and_private_boundary():
    zh_text = (REPO_ROOT / "docs" / "zh" / "how-to" / "webui-page.md").read_text(encoding="utf-8")
    en_text = (REPO_ROOT / "docs" / "en" / "how-to" / "webui-page.md").read_text(encoding="utf-8")
    ja_text = (REPO_ROOT / "docs" / "ja" / "how-to" / "webui-page.md").read_text(encoding="utf-8")

    for text in (zh_text, en_text, ja_text):
        assert "Trial Status" in text or "试用状态" in text or "トライアル状態" in text
        assert "20 MiB" in text
        assert "/member" in text
        assert "private" in text.lower() or "私有" in text or "非公開" in text
        assert "/api/admin/" not in text
        assert "/api/reviewer/" not in text


def test_bot_profile_guides_describe_member_submission_flow():
    zh_text = (REPO_ROOT / "docs" / "zh" / "how-to" / "bot-profile-pack.md").read_text(encoding="utf-8")
    en_text = (REPO_ROOT / "docs" / "en" / "how-to" / "bot-profile-pack.md").read_text(encoding="utf-8")
    ja_text = (REPO_ROOT / "docs" / "ja" / "how-to" / "bot-profile-pack.md").read_text(encoding="utf-8")

    for text in (zh_text, en_text, ja_text):
        assert "artifact_id" in text
        assert "replace_existing" in text
        assert "Profile-Pack" in text or "profile-pack" in text
        assert "/api/admin/" not in text
        assert "/api/reviewer/" not in text


def test_private_ops_guides_are_not_published_in_public_navigation():
    config_text = (REPO_ROOT / "docs" / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    zh_index = (REPO_ROOT / "docs" / "zh" / "index.md").read_text(encoding="utf-8")
    en_index = (REPO_ROOT / "docs" / "en" / "index.md").read_text(encoding="utf-8")
    ja_index = (REPO_ROOT / "docs" / "ja" / "index.md").read_text(encoding="utf-8")

    private_public_routes = [
        "/zh/how-to/community-first-workflow",
        "/en/how-to/community-first-workflow",
        "/ja/how-to/community-first-workflow",
        "/zh/how-to/featured-curation",
        "/en/how-to/featured-curation",
        "/ja/how-to/featured-curation",
        "/zh/how-to/webui-observability-runbook",
        "/en/how-to/webui-observability-runbook",
        "/ja/how-to/webui-observability-runbook",
        "/zh/reference/local-webui-auth-private-ops",
        "/en/reference/local-webui-auth-private-ops",
        "/ja/reference/local-webui-auth-private-ops",
        "/zh/reviewer/device-key-management",
        "/en/reviewer/device-key-management",
        "/ja/reviewer/device-key-management",
    ]

    for route in private_public_routes:
        assert route not in config_text
        assert route not in zh_index
        assert route not in en_index
        assert route not in ja_index


def test_onboarding_docs_surface_and_navigation_are_wired():
    config_text = (REPO_ROOT / "docs" / ".vitepress" / "config.ts").read_text(encoding="utf-8")
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for locale in ("en", "zh", "ja"):
        assert (REPO_ROOT / "docs" / locale / "tutorials" / "3-minute-quickstart.md").exists()
        assert (REPO_ROOT / "docs" / locale / "how-to" / "init-wizard-and-config-template.md").exists()
        assert f"/{locale}/tutorials/3-minute-quickstart" in config_text
        assert f"/{locale}/how-to/init-wizard-and-config-template" in config_text

    assert (REPO_ROOT / "QUICKSTART.md").exists()
    assert (REPO_ROOT / "config.template.yaml").exists()

    assert "3-Minute Onboarding" in readme_text
    assert "Init Wizard And Config Template" in readme_text
    assert "scripts/sharelife-init-wizard" in readme_text
    assert "--allow-anonymous-member" in readme_text
    assert "--anonymous-member-user-id" in readme_text
    assert "--anonymous-member-allowlist" in readme_text
    assert "QUICKSTART.md" in readme_text
    assert "config.template.yaml" in readme_text


def test_private_ops_docs_live_outside_public_docs_tree():
    ignored = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "docs-private/" in ignored

    for locale in ("en", "zh", "ja"):
        assert not (REPO_ROOT / "docs" / locale / "how-to" / "community-first-workflow.md").exists()
        assert not (REPO_ROOT / "docs" / locale / "how-to" / "featured-curation.md").exists()
        assert not (REPO_ROOT / "docs" / locale / "how-to" / "webui-observability-runbook.md").exists()
        assert not (REPO_ROOT / "docs" / locale / "reference" / "local-webui-auth-private-ops.md").exists()
        assert not (REPO_ROOT / "docs" / locale / "reviewer" / "device-key-management.md").exists()

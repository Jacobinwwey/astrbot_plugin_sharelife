from pathlib import Path

from sharelife.infrastructure.local_webui_auth import (
    ensure_local_webui_auth_template,
    merge_local_webui_auth_override,
    resolve_configured_local_webui_auth_path,
    resolve_local_webui_auth_path,
    strip_untrusted_standalone_admin_password,
)


def test_resolve_local_webui_auth_path_uses_secrets_dir(tmp_path):
    assert resolve_local_webui_auth_path(tmp_path) == tmp_path / "secrets" / "webui-auth.local.toml"


def test_resolve_configured_local_webui_auth_path_honors_env_override(tmp_path):
    override_path = tmp_path / "custom" / "webui-auth.toml"
    resolved = resolve_configured_local_webui_auth_path(
        data_root=tmp_path,
        env={"SHARELIFE_LOCAL_WEBUI_AUTH_FILE": str(override_path)},
    )
    assert resolved == override_path


def test_merge_local_webui_auth_override_applies_local_file(tmp_path):
    auth_path = resolve_local_webui_auth_path(tmp_path)
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(
        "\n".join(
            [
                "[webui.auth]",
                'member_password = "member-local"',
                'admin_password = "admin-local"',
                "login_rate_limit_max_attempts = 4",
                "allow_anonymous_member = true",
                'anonymous_member_user_id = "guest-member"',
                'anonymous_member_allowlist = ["POST /api/trial", "GET /api/preferences"]',
            ]
        ),
        encoding="utf-8",
    )

    merged = merge_local_webui_auth_override(
        {
            "webui": {
                "auth": {
                    "token_ttl_seconds": 7200,
                    "reviewer_password": "reviewer-from-config",
                }
            }
        },
        data_root=tmp_path,
    )

    assert merged["webui"]["auth"]["member_password"] == "member-local"
    assert merged["webui"]["auth"]["admin_password"] == "admin-local"
    assert merged["webui"]["auth"]["reviewer_password"] == "reviewer-from-config"
    assert merged["webui"]["auth"]["token_ttl_seconds"] == 7200
    assert merged["webui"]["auth"]["login_rate_limit_max_attempts"] == 4
    assert merged["webui"]["auth"]["allow_anonymous_member"] is True
    assert merged["webui"]["auth"]["anonymous_member_user_id"] == "guest-member"
    assert merged["webui"]["auth"]["anonymous_member_allowlist"] == [
        "POST /api/trial",
        "GET /api/preferences",
    ]


def test_merge_local_webui_auth_override_ignores_unknown_fields(tmp_path):
    auth_path = resolve_local_webui_auth_path(tmp_path)
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(
        "\n".join(
            [
                "[webui.auth]",
                'admin_password = "admin-local"',
                'unexpected = "discard-me"',
            ]
        ),
        encoding="utf-8",
    )

    merged = merge_local_webui_auth_override({}, data_root=tmp_path)

    assert merged["webui"]["auth"]["admin_password"] == "admin-local"
    assert "unexpected" not in merged["webui"]["auth"]


def test_ensure_local_webui_auth_template_creates_file_without_overwriting(tmp_path):
    auth_path = resolve_local_webui_auth_path(tmp_path)

    created = ensure_local_webui_auth_template(auth_path)
    assert created == auth_path
    assert auth_path.exists()
    text = auth_path.read_text(encoding="utf-8")
    assert "[webui.auth]" in text
    assert 'admin_password = ""' in text
    assert "allow_anonymous_member = false" in text
    assert 'anonymous_member_user_id = "webui-user"' in text
    assert "anonymous_member_allowlist = [" in text

    auth_path.write_text("# keep-my-local-edit\n", encoding="utf-8")
    ensure_local_webui_auth_template(auth_path)
    assert auth_path.read_text(encoding="utf-8") == "# keep-my-local-edit\n"


def test_strip_untrusted_standalone_admin_password_removes_config_admin_secret(tmp_path):
    sanitized = strip_untrusted_standalone_admin_password(
        {
            "webui": {
                "auth": {
                    "member_password": "member-secret",
                    "admin_password": "config-admin-secret",
                }
            }
        },
        data_root=tmp_path,
    )

    assert sanitized["webui"]["auth"]["member_password"] == "member-secret"
    assert "admin_password" not in sanitized["webui"]["auth"]


def test_strip_untrusted_standalone_admin_password_keeps_local_secret(tmp_path):
    auth_path = resolve_local_webui_auth_path(tmp_path)
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(
        "\n".join(
            [
                "[webui.auth]",
                'admin_password = "local-admin-secret"',
            ]
        ),
        encoding="utf-8",
    )

    sanitized = strip_untrusted_standalone_admin_password(
        {
            "webui": {
                "auth": {
                    "admin_password": "local-admin-secret",
                }
            }
        },
        data_root=tmp_path,
    )

    assert sanitized["webui"]["auth"]["admin_password"] == "local-admin-secret"


def test_strip_untrusted_standalone_admin_password_keeps_env_secret(tmp_path):
    sanitized = strip_untrusted_standalone_admin_password(
        {
            "webui": {
                "auth": {
                    "admin_password": "env-admin-secret",
                }
            }
        },
        data_root=tmp_path,
        env={"SHARELIFE_ADMIN_PASSWORD": "env-admin-secret"},
    )

    assert sanitized["webui"]["auth"]["admin_password"] == "env-admin-secret"


def test_strip_untrusted_standalone_admin_password_can_allow_config_secret(tmp_path):
    sanitized = strip_untrusted_standalone_admin_password(
        {
            "webui": {
                "auth": {
                    "admin_password": "config-admin-secret",
                }
            }
        },
        data_root=tmp_path,
        allow_config_admin_password=True,
    )

    assert sanitized["webui"]["auth"]["admin_password"] == "config-admin-secret"

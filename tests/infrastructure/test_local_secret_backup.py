import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sharelife.infrastructure.local_secret_backup import (
    backup_local_webui_auth,
    build_local_secret_backup_names,
)


def test_build_local_secret_backup_names_uses_utc_timestamp():
    artifact_name, manifest_name = build_local_secret_backup_names(
        prefix="sharelife-webui-auth",
        now=datetime(2026, 4, 4, 15, 30, 45, tzinfo=UTC),
    )

    assert artifact_name == "sharelife-webui-auth-20260404T153045Z.toml.enc"
    assert manifest_name == "sharelife-webui-auth-20260404T153045Z.manifest.json"


def test_backup_local_webui_auth_encrypts_then_uploads(tmp_path, monkeypatch):
    source_path = tmp_path / "webui-auth.local.toml"
    source_path.write_text('[webui.auth]\nadmin_password = "admin-secret"\n', encoding="utf-8")
    passphrase_path = tmp_path / "backup.passphrase.txt"
    passphrase_path.write_text("local-passphrase\n", encoding="utf-8")
    calls = []

    def fake_run(cmd, check, capture_output, text, timeout, stdin=None):
        calls.append(list(cmd))
        if cmd[0] == "openssl":
            output_path = Path(cmd[cmd.index("-out") + 1])
            output_path.write_bytes(b"encrypted-payload")
        if cmd[:2] == ["rclone", "rcat"] and stdin is not None:
            stdin.read()
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("sharelife.infrastructure.local_secret_backup.subprocess.run", fake_run)

    result = backup_local_webui_auth(
        source_path=source_path,
        passphrase_file=passphrase_path,
        remote_path="gdrive:/sharelife/secrets",
        now=datetime(2026, 4, 4, 15, 30, 45, tzinfo=UTC),
    )

    assert calls[0][0] == "openssl"
    assert calls[1][:2] == ["rclone", "rcat"]
    assert calls[2][:2] == ["rclone", "rcat"]
    assert result.remote_encrypted_path == "gdrive:/sharelife/secrets/sharelife-webui-auth-20260404T153045Z.toml.enc"
    assert result.remote_manifest_path == "gdrive:/sharelife/secrets/sharelife-webui-auth-20260404T153045Z.manifest.json"
    assert len(result.plaintext_sha256) == 64
    assert len(result.ciphertext_sha256) == 64

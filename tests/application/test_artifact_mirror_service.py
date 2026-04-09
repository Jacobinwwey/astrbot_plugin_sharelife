from datetime import UTC, datetime
import subprocess

from sharelife.application.services_artifact_mirror import ArtifactMirrorService
from sharelife.infrastructure.json_state_store import JsonStateStore
from sharelife.infrastructure.local_artifact_store import LocalArtifactStore


class FrozenClock:
    def __init__(self, start: datetime):
        self.current = start

    def utcnow(self) -> datetime:
        return self.current


def test_artifact_mirror_service_syncs_local_artifact_to_remote(tmp_path, monkeypatch):
    output_root = tmp_path / "packages"
    output_root.mkdir(parents=True, exist_ok=True)
    local_file = output_root / "community-basic.zip"
    local_file.write_text("zip-bytes", encoding="utf-8")
    clock = FrozenClock(datetime(2026, 4, 7, 13, 0, tzinfo=UTC))
    store = LocalArtifactStore(
        output_root=output_root,
        clock=clock,
        state_store=JsonStateStore(tmp_path / "artifact_state.json"),
    )
    artifact = store.register_local_file(
        artifact_kind="template_generated_package",
        path=local_file,
        filename=local_file.name,
        metadata={"template_id": "community/basic", "version": "1.0.0"},
    )
    calls: list[list[str]] = []

    def _fake_run(command, **kwargs):
        calls.append(list(command))
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="copy ok", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    service = ArtifactMirrorService(artifact_store=store, clock=clock)

    mirrored = service.mirror_artifact(
        artifact_id=artifact.artifact_id,
        remote_path="gdrive-crypt:/sharelife-artifacts",
        actor_id="admin-1",
    )

    assert mirrored["artifact"]["artifact_id"] == artifact.artifact_id
    assert mirrored["mirror"]["status"] == "succeeded"
    assert mirrored["mirror"]["remote_path"].startswith("gdrive-crypt:/sharelife-artifacts/")
    assert artifact.artifact_id in mirrored["mirror"]["remote_path"]
    assert calls[0][0:2] == ["rclone", "copyto"]

    reloaded_store = LocalArtifactStore(
        output_root=output_root,
        clock=clock,
        state_store=JsonStateStore(tmp_path / "artifact_state.json"),
    )
    reloaded = reloaded_store.get(artifact.artifact_id)
    assert reloaded.metadata["remote_mirror"]["status"] == "succeeded"


def test_artifact_mirror_service_requires_encrypted_remote_when_enabled(tmp_path, monkeypatch):
    output_root = tmp_path / "packages"
    output_root.mkdir(parents=True, exist_ok=True)
    local_file = output_root / "community-basic.zip"
    local_file.write_text("zip-bytes", encoding="utf-8")
    clock = FrozenClock(datetime(2026, 4, 7, 13, 0, tzinfo=UTC))
    store = LocalArtifactStore(output_root=output_root, clock=clock)
    artifact = store.register_local_file(
        artifact_kind="template_generated_package",
        path=local_file,
        filename=local_file.name,
    )

    def _unexpected_run(command, **kwargs):  # pragma: no cover
        raise AssertionError("subprocess.run should not be called for unencrypted remote")

    monkeypatch.setattr(subprocess, "run", _unexpected_run)
    service = ArtifactMirrorService(artifact_store=store, clock=clock)

    mirrored = service.mirror_artifact(
        artifact_id=artifact.artifact_id,
        remote_path="gdrive:/sharelife-artifacts",
        actor_id="admin-1",
        encryption_required=True,
    )

    assert mirrored["error"] == "remote_encryption_required"
    assert mirrored["artifact_id"] == artifact.artifact_id

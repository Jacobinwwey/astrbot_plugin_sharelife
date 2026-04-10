"""profile pack export/import/dryrun orchestration service."""

from __future__ import annotations

import base64
from copy import deepcopy
import difflib
import hashlib
import hmac
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
import secrets
from typing import Any
from uuid import uuid4
import zipfile

from .services_apply import ApplyService
from .services_profile_diff import ProfileDiffService
from .services_plugin_install import PluginInstallService
from .services_profile_redaction import ProfileRedactionService
from .services_profile_section_registry import ProfileSectionAdapterRegistry
from .services_scan import ScanService
from ..domain.profile_pack_models import (
    PROFILE_PACK_TYPE,
    PROFILE_PACK_TYPES,
    BotProfilePackManifest,
    PROFILE_CAPABILITY_OPTIONS,
    RedactionPolicy,
    profile_allowed_sections_for_pack,
)
from ..infrastructure.json_state_store import JsonStateStore
from ..infrastructure.profile_pack_repository import (
    JsonProfilePackRepository,
    ProfilePackRepository,
    SqliteProfilePackRepository,
)
from ..infrastructure.sqlite_state_store import SqliteStateStore
from ..infrastructure.system_clock import SystemClock

PROFILE_PACK_SUBMISSION_PENDING = "pending"
PROFILE_PACK_SUBMISSION_APPROVED = "approved"
PROFILE_PACK_SUBMISSION_REJECTED = "rejected"
PROFILE_PACK_SUBMISSION_REPLACED = "replaced"
PROFILE_PACK_SUBMISSION_WITHDRAWN = "withdrawn"
SELECTION_TREE_MAX_DEPTH = 3


@dataclass(slots=True)
class ProfilePackArtifact:
    artifact_id: str
    pack_id: str
    version: str
    exported_at: str
    path: Path
    filename: str
    sha256: str
    size_bytes: int
    manifest: BotProfilePackManifest
    redaction_notes: list[str]
    owner_user_id: str = ""


@dataclass(slots=True)
class ImportedProfilePack:
    import_id: str
    imported_at: str
    filename: str
    manifest: BotProfilePackManifest
    sections: dict[str, Any]
    scan_summary: dict[str, Any]
    compatibility: str
    compatibility_issues: list[str]
    user_id: str = ""
    source_artifact_id: str = ""
    import_origin: str = ""
    source_fingerprint: str = ""


@dataclass(slots=True)
class ProfilePackSubmission:
    submission_id: str
    user_id: str
    artifact_id: str
    import_id: str
    pack_type: str
    pack_id: str
    version: str
    status: str
    created_at: str
    updated_at: str
    reviewer_id: str | None = None
    review_note: str = ""
    review_labels: list[str] = field(default_factory=list)
    warning_flags: list[str] = field(default_factory=list)
    risk_level: str = "low"
    scan_summary: dict[str, Any] = field(default_factory=dict)
    compatibility: str = "compatible"
    compatibility_issues: list[str] = field(default_factory=list)
    filename: str = ""
    sha256: str = ""
    size_bytes: int = 0
    sections: list[str] = field(default_factory=list)
    redaction_mode: str = "exclude_secrets"
    capability_summary: dict[str, Any] = field(default_factory=dict)
    compatibility_matrix: dict[str, Any] = field(default_factory=dict)
    review_evidence: dict[str, Any] = field(default_factory=dict)
    submit_options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PublishedProfilePack:
    pack_type: str
    pack_id: str
    version: str
    source_submission_id: str
    artifact_id: str
    import_id: str
    published_at: str
    review_note: str = ""
    review_labels: list[str] = field(default_factory=list)
    warning_flags: list[str] = field(default_factory=list)
    risk_level: str = "low"
    scan_summary: dict[str, Any] = field(default_factory=dict)
    compatibility: str = "compatible"
    compatibility_issues: list[str] = field(default_factory=list)
    filename: str = ""
    sha256: str = ""
    size_bytes: int = 0
    sections: list[str] = field(default_factory=list)
    redaction_mode: str = "exclude_secrets"
    capability_summary: dict[str, Any] = field(default_factory=dict)
    compatibility_matrix: dict[str, Any] = field(default_factory=dict)
    review_evidence: dict[str, Any] = field(default_factory=dict)
    featured: bool = False
    featured_note: str = ""
    featured_by: str = ""
    featured_at: str = ""


@dataclass(slots=True)
class PreparedProfilePackImport:
    filename: str
    archive_bytes: bytes
    manifest: BotProfilePackManifest
    sections: dict[str, Any]
    extra_issues: list[str] = field(default_factory=list)


class ProfilePackService:
    def __init__(
        self,
        runtime,
        apply_service: ApplyService,
        output_root: Path | str,
        clock: SystemClock,
        *,
        scan_service: ScanService | None = None,
        section_registry: ProfileSectionAdapterRegistry | None = None,
        redaction_service: ProfileRedactionService | None = None,
        diff_service: ProfileDiffService | None = None,
        plugin_install_service: PluginInstallService | None = None,
        astrbot_version: str = "",
        plugin_version: str = "",
        state_store: JsonStateStore | SqliteStateStore | None = None,
        repository: ProfilePackRepository | None = None,
        signing_key_id: str = "",
        signing_secret: str = "",
        trusted_signing_keys: dict[str, str] | None = None,
        secrets_encryption_key: str = "",
    ):
        self.runtime = runtime
        self.apply_service = apply_service
        self.output_root = Path(output_root)
        self.clock = clock
        self.scan_service = scan_service or ScanService()
        self.section_registry = section_registry or ProfileSectionAdapterRegistry.default_registry()
        self.redaction_service = redaction_service or ProfileRedactionService()
        self.diff_service = diff_service or ProfileDiffService()
        self.plugin_install_service = plugin_install_service or PluginInstallService()
        self.astrbot_version = str(astrbot_version or "").strip()
        self.plugin_version = str(plugin_version or "").strip()
        self.state_store = state_store
        self.repository = self._build_repository(state_store=state_store, repository=repository)
        self.signing_key_id = str(signing_key_id or "").strip() or "default"
        self.signing_secret = str(signing_secret or "").strip()
        self.secrets_encryption_key = str(secrets_encryption_key or "").strip()
        self.trusted_signing_keys: dict[str, str] = {}
        for key_id, key_value in (trusted_signing_keys or {}).items():
            normalized_key_id = str(key_id or "").strip()
            normalized_value = str(key_value or "").strip()
            if normalized_key_id and normalized_value:
                self.trusted_signing_keys[normalized_key_id] = normalized_value
        if self.signing_secret:
            self.trusted_signing_keys.setdefault(self.signing_key_id, self.signing_secret)

        self._artifacts: dict[str, ProfilePackArtifact] = {}
        self._imports: dict[str, ImportedProfilePack] = {}
        self._submissions: dict[str, ProfilePackSubmission] = {}
        self._published: dict[str, PublishedProfilePack] = {}
        self._plugin_install_confirmations: dict[str, list[str]] = {}
        self._plugin_install_executions: dict[str, list[dict[str, Any]]] = {}
        self._load_state()

    @staticmethod
    def _build_repository(
        *,
        state_store: JsonStateStore | SqliteStateStore | None,
        repository: ProfilePackRepository | None,
    ) -> ProfilePackRepository | None:
        if repository is not None:
            return repository
        if state_store is None:
            return None
        if isinstance(state_store, SqliteStateStore):
            return SqliteProfilePackRepository(
                state_store.db_path,
                legacy_state_store=state_store,
            )
        return JsonProfilePackRepository(state_store)

    def export_bot_profile_pack(
        self,
        pack_id: str,
        version: str,
        *,
        pack_type: str = PROFILE_PACK_TYPE,
        redaction_mode: str = "exclude_secrets",
        sections: list[str] | None = None,
        mask_paths: list[str] | None = None,
        drop_paths: list[str] | None = None,
    ) -> ProfilePackArtifact:
        normalized_pack_type = self._normalize_pack_type(pack_type)
        selected_sections = self._resolve_export_sections(
            pack_type=normalized_pack_type,
            requested_sections=sections,
        )
        policy_payload = {"mode": redaction_mode}
        policy_payload["include_sections"] = selected_sections
        if mask_paths is not None:
            policy_payload["mask_paths"] = mask_paths
        if drop_paths is not None:
            policy_payload["drop_paths"] = drop_paths
        policy = RedactionPolicy.model_validate(policy_payload)

        snapshot = self.runtime.snapshot()
        raw_sections = self.section_registry.capture(
            snapshot=snapshot,
            selected_sections=policy.include_sections,
        )
        redacted_sections, redaction_notes = self._redact_sections(
            raw_sections,
            mode=policy.mode,
            mask_paths=policy.mask_paths,
            drop_paths=policy.drop_paths,
        )

        manifest_payload: dict[str, Any] = {
            "pack_type": normalized_pack_type,
            "pack_id": pack_id,
            "version": version,
            "created_at": self.clock.utcnow().isoformat(),
            "astrbot_version": self.astrbot_version,
            "plugin_compat": self.plugin_version,
            "sections": list(redacted_sections.keys()),
            "capabilities": self._infer_manifest_capabilities(
                sections=redacted_sections,
                pack_type=normalized_pack_type,
            ),
            "redaction_policy": policy.model_dump(),
            "hashes": {
                BotProfilePackManifest.hash_key(section_name): self._hash_json(payload)
                for section_name, payload in redacted_sections.items()
            },
        }
        signature = self._build_signature(manifest_payload)
        if signature:
            manifest_payload["signature"] = signature
        manifest = BotProfilePackManifest.model_validate(manifest_payload)

        artifact_id = str(uuid4())
        output_dir = self.output_root / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = self._safe_filename(f"{pack_id.replace('/', '__')}-{version}-{artifact_id[:8]}.zip")
        path = output_dir / filename

        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2))
            for section_name, payload in redacted_sections.items():
                zf.writestr(
                    BotProfilePackManifest.hash_key(section_name),
                    json.dumps(payload, ensure_ascii=False, indent=2),
                )

        artifact = ProfilePackArtifact(
            artifact_id=artifact_id,
            pack_id=manifest.pack_id,
            version=manifest.version,
            exported_at=self.clock.utcnow().isoformat(),
            path=path,
            filename=filename,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            size_bytes=path.stat().st_size,
            manifest=manifest,
            redaction_notes=redaction_notes,
            owner_user_id="",
        )
        self._artifacts[artifact_id] = artifact
        self._flush_state()
        return artifact

    def get_export_artifact(self, artifact_id: str) -> ProfilePackArtifact:
        artifact = self._artifacts.get(str(artifact_id or "").strip())
        if artifact is None:
            raise ValueError("PROFILE_PACK_ARTIFACT_NOT_FOUND")
        return artifact

    def import_bot_profile_pack(
        self,
        filename: str,
        content: bytes,
        *,
        user_id: str = "",
        source_artifact_id: str = "",
    ) -> ImportedProfilePack:
        imported, _prepared = self._import_profile_pack(
            filename=filename,
            content=content,
            user_id=user_id,
            source_artifact_id=source_artifact_id,
        )
        return imported

    def import_member_profile_pack(
        self,
        *,
        user_id: str,
        filename: str,
        content: bytes,
        import_origin: str = "",
        source_fingerprint: str = "",
        refresh_existing: bool = False,
    ) -> ImportedProfilePack:
        normalized_user_id = str(user_id or "").strip() or "member"
        normalized_import_origin = str(import_origin or "").strip()
        normalized_source_fingerprint = str(source_fingerprint or "").strip()
        if refresh_existing and normalized_import_origin and normalized_source_fingerprint:
            self._refresh_member_imports(
                user_id=normalized_user_id,
                import_origin=normalized_import_origin,
                source_fingerprint=normalized_source_fingerprint,
            )
        imported, prepared = self._import_profile_pack(
            filename=filename,
            content=content,
            user_id=normalized_user_id,
            import_origin=normalized_import_origin,
            source_fingerprint=normalized_source_fingerprint,
        )

        artifact_id = str(uuid4())
        output_dir = self.output_root / "member-imports"
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = self._safe_filename(
            f"{imported.manifest.pack_id.replace('/', '__')}-{imported.manifest.version}-{artifact_id[:8]}-{imported.filename}",
        )
        path = output_dir / safe_filename
        path.write_bytes(prepared.archive_bytes)
        artifact = ProfilePackArtifact(
            artifact_id=artifact_id,
            pack_id=imported.manifest.pack_id,
            version=imported.manifest.version,
            exported_at=imported.imported_at,
            path=path,
            filename=safe_filename,
            sha256=hashlib.sha256(prepared.archive_bytes).hexdigest(),
            size_bytes=len(prepared.archive_bytes),
            manifest=imported.manifest,
            redaction_notes=[],
            owner_user_id=normalized_user_id,
        )
        self._artifacts[artifact_id] = artifact
        imported.source_artifact_id = artifact_id
        self._imports[imported.import_id] = imported
        self._flush_state()
        return imported

    def _import_profile_pack(
        self,
        *,
        filename: str,
        content: bytes,
        user_id: str = "",
        source_artifact_id: str = "",
        import_origin: str = "",
        source_fingerprint: str = "",
    ) -> tuple[ImportedProfilePack, PreparedProfilePackImport]:
        prepared, hash_mismatches = self._prepare_profile_pack_import(
            filename=filename,
            content=content,
        )
        scan_summary = self.scan_service.to_dict(
            self.scan_service.scan(
                self._scan_payload(prepared.manifest, prepared.sections),
                manifest=prepared.manifest,
            )
        )
        signature_issue = self._verify_signature_issue(prepared.manifest)
        compatibility, issues = self._resolve_compatibility(
            prepared.manifest,
            sections=prepared.sections,
            hash_mismatches=hash_mismatches,
            signature_issue=signature_issue,
        )
        embedded_issues = self._embedded_profile_pack_issues(prepared.sections)
        issues = self._dedupe_issue_codes([*issues, *embedded_issues, *list(prepared.extra_issues or [])])
        if compatibility == "compatible" and issues:
            compatibility = "degraded"

        imported = ImportedProfilePack(
            import_id=str(uuid4()),
            imported_at=self.clock.utcnow().isoformat(),
            filename=prepared.filename,
            manifest=prepared.manifest,
            sections=prepared.sections,
            scan_summary=scan_summary,
            compatibility=compatibility,
            compatibility_issues=issues,
            user_id=str(user_id or "").strip(),
            source_artifact_id=str(source_artifact_id or "").strip(),
            import_origin=str(import_origin or "").strip(),
            source_fingerprint=str(source_fingerprint or "").strip(),
        )
        self._imports[imported.import_id] = imported
        self._flush_state()
        return imported, prepared

    def _prepare_profile_pack_import(
        self,
        *,
        filename: str,
        content: bytes,
    ) -> tuple[PreparedProfilePackImport, list[str]]:
        if not content:
            raise ValueError("PROFILE_PACK_BYTES_REQUIRED")

        standard_error: ValueError | None = None
        try:
            return self._prepare_standard_profile_pack_import(filename=filename, content=content)
        except ValueError as exc:
            standard_error = exc

        converted = self._try_prepare_astrbot_profile_pack_import(
            filename=filename,
            content=content,
        )
        if converted is not None:
            return converted
        if standard_error is not None:
            raise standard_error
        raise ValueError("PROFILE_PACK_INVALID_ARCHIVE")

    def _prepare_standard_profile_pack_import(
        self,
        *,
        filename: str,
        content: bytes,
    ) -> tuple[PreparedProfilePackImport, list[str]]:
        archive_buffer = io.BytesIO(content)
        if not zipfile.is_zipfile(archive_buffer):
            raise ValueError("PROFILE_PACK_INVALID_ARCHIVE")

        archive_buffer.seek(0)
        with zipfile.ZipFile(archive_buffer, "r") as zf:
            names = set(zf.namelist())
            if "manifest.json" not in names:
                raise ValueError("PROFILE_PACK_MANIFEST_MISSING")
            try:
                manifest = BotProfilePackManifest.model_validate(
                    json.loads(zf.read("manifest.json").decode("utf-8"))
                )
            except Exception as exc:  # pragma: no cover - normalized to api payload below
                raise ValueError("PROFILE_PACK_MANIFEST_INVALID") from exc
            sections: dict[str, Any] = {}
            hash_mismatches: list[str] = []
            for section in manifest.sections:
                section_path = BotProfilePackManifest.hash_key(section)
                if section_path not in names:
                    raise ValueError("PROFILE_PACK_SECTION_MISSING")
                payload = json.loads(zf.read(section_path).decode("utf-8"))
                sections[section] = payload
                actual_hash = self._hash_json(payload)
                expected_hash = manifest.hashes.get(section_path, "")
                if expected_hash != actual_hash:
                    hash_mismatches.append(section)

        prepared = PreparedProfilePackImport(
            filename=self._safe_filename(filename or "profile-pack.zip"),
            archive_bytes=content,
            manifest=manifest,
            sections=sections,
            extra_issues=[],
        )
        return prepared, hash_mismatches

    def _try_prepare_astrbot_profile_pack_import(
        self,
        *,
        filename: str,
        content: bytes,
    ) -> tuple[PreparedProfilePackImport, list[str]] | None:
        archive_buffer = io.BytesIO(content)
        if zipfile.is_zipfile(archive_buffer):
            archive_buffer.seek(0)
            with zipfile.ZipFile(archive_buffer, "r") as zf:
                names = set(zf.namelist())
                config_path = self._astrbot_backup_config_path(names)
                if not config_path:
                    return None
                raw_config = self._load_json_dict(
                    zf.read(config_path),
                    error_code="PROFILE_PACK_INVALID_ARCHIVE",
                )
                backup_manifest: dict[str, Any] = {}
                if "manifest.json" in names:
                    try:
                        backup_manifest = self._load_json_dict(
                            zf.read("manifest.json"),
                            error_code="PROFILE_PACK_INVALID_ARCHIVE",
                        )
                    except ValueError:
                        backup_manifest = {}
                prepared = self._build_astrbot_converted_profile_pack(
                    filename=filename,
                    raw_config=raw_config,
                    source_type="astrbot_backup_zip",
                    source_sha256=hashlib.sha256(content).hexdigest(),
                    astrbot_version=str(backup_manifest.get("astrbot_version", "") or ""),
                    backup_manifest=backup_manifest,
                    extra_issues=["astrbot_raw_import_converted", "astrbot_backup_runtime_payload_omitted"],
                )
                return prepared, []

        raw_config = self._try_load_astrbot_json_config(filename=filename, content=content)
        if raw_config is None:
            return None
        basename = Path(filename or "").name
        source_type = "astrbot_cmd_config_json"
        if basename.startswith("abconf_"):
            source_type = "astrbot_abconf_json"
        elif basename != "cmd_config.json":
            source_type = "astrbot_config_json"
        prepared = self._build_astrbot_converted_profile_pack(
            filename=filename,
            raw_config=raw_config,
            source_type=source_type,
            source_sha256=hashlib.sha256(content).hexdigest(),
            astrbot_version="",
            backup_manifest={},
            extra_issues=["astrbot_raw_import_converted"],
        )
        return prepared, []

    @staticmethod
    def _load_json_dict(payload: bytes, *, error_code: str) -> dict[str, Any]:
        try:
            data = json.loads(payload.decode("utf-8-sig"))
        except Exception as exc:
            raise ValueError(error_code) from exc
        if not isinstance(data, dict):
            raise ValueError(error_code)
        return data

    @staticmethod
    def _astrbot_backup_config_path(names: set[str]) -> str:
        if "config/cmd_config.json" in names:
            return "config/cmd_config.json"
        for name in sorted(names):
            if name.endswith("/cmd_config.json") or name == "cmd_config.json":
                return name
        return ""

    def _try_load_astrbot_json_config(self, *, filename: str, content: bytes) -> dict[str, Any] | None:
        basename = Path(filename or "").name
        if not basename.endswith(".json"):
            return None
        try:
            payload = json.loads(content.decode("utf-8-sig"))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        if not self._looks_like_astrbot_config_payload(payload):
            return None
        return payload

    @staticmethod
    def _looks_like_astrbot_config_payload(payload: dict[str, Any]) -> bool:
        if {"pack_id", "version", "sections", "hashes"} <= set(payload.keys()):
            return False
        astrbot_markers = {
            "provider",
            "provider_settings",
            "plugin_set",
            "dashboard",
            "platform",
            "timezone",
            "platform_settings",
        }
        return bool(set(payload.keys()) & astrbot_markers)

    def _build_astrbot_converted_profile_pack(
        self,
        *,
        filename: str,
        raw_config: dict[str, Any],
        source_type: str,
        source_sha256: str,
        astrbot_version: str,
        backup_manifest: dict[str, Any],
        extra_issues: list[str],
    ) -> PreparedProfilePackImport:
        sections, conversion_issues = self._build_astrbot_conversion_sections(
            raw_config=raw_config,
            source_type=source_type,
            filename=filename,
            source_sha256=source_sha256,
            backup_manifest=backup_manifest,
        )
        redacted_sections, _redaction_notes = self._redact_sections(
            sections,
            "exclude_secrets",
        )
        all_issues = self._dedupe_issue_codes([*extra_issues, *conversion_issues])
        sharelife_meta = redacted_sections.get("sharelife_meta")
        if isinstance(sharelife_meta, dict):
            astrbot_import = sharelife_meta.get("astrbot_import")
            if isinstance(astrbot_import, dict):
                astrbot_import["issues"] = list(all_issues)
        pack_id = self._astrbot_conversion_pack_id(
            filename=filename,
            source_sha256=source_sha256,
            raw_config=raw_config,
        )
        version = self._astrbot_conversion_version(source_sha256=source_sha256)
        manifest_payload: dict[str, Any] = {
            "pack_type": PROFILE_PACK_TYPE,
            "pack_id": pack_id,
            "version": version,
            "created_at": self.clock.utcnow().isoformat(),
            "astrbot_version": str(astrbot_version or "").strip() or "any",
            "plugin_compat": self.plugin_version or "any",
            "sections": list(redacted_sections.keys()),
            "capabilities": self._infer_manifest_capabilities(
                sections=redacted_sections,
                pack_type=PROFILE_PACK_TYPE,
            ),
            "redaction_policy": RedactionPolicy.model_validate(
                {
                    "mode": "exclude_secrets",
                    "include_sections": list(redacted_sections.keys()),
                }
            ).model_dump(),
            "hashes": {
                BotProfilePackManifest.hash_key(section_name): self._hash_json(payload)
                for section_name, payload in redacted_sections.items()
            },
        }
        manifest = BotProfilePackManifest.model_validate(manifest_payload)
        archive_bytes = self._build_profile_pack_archive_bytes(
            manifest=manifest,
            sections=redacted_sections,
        )
        normalized_filename = self._safe_filename(
            f"{pack_id.replace('/', '__')}-{version}-converted.zip",
        )
        prepared = PreparedProfilePackImport(
            filename=normalized_filename,
            archive_bytes=archive_bytes,
            manifest=manifest,
            sections=redacted_sections,
            extra_issues=all_issues,
        )
        return prepared

    def _build_astrbot_conversion_sections(
        self,
        *,
        raw_config: dict[str, Any],
        source_type: str,
        filename: str,
        source_sha256: str,
        backup_manifest: dict[str, Any],
    ) -> tuple[dict[str, Any], list[str]]:
        issues: list[str] = []
        sections: dict[str, Any] = {}
        personas_payload, personas_summary = self._build_astrbot_conversion_personas(raw_config)
        if personas_payload:
            sections["personas"] = personas_payload

        environment_payload, environment_summary = self._build_astrbot_conversion_environment(raw_config)
        if environment_payload:
            sections["environment_manifest"] = environment_payload

        core_payload: dict[str, Any] = {}
        operator_keys = {"dashboard", "admins_id"}
        if any(key in raw_config for key in operator_keys):
            issues.append("astrbot_operator_fields_omitted")
        extracted_keys = {
            "provider",
            "plugin_set",
            "persona",
            "default_personality",
            "subagent_orchestrator",
            "platform",
            "provider_sources",
            *operator_keys,
        }
        for key, value in raw_config.items():
            key_text = str(key or "").strip()
            if not key_text or key_text in extracted_keys:
                continue
            core_payload[key_text] = self._sanitize_astrbot_conversion_value(
                deepcopy(value),
                path=f"astrbot_core.{key_text}",
            )
        if core_payload:
            sections["astrbot_core"] = core_payload

        providers_payload = self._build_astrbot_conversion_providers(raw_config)
        if providers_payload:
            sections["providers"] = providers_payload

        plugins_payload, plugin_issues = self._build_astrbot_conversion_plugins(raw_config)
        issues.extend(plugin_issues)
        if plugins_payload is not None:
            sections["plugins"] = plugins_payload

        summary = self._build_astrbot_conversion_summary(
            raw_config=raw_config,
            personas_summary=personas_summary,
            environment_summary=environment_summary,
            plugins_payload=plugins_payload,
        )

        sections["sharelife_meta"] = {
            "astrbot_import": {
                "source_type": source_type,
                "source_filename": self._safe_filename(filename or "astrbot-import"),
                "source_sha256": source_sha256,
                "config_version": raw_config.get("config_version"),
                "backup_manifest": deepcopy(backup_manifest),
                "summary": summary,
                "issues": self._dedupe_issue_codes(issues),
            }
        }
        return sections, self._dedupe_issue_codes(issues)

    def _build_astrbot_conversion_providers(self, raw_config: dict[str, Any]) -> dict[str, Any]:
        providers = raw_config.get("provider", [])
        if not isinstance(providers, list):
            return {}
        out: dict[str, Any] = {}
        for index, item in enumerate(providers):
            if not isinstance(item, dict):
                continue
            provider_id = str(item.get("id", "") or "").strip() or f"provider-{index + 1}"
            normalized = deepcopy(item)
            if "key" in normalized and "api_key" not in normalized:
                normalized["api_key"] = normalized.pop("key")
            normalized = self._sanitize_astrbot_conversion_value(
                normalized,
                path=f"providers.{provider_id}",
            )
            out[provider_id] = normalized
        return out

    def _build_astrbot_conversion_plugins(self, raw_config: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        plugin_set = raw_config.get("plugin_set")
        if plugin_set is None:
            return None, []
        if not isinstance(plugin_set, list):
            return {}, []
        normalized = [str(item or "").strip() for item in plugin_set if str(item or "").strip()]
        if "*" in normalized:
            return None, ["astrbot_plugin_wildcard_unresolved"]
        return {plugin_id: {"enabled": True} for plugin_id in normalized}, []

    def _build_astrbot_conversion_personas(self, raw_config: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        payload: dict[str, Any] = {}
        summary: dict[str, Any] = {}
        raw_personas = raw_config.get("persona")
        entries: dict[str, Any] = {}
        if isinstance(raw_personas, list):
            for index, item in enumerate(raw_personas):
                if isinstance(item, dict):
                    name = (
                        str(item.get("name", "") or "").strip()
                        or str(item.get("id", "") or "").strip()
                        or f"persona-{index + 1}"
                    )
                    entries[name] = self._sanitize_astrbot_conversion_value(
                        deepcopy(item),
                        path=f"personas.entries.{name}",
                    )
                else:
                    text = str(item or "").strip()
                    if text:
                        entries[text] = {"name": text}
        provider_settings = raw_config.get("provider_settings")
        default_personality = ""
        persona_pool: list[str] = []
        if isinstance(provider_settings, dict):
            default_personality = str(provider_settings.get("default_personality", "") or "").strip()
            raw_pool = provider_settings.get("persona_pool")
            if isinstance(raw_pool, list):
                persona_pool = [str(item or "").strip() for item in raw_pool if str(item or "").strip()]
        if not default_personality:
            default_personality = str(raw_config.get("default_personality", "") or "").strip()
        runtime: dict[str, Any] = {}
        if default_personality:
            runtime["default_personality"] = default_personality
            summary["default_personality"] = default_personality
        if persona_pool:
            runtime["persona_pool"] = list(persona_pool)
            summary["persona_pool"] = list(persona_pool)
        if runtime:
            payload["runtime"] = runtime
        if entries:
            payload["entries"] = entries
            summary["persona_count"] = len(entries)
            summary["persona_ids"] = list(entries.keys())
        elif runtime:
            summary["persona_count"] = 0
            summary["persona_ids"] = []
        return (payload or None), summary

    def _build_astrbot_conversion_environment(self, raw_config: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        payload: dict[str, Any] = {}
        summary: dict[str, Any] = {}

        subagent_orchestrator = raw_config.get("subagent_orchestrator")
        if isinstance(subagent_orchestrator, dict):
            normalized = self._sanitize_astrbot_conversion_value(
                deepcopy(subagent_orchestrator),
                path="environment_manifest.subagent_orchestrator",
            )
            agents = normalized.get("agents") if isinstance(normalized, dict) else None
            enabled_agents = []
            if isinstance(agents, list):
                for item in agents:
                    if not isinstance(item, dict):
                        continue
                    if not bool(item.get("enabled", False)):
                        continue
                    name = str(item.get("name", "") or item.get("id", "") or "").strip()
                    if name:
                        enabled_agents.append(name)
                normalized["enabled_agents"] = enabled_agents
            payload["subagent_orchestrator"] = normalized
            summary["subagent_count"] = len(enabled_agents)
            summary["subagent_ids"] = enabled_agents

        platform = raw_config.get("platform")
        if isinstance(platform, list):
            normalized_platform = self._sanitize_astrbot_conversion_value(
                deepcopy(platform),
                path="environment_manifest.platform",
            )
            payload["platform"] = normalized_platform
            summary["platform_count"] = len(normalized_platform)

        provider_sources = raw_config.get("provider_sources")
        if isinstance(provider_sources, list):
            normalized_sources = self._sanitize_astrbot_conversion_value(
                deepcopy(provider_sources),
                path="environment_manifest.provider_sources",
            )
            payload["provider_sources"] = normalized_sources
            summary["provider_source_count"] = len(normalized_sources)

        return (payload or None), summary

    def _build_astrbot_conversion_summary(
        self,
        *,
        raw_config: dict[str, Any],
        personas_summary: dict[str, Any],
        environment_summary: dict[str, Any],
        plugins_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        summary.update(personas_summary)
        summary.update(environment_summary)
        if isinstance(plugins_payload, dict):
            summary["plugin_count"] = len(plugins_payload)
        provider_count = raw_config.get("provider")
        if isinstance(provider_count, list):
            summary["provider_count"] = len(provider_count)
        return summary

    def _sanitize_astrbot_conversion_value(self, value: Any, *, path: str) -> Any:
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key or "").strip()
                child_path = f"{path}.{key_text}" if path else key_text
                if self._astrbot_conversion_should_redact_key(key_text, child_path):
                    out[key_text] = self._astrbot_redacted_value(item)
                    continue
                out[key_text] = self._sanitize_astrbot_conversion_value(item, path=child_path)
            return out
        if isinstance(value, list):
            return [
                self._sanitize_astrbot_conversion_value(item, path=f"{path}[{index}]")
                for index, item in enumerate(value)
            ]
        return value

    @staticmethod
    def _astrbot_conversion_should_redact_key(key: str, path: str) -> bool:
        normalized_key = str(key or "").strip().lower()
        if not normalized_key:
            return False
        if ProfileRedactionService._is_sensitive_key(normalized_key):
            return True
        if normalized_key == "key":
            return True
        if normalized_key.endswith("_key"):
            return True
        return normalized_key == "jwt_secret"

    @staticmethod
    def _astrbot_redacted_value(value: Any) -> Any:
        if isinstance(value, list):
            return ["***REDACTED***"] if value else []
        if isinstance(value, dict):
            return "***REDACTED***"
        return "***REDACTED***"

    def _build_profile_pack_archive_bytes(
        self,
        *,
        manifest: BotProfilePackManifest,
        sections: dict[str, Any],
    ) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2))
            for section_name, payload in sections.items():
                zf.writestr(
                    BotProfilePackManifest.hash_key(section_name),
                    json.dumps(payload, ensure_ascii=False, indent=2),
                )
        return buffer.getvalue()

    def _astrbot_conversion_pack_id(
        self,
        *,
        filename: str,
        source_sha256: str,
        raw_config: dict[str, Any],
    ) -> str:
        basename = Path(filename or "").stem
        descriptor = self._astrbot_conversion_descriptor(raw_config=raw_config, fallback=basename or "astrbot-import")
        slug = self._official_record_slug(descriptor, source_sha256[:8])
        return f"profile/imported-{slug}"

    def _astrbot_conversion_descriptor(self, *, raw_config: dict[str, Any], fallback: str) -> str:
        provider_settings = raw_config.get("provider_settings")
        if isinstance(provider_settings, dict):
            default_personality = str(provider_settings.get("default_personality", "") or "").strip()
            if default_personality:
                return default_personality
        default_personality = str(raw_config.get("default_personality", "") or "").strip()
        if default_personality:
            return default_personality
        raw_personas = raw_config.get("persona")
        if isinstance(raw_personas, list):
            for item in raw_personas:
                if isinstance(item, dict):
                    name = str(item.get("name", "") or item.get("id", "") or "").strip()
                    if name:
                        return name
                else:
                    text = str(item or "").strip()
                    if text:
                        return text
        subagent_orchestrator = raw_config.get("subagent_orchestrator")
        if isinstance(subagent_orchestrator, dict):
            agents = subagent_orchestrator.get("agents")
            if isinstance(agents, list):
                for item in agents:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name", "") or item.get("id", "") or "").strip()
                    if name:
                        return name
        return str(fallback or "astrbot-import").strip() or "astrbot-import"

    @staticmethod
    def _astrbot_conversion_version(*, source_sha256: str) -> str:
        return f"0.1.0-converted-{source_sha256[:8]}"

    @staticmethod
    def _dedupe_issue_codes(values: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in values:
            text = str(item or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
        return out

    def _embedded_profile_pack_issues(self, sections: dict[str, Any]) -> list[str]:
        meta = sections.get("sharelife_meta")
        if not isinstance(meta, dict):
            return []
        astrbot_import = meta.get("astrbot_import")
        if not isinstance(astrbot_import, dict):
            return []
        raw_issues = astrbot_import.get("issues")
        if not isinstance(raw_issues, list):
            return []
        return self._dedupe_issue_codes([str(item or "").strip() for item in raw_issues])

    def get_import_record(self, import_id: str) -> ImportedProfilePack:
        record = self._imports.get(str(import_id or "").strip())
        if record is None:
            raise ValueError("PROFILE_IMPORT_NOT_FOUND")
        return record

    def delete_import(self, *, user_id: str, import_id: str) -> ImportedProfilePack:
        imported = self.get_import_record(import_id)
        normalized_user_id = str(user_id or "").strip()
        if not normalized_user_id or str(imported.user_id or "").strip() != normalized_user_id:
            raise ValueError("PROFILE_PACK_ARTIFACT_PERMISSION_DENIED")
        if not self._can_delete_import(imported):
            raise ValueError("PROFILE_IMPORT_IN_USE")
        self._delete_import_record(imported)
        self._flush_state()
        return imported

    def _refresh_member_imports(
        self,
        *,
        user_id: str,
        import_origin: str,
        source_fingerprint: str,
    ) -> None:
        normalized_user_id = str(user_id or "").strip()
        normalized_origin = str(import_origin or "").strip()
        normalized_fingerprint = str(source_fingerprint or "").strip()
        if not normalized_user_id or not normalized_origin or not normalized_fingerprint:
            return
        changed = False
        for imported in list(self._imports.values()):
            if str(imported.user_id or "").strip() != normalized_user_id:
                continue
            if str(imported.import_origin or "").strip() != normalized_origin:
                continue
            if str(imported.source_fingerprint or "").strip() != normalized_fingerprint:
                continue
            if not self._can_delete_import(imported):
                continue
            self._delete_import_record(imported)
            changed = True
        if changed:
            self._flush_state()

    def _can_delete_import(self, imported: ImportedProfilePack) -> bool:
        normalized_import_id = str(imported.import_id or "").strip()
        normalized_artifact_id = str(imported.source_artifact_id or "").strip()
        for submission in self._submissions.values():
            if normalized_import_id and str(submission.import_id or "").strip() == normalized_import_id:
                return False
            if normalized_artifact_id and str(submission.artifact_id or "").strip() == normalized_artifact_id:
                return False
        return True

    def _delete_import_record(self, imported: ImportedProfilePack) -> None:
        normalized_import_id = str(imported.import_id or "").strip()
        normalized_artifact_id = str(imported.source_artifact_id or "").strip()
        if normalized_import_id:
            self._imports.pop(normalized_import_id, None)
            self._plugin_install_confirmations.pop(normalized_import_id, None)
            self._plugin_install_executions.pop(normalized_import_id, None)
        if normalized_artifact_id:
            artifact = self._artifacts.pop(normalized_artifact_id, None)
            if artifact is not None:
                try:
                    if artifact.path.exists():
                        artifact.path.unlink()
                except OSError:
                    pass

    def _import_summary(self, imported: ImportedProfilePack) -> dict[str, Any]:
        meta = imported.sections.get("sharelife_meta")
        if not isinstance(meta, dict):
            return {}
        astrbot_import = meta.get("astrbot_import")
        if not isinstance(astrbot_import, dict):
            return {}
        summary = astrbot_import.get("summary")
        if not isinstance(summary, dict):
            return {}
        return dict(summary)

    def build_import_selection_tree(self, imported: ImportedProfilePack) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for section_name in imported.manifest.sections:
            payload = imported.sections.get(section_name)
            if payload is None:
                continue
            items = self._build_selection_items_for_section(section_name, payload)
            preview_lines, preview_truncated = self._selection_preview_lines(payload)
            out.append(
                {
                    "name": section_name,
                    "label": self._humanize_key(section_name),
                    "path": section_name,
                    "kind": self._selection_kind(payload),
                    "items": items,
                    "preview_lines": preview_lines,
                    "preview_truncated": preview_truncated,
                }
            )
        return out

    def _build_selection_items_for_section(self, section_name: str, payload: Any) -> list[dict[str, Any]]:
        if section_name == "personas" and isinstance(payload, dict):
            return self._build_personas_selection_items(payload)
        if section_name == "environment_manifest" and isinstance(payload, dict):
            return self._build_environment_selection_items(payload)
        if section_name == "astrbot_core" and isinstance(payload, dict):
            return self._build_astrbot_core_selection_items(payload)
        if section_name == "providers" and isinstance(payload, dict):
            return [
                self._build_nested_selection_item(
                    path=f"providers.{provider_id}",
                    label=str(provider_id or "").strip() or "Provider",
                    value=provider_payload,
                    max_depth=2,
                )
                for provider_id, provider_payload in payload.items()
            ]
        if section_name == "plugins" and isinstance(payload, dict):
            return [
                self._build_nested_selection_item(
                    path=f"plugins.{plugin_id}",
                    label=str(plugin_id or "").strip() or "Plugin",
                    value=plugin_payload,
                    max_depth=2,
                )
                for plugin_id, plugin_payload in payload.items()
            ]
        if section_name == "sharelife_meta":
            return []
        return self._build_generic_section_selection_items(section_name, payload)

    def _build_personas_selection_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        runtime = payload.get("runtime")
        if isinstance(runtime, dict) and runtime:
            items.append(
                self._selection_node(
                    path="personas.runtime",
                    label="Runtime Persona Settings",
                    kind="object",
                    value=runtime,
                    children=[
                        self._build_nested_selection_item(
                            path=f"personas.runtime.{key}",
                            label=self._humanize_key(str(key or "")),
                            value=value,
                            max_depth=SELECTION_TREE_MAX_DEPTH,
                        )
                        for key, value in runtime.items()
                    ],
                )
            )
        entries = payload.get("entries")
        if isinstance(entries, dict) and entries:
            items.append(
                self._selection_node(
                    path="personas.entries",
                    label="Persona Entries",
                    kind="object",
                    value=entries,
                    children=[
                        self._build_nested_selection_item(
                            path=f"personas.entries.{name}",
                            label=str(name or "").strip() or "Persona",
                            value=value,
                            max_depth=SELECTION_TREE_MAX_DEPTH,
                        )
                        for name, value in entries.items()
                    ],
                )
            )
        return items

    def _build_environment_selection_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for key, value in payload.items():
            key_text = str(key or "").strip()
            if not key_text:
                continue
            path = f"environment_manifest.{key_text}"
            if key_text == "subagent_orchestrator" and isinstance(value, dict):
                children: list[dict[str, Any]] = []
                for child_key, child_value in value.items():
                    if child_key == "enabled_agents":
                        continue
                    if child_key == "agents" and isinstance(child_value, list):
                        for index, item in enumerate(child_value):
                            children.append(
                                self._build_nested_selection_item(
                                    path=f"{path}.agents[{index}]",
                                    label=self._list_item_label(item, index, fallback_prefix="Agent"),
                                    value=item,
                                    max_depth=SELECTION_TREE_MAX_DEPTH,
                                )
                            )
                    else:
                        children.append(
                            self._build_nested_selection_item(
                                path=f"{path}.{child_key}",
                                label=self._humanize_key(str(child_key or "")),
                                value=child_value,
                                max_depth=SELECTION_TREE_MAX_DEPTH,
                            )
                        )
                items.append(
                    self._selection_node(
                        path=path,
                        label="Subagent Orchestrator",
                        kind="object",
                        value=value,
                        children=children,
                    )
                )
                continue
            if isinstance(value, list):
                children = [
                    self._build_nested_selection_item(
                        path=f"{path}[{index}]",
                        label=self._list_item_label(item, index, fallback_prefix=self._humanize_key(key_text)),
                        value=item,
                        max_depth=SELECTION_TREE_MAX_DEPTH,
                    )
                    for index, item in enumerate(value)
                ]
                items.append(
                    self._selection_node(
                        path=path,
                        label=self._humanize_key(key_text),
                        kind="list",
                        value=value,
                        children=children,
                    )
                )
                continue
            items.append(
                    self._build_nested_selection_item(
                        path=path,
                        label=self._humanize_key(key_text),
                        value=value,
                        max_depth=SELECTION_TREE_MAX_DEPTH,
                    )
                )
        return items

    def _build_astrbot_core_selection_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for key, value in payload.items():
            key_text = str(key or "").strip()
            if not key_text:
                continue
            path = f"astrbot_core.{key_text}"
            if key_text == "provider_settings" and isinstance(value, dict):
                children = [
                    self._build_nested_selection_item(
                        path=f"{path}.{child_key}",
                        label=self._humanize_key(str(child_key or "")),
                        value=child_value,
                        max_depth=SELECTION_TREE_MAX_DEPTH,
                    )
                    for child_key, child_value in value.items()
                ]
                items.append(
                    self._selection_node(
                        path=path,
                        label="Provider Settings",
                        kind="object",
                        value=value,
                        children=children,
                    )
                )
                continue
            items.append(
                self._build_nested_selection_item(
                    path=path,
                    label=self._humanize_key(key_text),
                    value=value,
                    max_depth=SELECTION_TREE_MAX_DEPTH,
                )
            )
        return items

    def _build_generic_section_selection_items(self, section_name: str, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, dict):
            return [
                self._build_nested_selection_item(
                    path=f"{section_name}.{key}",
                    label=self._humanize_key(str(key or "")),
                    value=value,
                    max_depth=SELECTION_TREE_MAX_DEPTH,
                )
                for key, value in payload.items()
            ]
        if isinstance(payload, list):
            return [
                self._build_nested_selection_item(
                    path=f"{section_name}[{index}]",
                    label=self._list_item_label(item, index, fallback_prefix=self._humanize_key(section_name)),
                    value=item,
                    max_depth=SELECTION_TREE_MAX_DEPTH,
                )
                for index, item in enumerate(payload)
            ]
        return []

    def _build_nested_selection_item(
        self,
        *,
        path: str,
        label: str,
        value: Any,
        max_depth: int,
        depth: int = 0,
    ) -> dict[str, Any]:
        if depth >= max_depth:
            return self._selection_leaf(
                path=path,
                label=label,
                kind=self._selection_kind(value),
                value=value,
            )

        if isinstance(value, dict):
            children = [
                self._build_nested_selection_item(
                    path=f"{path}.{key}",
                    label=self._humanize_key(str(key or "")),
                    value=nested,
                    max_depth=max_depth,
                    depth=depth + 1,
                )
                for key, nested in value.items()
                if str(key or "").strip()
            ]
            if children:
                return self._selection_node(
                    path=path,
                    label=label,
                    children=children,
                    kind="object",
                    value=value,
                )

        if isinstance(value, list):
            children = [
                self._build_nested_selection_item(
                    path=f"{path}[{index}]",
                    label=self._list_item_label(item, index, fallback_prefix=label),
                    value=item,
                    max_depth=max_depth,
                    depth=depth + 1,
                )
                for index, item in enumerate(value)
            ]
            if children:
                return self._selection_node(
                    path=path,
                    label=label,
                    children=children,
                    kind="list",
                    value=value,
                )

        return self._selection_leaf(path=path, label=label, kind=self._selection_kind(value), value=value)

    def _selection_leaf(
        self,
        *,
        path: str,
        label: str,
        kind: str = "scalar",
        value: Any = None,
    ) -> dict[str, Any]:
        preview_lines, preview_truncated = self._selection_preview_lines(value)
        return {
            "path": path,
            "label": label,
            "kind": kind,
            "children": [],
            "preview_lines": preview_lines,
            "preview_truncated": preview_truncated,
        }

    def _selection_node(
        self,
        *,
        path: str,
        label: str,
        children: list[dict[str, Any]],
        kind: str,
        value: Any,
    ) -> dict[str, Any]:
        preview_lines, preview_truncated = self._selection_preview_lines(value)
        return {
            "path": path,
            "label": label,
            "kind": kind,
            "children": children,
            "preview_lines": preview_lines,
            "preview_truncated": preview_truncated,
        }

    @staticmethod
    def _selection_preview_lines(value: Any) -> tuple[list[str], bool]:
        if value in (None, "", [], {}):
            return [], False
        if isinstance(value, str):
            lines = value.splitlines() or [value]
            if len(lines) <= 12:
                return lines, False
            return lines[:12], True
        if isinstance(value, (bool, int, float)):
            return [str(value)], False
        return ProfilePackService._json_preview_lines(value, limit=24)

    @staticmethod
    def _selection_kind(value: Any) -> str:
        if isinstance(value, dict):
            return "object"
        if isinstance(value, list):
            return "list"
        return "scalar"

    @staticmethod
    def _humanize_key(value: str) -> str:
        text = str(value or "").strip().replace("_", " ")
        if not text:
            return "Item"
        return " ".join(part.capitalize() for part in text.split())

    @staticmethod
    def _list_item_label(item: Any, index: int, *, fallback_prefix: str) -> str:
        if isinstance(item, dict):
            for key in ("name", "id", "type"):
                text = str(item.get(key, "") or "").strip()
                if text:
                    return text
        return f"{fallback_prefix} #{index + 1}"

    def profile_pack_plugin_install_plan(self, import_id: str) -> dict[str, Any]:
        imported = self.get_import_record(import_id)
        current_plugins = self._runtime_plugins_snapshot()
        target_plugins = imported.sections.get("plugins", {})
        candidates = self._plugin_install_candidates(
            target_plugins=target_plugins,
            current_plugins=current_plugins,
        )
        required_plugins = [item["plugin_id"] for item in candidates if item["install_required"]]
        confirmed_plugins = self._normalized_plugin_ids(
            self._plugin_install_confirmations.get(imported.import_id, [])
        )
        confirmed_set = set(confirmed_plugins)
        missing_plugins = [item for item in required_plugins if item not in confirmed_set]

        if not required_plugins:
            status = "not_required"
        elif missing_plugins:
            status = "confirmation_required"
        else:
            status = "confirmed"
        latest_execution = self._latest_plugin_install_execution(imported.import_id)
        execution_required = bool(required_plugins) and bool(
            self.plugin_install_service.require_success_before_apply
        )

        return {
            "import_id": imported.import_id,
            "pack_type": imported.manifest.pack_type,
            "pack_id": imported.manifest.pack_id,
            "status": status,
            "execution_required": execution_required,
            "confirmation_required": bool(missing_plugins),
            "required_plugins": required_plugins,
            "confirmed_plugins": [item for item in required_plugins if item in confirmed_set],
            "missing_plugins": missing_plugins,
            "candidates": candidates,
            "latest_execution": latest_execution,
        }

    def confirm_profile_pack_plugin_install(
        self,
        import_id: str,
        plugin_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        imported = self.get_import_record(import_id)
        plan = self.profile_pack_plugin_install_plan(imported.import_id)
        required = set(plan["required_plugins"])
        if not required:
            return plan

        to_confirm: set[str]
        if plugin_ids is None:
            to_confirm = set(required)
        else:
            normalized = self._normalized_plugin_ids(plugin_ids)
            if not normalized:
                raise ValueError("PROFILE_PACK_PLUGIN_ID_REQUIRED")
            to_confirm = set(normalized)
            invalid = sorted(to_confirm - required)
            if invalid:
                raise ValueError("PROFILE_PACK_PLUGIN_NOT_IN_INSTALL_PLAN")

        current = set(self._normalized_plugin_ids(self._plugin_install_confirmations.get(imported.import_id, [])))
        current.update(to_confirm)
        self._plugin_install_confirmations[imported.import_id] = sorted(current)
        self._flush_state()
        return self.profile_pack_plugin_install_plan(imported.import_id)

    def execute_profile_pack_plugin_install(
        self,
        import_id: str,
        *,
        plugin_ids: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        imported = self.get_import_record(import_id)
        plan = self.profile_pack_plugin_install_plan(imported.import_id)
        required_plugins = list(plan.get("required_plugins", []) or [])
        if not required_plugins:
            result = self._plugin_install_execution_result(
                imported=imported,
                plan=plan,
                execution_output={
                    "status": "not_required",
                    "dry_run": bool(dry_run),
                    "requested_plugins": self._normalized_plugin_ids(plugin_ids),
                    "executed_plugins": [],
                    "attempts": [],
                    "installed_count": 0,
                    "failed_count": 0,
                    "blocked_count": 0,
                },
                requested_plugins=self._normalized_plugin_ids(plugin_ids),
                dry_run=dry_run,
            )
            self._record_plugin_install_execution(imported.import_id, result["execution"])
            self._flush_state()
            return result
        if plan.get("confirmation_required"):
            raise ValueError("PROFILE_PACK_PLUGIN_INSTALL_CONFIRM_REQUIRED")

        requested_plugin_ids = (
            self._normalized_plugin_ids(plugin_ids) if plugin_ids is not None else list(required_plugins)
        )
        if plugin_ids is not None and not requested_plugin_ids:
            raise ValueError("PROFILE_PACK_PLUGIN_ID_REQUIRED")
        invalid = sorted(set(requested_plugin_ids) - set(required_plugins))
        if invalid:
            raise ValueError("PROFILE_PACK_PLUGIN_NOT_IN_INSTALL_PLAN")

        execution_output = self.plugin_install_service.execute(
            candidates=list(plan.get("candidates", []) or []),
            plugin_ids=requested_plugin_ids,
            dry_run=dry_run,
        )
        result = self._plugin_install_execution_result(
            imported=imported,
            plan=plan,
            execution_output=execution_output,
            requested_plugins=requested_plugin_ids,
            dry_run=dry_run,
        )
        self._record_plugin_install_execution(imported.import_id, result["execution"])
        self._flush_state()
        return result

    def prepare_apply_plan(
        self,
        import_id: str,
        plan_id: str,
        selected_sections: list[str] | None = None,
    ) -> dict[str, Any]:
        imported = self.get_import_record(import_id)
        if imported.compatibility == "blocked":
            raise ValueError("PROFILE_PACK_INCOMPATIBLE")

        requested_sections = selected_sections or list(imported.manifest.sections)
        normalized_sections = self.section_registry.normalize_sections(requested_sections)

        plugin_install = None
        if "plugins" in normalized_sections:
            plugin_install = self.profile_pack_plugin_install_plan(imported.import_id)
            if plugin_install.get("confirmation_required"):
                raise ValueError("PROFILE_PACK_PLUGIN_INSTALL_CONFIRM_REQUIRED")
            if (
                plugin_install.get("execution_required")
                and plugin_install.get("required_plugins")
            ):
                latest_execution = plugin_install.get("latest_execution") or {}
                latest_status = str(latest_execution.get("status", "") or "")
                if latest_status in {"executed", "not_required"}:
                    pass
                elif latest_status in {"partial_failed", "failed"}:
                    raise ValueError("PROFILE_PACK_PLUGIN_INSTALL_EXEC_FAILED")
                else:
                    raise ValueError("PROFILE_PACK_PLUGIN_INSTALL_EXEC_REQUIRED")

        target_sections = self._materialize_target_sections(
            imported=imported,
            selected_sections=normalized_sections,
        )

        current_snapshot = self.runtime.snapshot()
        current_sections = self.section_registry.capture(current_snapshot, selected_sections=normalized_sections)
        diff = self.diff_service.diff_sections(
            current_sections=current_sections,
            target_sections=target_sections,
        )

        patch = self.section_registry.build_patch(
            sections_payload=target_sections,
            selected_sections=normalized_sections,
        )
        registered = self.apply_service.register_plan(
            plan_id=plan_id,
            patch=patch,
            metadata={
                "actor_id": "admin",
                "actor_role": "admin",
                "source_id": str(imported.manifest.pack_id or imported.import_id or plan_id),
                "source_kind": "profile_pack",
                "selected_sections": normalized_sections,
                "recovery_class": "config_snapshot_restore",
            },
        )
        capability_summary = self._build_capability_summary(
            manifest=imported.manifest,
            sections=imported.sections,
        )
        compatibility_matrix = self._build_compatibility_matrix(
            manifest=imported.manifest,
            compatibility=imported.compatibility,
            compatibility_issues=imported.compatibility_issues,
        )
        review_evidence = self._build_review_evidence(
            scan_summary=imported.scan_summary,
            compatibility=imported.compatibility,
            compatibility_issues=imported.compatibility_issues,
            redaction_mode=imported.manifest.redaction_policy.mode,
            capability_summary=capability_summary,
        )
        return {
            "status": "dryrun_ready",
            "plan_id": registered.plan_id,
            "import_id": imported.import_id,
            "selected_sections": normalized_sections,
            "patch": patch,
            "diff": diff,
            "scan_summary": imported.scan_summary,
            "compatibility": imported.compatibility,
            "compatibility_issues": imported.compatibility_issues,
            "capability_summary": capability_summary,
            "compatibility_matrix": compatibility_matrix,
            "review_evidence": review_evidence,
            "featured": False,
            "featured_note": "",
            "plugin_install": plugin_install,
        }

    def list_imports(self, limit: int = 50, *, user_id: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit or 50), 200))
        normalized_user_id = str(user_id or "").strip()
        candidates = list(self._imports.values())
        if normalized_user_id:
            candidates = [item for item in candidates if str(item.user_id or "").strip() == normalized_user_id]
        candidates = [
            item
            for item in candidates
            if str(item.import_origin or "").strip() != "submission_materialized"
        ]
        rows = sorted(
            candidates,
            key=lambda item: item.imported_at,
            reverse=True,
        )[:bounded_limit]
        out: list[dict[str, Any]] = []
        for item in rows:
            out.append(
                {
                    "import_id": item.import_id,
                    "imported_at": item.imported_at,
                    "user_id": item.user_id,
                    "filename": item.filename,
                    "pack_type": item.manifest.pack_type,
                    "pack_id": item.manifest.pack_id,
                    "version": item.manifest.version,
                    "sections": list(item.manifest.sections),
                    "capabilities": list(item.manifest.capabilities),
                    "compatibility": item.compatibility,
                    "compatibility_issues": list(item.compatibility_issues),
                    "source_artifact_id": item.source_artifact_id,
                    "import_origin": item.import_origin,
                    "delete_allowed": self._can_delete_import(item),
                    "import_summary": self._import_summary(item),
                    "selection_tree": self.build_import_selection_tree(item),
                }
            )
        return out

    def list_exports(self, limit: int = 50) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit or 50), 200))
        rows = sorted(
            self._artifacts.values(),
            key=lambda item: item.exported_at,
            reverse=True,
        )[:bounded_limit]
        out: list[dict[str, Any]] = []
        for item in rows:
            out.append(
                {
                    "artifact_id": item.artifact_id,
                    "exported_at": item.exported_at,
                    "pack_type": item.manifest.pack_type,
                    "pack_id": item.pack_id,
                    "version": item.version,
                    "path": str(item.path),
                    "filename": item.filename,
                    "sha256": item.sha256,
                    "size_bytes": item.size_bytes,
                    "sections": list(item.manifest.sections),
                    "capabilities": list(item.manifest.capabilities),
                    "redaction_mode": item.manifest.redaction_policy.mode,
                }
            )
        return out

    def submit_export_artifact(
        self,
        user_id: str,
        artifact_id: str,
        *,
        submit_options: dict[str, Any] | None = None,
    ) -> ProfilePackSubmission:
        artifact = self.get_export_artifact(artifact_id=artifact_id)
        normalized_user_id = str(user_id or "").strip() or "member"
        if str(artifact.owner_user_id or "").strip() and artifact.owner_user_id != normalized_user_id:
            raise ValueError("PROFILE_PACK_ARTIFACT_PERMISSION_DENIED")
        if not artifact.path.exists():
            raise ValueError("PROFILE_PACK_ARTIFACT_NOT_FOUND")

        normalized_submit_options = dict(submit_options or {})
        imported = self.import_bot_profile_pack(
            filename=artifact.filename,
            content=artifact.path.read_bytes(),
        )
        selected_sections = self._resolve_submission_sections(
            manifest=imported.manifest,
            submit_options=normalized_submit_options,
        )
        selected_item_paths = self._normalize_selected_item_paths(
            normalized_submit_options.get("selected_item_paths"),
            selected_sections=selected_sections,
        )
        normalized_submit_options["selected_sections"] = list(selected_sections)
        normalized_submit_options["selected_item_paths"] = list(selected_item_paths)
        if self._requires_submission_materialization(
            manifest_sections=list(imported.manifest.sections),
            selected_sections=selected_sections,
            selected_item_paths=selected_item_paths,
        ):
            artifact, imported = self._materialize_submission_copy(
                source_artifact=artifact,
                imported=imported,
                user_id=normalized_user_id,
                selected_sections=selected_sections,
                selected_item_paths=selected_item_paths,
            )

        now = self.clock.utcnow().isoformat()
        scan_summary = dict(imported.scan_summary or {})
        capability_summary = self._build_capability_summary(
            manifest=imported.manifest,
            sections=imported.sections,
        )
        compatibility_matrix = self._build_compatibility_matrix(
            manifest=imported.manifest,
            compatibility=imported.compatibility,
            compatibility_issues=imported.compatibility_issues,
        )
        review_evidence = self._build_review_evidence(
            scan_summary=scan_summary,
            compatibility=imported.compatibility,
            compatibility_issues=imported.compatibility_issues,
            redaction_mode=imported.manifest.redaction_policy.mode,
            capability_summary=capability_summary,
        )
        submission = ProfilePackSubmission(
            submission_id=str(uuid4()),
            user_id=normalized_user_id,
            artifact_id=artifact.artifact_id,
            import_id=imported.import_id,
            pack_type=imported.manifest.pack_type,
            pack_id=artifact.pack_id,
            version=artifact.version,
            status=PROFILE_PACK_SUBMISSION_PENDING,
            created_at=now,
            updated_at=now,
            review_labels=list(scan_summary.get("review_labels", []) or []),
            warning_flags=list(scan_summary.get("warning_flags", []) or []),
            risk_level=str(scan_summary.get("risk_level", "low") or "low"),
            scan_summary=scan_summary,
            compatibility=imported.compatibility,
            compatibility_issues=list(imported.compatibility_issues),
            filename=artifact.filename,
            sha256=artifact.sha256,
            size_bytes=artifact.size_bytes,
            sections=list(imported.manifest.sections),
            redaction_mode=imported.manifest.redaction_policy.mode,
            capability_summary=capability_summary,
            compatibility_matrix=compatibility_matrix,
            review_evidence=review_evidence,
            submit_options=dict(normalized_submit_options),
        )
        self._submissions[submission.submission_id] = submission
        self._flush_state()
        return submission

    def _resolve_submission_sections(
        self,
        *,
        manifest: BotProfilePackManifest,
        submit_options: dict[str, Any],
    ) -> list[str]:
        requested_sections = submit_options.get("selected_sections")
        if isinstance(requested_sections, list):
            normalized_requested = [str(item or "").strip() for item in requested_sections if str(item or "").strip()]
        elif isinstance(requested_sections, str):
            normalized_requested = [item.strip() for item in requested_sections.split(",") if item.strip()]
        else:
            normalized_requested = []
        if not normalized_requested:
            return list(manifest.sections)
        return self._resolve_export_sections(
            pack_type=manifest.pack_type,
            requested_sections=normalized_requested,
        )

    def _normalize_selected_item_paths(
        self,
        value: Any,
        *,
        selected_sections: list[str] | None = None,
    ) -> list[str]:
        if isinstance(value, list):
            raw_items = [str(item or "").strip() for item in value]
        elif isinstance(value, str):
            raw_items = [item.strip() for item in value.split(",")]
        else:
            raw_items = []
        allowed_sections = set(selected_sections or [])
        out: list[str] = []
        seen: set[str] = set()
        for entry in raw_items:
            item = str(entry or "").strip()
            if not item:
                continue
            section = self._selection_root_section(item)
            if not section:
                raise ValueError("PROFILE_SECTION_ITEM_SELECTION_INVALID")
            if allowed_sections and section not in allowed_sections:
                raise ValueError("PROFILE_SECTION_ITEM_SELECTION_INVALID")
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    @staticmethod
    def _selection_root_section(path: str) -> str:
        text = str(path or "").strip()
        if not text:
            return ""
        segment = text.split(".", 1)[0]
        segment = segment.split("[", 1)[0]
        return segment

    @staticmethod
    def _requires_submission_materialization(
        *,
        manifest_sections: list[str],
        selected_sections: list[str],
        selected_item_paths: list[str],
    ) -> bool:
        if list(manifest_sections) != list(selected_sections):
            return True
        return bool(selected_item_paths)

    def _materialize_submission_copy(
        self,
        *,
        source_artifact: ProfilePackArtifact,
        imported: ImportedProfilePack,
        user_id: str,
        selected_sections: list[str],
        selected_item_paths: list[str],
    ) -> tuple[ProfilePackArtifact, ImportedProfilePack]:
        filtered_sections = self._materialize_target_sections(
            imported=imported,
            selected_sections=selected_sections,
            selected_item_paths=selected_item_paths or None,
        )
        created_at = self.clock.utcnow().isoformat()
        manifest = self._build_materialized_manifest(
            source_manifest=imported.manifest,
            sections=filtered_sections,
            created_at=created_at,
        )
        archive_bytes = self._build_profile_pack_archive_bytes(
            manifest=manifest,
            sections=filtered_sections,
        )
        artifact_id = str(uuid4())
        output_dir = self.output_root / "member-submissions"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = self._safe_filename(
            f"{manifest.pack_id.replace('/', '__')}-{manifest.version}-{artifact_id[:8]}-submission.zip"
        )
        path = output_dir / filename
        path.write_bytes(archive_bytes)
        artifact = ProfilePackArtifact(
            artifact_id=artifact_id,
            pack_id=manifest.pack_id,
            version=manifest.version,
            exported_at=created_at,
            path=path,
            filename=filename,
            sha256=hashlib.sha256(archive_bytes).hexdigest(),
            size_bytes=len(archive_bytes),
            manifest=manifest,
            redaction_notes=[],
            owner_user_id=str(user_id or "").strip(),
        )
        self._artifacts[artifact_id] = artifact

        scan_summary = self.scan_service.to_dict(
            self.scan_service.scan(
                self._scan_payload(manifest, filtered_sections),
                manifest=manifest,
            )
        )
        signature_issue = self._verify_signature_issue(manifest)
        compatibility, compatibility_issues = self._resolve_compatibility(
            manifest,
            sections=filtered_sections,
            hash_mismatches=[],
            signature_issue=signature_issue,
        )
        if compatibility == "compatible" and compatibility_issues:
            compatibility = "degraded"
        imported_record = ImportedProfilePack(
            import_id=str(uuid4()),
            imported_at=created_at,
            filename=filename,
            manifest=manifest,
            sections=filtered_sections,
            scan_summary=scan_summary,
            compatibility=compatibility,
            compatibility_issues=list(compatibility_issues),
            user_id=str(user_id or "").strip(),
            source_artifact_id=artifact_id,
            import_origin="submission_materialized",
            source_fingerprint=str(source_artifact.sha256 or "").strip(),
        )
        self._imports[imported_record.import_id] = imported_record
        self._flush_state()
        return artifact, imported_record

    def _build_materialized_manifest(
        self,
        *,
        source_manifest: BotProfilePackManifest,
        sections: dict[str, Any],
        created_at: str,
    ) -> BotProfilePackManifest:
        policy_payload = source_manifest.redaction_policy.model_dump()
        policy_payload["include_sections"] = list(sections.keys())
        manifest_payload: dict[str, Any] = {
            "pack_type": source_manifest.pack_type,
            "pack_id": source_manifest.pack_id,
            "version": source_manifest.version,
            "created_at": created_at,
            "astrbot_version": source_manifest.astrbot_version,
            "plugin_compat": source_manifest.plugin_compat,
            "sections": list(sections.keys()),
            "capabilities": self._infer_manifest_capabilities(
                sections=sections,
                pack_type=source_manifest.pack_type,
            ),
            "redaction_policy": policy_payload,
            "hashes": {
                BotProfilePackManifest.hash_key(section_name): self._hash_json(payload)
                for section_name, payload in sections.items()
            },
        }
        signature = self._build_signature(manifest_payload)
        if signature:
            manifest_payload["signature"] = signature
        return BotProfilePackManifest.model_validate(manifest_payload)

    @staticmethod
    def _build_profile_pack_archive_bytes(
        *,
        manifest: BotProfilePackManifest,
        sections: dict[str, Any],
    ) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2))
            for section_name, payload in sections.items():
                zf.writestr(
                    BotProfilePackManifest.hash_key(section_name),
                    json.dumps(payload, ensure_ascii=False, indent=2),
                )
        return buffer.getvalue()

    def replace_pending_submissions(
        self,
        *,
        user_id: str,
        pack_id: str,
        exclude_submission_id: str = "",
    ) -> list[str]:
        normalized_user_id = str(user_id or "").strip()
        normalized_pack_id = str(pack_id or "").strip()
        normalized_exclude = str(exclude_submission_id or "").strip()
        if not normalized_user_id or not normalized_pack_id:
            return []
        now = self.clock.utcnow().isoformat()
        replaced: list[str] = []
        for item in self._submissions.values():
            if item.submission_id == normalized_exclude:
                continue
            if item.user_id != normalized_user_id or item.pack_id != normalized_pack_id:
                continue
            if item.status != PROFILE_PACK_SUBMISSION_PENDING:
                continue
            item.status = PROFILE_PACK_SUBMISSION_REPLACED
            item.updated_at = now
            replaced.append(item.submission_id)
        if replaced:
            self._flush_state()
        return replaced

    def get_submission(self, submission_id: str) -> ProfilePackSubmission:
        record = self._submissions.get(str(submission_id or "").strip())
        if record is None:
            raise ValueError("PROFILE_PACK_SUBMISSION_NOT_FOUND")
        return record

    def withdraw_submission(
        self,
        *,
        user_id: str,
        submission_id: str,
    ) -> ProfilePackSubmission:
        submission = self.get_submission(submission_id=submission_id)
        normalized_user_id = str(user_id or "").strip()
        if not normalized_user_id or str(submission.user_id or "").strip() != normalized_user_id:
            raise ValueError("PROFILE_PACK_SUBMISSION_PERMISSION_DENIED")
        if submission.status == PROFILE_PACK_SUBMISSION_WITHDRAWN:
            return submission
        if submission.status != PROFILE_PACK_SUBMISSION_PENDING:
            raise ValueError("PROFILE_PACK_SUBMISSION_STATE_INVALID")
        submission.status = PROFILE_PACK_SUBMISSION_WITHDRAWN
        submission.updated_at = self.clock.utcnow().isoformat()
        self._flush_state()
        return submission

    def list_submissions(self, status: str = "") -> list[ProfilePackSubmission]:
        normalized_status = str(status or "").strip().lower()
        rows = list(self._submissions.values())
        if normalized_status:
            rows = [item for item in rows if item.status == normalized_status]
        return sorted(rows, key=lambda item: item.created_at, reverse=True)

    def decide_submission(
        self,
        submission_id: str,
        reviewer_id: str,
        decision: str,
        review_note: str = "",
        review_labels: list[str] | None = None,
    ) -> ProfilePackSubmission:
        submission = self.get_submission(submission_id=submission_id)
        if submission.status != PROFILE_PACK_SUBMISSION_PENDING:
            raise ValueError("PROFILE_PACK_SUBMISSION_STATE_INVALID")
        normalized = str(decision or "").strip().lower()
        if normalized not in {"approve", "approved", "reject", "rejected"}:
            raise ValueError("INVALID_PROFILE_PACK_SUBMISSION_DECISION")

        if review_note:
            submission.review_note = review_note
        if review_labels is not None:
            submission.review_labels = list(review_labels)
        submission.reviewer_id = str(reviewer_id or "").strip() or "admin"
        submission.updated_at = self.clock.utcnow().isoformat()
        submission.status = (
            PROFILE_PACK_SUBMISSION_APPROVED
            if normalized.startswith("approve")
            else PROFILE_PACK_SUBMISSION_REJECTED
        )

        if submission.status == PROFILE_PACK_SUBMISSION_APPROVED:
            existing = self._published.get(submission.pack_id)
            self._published[submission.pack_id] = PublishedProfilePack(
                pack_type=submission.pack_type,
                pack_id=submission.pack_id,
                version=submission.version,
                source_submission_id=submission.submission_id,
                artifact_id=submission.artifact_id,
                import_id=submission.import_id,
                published_at=submission.updated_at,
                review_note=submission.review_note,
                review_labels=list(submission.review_labels),
                warning_flags=list(submission.warning_flags),
                risk_level=submission.risk_level,
                scan_summary=dict(submission.scan_summary),
                compatibility=submission.compatibility,
                compatibility_issues=list(submission.compatibility_issues),
                filename=submission.filename,
                sha256=submission.sha256,
                size_bytes=submission.size_bytes,
                sections=list(submission.sections),
                redaction_mode=submission.redaction_mode,
                capability_summary=dict(submission.capability_summary),
                compatibility_matrix=dict(submission.compatibility_matrix),
                review_evidence=dict(submission.review_evidence),
                featured=bool(existing.featured) if existing else False,
                featured_note=str(existing.featured_note) if existing else "",
                featured_by=str(existing.featured_by) if existing else "",
                featured_at=str(existing.featured_at) if existing else "",
            )
        else:
            self._published.pop(submission.pack_id, None)

        self._flush_state()
        return submission

    def list_published_packs(self) -> list[PublishedProfilePack]:
        return sorted(self._published.values(), key=lambda item: item.pack_id)

    def get_published_pack(self, pack_id: str) -> PublishedProfilePack | None:
        return self._published.get(str(pack_id or "").strip())

    def set_published_featured(
        self,
        *,
        pack_id: str,
        reviewer_id: str,
        featured: bool,
        note: str = "",
    ) -> PublishedProfilePack:
        record = self.get_published_pack(pack_id=pack_id)
        if record is None:
            raise ValueError("PROFILE_PACK_NOT_PUBLISHED")
        record.featured = bool(featured)
        record.featured_note = str(note or "").strip()
        record.featured_by = str(reviewer_id or "").strip() or "admin"
        record.featured_at = self.clock.utcnow().isoformat() if record.featured else ""
        self._flush_state()
        return record

    def publish_official_pack(
        self,
        *,
        pack_id: str,
        version: str,
        sections: dict[str, Any],
        pack_type: str = PROFILE_PACK_TYPE,
        review_note: str = "Bundled official profile-pack baseline.",
        reviewer_id: str = "official:sharelife",
        featured: bool = True,
        featured_note: str = "Official reference profile-pack.",
    ) -> PublishedProfilePack:
        normalized_pack_id = str(pack_id or "").strip()
        normalized_version = str(version or "").strip()
        if not normalized_pack_id or not normalized_version:
            raise ValueError("PROFILE_PACK_ID_VERSION_REQUIRED")
        if not isinstance(sections, dict) or not sections:
            raise ValueError("PROFILE_SECTION_SELECTION_EMPTY")

        normalized_pack_type = self._normalize_pack_type(pack_type)
        selected_sections = self._resolve_export_sections(
            pack_type=normalized_pack_type,
            requested_sections=list(sections.keys()),
        )
        materialized_sections: dict[str, Any] = {}
        for section_name in selected_sections:
            if section_name not in sections:
                raise ValueError("PROFILE_SECTION_PAYLOAD_MISSING")
            materialized_sections[section_name] = json.loads(
                json.dumps(sections[section_name], ensure_ascii=False)
            )

        policy = RedactionPolicy.model_validate(
            {"mode": "exclude_secrets", "include_sections": selected_sections}
        )
        created_at = self.clock.utcnow().isoformat()
        manifest_payload: dict[str, Any] = {
            "pack_type": normalized_pack_type,
            "pack_id": normalized_pack_id,
            "version": normalized_version,
            "created_at": created_at,
            "astrbot_version": self.astrbot_version or "any",
            "plugin_compat": self.plugin_version or "any",
            "sections": list(materialized_sections.keys()),
            "capabilities": self._infer_manifest_capabilities(
                sections=materialized_sections,
                pack_type=normalized_pack_type,
            ),
            "redaction_policy": policy.model_dump(),
            "hashes": {
                BotProfilePackManifest.hash_key(section_name): self._hash_json(payload)
                for section_name, payload in materialized_sections.items()
            },
        }
        signature = self._build_signature(manifest_payload)
        if signature:
            manifest_payload["signature"] = signature
        manifest = BotProfilePackManifest.model_validate(manifest_payload)

        record_slug = self._official_record_slug(normalized_pack_id, normalized_version)
        artifact_id = f"official-artifact:{record_slug}"
        import_id = f"official-import:{record_slug}"
        submission_id = f"official:{record_slug}"

        output_dir = self.output_root / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = self._safe_filename(
            f"{normalized_pack_id.replace('/', '__')}-{normalized_version}-official.zip"
        )
        path = output_dir / filename
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2))
            for section_name, payload in materialized_sections.items():
                zf.writestr(
                    BotProfilePackManifest.hash_key(section_name),
                    json.dumps(payload, ensure_ascii=False, indent=2),
                )
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        size_bytes = path.stat().st_size

        artifact = ProfilePackArtifact(
            artifact_id=artifact_id,
            pack_id=normalized_pack_id,
            version=normalized_version,
            exported_at=created_at,
            path=path,
            filename=filename,
            sha256=sha256,
            size_bytes=size_bytes,
            manifest=manifest,
            redaction_notes=[],
        )
        self._artifacts[artifact_id] = artifact

        scan_summary = self.scan_service.to_dict(
            self.scan_service.scan(
                self._scan_payload(manifest, materialized_sections),
                manifest=manifest,
            )
        )
        signature_issue = self._verify_signature_issue(manifest)
        compatibility, compatibility_issues = self._resolve_compatibility(
            manifest,
            sections=materialized_sections,
            hash_mismatches=[],
            signature_issue=signature_issue,
        )
        imported = ImportedProfilePack(
            import_id=import_id,
            imported_at=created_at,
            filename=filename,
            manifest=manifest,
            sections=materialized_sections,
            scan_summary=scan_summary,
            compatibility=compatibility,
            compatibility_issues=compatibility_issues,
        )
        self._imports[import_id] = imported

        capability_summary = self._build_capability_summary(
            manifest=manifest,
            sections=materialized_sections,
        )
        compatibility_matrix = self._build_compatibility_matrix(
            manifest=manifest,
            compatibility=compatibility,
            compatibility_issues=compatibility_issues,
        )
        review_evidence = self._build_review_evidence(
            scan_summary=scan_summary,
            compatibility=compatibility,
            compatibility_issues=compatibility_issues,
            redaction_mode=policy.mode,
            capability_summary=capability_summary,
        )
        review_labels = sorted(
            set(["official_profile_pack", *(scan_summary.get("review_labels", []) or [])])
        )
        warning_flags = sorted(set(scan_summary.get("warning_flags", []) or []))
        risk_level = str(scan_summary.get("risk_level", "low") or "low")

        submission = ProfilePackSubmission(
            submission_id=submission_id,
            user_id="official:sharelife",
            artifact_id=artifact_id,
            import_id=import_id,
            pack_type=normalized_pack_type,
            pack_id=normalized_pack_id,
            version=normalized_version,
            status=PROFILE_PACK_SUBMISSION_APPROVED,
            created_at=created_at,
            updated_at=created_at,
            reviewer_id=str(reviewer_id or "").strip() or "official:sharelife",
            review_note=str(review_note or "").strip(),
            review_labels=review_labels,
            warning_flags=warning_flags,
            risk_level=risk_level,
            scan_summary=scan_summary,
            compatibility=compatibility,
            compatibility_issues=list(compatibility_issues),
            filename=filename,
            sha256=sha256,
            size_bytes=size_bytes,
            sections=list(manifest.sections),
            redaction_mode=policy.mode,
            capability_summary=capability_summary,
            compatibility_matrix=compatibility_matrix,
            review_evidence=review_evidence,
        )
        self._submissions[submission_id] = submission
        self._published[normalized_pack_id] = PublishedProfilePack(
            pack_type=normalized_pack_type,
            pack_id=normalized_pack_id,
            version=normalized_version,
            source_submission_id=submission_id,
            artifact_id=artifact_id,
            import_id=import_id,
            published_at=created_at,
            review_note=submission.review_note,
            review_labels=list(review_labels),
            warning_flags=list(warning_flags),
            risk_level=risk_level,
            scan_summary=dict(scan_summary),
            compatibility=compatibility,
            compatibility_issues=list(compatibility_issues),
            filename=filename,
            sha256=sha256,
            size_bytes=size_bytes,
            sections=list(manifest.sections),
            redaction_mode=policy.mode,
            capability_summary=dict(capability_summary),
            compatibility_matrix=dict(compatibility_matrix),
            review_evidence=dict(review_evidence),
            featured=bool(featured),
            featured_note=str(featured_note or "").strip(),
            featured_by=str(reviewer_id or "").strip() or "official:sharelife",
            featured_at=created_at if featured else "",
        )
        self._flush_state()
        return self._published[normalized_pack_id]

    def preview_published_pack_compare(
        self,
        *,
        pack_id: str,
        selected_sections: list[str] | None = None,
    ) -> dict[str, Any]:
        normalized_pack_id = str(pack_id or "").strip()
        if not normalized_pack_id:
            raise ValueError("PACK_ID_REQUIRED")

        published = self.get_published_pack(pack_id=normalized_pack_id)
        if published is None:
            raise ValueError("PROFILE_PACK_NOT_PUBLISHED")

        imported = self.get_import_record(published.import_id)
        if imported.compatibility == "blocked":
            raise ValueError("PROFILE_PACK_INCOMPATIBLE")

        requested_sections = selected_sections or list(imported.manifest.sections)
        normalized_sections = self.section_registry.normalize_sections(requested_sections)

        plugin_install = None
        if "plugins" in normalized_sections:
            plugin_install = self.profile_pack_plugin_install_plan(imported.import_id)

        target_sections = self._materialize_target_sections(
            imported=imported,
            selected_sections=normalized_sections,
        )

        current_snapshot = self.runtime.snapshot()
        current_sections = self.section_registry.capture(
            current_snapshot,
            selected_sections=normalized_sections,
        )
        diff = self.diff_service.diff_sections(
            current_sections=current_sections,
            target_sections=target_sections,
        )
        diff = self._normalize_compare_diff_payload(
            diff=diff,
            current_sections=current_sections,
            target_sections=target_sections,
            selected_sections=normalized_sections,
        )
        changed_sections = list(diff.get("changed_sections", []) or [])

        return {
            "status": "compare_ready",
            "pack_id": published.pack_id,
            "pack_type": published.pack_type,
            "version": published.version,
            "import_id": imported.import_id,
            "source_submission_id": published.source_submission_id,
            "selected_sections": normalized_sections,
            "changed_sections": changed_sections,
            "changed_sections_count": len(changed_sections),
            "diff": diff,
            "scan_summary": imported.scan_summary,
            "compatibility": imported.compatibility,
            "compatibility_issues": imported.compatibility_issues,
            "capability_summary": dict(published.capability_summary),
            "compatibility_matrix": dict(published.compatibility_matrix),
            "review_evidence": dict(published.review_evidence),
            "featured": published.featured,
            "featured_note": published.featured_note,
            "plugin_install": plugin_install,
        }

    def _normalize_compare_diff_payload(
        self,
        *,
        diff: dict[str, Any] | None,
        current_sections: dict[str, Any],
        target_sections: dict[str, Any],
        selected_sections: list[str],
    ) -> dict[str, Any]:
        source = dict(diff or {})
        section_rows = source.get("sections")
        rows = section_rows if isinstance(section_rows, list) else []

        row_by_section: dict[str, dict[str, Any]] = {}
        row_order: list[str] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            section = str(item.get("section", "") or "").strip()
            if not section:
                continue
            row_by_section[section] = dict(item)
            row_order.append(section)

        ordered_sections = list(
            dict.fromkeys(
                [
                    *(selected_sections or []),
                    *row_order,
                    *list(current_sections.keys()),
                    *list(target_sections.keys()),
                ]
            )
        )

        normalized_rows: list[dict[str, Any]] = []
        changed_sections: list[str] = []
        for section in ordered_sections:
            base = row_by_section.get(section, {})
            before = current_sections.get(section)
            after = target_sections.get(section)
            changed = bool(base.get("changed", before != after))
            file_path = str(base.get("file_path", "") or "").strip() or f"sections/{section}.json"

            changed_paths_preview = self._normalize_string_list(base.get("changed_paths_preview"))
            if changed and not changed_paths_preview:
                changed_paths_preview = [file_path]
            changed_paths_count = self._to_int(
                base.get("changed_paths_count"),
                default=len(changed_paths_preview),
            )
            if not changed:
                changed_paths_count = 0

            before_preview = self._normalize_string_list(base.get("before_preview"))
            before_preview_truncated = bool(base.get("before_preview_truncated"))
            if changed and not before_preview:
                before_preview, before_preview_truncated = self._json_preview_lines(before)

            after_preview = self._normalize_string_list(base.get("after_preview"))
            after_preview_truncated = bool(base.get("after_preview_truncated"))
            if changed and not after_preview:
                after_preview, after_preview_truncated = self._json_preview_lines(after)

            diff_preview = self._normalize_string_list(base.get("diff_preview"))
            diff_preview_truncated = bool(base.get("diff_preview_truncated"))
            if changed and not diff_preview:
                diff_preview, diff_preview_truncated = self._unified_diff_preview_lines(
                    before_lines=before_preview,
                    after_lines=after_preview,
                    section_name=section,
                )

            normalized_row = {
                "section": section,
                "changed": changed,
                "before_hash": str(base.get("before_hash", "") or self._hash_json(before)),
                "after_hash": str(base.get("after_hash", "") or self._hash_json(after)),
                "before_size": self._to_int(base.get("before_size"), default=self._json_size(before)),
                "after_size": self._to_int(base.get("after_size"), default=self._json_size(after)),
                "file_path": file_path,
                "changed_paths_preview": changed_paths_preview if changed else [],
                "changed_paths_count": max(changed_paths_count, len(changed_paths_preview)) if changed else 0,
                "changed_paths_truncated": bool(changed and base.get("changed_paths_truncated", False)),
                "before_preview": before_preview if changed else [],
                "after_preview": after_preview if changed else [],
                "before_preview_truncated": bool(changed and before_preview_truncated),
                "after_preview_truncated": bool(changed and after_preview_truncated),
                "diff_preview": diff_preview if changed else [],
                "diff_preview_truncated": bool(changed and diff_preview_truncated),
            }
            normalized_rows.append(normalized_row)
            if changed:
                changed_sections.append(section)

        source["sections"] = normalized_rows
        source["changed_sections"] = changed_sections
        return source

    @staticmethod
    def _normalize_string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        out: list[str] = []
        for item in value:
            text = str(item or "").strip()
            if text:
                out.append(text)
        return out

    @staticmethod
    def _to_int(value: Any, *, default: int) -> int:
        try:
            return int(value)
        except Exception:
            return int(default)

    @staticmethod
    def _json_size(value: Any) -> int:
        return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

    @staticmethod
    def _json_preview_lines(value: Any, *, limit: int = 180) -> tuple[list[str], bool]:
        lines = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).splitlines()
        if len(lines) <= limit:
            return lines, False
        return lines[:limit], True

    @staticmethod
    def _unified_diff_preview_lines(
        *,
        before_lines: list[str],
        after_lines: list[str],
        section_name: str,
        limit: int = 240,
    ) -> tuple[list[str], bool]:
        rows = list(
            difflib.unified_diff(
                before_lines,
                after_lines,
                fromfile=f"before/{section_name}.json",
                tofile=f"after/{section_name}.json",
                lineterm="",
                n=2,
            )
        )
        if len(rows) <= limit:
            return rows, False
        return rows[:limit], True

    @staticmethod
    def _normalize_pack_type(pack_type: str) -> str:
        normalized = str(pack_type or PROFILE_PACK_TYPE).strip()
        if not normalized:
            normalized = PROFILE_PACK_TYPE
        if normalized not in PROFILE_PACK_TYPES:
            raise ValueError("PROFILE_PACK_TYPE_UNSUPPORTED")
        return normalized

    def _resolve_export_sections(
        self,
        *,
        pack_type: str,
        requested_sections: list[str] | None,
    ) -> list[str]:
        if requested_sections is None or len(requested_sections) == 0:
            allowed = set(profile_allowed_sections_for_pack(pack_type))
            defaults = [item for item in self.section_registry.allowed_sections() if item in allowed]
            if not defaults:
                raise ValueError("PROFILE_SECTION_SELECTION_EMPTY")
            return defaults

        selected = self.section_registry.normalize_sections(requested_sections)
        allowed = set(profile_allowed_sections_for_pack(pack_type))
        invalid = [item for item in selected if item not in allowed]
        if invalid:
            raise ValueError("PROFILE_PACK_SECTION_NOT_ALLOWED_FOR_TYPE")
        return selected

    @staticmethod
    def _normalized_plugin_ids(plugin_ids: list[str] | None) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in plugin_ids or []:
            normalized = str(item or "").strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            out.append(normalized)
        return out

    def _plugin_install_execution_result(
        self,
        *,
        imported: ImportedProfilePack,
        plan: dict[str, Any],
        execution_output: dict[str, Any],
        requested_plugins: list[str],
        dry_run: bool,
    ) -> dict[str, Any]:
        execution = {
            "execution_id": str(uuid4()),
            "executed_at": self.clock.utcnow().isoformat(),
            "status": str(execution_output.get("status", "unknown") or "unknown"),
            "dry_run": bool(dry_run),
            "requested_plugins": list(requested_plugins),
            "result": dict(execution_output),
        }
        return {
            "status": execution["status"],
            "import_id": imported.import_id,
            "pack_type": imported.manifest.pack_type,
            "pack_id": imported.manifest.pack_id,
            "plan_status": str(plan.get("status", "unknown") or "unknown"),
            "required_plugins": list(plan.get("required_plugins", []) or []),
            "confirmed_plugins": list(plan.get("confirmed_plugins", []) or []),
            "missing_plugins": list(plan.get("missing_plugins", []) or []),
            "execution_required": bool(plan.get("execution_required", False)),
            "execution": execution,
        }

    def _record_plugin_install_execution(self, import_id: str, execution: dict[str, Any]) -> None:
        normalized_import_id = str(import_id or "").strip()
        if not normalized_import_id:
            return
        rows = list(self._plugin_install_executions.get(normalized_import_id, []))
        rows.append(dict(execution))
        self._plugin_install_executions[normalized_import_id] = rows[-20:]

    def _latest_plugin_install_execution(self, import_id: str) -> dict[str, Any] | None:
        normalized_import_id = str(import_id or "").strip()
        if not normalized_import_id:
            return None
        rows = self._plugin_install_executions.get(normalized_import_id, [])
        if not rows:
            return None
        latest = rows[-1]
        if not isinstance(latest, dict):
            return None
        return dict(latest)

    def _runtime_plugins_snapshot(self) -> dict[str, Any]:
        snapshot = self.runtime.snapshot()
        if not isinstance(snapshot, dict):
            return {}
        plugins = snapshot.get("plugins", {})
        if isinstance(plugins, dict):
            return plugins
        return {}

    @staticmethod
    def _plugin_install_candidates(
        *,
        target_plugins: Any,
        current_plugins: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not isinstance(target_plugins, dict):
            return []

        out: list[dict[str, Any]] = []
        for raw_plugin_id in sorted(target_plugins.keys()):
            plugin_id = str(raw_plugin_id or "").strip()
            if not plugin_id:
                continue
            payload = target_plugins.get(raw_plugin_id)
            info = payload if isinstance(payload, dict) else {}
            source = str(
                info.get("source")
                or info.get("repository")
                or info.get("repo")
                or info.get("package")
                or ""
            ).strip()
            version = str(info.get("version") or info.get("plugin_version") or "").strip()
            digest = str(info.get("hash") or info.get("sha256") or "").strip()
            install_cmd = str(info.get("install_cmd") or info.get("install_command") or "").strip()
            has_install_metadata = bool(source or version or digest or install_cmd)
            present_in_runtime = plugin_id in current_plugins
            install_required = bool(has_install_metadata and not present_in_runtime)
            source_risk = "high" if source.startswith("http://") else ("medium" if source else "low")

            out.append(
                {
                    "plugin_id": plugin_id,
                    "version": version,
                    "source": source,
                    "hash": digest,
                    "install_cmd": install_cmd,
                    "has_install_metadata": has_install_metadata,
                    "present_in_runtime": present_in_runtime,
                    "install_required": install_required,
                    "source_risk": source_risk,
                }
            )
        return out

    def _infer_manifest_capabilities(
        self,
        *,
        sections: dict[str, Any],
        pack_type: str,
    ) -> list[str]:
        inferred: set[str] = set()
        if pack_type in {"bot_profile_pack", "extension_pack"}:
            inferred.add("file.read")
            inferred.add("file.write")

        if "providers" in sections:
            inferred.add("provider.access")
        if "mcp_servers" in sections:
            inferred.add("mcp.invoke")
        if "memory_store" in sections:
            inferred.add("memory.export")
        if "conversation_history" in sections:
            inferred.add("conversation.export")
        if "knowledge_base" in sections:
            inferred.add("knowledge.export")
        if "environment_manifest" in sections:
            inferred.add("environment.reconfigure")

        plugins = sections.get("plugins", {})
        if isinstance(plugins, dict):
            candidates = self._plugin_install_candidates(
                target_plugins=plugins,
                current_plugins={},
            )
            if any(item.get("has_install_metadata") for item in candidates):
                inferred.add("command.exec")
                inferred.add("network.outbound")

        allowed = set(PROFILE_CAPABILITY_OPTIONS)
        return [item for item in sorted(inferred) if item in allowed]

    def _build_capability_summary(
        self,
        *,
        manifest: BotProfilePackManifest,
        sections: dict[str, Any],
    ) -> dict[str, Any]:
        declared = sorted(set(manifest.capabilities))
        derived = self._infer_manifest_capabilities(sections=sections, pack_type=manifest.pack_type)
        high_risk = [
            item
            for item in declared
            if item in {"network.outbound", "file.write", "command.exec", "provider.access", "mcp.invoke"}
        ]
        missing_declared = [item for item in derived if item not in declared]
        return {
            "declared": declared,
            "derived": derived,
            "high_risk_declared": high_risk,
            "missing_declared": missing_declared,
            "high_risk_count": len(high_risk),
        }

    @staticmethod
    def _build_compatibility_matrix(
        *,
        manifest: BotProfilePackManifest,
        compatibility: str,
        compatibility_issues: list[str],
    ) -> dict[str, Any]:
        return {
            "runtime_result": compatibility,
            "runtime_issues": list(compatibility_issues),
            "manifest": {
                "astrbot_version": manifest.astrbot_version,
                "plugin_compat": manifest.plugin_compat,
            },
        }

    @staticmethod
    def _build_review_evidence(
        *,
        scan_summary: dict[str, Any],
        compatibility: str,
        compatibility_issues: list[str],
        redaction_mode: str,
        capability_summary: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "risk_level": str(scan_summary.get("risk_level", "low") or "low"),
            "review_labels": list(scan_summary.get("review_labels", []) or []),
            "warning_flags": list(scan_summary.get("warning_flags", []) or []),
            "compatibility": compatibility,
            "compatibility_issues": list(compatibility_issues),
            "redaction_mode": redaction_mode,
            "capability_summary": capability_summary,
        }

    def _redact_sections(
        self,
        sections: dict[str, Any],
        mode: str,
        *,
        mask_paths: list[str] | None = None,
        drop_paths: list[str] | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        redacted: dict[str, Any] = {}
        notes: list[str] = []
        secret_transformer = None
        if mode == "include_encrypted_secrets":
            if not self.secrets_encryption_key:
                raise ValueError("PROFILE_PACK_ENCRYPTION_KEY_REQUIRED")
            secret_transformer = self._encrypt_secret_value
        for section_name, payload in sections.items():
            result = self.redaction_service.redact_section(
                section_name,
                payload,
                mode,
                mask_paths=mask_paths,
                drop_paths=drop_paths,
                secret_transformer=secret_transformer,
            )
            if result.dropped:
                notes.append(f"{section_name}:dropped")
                continue
            redacted[section_name] = result.payload
            for path in result.redacted_paths:
                notes.append(f"{path}:redacted")
        return redacted, notes

    def _resolve_compatibility(
        self,
        manifest: BotProfilePackManifest,
        *,
        sections: dict[str, Any],
        hash_mismatches: list[str],
        signature_issue: str | None = None,
    ) -> tuple[str, list[str]]:
        issues: list[str] = []
        if hash_mismatches:
            issues.append(f"section_hash_mismatch:{','.join(sorted(hash_mismatches))}")
        if signature_issue:
            issues.append(signature_issue)
        encrypted_secret_issue = self._encrypted_secret_issue(
            manifest=manifest,
            sections=sections,
        )
        if encrypted_secret_issue:
            issues.append(encrypted_secret_issue)
        if self.astrbot_version and manifest.astrbot_version and manifest.astrbot_version not in {
            self.astrbot_version,
            "any",
            "*",
        }:
            issues.append("astrbot_version_mismatch")
        if self.plugin_version and manifest.plugin_compat:
            if not self._version_satisfies(self.plugin_version, manifest.plugin_compat):
                issues.append("plugin_compat_mismatch")
        issues.extend(self._environment_reconfigure_issues(sections=sections))

        if any(
            item in {"astrbot_version_mismatch", "plugin_compat_mismatch"}
            or item.startswith("encrypted_secret")
            or item.startswith("signature_")
            for item in issues
        ):
            return "blocked", issues
        if issues:
            return "degraded", issues
        return "compatible", issues

    @staticmethod
    def _environment_reconfigure_issues(*, sections: dict[str, Any]) -> list[str]:
        out: list[str] = []
        environment_manifest = sections.get("environment_manifest")
        if isinstance(environment_manifest, dict):
            if environment_manifest.get("container_runtime") or environment_manifest.get(
                "requires_container_rebuild"
            ):
                out.append("environment_container_reconfigure_required")
            if environment_manifest.get("system_dependencies") or environment_manifest.get(
                "requires_system_dependencies"
            ):
                out.append("environment_system_dependencies_reconfigure_required")
            if environment_manifest.get("plugin_binaries") or environment_manifest.get(
                "requires_plugin_binaries"
            ):
                out.append("environment_plugin_binary_reconfigure_required")

        knowledge_base = sections.get("knowledge_base")
        if isinstance(knowledge_base, dict):
            if ProfilePackService._nested_has_any_key(
                knowledge_base,
                {"storage_path", "external_paths", "index_path", "vector_store_path"},
            ):
                out.append("knowledge_base_storage_sync_required")
        return out

    @staticmethod
    def _nested_has_any_key(value: Any, keys: set[str], depth: int = 0) -> bool:
        if depth > 8:
            return False
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key) in keys and nested not in (None, "", [], {}):
                    return True
                if ProfilePackService._nested_has_any_key(nested, keys, depth + 1):
                    return True
            return False
        if isinstance(value, list):
            for nested in value[:80]:
                if ProfilePackService._nested_has_any_key(nested, keys, depth + 1):
                    return True
        return False

    def _materialize_target_sections(
        self,
        *,
        imported: ImportedProfilePack,
        selected_sections: list[str],
        selected_item_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        mode = imported.manifest.redaction_policy.mode
        if mode == "include_encrypted_secrets" and not self.secrets_encryption_key:
            raise ValueError("PROFILE_PACK_ENCRYPTION_KEY_REQUIRED")

        normalized_item_paths = self._normalize_selected_item_paths(
            selected_item_paths,
            selected_sections=selected_sections,
        )
        paths_by_section: dict[str, list[str]] = {}
        for path in normalized_item_paths:
            section = self._selection_root_section(path)
            paths_by_section.setdefault(section, []).append(path)

        out: dict[str, Any] = {}
        for section_name in selected_sections:
            if section_name not in imported.sections:
                raise ValueError("PROFILE_SECTION_PAYLOAD_MISSING")
            payload = json.loads(json.dumps(imported.sections[section_name], ensure_ascii=False))
            if mode == "include_encrypted_secrets":
                payload = self._decrypt_section_secrets(payload, path=section_name)
            section_paths = paths_by_section.get(section_name, [])
            if section_paths and section_name not in section_paths:
                payload = self._select_payload_paths(
                    payload,
                    base_path=section_name,
                    selected_paths=section_paths,
                )
            out[section_name] = payload
        return out

    def _select_payload_paths(
        self,
        value: Any,
        *,
        base_path: str,
        selected_paths: list[str],
    ) -> Any:
        matched: set[str] = set()
        result = self._copy_selected_payload(
            value=value,
            current_path=base_path,
            selected_paths=set(selected_paths),
            matched_paths=matched,
        )
        if result in (None, {}, []):
            raise ValueError("PROFILE_SECTION_ITEM_SELECTION_INVALID")
        if matched != set(selected_paths):
            raise ValueError("PROFILE_SECTION_ITEM_SELECTION_INVALID")
        return result

    def _copy_selected_payload(
        self,
        *,
        value: Any,
        current_path: str,
        selected_paths: set[str],
        matched_paths: set[str],
    ) -> Any:
        if current_path in selected_paths:
            matched_paths.add(current_path)
            return json.loads(json.dumps(value, ensure_ascii=False))

        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, nested in value.items():
                child_path = f"{current_path}.{key}" if current_path else str(key)
                if not self._selection_path_may_match(child_path, selected_paths):
                    continue
                copied = self._copy_selected_payload(
                    value=nested,
                    current_path=child_path,
                    selected_paths=selected_paths,
                    matched_paths=matched_paths,
                )
                if copied not in (None, {}, []):
                    out[str(key)] = copied
            return out

        if isinstance(value, list):
            out: list[Any] = []
            for index, nested in enumerate(value):
                child_path = f"{current_path}[{index}]"
                if not self._selection_path_may_match(child_path, selected_paths):
                    continue
                copied = self._copy_selected_payload(
                    value=nested,
                    current_path=child_path,
                    selected_paths=selected_paths,
                    matched_paths=matched_paths,
                )
                if copied not in (None, {}, []):
                    out.append(copied)
            return out

        return None

    @staticmethod
    def _selection_path_may_match(current_path: str, selected_paths: set[str]) -> bool:
        for item in selected_paths:
            if item == current_path:
                return True
            if item.startswith(f"{current_path}."):
                return True
            if item.startswith(f"{current_path}["):
                return True
        return False

    def _encrypted_secret_issue(
        self,
        *,
        manifest: BotProfilePackManifest,
        sections: dict[str, Any],
    ) -> str | None:
        if manifest.redaction_policy.mode != "include_encrypted_secrets":
            return None
        if not self.secrets_encryption_key:
            return "encrypted_secrets_key_unavailable"

        for section_name, payload in sections.items():
            for path, value in self._iter_encrypted_secret_values(payload, path=section_name):
                try:
                    self._decrypt_secret_value(value, path)
                except ValueError:
                    return "encrypted_secret_payload_invalid"
        return None

    def _iter_encrypted_secret_values(self, value: Any, *, path: str):
        if isinstance(value, dict):
            for key, item in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if (
                    ProfileRedactionService._is_sensitive_key(key)
                    and isinstance(item, str)
                    and item.startswith("enc-v1:")
                ):
                    yield child_path, item
                yield from self._iter_encrypted_secret_values(item, path=child_path)
            return

        if isinstance(value, list):
            for index, item in enumerate(value):
                child_path = f"{path}[{index}]"
                yield from self._iter_encrypted_secret_values(item, path=child_path)

    def _decrypt_section_secrets(self, value: Any, *, path: str) -> Any:
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, item in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if (
                    ProfileRedactionService._is_sensitive_key(key)
                    and isinstance(item, str)
                    and item.startswith("enc-v1:")
                ):
                    out[key] = self._decrypt_secret_value(item, child_path)
                else:
                    out[key] = self._decrypt_section_secrets(item, path=child_path)
            return out

        if isinstance(value, list):
            return [
                self._decrypt_section_secrets(item, path=f"{path}[{index}]")
                for index, item in enumerate(value)
            ]

        return value

    @staticmethod
    def _version_satisfies(version: str, constraints: str) -> bool:
        text = str(constraints or "").strip()
        if not text or text in {"*", "any"}:
            return True

        version_tuple = ProfilePackService._version_tuple(version)
        if version_tuple is None:
            return False

        clauses = [item.strip() for item in text.split(",") if item.strip()]
        for clause in clauses:
            operator = ""
            raw_version = clause
            for token in (">=", "<=", "==", ">", "<", "="):
                if clause.startswith(token):
                    operator = token
                    raw_version = clause[len(token):].strip()
                    break
            target = ProfilePackService._version_tuple(raw_version)
            if target is None:
                return False

            if operator in {"=", "=="} and version_tuple != target:
                return False
            if operator == ">=" and version_tuple < target:
                return False
            if operator == "<=" and version_tuple > target:
                return False
            if operator == ">" and version_tuple <= target:
                return False
            if operator == "<" and version_tuple >= target:
                return False
            if operator == "" and version_tuple != target:
                return False
        return True

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int] | None:
        text = str(value or "").strip()
        if not text:
            return None
        parts = text.split(".")
        normalized: list[int] = []
        for item in parts[:3]:
            if not item.isdigit():
                return None
            normalized.append(int(item))
        while len(normalized) < 3:
            normalized.append(0)
        return tuple(normalized[:3])

    @staticmethod
    def _scan_payload(manifest: BotProfilePackManifest, sections: dict[str, Any]) -> dict[str, Any]:
        text_parts: list[str] = []
        scan_sources: list[dict[str, str]] = []
        for section_name, payload in sections.items():
            file_path = f"sections/{section_name}.json"
            serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            text_parts.append(f"[{section_name}]\n{serialized[:2000]}")
            ProfilePackService._append_scan_source(scan_sources, file_path, "$", serialized)
            ProfilePackService._collect_section_scan_sources(
                payload,
                file_path=file_path,
                path="$",
                sink=scan_sources,
                max_sources=200,
            )
        return {
            "pack_type": manifest.pack_type,
            "pack_id": manifest.pack_id,
            "version": manifest.version,
            "files": [BotProfilePackManifest.hash_key(name) for name in sections.keys()],
            "raw_text": "\n".join(text_parts)[:8000],
            "scan_sources": scan_sources[:200],
        }

    @staticmethod
    def _append_scan_source(
        sink: list[dict[str, str]],
        file_path: str,
        path: str,
        text: Any,
    ) -> None:
        snippet = str(text or "").strip()
        if not snippet:
            return
        sink.append(
            {
                "file": str(file_path or "payload"),
                "path": str(path or "$"),
                "text": snippet[:4000],
            }
        )

    @staticmethod
    def _collect_section_scan_sources(
        value: Any,
        *,
        file_path: str,
        path: str,
        sink: list[dict[str, str]],
        max_sources: int,
        depth: int = 0,
    ) -> None:
        if len(sink) >= max_sources or depth > 8:
            return
        if isinstance(value, str):
            ProfilePackService._append_scan_source(sink, file_path, path, value)
            return
        if isinstance(value, dict):
            for index, (key, nested) in enumerate(value.items()):
                if index >= 60 or len(sink) >= max_sources:
                    break
                key_text = str(key)
                if key_text.isidentifier():
                    nested_path = f"{path}.{key_text}" if path != "$" else f"$.{key_text}"
                else:
                    nested_path = f'{path}["{key_text}"]'
                ProfilePackService._collect_section_scan_sources(
                    nested,
                    file_path=file_path,
                    path=nested_path,
                    sink=sink,
                    max_sources=max_sources,
                    depth=depth + 1,
                )
            return
        if isinstance(value, list):
            for index, nested in enumerate(value[:40]):
                if len(sink) >= max_sources:
                    break
                ProfilePackService._collect_section_scan_sources(
                    nested,
                    file_path=file_path,
                    path=f"{path}[{index}]",
                    sink=sink,
                    max_sources=max_sources,
                    depth=depth + 1,
                )

    def _build_signature(self, manifest_payload: dict[str, Any]) -> dict[str, str] | None:
        if not self.signing_secret:
            return None
        return {
            "algorithm": "hmac-sha256",
            "key_id": self.signing_key_id,
            "value": self._manifest_signature_value(manifest_payload, self.signing_secret),
        }

    def _verify_signature_issue(self, manifest: BotProfilePackManifest) -> str | None:
        signature = manifest.signature
        if signature is None:
            return None
        if signature.algorithm != "hmac-sha256":
            return "signature_algorithm_unsupported"
        trusted_secret = str(self.trusted_signing_keys.get(signature.key_id, "") or "")
        if not trusted_secret:
            return "signature_untrusted_key"
        payload = manifest.model_dump(exclude={"signature"})
        expected = self._manifest_signature_value(payload, trusted_secret)
        if not hmac.compare_digest(expected, signature.value):
            return "signature_invalid"
        return None

    @staticmethod
    def _manifest_signature_value(manifest_payload: dict[str, Any], secret_key: str) -> str:
        encoded = json.dumps(
            manifest_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hmac.new(secret_key.encode("utf-8"), encoded, hashlib.sha256).hexdigest()

    def _encrypt_secret_value(self, value: Any, path: str) -> Any:
        if not self.secrets_encryption_key:
            return value
        if value is None:
            return value
        plaintext = str(value).encode("utf-8")
        nonce = secrets.token_bytes(8)
        key = hashlib.sha256(self.secrets_encryption_key.encode("utf-8")).digest()
        keystream = bytearray()
        counter = 0
        while len(keystream) < len(plaintext):
            block = hashlib.sha256(key + nonce + counter.to_bytes(4, "big")).digest()
            keystream.extend(block)
            counter += 1
        encrypted = bytes(
            source ^ mask
            for source, mask in zip(plaintext, keystream)
        )
        return f"enc-v1:{self._urlsafe_b64(nonce)}:{self._urlsafe_b64(encrypted)}"

    def _decrypt_secret_value(self, value: Any, path: str) -> Any:
        if not self.secrets_encryption_key:
            raise ValueError("PROFILE_PACK_ENCRYPTION_KEY_REQUIRED")
        text = str(value or "")
        if not text.startswith("enc-v1:"):
            return value

        try:
            _, nonce_token, encrypted_token = text.split(":", 2)
            nonce = self._urlsafe_b64_decode(nonce_token)
            encrypted = self._urlsafe_b64_decode(encrypted_token)
        except Exception as exc:
            raise ValueError("PROFILE_PACK_ENCRYPTED_SECRET_INVALID") from exc

        key = hashlib.sha256(self.secrets_encryption_key.encode("utf-8")).digest()
        keystream = bytearray()
        counter = 0
        while len(keystream) < len(encrypted):
            block = hashlib.sha256(key + nonce + counter.to_bytes(4, "big")).digest()
            keystream.extend(block)
            counter += 1
        plaintext = bytes(
            source ^ mask
            for source, mask in zip(encrypted, keystream)
        )
        try:
            return plaintext.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("PROFILE_PACK_ENCRYPTED_SECRET_INVALID") from exc

    @staticmethod
    def _urlsafe_b64(payload: bytes) -> str:
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def _urlsafe_b64_decode(value: str) -> bytes:
        text = str(value or "")
        if not text:
            return b""
        padding = "=" * (-len(text) % 4)
        return base64.urlsafe_b64decode(f"{text}{padding}")

    @staticmethod
    def _safe_filename(filename: str) -> str:
        return (
            Path(filename).name.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
            or "profile-pack.zip"
        )

    @staticmethod
    def _official_record_slug(pack_id: str, version: str) -> str:
        raw = f"{str(pack_id or '').strip()}-{str(version or '').strip()}"
        normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw).strip("-._")
        return normalized or "official-profile-pack"

    @staticmethod
    def _hash_json(payload: Any) -> str:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _load_state(self) -> None:
        if self.repository is None:
            return
        payload = self.repository.load_state()

        for item in payload.get("exports", []):
            try:
                manifest = BotProfilePackManifest.model_validate(item.get("manifest", {}))
                artifact = ProfilePackArtifact(
                    artifact_id=str(item.get("artifact_id", "")),
                    pack_id=str(item.get("pack_id", "") or manifest.pack_id),
                    version=str(item.get("version", "") or manifest.version),
                    exported_at=str(item.get("exported_at", "") or manifest.created_at),
                    path=Path(str(item.get("path", ""))),
                    filename=str(item.get("filename", "")),
                    sha256=str(item.get("sha256", "")),
                    size_bytes=int(item.get("size_bytes", 0) or 0),
                    manifest=manifest,
                    redaction_notes=list(item.get("redaction_notes", []) or []),
                    owner_user_id=str(item.get("owner_user_id", "") or ""),
                )
            except Exception:
                continue
            if artifact.artifact_id:
                self._artifacts[artifact.artifact_id] = artifact

        for item in payload.get("imports", []):
            try:
                manifest = BotProfilePackManifest.model_validate(item.get("manifest", {}))
                imported = ImportedProfilePack(
                    import_id=str(item.get("import_id", "")),
                    imported_at=str(item.get("imported_at", "") or manifest.created_at),
                    filename=str(item.get("filename", "")),
                    manifest=manifest,
                    sections=dict(item.get("sections", {}) or {}),
                    scan_summary=dict(item.get("scan_summary", {}) or {}),
                    compatibility=str(item.get("compatibility", "compatible") or "compatible"),
                    compatibility_issues=list(item.get("compatibility_issues", []) or []),
                    user_id=str(item.get("user_id", "") or ""),
                    source_artifact_id=str(item.get("source_artifact_id", "") or ""),
                    import_origin=str(item.get("import_origin", "") or ""),
                    source_fingerprint=str(item.get("source_fingerprint", "") or ""),
                )
            except Exception:
                continue
            if imported.import_id:
                self._imports[imported.import_id] = imported

        for item in payload.get("submissions", []):
            try:
                submission = ProfilePackSubmission(
                    submission_id=str(item.get("submission_id", "")),
                    user_id=str(item.get("user_id", "") or ""),
                    artifact_id=str(item.get("artifact_id", "") or ""),
                    import_id=str(item.get("import_id", "") or ""),
                    pack_type=self._normalize_pack_type(
                        str(item.get("pack_type", "") or PROFILE_PACK_TYPE)
                    ),
                    pack_id=str(item.get("pack_id", "") or ""),
                    version=str(item.get("version", "") or ""),
                    status=str(item.get("status", PROFILE_PACK_SUBMISSION_PENDING) or PROFILE_PACK_SUBMISSION_PENDING),
                    created_at=str(item.get("created_at", "") or ""),
                    updated_at=str(item.get("updated_at", "") or ""),
                    reviewer_id=str(item.get("reviewer_id", "") or "") or None,
                    review_note=str(item.get("review_note", "") or ""),
                    review_labels=list(item.get("review_labels", []) or []),
                    warning_flags=list(item.get("warning_flags", []) or []),
                    risk_level=str(item.get("risk_level", "low") or "low"),
                    scan_summary=dict(item.get("scan_summary", {}) or {}),
                    compatibility=str(item.get("compatibility", "compatible") or "compatible"),
                    compatibility_issues=list(item.get("compatibility_issues", []) or []),
                    filename=str(item.get("filename", "") or ""),
                    sha256=str(item.get("sha256", "") or ""),
                    size_bytes=int(item.get("size_bytes", 0) or 0),
                    sections=list(item.get("sections", []) or []),
                    redaction_mode=str(item.get("redaction_mode", "exclude_secrets") or "exclude_secrets"),
                    capability_summary=dict(item.get("capability_summary", {}) or {}),
                    compatibility_matrix=dict(item.get("compatibility_matrix", {}) or {}),
                    review_evidence=dict(item.get("review_evidence", {}) or {}),
                    submit_options=dict(item.get("submit_options", {}) or {}),
                )
            except Exception:
                continue
            if submission.submission_id:
                self._submissions[submission.submission_id] = submission

        for item in payload.get("published", []):
            try:
                published = PublishedProfilePack(
                    pack_type=self._normalize_pack_type(
                        str(item.get("pack_type", "") or PROFILE_PACK_TYPE)
                    ),
                    pack_id=str(item.get("pack_id", "") or ""),
                    version=str(item.get("version", "") or ""),
                    source_submission_id=str(item.get("source_submission_id", "") or ""),
                    artifact_id=str(item.get("artifact_id", "") or ""),
                    import_id=str(item.get("import_id", "") or ""),
                    published_at=str(item.get("published_at", "") or ""),
                    review_note=str(item.get("review_note", "") or ""),
                    review_labels=list(item.get("review_labels", []) or []),
                    warning_flags=list(item.get("warning_flags", []) or []),
                    risk_level=str(item.get("risk_level", "low") or "low"),
                    scan_summary=dict(item.get("scan_summary", {}) or {}),
                    compatibility=str(item.get("compatibility", "compatible") or "compatible"),
                    compatibility_issues=list(item.get("compatibility_issues", []) or []),
                    filename=str(item.get("filename", "") or ""),
                    sha256=str(item.get("sha256", "") or ""),
                    size_bytes=int(item.get("size_bytes", 0) or 0),
                    sections=list(item.get("sections", []) or []),
                    redaction_mode=str(item.get("redaction_mode", "exclude_secrets") or "exclude_secrets"),
                    capability_summary=dict(item.get("capability_summary", {}) or {}),
                    compatibility_matrix=dict(item.get("compatibility_matrix", {}) or {}),
                    review_evidence=dict(item.get("review_evidence", {}) or {}),
                    featured=bool(item.get("featured", False)),
                    featured_note=str(item.get("featured_note", "") or ""),
                    featured_by=str(item.get("featured_by", "") or ""),
                    featured_at=str(item.get("featured_at", "") or ""),
                )
            except Exception:
                continue
            if published.pack_id:
                self._published[published.pack_id] = published

        raw_confirmations = payload.get("plugin_install_confirmations", {})
        if isinstance(raw_confirmations, dict):
            for import_id, plugin_ids in raw_confirmations.items():
                normalized_import_id = str(import_id or "").strip()
                if not normalized_import_id:
                    continue
                normalized_plugin_ids = self._normalized_plugin_ids(
                    list(plugin_ids) if isinstance(plugin_ids, list) else []
                )
                if not normalized_plugin_ids:
                    continue
                self._plugin_install_confirmations[normalized_import_id] = normalized_plugin_ids

        raw_executions = payload.get("plugin_install_executions", {})
        if isinstance(raw_executions, dict):
            for import_id, rows in raw_executions.items():
                normalized_import_id = str(import_id or "").strip()
                if not normalized_import_id or not isinstance(rows, list):
                    continue
                normalized_rows: list[dict[str, Any]] = []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    normalized_rows.append(dict(row))
                if normalized_rows:
                    self._plugin_install_executions[normalized_import_id] = normalized_rows[-20:]

    def _flush_state(self) -> None:
        if self.repository is None:
            return
        exports = []
        for item in self._artifacts.values():
            exports.append(
                {
                    "artifact_id": item.artifact_id,
                    "pack_id": item.pack_id,
                    "version": item.version,
                    "exported_at": item.exported_at,
                    "path": str(item.path),
                    "filename": item.filename,
                    "sha256": item.sha256,
                    "size_bytes": item.size_bytes,
                    "manifest": item.manifest.model_dump(),
                    "redaction_notes": list(item.redaction_notes),
                    "owner_user_id": item.owner_user_id,
                }
            )
        imports = []
        for item in self._imports.values():
            imports.append(
                {
                    "import_id": item.import_id,
                    "imported_at": item.imported_at,
                    "filename": item.filename,
                    "manifest": item.manifest.model_dump(),
                    "sections": item.sections,
                    "scan_summary": item.scan_summary,
                    "compatibility": item.compatibility,
                    "compatibility_issues": list(item.compatibility_issues),
                    "user_id": item.user_id,
                    "source_artifact_id": item.source_artifact_id,
                    "import_origin": item.import_origin,
                    "source_fingerprint": item.source_fingerprint,
                }
            )
        submissions = []
        for item in self._submissions.values():
            submissions.append(
                {
                    "submission_id": item.submission_id,
                    "user_id": item.user_id,
                    "artifact_id": item.artifact_id,
                    "import_id": item.import_id,
                    "pack_type": item.pack_type,
                    "pack_id": item.pack_id,
                    "version": item.version,
                    "status": item.status,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "reviewer_id": item.reviewer_id,
                    "review_note": item.review_note,
                    "review_labels": list(item.review_labels),
                    "warning_flags": list(item.warning_flags),
                    "risk_level": item.risk_level,
                    "scan_summary": item.scan_summary,
                    "compatibility": item.compatibility,
                    "compatibility_issues": list(item.compatibility_issues),
                    "filename": item.filename,
                    "sha256": item.sha256,
                    "size_bytes": item.size_bytes,
                    "sections": list(item.sections),
                    "redaction_mode": item.redaction_mode,
                    "capability_summary": dict(item.capability_summary),
                    "compatibility_matrix": dict(item.compatibility_matrix),
                    "review_evidence": dict(item.review_evidence),
                    "submit_options": dict(item.submit_options),
                }
            )
        published = []
        for item in self._published.values():
            published.append(
                {
                    "pack_type": item.pack_type,
                    "pack_id": item.pack_id,
                    "version": item.version,
                    "source_submission_id": item.source_submission_id,
                    "artifact_id": item.artifact_id,
                    "import_id": item.import_id,
                    "published_at": item.published_at,
                    "review_note": item.review_note,
                    "review_labels": list(item.review_labels),
                    "warning_flags": list(item.warning_flags),
                    "risk_level": item.risk_level,
                    "scan_summary": item.scan_summary,
                    "compatibility": item.compatibility,
                    "compatibility_issues": list(item.compatibility_issues),
                    "filename": item.filename,
                    "sha256": item.sha256,
                    "size_bytes": item.size_bytes,
                    "sections": list(item.sections),
                    "redaction_mode": item.redaction_mode,
                    "capability_summary": dict(item.capability_summary),
                    "compatibility_matrix": dict(item.compatibility_matrix),
                    "review_evidence": dict(item.review_evidence),
                    "featured": item.featured,
                    "featured_note": item.featured_note,
                    "featured_by": item.featured_by,
                    "featured_at": item.featured_at,
                }
            )
        self.repository.save_state(
            {
                "exports": exports,
                "imports": imports,
                "submissions": submissions,
                "published": published,
                "plugin_install_confirmations": dict(self._plugin_install_confirmations),
                "plugin_install_executions": dict(self._plugin_install_executions),
            }
        )

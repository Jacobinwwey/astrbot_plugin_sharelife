"""Template package generation for community market templates."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .services_scan import ScanService
from .services_market import MarketService
from ..infrastructure.system_clock import SystemClock


@dataclass(slots=True)
class PackageArtifact:
    template_id: str
    version: str
    path: Path
    sha256: str
    filename: str
    source: str
    size_bytes: int


@dataclass(slots=True)
class SubmissionPackageImport:
    template_id: str
    version: str
    path: Path
    sha256: str
    filename: str
    size_bytes: int
    prompt_template: str
    scan_summary: dict[str, Any]
    review_labels: list[str]
    warning_flags: list[str]
    risk_level: str


class PackageService:
    DEFAULT_MAX_SUBMISSION_PACKAGE_BYTES = 20 * 1024 * 1024

    def __init__(
        self,
        market_service: MarketService,
        output_root: Path | str,
        clock: SystemClock,
        scan_service: ScanService | None = None,
        max_submission_package_bytes: int = DEFAULT_MAX_SUBMISSION_PACKAGE_BYTES,
    ):
        self.market_service = market_service
        self.output_root = Path(output_root)
        self.clock = clock
        self.scan_service = scan_service or ScanService()
        self.max_submission_package_bytes = max(1, int(max_submission_package_bytes or self.DEFAULT_MAX_SUBMISSION_PACKAGE_BYTES))

    def ingest_submission_package(
        self,
        template_id: str,
        version: str,
        filename: str,
        content: bytes,
    ) -> SubmissionPackageImport:
        if not content:
            raise ValueError("PACKAGE_BYTES_REQUIRED")
        if len(content) > self.max_submission_package_bytes:
            raise ValueError("PACKAGE_TOO_LARGE")

        sha256 = hashlib.sha256(content).hexdigest()
        safe_name = self._safe_filename(filename or f"{template_id.replace('/', '__')}-{version}.zip")
        upload_root = self.output_root / "uploads"
        upload_root.mkdir(parents=True, exist_ok=True)
        path = upload_root / f"{template_id.replace('/', '__')}-{version}-{sha256[:12]}-{safe_name}"
        path.write_bytes(content)

        prompt_template, scan_payload = self._extract_submission_payload(
            template_id=template_id,
            version=version,
            filename=safe_name,
            content=content,
        )
        report = self.scan_service.scan(scan_payload)
        summary = self.scan_service.to_dict(report)
        return SubmissionPackageImport(
            template_id=template_id,
            version=version,
            path=path,
            sha256=sha256,
            filename=safe_name,
            size_bytes=len(content),
            prompt_template=prompt_template,
            scan_summary=summary,
            review_labels=list(summary["review_labels"]),
            warning_flags=list(summary["warning_flags"]),
            risk_level=str(summary["risk_level"]),
        )

    def export_template_package(self, template_id: str, source_preference: str = "auto") -> PackageArtifact:
        normalized_source_preference = str(source_preference or "auto").strip().lower()
        if normalized_source_preference not in {"auto", "uploaded_submission", "generated"}:
            normalized_source_preference = "auto"

        uploaded = None
        if normalized_source_preference != "generated":
            uploaded = self._published_upload(template_id)
        if uploaded is not None:
            return uploaded

        bundle = self.market_service.build_prompt_bundle(template_id=template_id)
        version = bundle["version"]
        slug = template_id.replace("/", "__")
        self.output_root.mkdir(parents=True, exist_ok=True)
        path = self.output_root / f"{slug}-{version}.zip"

        bundle_payload = {
            "template_id": template_id,
            "version": version,
            "prompt": bundle["prompt"],
            "generated_at": self.clock.utcnow().isoformat(),
        }

        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("bundle.json", json.dumps(bundle_payload, ensure_ascii=False, indent=2))
            zf.writestr(
                "README.txt",
                (
                    "Sharelife template package.\n"
                    f"template_id={template_id}\n"
                    f"version={version}\n"
                ),
            )

        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        return PackageArtifact(
            template_id=template_id,
            version=version,
            path=path,
            sha256=sha256,
            filename=path.name,
            source="generated",
            size_bytes=path.stat().st_size,
        )

    def get_submission_package_artifact(self, submission_id: str) -> PackageArtifact:
        submission = self.market_service.get_submission(submission_id=submission_id)
        artifact = submission.package_artifact or {}
        path = Path(str(artifact.get("path", "") or ""))
        if not path.exists():
            raise ValueError("SUBMISSION_PACKAGE_NOT_AVAILABLE")
        sha256 = str(artifact.get("sha256", "") or hashlib.sha256(path.read_bytes()).hexdigest())
        filename = str(artifact.get("filename", "") or path.name)
        size_bytes = int(artifact.get("size_bytes", 0) or path.stat().st_size)
        source = str(artifact.get("source", "") or "uploaded_submission")
        return PackageArtifact(
            template_id=submission.template_id,
            version=submission.version,
            path=path,
            sha256=sha256,
            filename=filename,
            source=source,
            size_bytes=size_bytes,
        )

    def _published_upload(self, template_id: str) -> PackageArtifact | None:
        published = self.market_service.get_published_template(template_id=template_id)
        if published is None or not published.package_artifact:
            return None
        artifact = published.package_artifact
        path = Path(str(artifact.get("path", "")))
        if not path.exists():
            return None
        sha256 = str(artifact.get("sha256", "") or hashlib.sha256(path.read_bytes()).hexdigest())
        filename = str(artifact.get("filename", "") or path.name)
        size_bytes = int(artifact.get("size_bytes", 0) or path.stat().st_size)
        source = str(artifact.get("source", "") or "uploaded_submission")
        return PackageArtifact(
            template_id=template_id,
            version=published.version,
            path=path,
            sha256=sha256,
            filename=filename,
            source=source,
            size_bytes=size_bytes,
        )

    @staticmethod
    def _safe_filename(filename: str) -> str:
        return (
            Path(filename).name.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
            or "package.zip"
        )

    def _extract_submission_payload(
        self,
        template_id: str,
        version: str,
        filename: str,
        content: bytes,
    ) -> tuple[str, dict[str, Any]]:
        scan_sources: list[dict[str, str]] = []

        def add_scan_source(file_name: str, path: str, text: Any) -> None:
            snippet = str(text or "").strip()
            if not snippet:
                return
            scan_sources.append(
                {
                    "file": str(file_name or "payload"),
                    "path": str(path or "$"),
                    "text": snippet[:4000],
                }
            )

        def collect_text_fields(value: Any, path: str = "$", *, depth: int = 0) -> None:
            if len(scan_sources) >= 180 or depth > 8:
                return
            if isinstance(value, str):
                add_scan_source("bundle.json", path, value)
                return
            if isinstance(value, dict):
                for index, (key, nested) in enumerate(value.items()):
                    if index >= 48:
                        break
                    key_text = str(key)
                    if key_text.isidentifier():
                        nested_path = f"{path}.{key_text}" if path != "$" else f"$.{key_text}"
                    else:
                        nested_path = f'{path}["{key_text}"]'
                    collect_text_fields(nested, nested_path, depth=depth + 1)
                return
            if isinstance(value, list):
                for index, nested in enumerate(value[:40]):
                    collect_text_fields(nested, f"{path}[{index}]", depth=depth + 1)

        payload: dict[str, Any] = {
            "template_id": template_id,
            "version": version,
            "filename": filename,
            "files": [],
            "raw_text": "",
        }
        prompt_template = ""
        archive_buffer = io.BytesIO(content)
        text_parts: list[str] = []

        if zipfile.is_zipfile(archive_buffer):
            archive_buffer.seek(0)
            with zipfile.ZipFile(archive_buffer, "r") as zf:
                names = zf.namelist()
                payload["files"] = names
                if "bundle.json" in names:
                    try:
                        bundle_data = json.loads(zf.read("bundle.json").decode("utf-8"))
                    except Exception:
                        bundle_data = {}
                    add_scan_source("bundle.json", "$", json.dumps(bundle_data, ensure_ascii=False, sort_keys=True))
                    if isinstance(bundle_data, dict):
                        payload.update(bundle_data)
                        prompt_template = str(
                            bundle_data.get("prompt")
                            or bundle_data.get("prompt_template")
                            or ""
                        ).strip()
                        collect_text_fields(bundle_data, "$")
                for name in names[:12]:
                    lowered = name.lower()
                    if not lowered.endswith((".txt", ".md", ".json", ".yaml", ".yml", ".prompt")):
                        continue
                    try:
                        snippet = zf.read(name).decode("utf-8", errors="ignore").strip()
                    except Exception:
                        continue
                    if snippet:
                        text_parts.append(snippet[:2000])
                        add_scan_source(name, "$", snippet)
        else:
            raw_text = content.decode("utf-8", errors="ignore")[:8000]
            text_parts.append(raw_text)
            add_scan_source(filename or "uploaded_payload", "$", raw_text)

        if not prompt_template:
            prompt_template = (
                "You are running uploaded template "
                f"{template_id} (version {version}). "
                "Follow strict-mode safety boundaries and avoid privilege escalation."
            )
        payload["prompt"] = str(payload.get("prompt") or prompt_template)
        payload["prompt_template"] = prompt_template
        payload["raw_text"] = "\n".join(text_parts)[:8000]
        payload["scan_sources"] = scan_sources[:180]
        return prompt_template, payload

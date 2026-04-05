"""Controlled plugin install command execution for profile-pack imports."""

from __future__ import annotations

import shlex
import subprocess
from typing import Any, Callable


PluginCommandRunner = Callable[[list[str], int], dict[str, Any]]


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _trim_text(value: Any, *, max_len: int = 4000) -> str:
    text = str(value or "")
    if len(text) <= max_len:
        return text
    return text[:max_len]


def _split_prefixes(value: Any) -> list[str]:
    if isinstance(value, str):
        raw = value.split(",")
    elif isinstance(value, list):
        raw = value
    else:
        raw = []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _default_runner(command: list[str], timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=max(1, int(timeout_seconds)),
        )
        return {
            "returncode": int(completed.returncode),
            "stdout": completed.stdout or "",
            "stderr": completed.stderr or "",
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": 124,
            "stdout": str(exc.stdout or ""),
            "stderr": str(exc.stderr or ""),
            "timed_out": True,
        }
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }


class PluginInstallService:
    """Executes plugin install commands with explicit safety gates."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        command_timeout_seconds: int = 180,
        allowed_command_prefixes: list[str] | str | None = None,
        allow_http_source: bool = False,
        require_success_before_apply: bool = False,
        command_runner: PluginCommandRunner | None = None,
    ):
        self.enabled = bool(enabled)
        self.command_timeout_seconds = max(1, _to_int(command_timeout_seconds, 180))
        prefixes = _split_prefixes(allowed_command_prefixes)
        if not prefixes:
            prefixes = ["astrbot", "pip", "uv", "npm", "pnpm"]
        self.allowed_command_prefixes = set(prefixes)
        self.allow_http_source = _to_bool(allow_http_source, default=False)
        self.require_success_before_apply = _to_bool(require_success_before_apply, default=False)
        self.command_runner = command_runner or _default_runner

    def execute(
        self,
        *,
        candidates: list[dict[str, Any]],
        plugin_ids: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        requested_ids = self._normalize_plugin_ids(plugin_ids)
        by_plugin: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            plugin_id = str(candidate.get("plugin_id", "") or "").strip()
            if plugin_id:
                by_plugin[plugin_id] = candidate

        selected_plugin_ids: list[str]
        if requested_ids:
            selected_plugin_ids = requested_ids
        else:
            selected_plugin_ids = [
                plugin_id
                for plugin_id, candidate in by_plugin.items()
                if bool(candidate.get("install_required", False))
            ]

        if not selected_plugin_ids:
            return {
                "status": "not_required",
                "dry_run": bool(dry_run),
                "requested_plugins": requested_ids,
                "executed_plugins": [],
                "attempts": [],
                "installed_count": 0,
                "failed_count": 0,
                "blocked_count": 0,
            }

        if not dry_run and not self.enabled:
            raise ValueError("PROFILE_PACK_PLUGIN_INSTALL_EXEC_DISABLED")

        attempts: list[dict[str, Any]] = []
        installed_count = 0
        failed_count = 0
        blocked_count = 0

        for plugin_id in selected_plugin_ids:
            candidate = by_plugin.get(plugin_id)
            if candidate is None:
                raise ValueError("PROFILE_PACK_PLUGIN_NOT_IN_INSTALL_PLAN")
            attempt = self._execute_candidate(
                candidate=candidate,
                dry_run=dry_run,
            )
            attempts.append(attempt)
            status = str(attempt.get("status", "") or "")
            if status in {"installed", "dryrun_ready"}:
                installed_count += 1
            elif status == "blocked":
                blocked_count += 1
            elif status not in {"not_required", "skipped"}:
                failed_count += 1

        if dry_run and failed_count == 0 and blocked_count == 0:
            status = "dryrun_ready"
        elif failed_count > 0 or blocked_count > 0:
            status = "partial_failed" if installed_count > 0 else "failed"
        elif installed_count > 0:
            status = "executed"
        else:
            status = "not_required"

        return {
            "status": status,
            "dry_run": bool(dry_run),
            "requested_plugins": requested_ids,
            "executed_plugins": selected_plugin_ids,
            "attempts": attempts,
            "installed_count": installed_count,
            "failed_count": failed_count,
            "blocked_count": blocked_count,
        }

    @staticmethod
    def _normalize_plugin_ids(plugin_ids: list[str] | None) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in plugin_ids or []:
            plugin_id = str(item or "").strip()
            if not plugin_id or plugin_id in seen:
                continue
            seen.add(plugin_id)
            out.append(plugin_id)
        return out

    def _execute_candidate(
        self,
        *,
        candidate: dict[str, Any],
        dry_run: bool,
    ) -> dict[str, Any]:
        plugin_id = str(candidate.get("plugin_id", "") or "").strip()
        source = str(candidate.get("source", "") or "").strip()
        install_cmd = str(candidate.get("install_cmd", "") or "").strip()
        install_required = bool(candidate.get("install_required", False))

        base = {
            "plugin_id": plugin_id,
            "source": source,
            "version": str(candidate.get("version", "") or ""),
            "install_required": install_required,
            "install_cmd": install_cmd,
            "source_risk": str(candidate.get("source_risk", "unknown") or "unknown"),
        }

        if not install_required:
            return {
                **base,
                "status": "not_required",
                "reason": "already_present_or_metadata_missing",
            }
        if source.startswith("http://") and not self.allow_http_source:
            return {
                **base,
                "status": "blocked",
                "reason": "insecure_source_http_not_allowed",
            }
        if not install_cmd:
            return {
                **base,
                "status": "blocked",
                "reason": "install_command_missing",
            }
        if any(token in install_cmd for token in [";", "&&", "||", "|", "`", "$(", "\n", "\r"]):
            return {
                **base,
                "status": "blocked",
                "reason": "install_command_contains_shell_operators",
            }
        try:
            command = shlex.split(install_cmd, posix=True)
        except Exception:
            return {
                **base,
                "status": "blocked",
                "reason": "install_command_parse_error",
            }
        if not command:
            return {
                **base,
                "status": "blocked",
                "reason": "install_command_empty",
            }
        prefix = command[0]
        if self.allowed_command_prefixes and prefix not in self.allowed_command_prefixes:
            return {
                **base,
                "status": "blocked",
                "reason": "install_command_prefix_not_allowed",
                "command_prefix": prefix,
            }
        if dry_run:
            return {
                **base,
                "status": "dryrun_ready",
                "reason": "dry_run",
                "command": command,
            }

        runner_output = self.command_runner(command, self.command_timeout_seconds)
        raw_return_code = runner_output.get("returncode", 1)
        if raw_return_code is None:
            raw_return_code = 1
        try:
            return_code = int(raw_return_code)
        except Exception:
            return_code = 1
        status = "installed" if return_code == 0 else "failed"
        return {
            **base,
            "status": status,
            "reason": "completed" if status == "installed" else "command_failed",
            "command": command,
            "returncode": return_code,
            "timed_out": bool(runner_output.get("timed_out", False)),
            "stdout": _trim_text(runner_output.get("stdout", "")),
            "stderr": _trim_text(runner_output.get("stderr", "")),
        }

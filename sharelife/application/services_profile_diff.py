"""Dry-run diff helpers for profile pack apply plans."""

from __future__ import annotations

import difflib
import hashlib
import json
from typing import Any


class ProfileDiffService:
    _CHANGE_PATH_DISCOVERY_LIMIT = 64
    _CHANGE_PATH_PREVIEW_LIMIT = 6
    _PRETTY_JSON_LINE_LIMIT = 180
    _UNIFIED_DIFF_LINE_LIMIT = 240

    def diff_sections(
        self,
        current_sections: dict[str, Any],
        target_sections: dict[str, Any],
    ) -> dict[str, Any]:
        out_rows: list[dict[str, Any]] = []
        changed_sections: list[str] = []

        section_names = list(dict.fromkeys([*current_sections.keys(), *target_sections.keys()]))
        for section in section_names:
            before = current_sections.get(section)
            after = target_sections.get(section)
            changed = before != after
            changed_paths, changed_paths_truncated = self._diff_paths(
                before,
                after,
                limit=self._CHANGE_PATH_DISCOVERY_LIMIT,
            )
            scoped_paths = [
                section if path == "<value>" else self._join_path(section, path)
                for path in changed_paths
            ]
            before_preview, before_preview_truncated = self._json_preview(before)
            after_preview, after_preview_truncated = self._json_preview(after)
            diff_preview, diff_preview_truncated = self._diff_preview(
                before_preview,
                after_preview,
                section_name=section,
            )
            if changed:
                changed_sections.append(section)
            out_rows.append(
                {
                    "section": section,
                    "changed": changed,
                    "before_hash": self._hash_value(before),
                    "after_hash": self._hash_value(after),
                    "before_size": len(self._to_json(before)),
                    "after_size": len(self._to_json(after)),
                    "file_path": f"sections/{section}.json",
                    "changed_paths_preview": scoped_paths[: self._CHANGE_PATH_PREVIEW_LIMIT]
                    if changed
                    else [],
                    "changed_paths_count": len(scoped_paths) if changed else 0,
                    "changed_paths_truncated": bool(changed and changed_paths_truncated),
                    "before_preview": before_preview if changed else [],
                    "after_preview": after_preview if changed else [],
                    "before_preview_truncated": bool(changed and before_preview_truncated),
                    "after_preview_truncated": bool(changed and after_preview_truncated),
                    "diff_preview": diff_preview if changed else [],
                    "diff_preview_truncated": bool(changed and diff_preview_truncated),
                }
            )

        return {
            "sections": out_rows,
            "changed_sections": changed_sections,
        }

    @staticmethod
    def _to_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _to_pretty_json_lines(value: Any) -> list[str]:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
        return text.splitlines()

    def _hash_value(self, value: Any) -> str:
        return hashlib.sha256(self._to_json(value).encode("utf-8")).hexdigest()

    def _diff_paths(self, before: Any, after: Any, *, limit: int) -> tuple[list[str], bool]:
        if before == after:
            return [], False
        changed_paths: list[str] = []
        truncated = self._collect_changed_paths(
            before,
            after,
            path="",
            limit=max(1, int(limit)),
            output=changed_paths,
        )
        if not changed_paths:
            changed_paths.append("<value>")
        return changed_paths, truncated

    def _collect_changed_paths(
        self,
        before: Any,
        after: Any,
        *,
        path: str,
        limit: int,
        output: list[str],
    ) -> bool:
        if before == after:
            return False

        if isinstance(before, dict) and isinstance(after, dict):
            keys = sorted(
                set(before.keys()) | set(after.keys()),
                key=lambda value: str(value),
            )
            for key in keys:
                child_path = self._join_path(path, str(key))
                if key not in before or key not in after:
                    if self._append_path(output, child_path, limit=limit):
                        return True
                else:
                    truncated = self._collect_changed_paths(
                        before[key],
                        after[key],
                        path=child_path,
                        limit=limit,
                        output=output,
                    )
                    if truncated:
                        return True
            return False

        if isinstance(before, list) and isinstance(after, list):
            max_len = max(len(before), len(after))
            for idx in range(max_len):
                child_path = self._join_path(path, f"[{idx}]")
                if idx >= len(before) or idx >= len(after):
                    if self._append_path(output, child_path, limit=limit):
                        return True
                else:
                    truncated = self._collect_changed_paths(
                        before[idx],
                        after[idx],
                        path=child_path,
                        limit=limit,
                        output=output,
                    )
                    if truncated:
                        return True
            return False

        return self._append_path(output, path or "<value>", limit=limit)

    @staticmethod
    def _join_path(base: str, node: str) -> str:
        if not base:
            return node
        if node.startswith("["):
            return f"{base}{node}"
        return f"{base}.{node}"

    @staticmethod
    def _append_path(output: list[str], path: str, *, limit: int) -> bool:
        if len(output) >= limit:
            return True
        output.append(path)
        return False

    def _json_preview(self, value: Any) -> tuple[list[str], bool]:
        lines = self._to_pretty_json_lines(value)
        limit = self._PRETTY_JSON_LINE_LIMIT
        if len(lines) <= limit:
            return lines, False
        return lines[:limit], True

    def _diff_preview(
        self,
        before_lines: list[str],
        after_lines: list[str],
        *,
        section_name: str,
    ) -> tuple[list[str], bool]:
        diff_lines = list(
            difflib.unified_diff(
                before_lines,
                after_lines,
                fromfile=f"before/{section_name}.json",
                tofile=f"after/{section_name}.json",
                lineterm="",
                n=2,
            )
        )
        limit = self._UNIFIED_DIFF_LINE_LIMIT
        if len(diff_lines) <= limit:
            return diff_lines, False
        return diff_lines[:limit], True

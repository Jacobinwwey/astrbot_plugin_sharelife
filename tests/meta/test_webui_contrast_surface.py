from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
STYLE_PATH = REPO_ROOT / "sharelife" / "webui" / "style.css"


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    text = value.strip().lower()
    if not text.startswith("#"):
        raise ValueError(f"expected hex color, got: {value}")
    payload = text[1:]
    if len(payload) == 3:
        payload = "".join(ch * 2 for ch in payload)
    if len(payload) != 6:
        raise ValueError(f"expected #RRGGBB color, got: {value}")
    return (
        int(payload[0:2], 16) / 255.0,
        int(payload[2:4], 16) / 255.0,
        int(payload[4:6], 16) / 255.0,
    )


def _relative_luminance(value: str) -> float:
    rgb = _hex_to_rgb(value)

    def _channel(v: float) -> float:
        if v <= 0.03928:
            return v / 12.92
        return ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (_channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(foreground: str, background: str) -> float:
    fg = _relative_luminance(foreground)
    bg = _relative_luminance(background)
    lighter = max(fg, bg)
    darker = min(fg, bg)
    return (lighter + 0.05) / (darker + 0.05)


def _collect_css_hex_vars(text: str) -> dict[str, str]:
    matches = re.findall(r"(--[a-zA-Z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\s*;", text)
    values: dict[str, str] = {}
    for key, value in matches:
        # Keep the last assignment in file order to reflect effective overrides.
        values[key] = value
    return values


def test_core_webui_theme_tokens_keep_safe_text_contrast() -> None:
    text = STYLE_PATH.read_text(encoding="utf-8")
    vars_map = _collect_css_hex_vars(text)

    required_tokens = (
        "--bg",
        "--surface",
        "--text",
        "--text-muted",
        "--market-surface",
        "--market-surface-soft",
        "--market-ink",
        "--market-muted",
        "--market-muted-strong",
    )
    for key in required_tokens:
        assert key in vars_map, f"missing theme token {key}"

    pairs = (
        ("--text", "--bg", 7.0),
        ("--text-muted", "--bg", 4.5),
        ("--text", "--surface", 6.5),
        ("--text-muted", "--surface", 4.5),
        ("--market-ink", "--market-surface", 8.5),
        ("--market-muted", "--market-surface", 6.0),
        ("--market-muted-strong", "--market-surface", 7.0),
        ("--market-muted", "--market-surface-soft", 5.5),
    )
    for fg_token, bg_token, minimum in pairs:
        ratio = _contrast_ratio(vars_map[fg_token], vars_map[bg_token])
        assert ratio >= minimum, (
            f"contrast regression: {fg_token} on {bg_token} = {ratio:.2f}, expected >= {minimum:.2f}"
        )

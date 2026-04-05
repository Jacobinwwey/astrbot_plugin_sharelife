from pathlib import Path

import yaml


BASE = Path(__file__).resolve().parents[2] / "sharelife" / "i18n"


def load_locale(locale: str) -> dict:
    path = BASE / locale / "messages.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_zh_and_en_have_same_keys():
    zh = load_locale("zh-CN")
    en = load_locale("en-US")

    assert set(zh.keys()) == set(en.keys())

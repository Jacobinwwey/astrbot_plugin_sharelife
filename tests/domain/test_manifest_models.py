import pytest

from sharelife.domain.models import TemplateManifest


def test_manifest_minimal_fields():
    data = {
        "template_id": "community/basic",
        "version": "1.0.0",
        "title_i18n": {"zh-CN": "示例", "en-US": "Example"},
    }
    manifest = TemplateManifest.model_validate(data)
    assert manifest.template_id == "community/basic"


def test_manifest_requires_zh_and_en_titles():
    data = {
        "template_id": "community/basic",
        "version": "1.0.0",
        "title_i18n": {"zh-CN": "仅中文"},
    }
    with pytest.raises(ValueError):
        TemplateManifest.model_validate(data)

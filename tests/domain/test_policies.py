from sharelife.domain.models import TemplateManifest
from sharelife.domain.policies import classify_levels, resolve_compatibility


def test_classify_levels_marks_l3_for_provider_settings():
    levels = classify_levels({"provider_settings": {"x": 1}})
    assert "L3" in levels


def test_resolve_compatibility_without_version_is_degraded():
    manifest = TemplateManifest.model_validate(
        {
            "template_id": "community/basic",
            "version": "1.0.0",
            "title_i18n": {"zh-CN": "示例", "en-US": "Example"},
        }
    )
    assert resolve_compatibility(manifest) == "degraded"

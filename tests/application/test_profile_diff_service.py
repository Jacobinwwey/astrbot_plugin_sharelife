from sharelife.application.services_profile_diff import ProfileDiffService


def test_diff_sections_emits_changed_path_preview_for_nested_updates() -> None:
    service = ProfileDiffService()

    diff = service.diff_sections(
        current_sections={
            "providers": {
                "openai": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.2,
                }
            }
        },
        target_sections={
            "providers": {
                "openai": {
                    "model": "gpt-4.1",
                    "temperature": 0.7,
                }
            }
        },
    )

    providers_row = next(row for row in diff["sections"] if row["section"] == "providers")
    assert providers_row["changed"] is True
    assert providers_row["changed_paths_count"] >= 2
    assert "providers.openai.model" in providers_row["changed_paths_preview"]
    assert "providers.openai.temperature" in providers_row["changed_paths_preview"]
    assert providers_row["changed_paths_truncated"] is False


def test_diff_sections_reports_no_changed_paths_for_unchanged_section() -> None:
    service = ProfileDiffService()

    diff = service.diff_sections(
        current_sections={"plugins": {"sharelife": {"enabled": True}}},
        target_sections={"plugins": {"sharelife": {"enabled": True}}},
    )

    plugins_row = next(row for row in diff["sections"] if row["section"] == "plugins")
    assert plugins_row["changed"] is False
    assert plugins_row["changed_paths_count"] == 0
    assert plugins_row["changed_paths_preview"] == []
    assert plugins_row["changed_paths_truncated"] is False

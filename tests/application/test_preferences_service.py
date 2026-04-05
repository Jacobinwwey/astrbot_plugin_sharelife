from sharelife.application.services_preferences import PreferenceService


def test_user_can_switch_execution_mode():
    service = PreferenceService()

    pref = service.set_execution_mode(user_id="u1", mode="subagent_driven")

    assert pref.execution_mode == "subagent_driven"


def test_user_can_toggle_detail_observability():
    service = PreferenceService()

    pref = service.set_observe_details(user_id="u1", enabled=True)

    assert pref.observe_task_details is True

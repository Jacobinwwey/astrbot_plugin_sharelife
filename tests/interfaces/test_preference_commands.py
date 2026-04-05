from sharelife.application.services_preferences import PreferenceService
from sharelife.interfaces.commands_user import UserCommands


def test_preference_command_updates_mode():
    service = PreferenceService()
    cmd = UserCommands(preference_service=service)

    resp = cmd.set_mode(user_id="u1", mode="inline_execution")

    assert resp.data["execution_mode"] == "inline_execution"


def test_preference_command_updates_observe_toggle():
    service = PreferenceService()
    cmd = UserCommands(preference_service=service)

    resp = cmd.set_observe_details(user_id="u1", enabled=True)

    assert resp.data["observe_task_details"] is True


def test_preference_command_reads_defaults():
    service = PreferenceService()
    cmd = UserCommands(preference_service=service)

    resp = cmd.get_preferences(user_id="u2")

    assert resp.data["execution_mode"] == "subagent_driven"
    assert resp.data["observe_task_details"] is False

from stockbot.commands.parser import parse_command


def test_parses_bot_mention_and_arguments() -> None:
    command = parse_command("/approve@DideBehtar_bot abc 2026-12-31")
    assert command is not None
    assert command.name == "approve"
    assert command.arguments == ("abc", "2026-12-31")


def test_ignores_regular_messages() -> None:
    assert parse_command("سلام") is None

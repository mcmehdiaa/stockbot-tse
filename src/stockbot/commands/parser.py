from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    name: str
    arguments: tuple[str, ...]


def parse_command(text: str | None) -> Command | None:
    if not text or not text.startswith("/"):
        return None
    parts = text.strip().split()
    if not parts:
        return None
    name = parts[0][1:].split("@", 1)[0].lower()
    return Command(name=name, arguments=tuple(parts[1:])) if name else None

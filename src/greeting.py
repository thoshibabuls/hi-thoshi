"""Time-of-day greeting. Pure functions, no I/O."""

_MESSAGES = {
    "morning": "Good morning, {name} ☀️",
    "afternoon": "Good afternoon, {name} 👋",
    "evening": "Good evening, {name} 🌆",
    "night": "Still up, {name}? 🌙",
}


def part_of_day(hour: int) -> str:
    """Map an hour (0-23) to morning, afternoon, evening or night."""
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 22:
        return "evening"
    return "night"


def greeting_for(name: str, hour: int) -> str:
    return _MESSAGES[part_of_day(hour)].format(name=name)

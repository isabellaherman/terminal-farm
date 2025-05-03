from interfaces.game_system import IGameSystem
from typing import Any


class TimeSystem(IGameSystem):
    def __init__(self):
        self.day = 1

    def update(self):
        self.day += 1

    def get_day(self) -> int:
        return self.day

    def to_dict(self) -> dict[str, Any]:
        return {"day": self.day}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimeSystem":
        system = cls()
        system.day = data["day"]
        return system

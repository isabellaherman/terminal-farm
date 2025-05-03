from datetime import datetime
from typing import Any
from interfaces.serializable import ISerializable
from service.time_system import TimeSystem


class DayCycleSystem(ISerializable):
    PARTS = ["morning", "afternoon", "evening", "night"]

    def __init__(self, time_system: TimeSystem):
        self.time_system = time_system
        self.current_part_index = 0
        self.last_update_time = datetime.now()
        self.durations = self.get_durations_for_current_season()

    def get_season(self) -> str:
        season_index = (self.time_system.day - 1) // 30 % 4
        return ["spring", "summer", "autumn", "winter"][season_index]

    def get_durations_for_current_season(self) -> dict[str, int]:
        season = self.get_season()

        if season == "summer":
            return {"morning": 4, "afternoon": 4, "evening": 2, "night": 3}
        elif season == "winter":
            return {"morning": 3, "afternoon": 3, "evening": 4, "night": 3}
        else:
            return {"morning": 3, "afternoon": 3, "evening": 3, "night": 3}

    def update(self):
        now = datetime.now()
        current_part = self.PARTS[self.current_part_index]
        duration_minutes = self.durations[current_part]

        if (now - self.last_update_time).total_seconds() >= duration_minutes * 60:
            self.current_part_index = (self.current_part_index + 1) % len(self.PARTS)
            self.last_update_time = now
            self.durations = self.get_durations_for_current_season()
            return f"Part of the day changed: {self.get_current_part().capitalize()}!"
        return None

    def get_current_part(self) -> str:
        return self.PARTS[self.current_part_index]

    def is_night(self) -> bool:
        return self.get_current_part() == "night"

    def to_dict(self):
        return {
            "current_part_index": self.current_part_index,
            "last_update_time": self.last_update_time.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        instance = cls(TimeSystem())
        instance.current_part_index = data["current_part_index"]
        instance.last_update_time = datetime.fromisoformat(data["last_update_time"])
        return instance

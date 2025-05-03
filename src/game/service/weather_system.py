import random
from interfaces.game_system import IGameSystem
from typing import Any


class WeatherSystem(IGameSystem):
    WEATHER_TYPES = ["sunny", "rainy", "cloudy", "windy"]

    def __init__(self):
        self.current_weather = "sunny"

    def update(self):
        if random.random() < 0.2:
            self.current_weather = random.choice(self.WEATHER_TYPES)

    def get_weather(self) -> str:
        return self.current_weather

    def to_dict(self) -> dict[str, Any]:
        return {"current_weather": self.current_weather}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeatherSystem":
        system = cls()
        system.current_weather = data["current_weather"]
        return system

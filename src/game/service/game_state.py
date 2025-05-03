import random
import json
import os
from interfaces.serializable import ISerializable
from model.player import Player
from service.farm_system import FarmSystem
from service.crop_system import CropSystem
from service.weather_system import WeatherSystem
from service.time_system import TimeSystem
from service.event_system import EventSystem
from service.merchant_system import MerchantSystem
from service.fishing_system import FishingSystem
from service.daycycle_system import DayCycleSystem
from typing import Optional, Any, Tuple
from datetime import datetime
from utils.constants import GameStateConstants


class GameState(ISerializable):
    SAVE_FILE = "terminal_farmer_save.json"

    def __init__(self):
        self.player = Player()
        self.farm = FarmSystem()
        self.farm.game = self
        self.crop_system = CropSystem()
        self.weather_system = WeatherSystem()
        self.time_system = TimeSystem()
        self.event_system = EventSystem(self.farm, self.player)
        self.event_system.game = self
        self.day_cycle_system = DayCycleSystem(self.time_system)
        self.merchant_system = MerchantSystem(self.crop_system, self.player)
        self.fishing_system = FishingSystem(self.player)
        self.fishing_system.game = self
        self.lazy_day_active = False

    def next_day(self) -> Tuple[bool, Optional[str]]:
        """Advance to next day, returns (success, event_message)"""
        if not self.player.has_stamina(1.0):
            return False, None

        self.player.use_stamina(1.0)
        self.time_system.update()
        self.weather_system.update()
        self.day_cycle_system = DayCycleSystem(self.time_system)

        if self.player.has_farmdex and self.time_system.day % 2 == 0:
            if random.random() < 0.75 and len(self.player.fossils_found) < 50:
                undiscovered = [
                    f
                    for f in GameStateConstants.FOSSILS
                    if f not in self.player.fossils_found
                ]
                if undiscovered:
                    found = random.choice(undiscovered)
                    self.player.fossils_found.append(found)
                    return True, f"NEW FOSSIL DISCOVERED: {found}!"

        unlock_message = None
        if self.time_system.day == 3 and "corn" not in self.crop_system.unlocked_crops:
            unlock_message = self.crop_system.unlock_crop("corn")
        elif (
            self.time_system.day == 7
            and "pumpkin" not in self.crop_system.unlocked_crops
        ):
            unlock_message = self.crop_system.unlock_crop("pumpkin")

        self.market_inflated = False
        self.fishing_bonus = False
        if self.lazy_day_active:
            self.player.max_stamina += 2
            if self.player.stamina > self.player.max_stamina:
                self.player.stamina = self.player.max_stamina
            self.lazy_day_active = False
        event_message = self.event_system.update(self.time_system.day)

        return True, unlock_message or event_message

    def save(self) -> bool:
        try:
            with open(self.SAVE_FILE, "w") as f:
                json.dump(self.to_dict(), f)
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load(self) -> bool:
        try:
            if not os.path.exists(self.SAVE_FILE):
                return False

            with open(self.SAVE_FILE, "r") as f:
                data = json.load(f)
                self.from_dict(data, fallback=True)

            time_passed = datetime.now() - self.player.last_sleep_time
            hours_passed = time_passed.total_seconds() / 3600
            stamina_to_restore = min(
                int(hours_passed / 2), self.player.max_stamina - self.player.stamina
            )
            if stamina_to_restore > 0:
                self.player.restore_stamina(stamina_to_restore)

            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False

    def new_game(self):
        self.__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "player": self.player.to_dict(),
            "farm": self.farm.to_dict(),
            "crop_system": self.crop_system.to_dict(),
            "weather_system": self.weather_system.to_dict(),
            "time_system": self.time_system.to_dict(),
            "day_cycle_system": self.day_cycle_system.to_dict(),
            "merchant": {"fishing_unlocked": self.merchant_system.fishing_unlocked},
        }

    def from_dict(self, data: dict[str, Any], fallback: bool = False):
        self.player = Player.from_dict(data["player"])
        self.farm = FarmSystem.from_dict(data["farm"])
        self.farm.game = self
        self.crop_system = CropSystem.from_dict(data["crop_system"])
        self.weather_system = WeatherSystem.from_dict(data["weather_system"])
        self.time_system = TimeSystem.from_dict(data["time_system"])
        if "day_cycle_system" in data:
            self.day_cycle_system = DayCycleSystem.from_dict(data["day_cycle_system"])
        elif fallback:
            self.day_cycle_system = DayCycleSystem(self.time_system)
        self.event_system = EventSystem(self.farm, self.player)
        self.event_system.game = self
        self.merchant_system = MerchantSystem(self.crop_system, self.player)
        self.fishing_system = FishingSystem(self.player)
        self.fishing_system.game = self
        if "merchant" in data and data["merchant"].get("fishing_unlocked"):
            self.merchant_system.fishing_unlocked = True

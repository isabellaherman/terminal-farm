import os
import json
import time
import random
import sys
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any


# ==================== Interfaces e Classes Base ====================
class ISerializable(ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        pass


class IGameSystem(ABC):
    @abstractmethod
    def update(self):
        pass


# ==================== Modelos do Jogo ====================
class Crop(ISerializable):
    def __init__(
        self,
        name: str,
        cost: int,
        growth_time: int,
        value: int,
        color: str,
        stamina_cost: float,
    ):
        self.name = name
        self.cost = cost
        self.growth_time = growth_time
        self.value = value
        self.color = color
        self.stamina_cost = stamina_cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cost": self.cost,
            "growth_time": self.growth_time,
            "value": self.value,
            "color": self.color,
            "stamina_cost": self.stamina_cost,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Crop":
        return cls(
            name=data["name"],
            cost=data["cost"],
            growth_time=data["growth_time"],
            value=data["value"],
            color=data["color"],
            stamina_cost=data["stamina_cost"],
        )


# ==================== Sistema de cultivo ====================
class Plot(ISerializable):
    def __init__(
        self, crop: Optional[Crop] = None, planted_at: Optional[datetime] = None
    ):
        self.crop = crop
        self.planted_at = planted_at

    @property
    def is_empty(self) -> bool:
        return self.crop is None

    @property
    def growth_progress(self) -> float:
        if self.is_empty or self.planted_at is None:
            return 0.0

        elapsed = (datetime.now() - self.planted_at).total_seconds()
        return min(1.0, elapsed / self.crop.growth_time)

    @property
    def is_ready(self) -> bool:
        return self.growth_progress >= 1.0

    def plant(self, crop: Crop):
        self.crop = crop
        self.planted_at = datetime.now()

    def harvest(self) -> int:
        if self.is_empty or not self.is_ready:
            return 0

        value = self.crop.value
        self.crop = None
        self.planted_at = None
        return value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crop": self.crop.to_dict() if self.crop else None,
            "planted_at": self.planted_at.isoformat() if self.planted_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Plot":
        crop_data = data["crop"]
        planted_at = data["planted_at"]

        return cls(
            crop=Crop.from_dict(crop_data) if crop_data else None,
            planted_at=datetime.fromisoformat(planted_at) if planted_at else None,
        )


# ==================== Status do Player ====================
class Player(ISerializable):
    def __init__(
        self,
        money: int = 50,
        stamina: float = 5.0,
        max_stamina: int = 5,
        last_sleep_time: Optional[datetime] = None,
    ):
        self.money = money
        self.stamina = stamina
        self.max_stamina = max_stamina
        self.last_sleep_time = last_sleep_time or datetime.now()
        self.has_farmdex = False
        self.fossils_found = []
        self.can_sleep_anytime = False

    def can_afford(self, amount: int) -> bool:
        return self.money >= amount

    def spend_money(self, amount: int):
        self.money -= amount

    def earn_money(self, amount: int):
        self.money += amount

    def has_stamina(self, amount: float) -> bool:
        return self.stamina >= amount

    def use_stamina(self, amount: float):
        self.stamina -= amount

    def restore_stamina(self, amount: float):
        self.stamina = min(self.max_stamina, self.stamina + amount)

    def full_restore(self):
        self.stamina = self.max_stamina

    def to_dict(self) -> Dict[str, Any]:
        return {
            "money": self.money,
            "stamina": self.stamina,
            "max_stamina": self.max_stamina,
            "last_sleep_time": self.last_sleep_time.isoformat(),
            "has_farmdex": getattr(self, "has_farmdex", False),
            "fossils_found": getattr(self, "fossils_found", []),
            "can_sleep_anytime": getattr(self, "can_sleep_anytime", False),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        obj = cls(
            money=data["money"],
            stamina=data["stamina"],
            max_stamina=data["max_stamina"],
            last_sleep_time=datetime.fromisoformat(data["last_sleep_time"]),
        )
        obj.has_farmdex = data.get("has_farmdex", False)
        obj.fossils_found = data.get("fossils_found", [])
        obj.can_sleep_anytime = data.get("can_sleep_anytime", False)
        return obj


# ==================== Sistemas do Jogo ====================
class FarmSystem(ISerializable):
    def __init__(self, size: int = 9):
        self.plots = [Plot() for _ in range(size)]

    def plant_crop(self, plot_index: int, crop: Crop):
        if 0 <= plot_index < len(self.plots):
            self.plots[plot_index].plant(crop)

    def harvest_ready_crops(self) -> int:
        total = 0
        for plot in self.plots:
            if not plot.is_empty and plot.is_ready:
                total += plot.harvest()
        return total

    def get_plot_status(self, plot_index: int) -> Tuple[Optional[Crop], float]:
        if 0 <= plot_index < len(self.plots):
            plot = self.plots[plot_index]
            return plot.crop, plot.growth_progress
        return None, 0.0

    def damage_random_crop(self):
        occupied_plots = [i for i, plot in enumerate(self.plots) if not plot.is_empty]
        if occupied_plots:
            plot_idx = random.choice(occupied_plots)
            self.plots[plot_idx] = Plot()
            return "A storm came! Some crops were damaged."
        return None

    def apply_growth_bonus(self, bonus_percent: float):
        for plot in self.plots:
            if not plot.is_empty and plot.planted_at:
                bonus_time = plot.crop.growth_time * (bonus_percent / 100)
                plot.planted_at -= timedelta(seconds=bonus_time)
        return "Sunny day bonus! Crops grow faster today."

    def to_dict(self) -> Dict[str, Any]:
        return {"plots": [plot.to_dict() for plot in self.plots]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FarmSystem":
        farm = cls(size=len(data["plots"]))
        farm.plots = [Plot.from_dict(plot_data) for plot_data in data["plots"]]
        return farm


# ==================== Sistema de Colheita ====================
class CropSystem(ISerializable):
    def __init__(self):
        self.available_crops = self._load_default_crops()
        self.unlocked_crops = ["wheat"]

    def _load_default_crops(self) -> Dict[str, Crop]:
        return {
            "wheat": Crop("wheat", 10, 10, 20, "yellow", 0.5),
            "corn": Crop("corn", 20, 20, 45, "bright_yellow", 0.5),
            "pumpkin": Crop("pumpkin", 40, 40, 100, "orange", 1.0),
            "carrot": Crop("carrot", 15, 12, 25, "orange", 0.5),
            "eggplant": Crop("eggplant", 35, 30, 70, "purple", 1.0),
            "blueberry": Crop("blueberry", 60, 35, 90, "blue", 1.0),
            "lazy_ghost": Crop("lazy ghost seed [rare]", 0, 30, 100, "white", 0),
        }

    def get_crop(self, name: str) -> Optional[Crop]:
        return self.available_crops.get(name)

    def unlock_crop(self, name: str):
        if name in self.available_crops and name not in self.unlocked_crops:
            self.unlocked_crops.append(name)
            return f"NEW CROP UNLOCKED: {name.capitalize()}!"
        return None

    def get_unlocked_crops(self) -> List[Crop]:
        return [self.available_crops[name] for name in self.unlocked_crops]

    def to_dict(self) -> Dict[str, Any]:
        return {"unlocked_crops": self.unlocked_crops}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CropSystem":
        system = cls()
        system.unlocked_crops = data["unlocked_crops"]
        return system


# ==================== Sistema de Clima ====================
class WeatherSystem(IGameSystem):
    WEATHER_TYPES = ["sunny", "rainy", "cloudy", "windy"]

    def __init__(self):
        self.current_weather = "sunny"

    def update(self):
        if random.random() < 0.2:
            self.current_weather = random.choice(self.WEATHER_TYPES)

    def get_weather(self) -> str:
        return self.current_weather

    def to_dict(self) -> Dict[str, Any]:
        return {"current_weather": self.current_weather}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeatherSystem":
        system = cls()
        system.current_weather = data["current_weather"]
        return system


# ==================== Sistema de Tempo ====================
class TimeSystem(IGameSystem):
    def __init__(self):
        self.day = 1

    def update(self):
        self.day += 1

    def get_day(self) -> int:
        return self.day

    def to_dict(self) -> Dict[str, Any]:
        return {"day": self.day}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeSystem":
        system = cls()
        system.day = data["day"]
        return system


# ==================== Sistema de Eventos ====================
class EventSystem(IGameSystem):
    def __init__(self, farm: FarmSystem, player: Player):
        self.farm = farm
        self.player = player
        self.last_event_day = -1

    def update(self, current_day: int):
        base_chance = 0.4
        if random.random() < base_chance and self.last_event_day != current_day:
            self.last_event_day = current_day
            event = random.choice(
                [
                    self._storm_event,
                    self._sunny_bonus_event,
                    self._found_money_event,
                    self._found_energy_event,
                    self._fish_rain_event,
                    self._plague_event,
                    self._spirit_farmer_event,
                    self._lazy_day_event,
                    self._starry_night_event,
                    self._inflated_market_event,
                    self._night_robbery_event,
                    self._perfect_fishing_day_event,
                    self._rich_farmer_patron_event,
                    self._sugar_daddy_marriage_event,
                ]
            )
            return event()
        return None

    def _rich_farmer_patron_event(self):
        amount = 500
        self.player.earn_money(amount)
        return "Your charm paid off. A rich old farmer who just loves your crops appears. 💖 (+$500)"

    def _sugar_daddy_marriage_event(self):
        amount = 3000
        self.player.earn_money(amount)
        return "Farm life is tough… unless you marry rich! 💍 (+$3,000)"

    def _storm_event(self):
        return self.farm.damage_random_crop()

    def _sunny_bonus_event(self):
        return self.farm.apply_growth_bonus(20)

    def _found_money_event(self):
        amount = random.randint(10, 50)
        self.player.earn_money(amount)
        return f"You found money on the ground! (+${amount})"

    def _found_energy_event(self):
        self.player.restore_stamina(1)
        return "You found an energy drink! (+1 heart)"

    def _fish_rain_event(self):
        if hasattr(self, "game") and hasattr(self.game, "fishing_system"):
            self.game.fishing_system.caught_fish.append(
                {"name": "Skyfish", "value": 150}
            )
            return "A mysterious rain dropped a Skyfish into your bucket! (+$150)"
        return None

    def _plague_event(self):
        damaged = 0
        for _ in range(2):
            result = self.farm.damage_random_crop()
            if result:
                damaged += 1
        if damaged:
            return "A mysterious plague destroyed some crops!"
        return None

    def _spirit_farmer_event(self):
        if hasattr(self, "game") and hasattr(self.game, "crop_system"):
            if "lazy_ghost" not in self.game.crop_system.unlocked_crops:
                self.game.crop_system.unlocked_crops.append("lazy_ghost")
        return "A benevolent spirit gifted you a Lazy Ghost Seed!"

    def _lazy_day_event(self):
        if self.player.max_stamina > 1:
            self.player.max_stamina -= 2
            if self.player.stamina > self.player.max_stamina:
                self.player.stamina = self.player.max_stamina
            if hasattr(self, "game"):
                self.game.lazy_day_active = True
            return "You feel extremely lazy today... (-2 Max Hearts)"
        return None

    def _starry_night_event(self):
        return self.farm.apply_growth_bonus(100)

    def _inflated_market_event(self):
        if hasattr(self, "game"):
            self.game.market_inflated = True
        return "Prices have doubled today! (Inflated Market)"

    def _night_robbery_event(self):
        stolen = min(100, self.player.money)
        self.player.spend_money(stolen)
        return f"Thieves stole ${stolen} from your farm during the night!"

    def _perfect_fishing_day_event(self):
        if hasattr(self, "game"):
            self.game.fishing_bonus = True
        return "The fish are biting! (+50% fish value today!)"


# ==================== Sistema do Mercador ====================
class MerchantSystem:
    def __init__(self, crop_system: CropSystem, player: Player):
        self.crop_system = crop_system
        self.player = player
        self.fishing_unlocked = False

        if "Skyfish" not in [fish["name"] for fish in getattr(self, "fish_types", [])]:
            pass
        if "lazy_ghost" not in self.crop_system.available_crops:
            self.crop_system.available_crops["lazy_ghost"] = Crop(
                "lazy_ghost", 0, 30, 100, "white", 0
            )

        self.inventory = {
            "seeds": {
                "eggplant_seed": {"crop": "eggplant", "price": 80},
                "blueberry_seed": {"crop": "blueberry", "price": 120},
            },
            "items": {
                "farmdex_scanner": {
                    "price": 300,
                    "effect": "unlock_farmdex",
                    "narrative": True,
                },
                "fishing_rod": {"price": 5000, "unlocks": "fishing"},
                "golden_hat": {"price": 6666, "effect": "cosmetic", "narrative": True},
                "lucky_egg": {"price": 5000, "effect": "increase_event_chance"},
                "balatro_card": {"price": 8888, "effect": "increase_max_stamina"},
                "lantern": {"price": 2000, "effect": "unlock_night_work"},
                "sleep_pills": {
                    "price": 3000,
                    "effect": "unlock_anytime_sleep",
                    "narrative": True,
                },
            },
        }

    def is_available(self, part_of_day: str) -> bool:
        return part_of_day == "morning"

    def buy_seed(self, seed_key: str) -> Optional[str]:
        if seed_key not in self.inventory["seeds"]:
            return "Invalid seed."

        seed = self.inventory["seeds"][seed_key]
        price = seed["price"]
        if hasattr(self.player, "game") and getattr(
            self.player.game, "market_inflated", False
        ):
            price *= 2
        if not self.player.can_afford(price):
            return "Not enough money."

        self.player.spend_money(price)
        result = self.crop_system.unlock_crop(seed["crop"])
        return result or f"{seed['crop'].capitalize()} is already unlocked."

    def buy_item(self, item_key: str) -> Optional[str]:
        if item_key not in self.inventory["items"]:
            return "Invalid item."

        item = self.inventory["items"][item_key]

        if item.get("unlocks") == "fishing" and self.fishing_unlocked:
            return "You already own this item."
        if (
            item.get("effect") == "increase_event_chance"
            and hasattr(self.player, "event_bonus")
            and self.player.event_bonus == "lucky_egg"
        ):
            return "You already own this item."
        if item.get("effect") == "increase_max_stamina" and self.player.max_stamina > 5:
            return "You already own this item."
        if (
            item.get("effect") == "cosmetic"
            and hasattr(self.player, "bought_hat")
            and self.player.bought_hat
        ):
            return "You already own this item."
        if item.get("effect") == "unlock_night_work" and getattr(
            self.player, "has_lantern", False
        ):
            return "You already own this item."
        if item.get("effect") == "unlock_farmdex" and getattr(
            self.player, "has_farmdex", False
        ):
            return "You already own this item."
        if item.get("effect") == "unlock_anytime_sleep" and getattr(
            self.player, "can_sleep_anytime", False
        ):
            return "You already own this item."

        if not self.player.can_afford(item["price"]):
            return "Not enough money."

        self.player.spend_money(item["price"])
        if item.get("unlocks") == "fishing":
            self.fishing_unlocked = True
            return "You bought a fishing rod! Fishing is now available."
        elif item.get("effect") == "increase_event_chance":
            self.player.event_bonus = "lucky_egg"
            return "You feel luckier already... (+Event Chance)"
        elif item.get("effect") == "increase_max_stamina":
            self.player.max_stamina += 4
            self.player.stamina = self.player.max_stamina
            return "Your soul feels stronger... (+4 Max Stamina)"
        elif item.get("effect") == "cosmetic":
            self.player.bought_hat = True
            return "Cosmetic item? In a CLI game? Bro... you deserved to lose that money. I'm sorry."
        elif item.get("effect") == "unlock_night_work":
            self.player.has_lantern = True
            return "You bought a lantern! Now you can work through the night."
        elif item.get("effect") == "unlock_farmdex":
            self.player.has_farmdex = True
            return "Every two days, you have a 75% chance to discover a buried fossil! Help the local museum build the greatest dinosaur collection in history!"
        elif item.get("effect") == "unlock_anytime_sleep":
            self.player.can_sleep_anytime = True
            return "You bought Sleep Pills! Now you can sleep anytime to skip the day."
        return "Item purchased."


# ==================== Sistema de Pescaria ====================
class FishingSystem:
    def __init__(self, player: Player):
        self.player = player
        self.game = None
        self.caught_fish = []

        self.fish_types = [
            {"name": "Salmon", "value": 40},
            {"name": "Tuna", "value": 50},
            {"name": "Golden Fish", "value": 100},
            {"name": "Skyfish", "value": 150},
        ]

    def fish(self) -> str:
        if not self.player.has_stamina(2.0):
            return "Not enough stamina to fish."

        self.player.use_stamina(2.0)
        fish = random.choice(self.fish_types)
        self.caught_fish.append(fish)
        return f"You caught a {fish['name']} worth ${fish['value']}!"

    def sell_all_fish(self) -> str:
        bonus_multiplier = (
            1.5
            if getattr(self, "game", None)
            and getattr(self.game, "fishing_bonus", False)
            else 1.0
        )
        total = sum(int(f["value"] * bonus_multiplier) for f in self.caught_fish)
        self.player.earn_money(total)
        self.caught_fish = []
        return f"Sold all fish for ${total}!"


# ==================== Gerenciamento do Jogo ====================
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
                all_fossils = [
                    "Tyrannosaurus",
                    "Triceratops",
                    "Velociraptor",
                    "Brachiosaurus",
                    "Stegosaurus",
                    "Spinosaurus",
                    "Ankylosaurus",
                    "Parasaurolophus",
                    "Allosaurus",
                    "Diplodocus",
                    "Iguanodon",
                    "Archaeopteryx",
                    "Pteranodon",
                    "Deinonychus",
                    "Megalosaurus",
                    "Pachycephalosaurus",
                    "Corythosaurus",
                    "Oviraptor",
                    "Plateosaurus",
                    "Styracosaurus",
                    "Suchomimus",
                    "Troodon",
                    "Carnotaurus",
                    "Sauropelta",
                    "Albertosaurus",
                    "Mamenchisaurus",
                    "Edmontosaurus",
                    "Herrerasaurus",
                    "Giganotosaurus",
                    "Therizinosaurus",
                    "Kentrosaurus",
                    "Dilophosaurus",
                    "Coelophysis",
                    "Protoceratops",
                    "Sinraptor",
                    "Rugops",
                    "Lambeosaurus",
                    "Mononykus",
                    "Torosaurus",
                    "Rhabdodon",
                    "Ouranosaurus",
                    "Microceratus",
                    "Zuniceratops",
                    "Einiosaurus",
                    "Dromaeosaurus",
                    "Massospondylus",
                    "Lesothosaurus",
                    "Noasaurus",
                    "Gasparinisaura",
                    "Minmi",
                ]
                undiscovered = [
                    f for f in all_fossils if f not in self.player.fossils_found
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player": self.player.to_dict(),
            "farm": self.farm.to_dict(),
            "crop_system": self.crop_system.to_dict(),
            "weather_system": self.weather_system.to_dict(),
            "time_system": self.time_system.to_dict(),
            "day_cycle_system": self.day_cycle_system.to_dict(),
            "merchant": {"fishing_unlocked": self.merchant_system.fishing_unlocked},
        }

    def from_dict(self, data: Dict[str, Any], fallback: bool = False):
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


# ==================== Interface do Usuário ====================
class TerminalUI:
    MENU_COOLDOWN_TIME = 2.6

    EMOJI_HEART = "♥"

    COLORS = {
        "reset": "\033[0m",
        "green": "\033[32m",
        "bright_green": "\033[1;32m",
        "yellow": "\033[33m",
        "bright_yellow": "\033[1;33m",
        "blue": "\033[34m",
        "bright_blue": "\033[1;34m",
        "cyan": "\033[36m",
        "bright_cyan": "\033[1;36m",
        "red": "\033[31m",
        "bright_red": "\033[1;31m",
        "orange": "\033[38;5;208m",
        "gray": "\033[90m",
        "white": "\033[97m",
        "pink": "\033[38;5;213m",
        "heart_red": "\033[38;5;161m",
    }

    BG_COLORS = {
        "reset": "\033[0m",
        "orange": "\033[48;5;94m",
        "yellow_pastel": "\033[48;5;187m",
        "gray": "\033[48;5;240m",
        "green": "\033[42m",
        "green_custom": "\033[48;5;115m",
    }

    WEATHER_ICONS = {"sunny": "☀️", "rainy": "🌧️", "cloudy": "☁️", "windy": "🌬️"}

    SEASON_ICONS = {"spring": "🌸", "summer": "☀️", "autumn": "🍂", "winter": "❄️"}

    def display_status(self):
        weather = self.game.weather_system.get_weather()
        weather_icon = self.WEATHER_ICONS.get(weather, "")
        money_text = f"💰 Money: ${self.game.player.money}"
        weather_text = f"Weather: {weather_icon} {weather.capitalize()}"

        header_width = self.last_box_width if hasattr(self, "last_box_width") else 50
        content = f"{money_text}   {weather_text}"

        print(self.color_text("═" * header_width, "bright_cyan"))
        print(content)
        print(self.color_text("═" * header_width, "bright_cyan"))

    def display_farm(self):
        self.clear_screen()
        self.display_header()
        self.display_status()

        print(f"{self.color_text('🌱 Farm Layout:', 'bright_green')}\n")

        for i in range(0, 9, 3):
            row_lines = ["", "", ""]
            for j in range(3):
                plot_idx = i + j
                crop, progress = self.game.farm.get_plot_status(plot_idx)

                if crop:
                    bg_color = "green" if progress >= 1.0 else "yellow_pastel"
                    fg_color = "white" if progress >= 1.0 else "gray"
                else:
                    bg_color = "orange"
                    fg_color = "white"
                slot_text = str(plot_idx + 1).center(9)
                content_text = crop.name[:7].center(9) if crop else "Empty".center(9)
                spacer = " "

                row_lines[0] += (
                    self.bg_color_text(slot_text, fg_color, bg_color) + spacer
                )
                row_lines[1] += (
                    self.bg_color_text(content_text, fg_color, bg_color) + spacer
                )
                row_lines[2] += self.bg_color_text(" " * 9, fg_color, bg_color) + spacer

            for line in row_lines:
                print(line)
            print()

    def bg_color_text(self, text: str, fg_color: str, bg_color: str) -> str:
        fg = self.COLORS.get(fg_color, "")
        bg = self.BG_COLORS.get(bg_color, "")
        return f"{bg}{fg}{text}{self.COLORS['reset']}"

    def __init__(self, game_state: GameState):
        self.game = game_state

    def clear_screen(self):
        print("\033[H\033[J")

    def color_text(self, text: str, color: str) -> str:
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"

    def strip_ansi(self, text: str) -> str:
        import re

        ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", text)

    def display_stamina(self, stamina: float, max_stamina: int) -> str:
        full_hearts = int(stamina)
        half_heart = (stamina - full_hearts) >= 0.5
        empty_hearts = max_stamina - full_hearts - (1 if half_heart else 0)

        hearts = []
        hearts.extend([self.color_text("♥", "heart_red")] * full_hearts)
        if half_heart:
            hearts.append(self.color_text("♥", "pink"))
        hearts.extend([self.color_text("♡", "gray")] * empty_hearts)

        return " ".join(hearts)

    def get_greeting(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        else:
            return "Good night"

    def get_season_icon(self) -> str:
        return self.SEASON_ICONS.get(self.game.day_cycle_system.get_season(), "")

    def display_action_message(
        self,
        cancellable: bool = False,
        message: str = "Choose action",
        cancel_message: str = "(0 to cancel): ",
    ) -> str:
        cancel_text = cancel_message if cancellable else ""
        return f"\n{self.color_text(message, 'bright_cyan')} {cancel_text}"

    def display_header(self):
        message = self.game.day_cycle_system.update()
        if message:
            print(self.color_text(message, "bright_cyan"))
        import getpass

        username = getpass.getuser()
        greeting = self.get_greeting()
        stamina_display = self.display_stamina(
            self.game.player.stamina, self.game.player.max_stamina
        )
        season = self.game.day_cycle_system.get_season().capitalize()
        current_part = self.game.day_cycle_system.get_current_part().capitalize()
        season_icon = self.get_season_icon()
        day = self.game.time_system.day

        TITLE_LINE_LEFT = "🌱 TERMINAL FARM"
        TITLE_LINE_RIGHT = f"Day {day} ({current_part}) {season_icon} {season}"
        GREETING_LINE = f"{greeting}, {username}!"

        content_width = (
            max(
                len(TITLE_LINE_LEFT) + len(TITLE_LINE_RIGHT) + 2,
                len(GREETING_LINE),
                len(self.strip_ansi(stamina_display)) + len("Stamina: "),
            )
            + 6
        )
        BOX_WIDTH = content_width
        BOX_BORDER_HORIZONTAL = "═" * BOX_WIDTH

        spacing = BOX_WIDTH - len(TITLE_LINE_LEFT) - len(TITLE_LINE_RIGHT) - 2
        TITLE_LINE = f"{TITLE_LINE_LEFT}{' ' * spacing}{TITLE_LINE_RIGHT}"

        centered_title = TITLE_LINE
        title_line = f"{self.color_text('║', 'bright_cyan')}{self.color_text(centered_title.ljust(BOX_WIDTH - 2), 'bright_green')}{self.color_text('║', 'bright_cyan')}"
        greeting_line = f"{self.color_text('║', 'bright_cyan')}  {self.color_text(GREETING_LINE.ljust(BOX_WIDTH - 4), 'green')}  {self.color_text('║', 'bright_cyan')}"
        stamina_text = f"Stamina: {stamina_display}"
        padding = (BOX_WIDTH - 4) - len(self.strip_ansi(stamina_text))
        stamina_line = f"{self.color_text('║', 'bright_cyan')}  {stamina_text}{' ' * padding}  {self.color_text('║', 'bright_cyan')}"

        print(self.color_text(f"╔{BOX_BORDER_HORIZONTAL}╗", "bright_cyan"))
        print(title_line)
        print(self.color_text(f"╠{BOX_BORDER_HORIZONTAL}╣", "bright_cyan"))
        print(greeting_line)
        print(stamina_line)
        self.last_box_width = BOX_WIDTH
        print(self.color_text(f"╚{BOX_BORDER_HORIZONTAL}╝", "bright_cyan"))

    def plant_crop_menu(self):
        self.display_farm()
        unlocked_crops = self.game.crop_system.get_unlocked_crops()

        print(f"{self.color_text('Available Crops:', 'bright_blue')}")
        for i, crop in enumerate(unlocked_crops, 1):
            cost = self.color_text(f"${crop.cost}", "yellow")
            value = self.color_text(f"${crop.value}", "bright_yellow")
            stamina = self.color_text(f"{crop.stamina_cost}♥", "pink")
            name = crop.name.capitalize()
            rare_tag = ""
            if "rare" in name.lower():
                name = name.replace(" [Rare]", "").replace(" [rare]", "")
                rare_tag = self.color_text(" [Rare]", "orange")
            name_display = self.color_text(name, crop.color)
            print(
                f"{self.color_text(f'{i}.', 'white')} {name_display} "
                f"(Cost: {cost}, Value: {value}, Stamina: {stamina}, Time: {crop.growth_time}s){rare_tag}"
            )

        try:
            choice = input(
                self.display_action_message(
                    message="Choose crop to plant", cancellable=True
                )
            )
            if choice == "0":
                return

            crop_idx = int(choice) - 1
            if crop_idx < 0 or crop_idx >= len(unlocked_crops):
                raise IndexError

            crop = unlocked_crops[crop_idx]

            if not self.game.player.has_stamina(crop.stamina_cost):
                input(f"{self.color_text('Not enough stamina!', 'red')} Press Enter...")
                return

            if not self.game.player.can_afford(crop.cost):
                input(f"{self.color_text('Not enough money!', 'red')} Press Enter...")
                return

            print(f"\n{self.color_text('Farm Layout:', 'bright_green')}")
            for i in range(0, 9, 3):
                print(f"{self.color_text(f'{i + 1}-{i + 3}', 'cyan')} ", end="")
            print("\n")

            plot = (
                int(input(f"{self.color_text('Choose plot', 'bright_cyan')} (1-9): "))
                - 1
            )
            if plot < 0 or plot > 8:
                return

            if not self.game.farm.plots[plot].is_empty:
                input(
                    f"{self.color_text('Plot already occupied!', 'red')} Press Enter..."
                )
                return

            self.game.player.spend_money(crop.cost)
            self.game.player.use_stamina(crop.stamina_cost)
            self.game.farm.plant_crop(plot, crop)
            print(
                f"\n{self.color_text(f'Planted {crop.name} in plot {plot + 1}!', 'green')}"
            )
            time.sleep(self.MENU_COOLDOWN_TIME)

        except (ValueError, IndexError):
            input(f"{self.color_text('Invalid choice!', 'red')} Press Enter...")
            return

    def harvest_menu(self):
        if not self.game.player.has_stamina(0.5):
            input(f"{self.color_text('Not enough stamina!', 'red')} Press Enter...")
            return

        harvested_value = self.game.farm.harvest_ready_crops()

        if harvested_value > 0:
            self.game.player.earn_money(harvested_value)
            self.game.player.use_stamina(0.5)
            print(
                f"{self.color_text(f'Harvested crops worth ${harvested_value}!', 'green')}"
            )
        else:
            print(f"{self.color_text('Nothing ready to harvest yet!', 'yellow')}")
        time.sleep(self.MENU_COOLDOWN_TIME)

    def sleep_menu(self):
        self.clear_screen()
        print(f"{self.color_text('Sleep Options:', 'bright_blue')}\n")
        print(
            f"{self.color_text('1.', 'cyan')} Sleep until next day {self.color_text(f'(Recover all {self.EMOJI_HEART})', 'cyan')}"
        )
        print(
            f"{self.color_text('2.', 'cyan')} Take a nap (advance time) {self.color_text(f'(+1 {self.EMOJI_HEART})', 'cyan')}"
        )

        choice = input(self.display_action_message(cancellable=True))
        if choice == "1":
            if not self.game.day_cycle_system.is_night() and not getattr(
                self.game.player, "can_sleep_anytime", False
            ):
                print(
                    self.color_text(
                        "\nYou can only sleep at night… try taking a nap.", "red"
                    )
                )
                time.sleep(self.MENU_COOLDOWN_TIME)
                return
            _, message = self.game.next_day()
            self.game.player.full_restore()
            self.game.player.last_sleep_time = datetime.now()

            print(
                self.color_text(
                    "\nYou slept soundly and woke up refreshed the next day!",
                    "bright_green",
                )
            )
            if message:
                print(f"{self.color_text('EVENT:', 'bright_blue')} {message}")
            time.sleep(self.MENU_COOLDOWN_TIME)
        elif choice == "2":
            self.game.player.restore_stamina(1)

            self.game.day_cycle_system.current_part_index = (
                self.game.day_cycle_system.current_part_index + 1
            ) % len(self.game.day_cycle_system.PARTS)
            self.game.day_cycle_system.last_update_time = datetime.now()
            print(
                self.color_text(
                    f"\nYou took a nap and time passed... (+1 {self.EMOJI_HEART})",
                    "green",
                )
            )
            time.sleep(self.MENU_COOLDOWN_TIME)

    def start_game_loop(self):
        while True:
            self.display_farm()
            print(self.color_text("Actions:", "bright_blue"))

            actions = []
            actions.append(
                f"{self.color_text('1.', 'cyan')} {self.color_text('Plant Crop', 'bright_green')}"
            )
            actions.append(
                f"{self.color_text('2.', 'cyan')} {self.color_text('Harvest Crops', 'grey')}"
            )
            actions.append(
                f"{self.color_text('3.', 'cyan')} {self.color_text('Next Day', 'grey')}"
            )
            actions.append(
                f"{self.color_text('4.', 'cyan')} {self.color_text('Sleep/Rest', 'grey')}"
            )
            actions.append(
                f"{self.color_text('5.', 'cyan')} {self.color_text('Save & Quit', 'grey')}"
            )
            actions.append(
                f"{self.color_text('6.', 'cyan')} {self.color_text('Reset Game', 'red')}"
            )

            if self.game.merchant_system.is_available(
                self.game.day_cycle_system.get_current_part()
            ):
                actions.append(
                    f"{self.color_text('7.', 'cyan')} {self.color_text('Joji the Merchant', 'bright_yellow')}"
                )

            if self.game.merchant_system.fishing_unlocked:
                actions.append(
                    f"{self.color_text('8.', 'cyan')} {self.color_text('Go Fishing', 'grey')}"
                )

            if self.game.player.has_farmdex:
                actions.append(
                    f"{self.color_text('9.', 'cyan')} {self.color_text('Farmdex', 'grey')}"
                )

            max_widths = [0, 0, 0]
            for i, action in enumerate(actions):
                col = i % 3
                length = len(self.strip_ansi(action))
                if length > max_widths[col]:
                    max_widths[col] = length

            for i in range(0, len(actions), 3):
                row = actions[i : i + 3]
                padded_row = []
                for j, action in enumerate(row):
                    col_width = max_widths[j]
                    raw = self.strip_ansi(action)
                    pad = col_width - len(raw)
                    padded_row.append(action + (" " * pad))
                print(" | ".join(padded_row))

            choice = input(self.display_action_message())

            if choice == "1":
                if (
                    self.game.day_cycle_system.get_current_part() == "night"
                    and not getattr(self.game.player, "has_lantern", False)
                ):
                    input(
                        self.color_text(
                            "It's too dark to work without a lantern!", "red"
                        )
                        + " Press Enter..."
                    )
                    continue
                self.plant_crop_menu()
            elif choice == "2":
                if (
                    self.game.day_cycle_system.get_current_part() == "night"
                    and not getattr(self.game.player, "has_lantern", False)
                ):
                    input(
                        self.color_text(
                            "It's too dark to work without a lantern!", "red"
                        )
                        + " Press Enter..."
                    )
                    continue
                self.harvest_menu()
            elif choice == "3":
                success, message = self.game.next_day()
                if success:
                    print(
                        f"{self.color_text('Advanced to day', 'blue')} "
                        f"{self.color_text(self.game.time_system.day, 'bright_blue')}!"
                    )
                    if message:
                        print(f"{self.color_text('EVENT:', 'bright_blue')} {message}")
                    time.sleep(self.MENU_COOLDOWN_TIME)
                else:
                    input(
                        f"{self.color_text('Not enough stamina!', 'red')} Press Enter..."
                    )
            elif choice == "4":
                self.sleep_menu()
            elif choice == "5":
                if self.game.save():
                    print(f"\n{self.color_text('Game saved!', 'green')}")
                    sys.exit()
            elif choice == "6":
                confirm = input(
                    self.color_text("Are you sure you want to reset? (y/n): ", "red")
                )
                if confirm.lower() == "y":
                    self.game.new_game()
                    print(self.color_text("Game reset!", "green"))
                    time.sleep(1)
            elif choice == "7" and self.game.merchant_system.is_available(
                self.game.day_cycle_system.get_current_part()
            ):
                self.merchant_menu()
            elif choice == "8" and self.game.merchant_system.fishing_unlocked:
                if (
                    self.game.day_cycle_system.get_current_part() == "night"
                    and not getattr(self.game.player, "has_lantern", False)
                ):
                    input(
                        self.color_text(
                            "It's too dark to work without a lantern!", "red"
                        )
                        + " Press Enter..."
                    )
                    continue
                self.fishing_menu()
            elif choice == "9" and self.game.player.has_farmdex:
                self.farmdex_menu()
            else:
                print(f"{self.color_text('Invalid choice!', 'red')}")
                time.sleep(self.MENU_COOLDOWN_TIME)

    def farmdex_menu(self):
        self.clear_screen()
        print(self.color_text("🦖 Farmdex Collection", "bright_green"))
        print(
            self.color_text(
                f"Fossils Discovered: {len(self.game.player.fossils_found)}/50", "cyan"
            )
        )
        print()
        all_fossils = [
            "Tyrannosaurus",
            "Triceratops",
            "Velociraptor",
            "Brachiosaurus",
            "Stegosaurus",
            "Spinosaurus",
            "Ankylosaurus",
            "Parasaurolophus",
            "Allosaurus",
            "Diplodocus",
            "Iguanodon",
            "Archaeopteryx",
            "Pteranodon",
            "Deinonychus",
            "Megalosaurus",
            "Pachycephalosaurus",
            "Corythosaurus",
            "Oviraptor",
            "Plateosaurus",
            "Styracosaurus",
            "Suchomimus",
            "Troodon",
            "Carnotaurus",
            "Sauropelta",
            "Albertosaurus",
            "Mamenchisaurus",
            "Edmontosaurus",
            "Herrerasaurus",
            "Giganotosaurus",
            "Therizinosaurus",
            "Kentrosaurus",
            "Dilophosaurus",
            "Coelophysis",
            "Protoceratops",
            "Sinraptor",
            "Rugops",
            "Lambeosaurus",
            "Mononykus",
            "Torosaurus",
            "Rhabdodon",
            "Ouranosaurus",
            "Microceratus",
            "Zuniceratops",
            "Einiosaurus",
            "Dromaeosaurus",
            "Massospondylus",
            "Lesothosaurus",
            "Noasaurus",
            "Gasparinisaura",
            "Minmi",
        ]
        columns = 3
        rows = (len(all_fossils) + columns - 1) // columns
        fossil_entries = []

        for name in all_fossils:
            if name in self.game.player.fossils_found:
                fossil_entries.append(self.color_text(name, "bright_green"))
            else:
                fossil_entries.append(self.color_text("?????", "gray"))

        for row in range(rows):
            line = ""
            for col in range(columns):
                idx = row + col * rows
                if idx < len(fossil_entries):
                    entry = fossil_entries[idx]
                    entry_padded = entry + " " * (20 - len(self.strip_ansi(entry)))
                    line += entry_padded
            print(line)
        input(self.color_text("\n(Press Enter to return)", "white"))

    def merchant_menu(self):
        self.clear_screen()
        print(self.color_text("🧙‍♂️ Joji, the Morning Merchant", "bright_yellow"))
        print(self.color_text("═" * 40, "bright_cyan"))
        print(self.color_text("Welcome! Take a look at my goods:", "white"))
        print(self.color_text(f"\n💰 Money: ${self.game.player.money}", "white"))
        print()

        print(self.color_text("🌱 Seeds:", "bright_blue"))
        for key, seed in self.game.merchant_system.inventory["seeds"].items():
            already_unlocked = seed["crop"] in self.game.crop_system.unlocked_crops
            item_name = self.color_text(key, "gray" if already_unlocked else "cyan")
            unlock = self.color_text(f"(Unlocks {seed['crop'].capitalize()})", "grey")
            inflated = (
                hasattr(self.game, "market_inflated") and self.game.market_inflated
            )
            price_display = f"${seed['price'] * 2}" if inflated else f"${seed['price']}"
            inflated_tag = self.color_text(" [INFLATED]", "red") if inflated else ""
            print(f" - {item_name}: {price_display} {unlock}{inflated_tag}")

        print()
        print(self.color_text("🎁 Items:", "bright_blue"))
        for key, item in self.game.merchant_system.inventory["items"].items():
            already_owned = False
            if (
                item.get("unlocks") == "fishing"
                and self.game.merchant_system.fishing_unlocked
            ):
                already_owned = True
            elif (
                item.get("effect") == "increase_event_chance"
                and hasattr(self.game.player, "event_bonus")
                and self.game.player.event_bonus == "lucky_egg"
            ):
                already_owned = True
            elif (
                item.get("effect") == "increase_max_stamina"
                and self.game.player.max_stamina > 5
            ):
                already_owned = True
            elif item.get("effect") == "cosmetic":
                already_owned = (
                    hasattr(self.game.player, "bought_hat")
                    and self.game.player.bought_hat
                )
            elif item.get("effect") == "unlock_anytime_sleep":
                already_owned = getattr(self.game.player, "can_sleep_anytime", False)

            item_name = self.color_text(key, "gray" if already_owned else "cyan")
            if "unlocks" in item:
                detail = self.color_text(
                    f"(Unlocks {item['unlocks'].capitalize()})", "grey"
                )
            elif "effect" in item:
                readable_effects = {
                    "cosmetic": "Visual cosmetic item",
                    "increase_event_chance": "Boosts daily events: 80% chance to occur each day!",
                    "increase_max_stamina": "Double your max stamina",
                    "unlock_night_work": "Allow you to work at night",
                    "unlock_anytime_sleep": "Sleep anytime to recover stamina.",
                }
                effect_description = readable_effects.get(item.get("effect", ""), "")
                detail = (
                    self.color_text(f"({effect_description})", "grey")
                    if effect_description
                    else ""
                )
            else:
                detail = ""
            inflated = (
                hasattr(self.game, "market_inflated") and self.game.market_inflated
            )
            price_display = f"${item['price'] * 2}" if inflated else f"${item['price']}"
            inflated_tag = self.color_text(" [INFLATED]", "red") if inflated else ""
            print(f" - {item_name}: {price_display} {detail}{inflated_tag}")

        choice = input(
            self.display_action_message(
                message="What would you like to buy?",
                cancellable=True,
                cancel_message=f"(type {self.color_text('item_key', 'cyan')} or '0' to cancel): ",
            )
        ).strip()

        if choice == "0":
            return
        narrative = False
        item = None
        if choice in self.game.merchant_system.inventory["seeds"]:
            msg = self.game.merchant_system.buy_seed(choice)
        elif choice in self.game.merchant_system.inventory["items"]:
            item = self.game.merchant_system.inventory["items"][choice]
            narrative = item.get("narrative", False)
            msg = self.game.merchant_system.buy_item(choice)
        else:
            msg = "Invalid option."

        error_keywords = ["invalid", "not enough"]
        is_error = msg is None or any(kw in msg.lower() for kw in error_keywords)

        if is_error:
            print(self.color_text(msg, "red"))
            time.sleep(self.MENU_COOLDOWN_TIME)
        elif narrative:
            print(self.color_text(msg, "green"))
            input(self.color_text("\n(Press Enter to continue)", "white"))
        else:
            print(self.color_text(msg, "green"))
            time.sleep(self.MENU_COOLDOWN_TIME)

    def fishing_menu(self):
        self.clear_screen()
        print(self.color_text("🎣 Fishing Spot", "bright_blue"))

        print(
            f"{self.color_text('1.', 'cyan')} Go fishing {self.color_text('(-2 ♥)', 'red')}"
        )
        print(f"{self.color_text('2.', 'cyan')} Sell all fish")

        choice = input(self.display_action_message(cancellable=True))
        if choice == "1":
            result = self.game.fishing_system.fish()
        elif choice == "2":
            result = self.game.fishing_system.sell_all_fish()
        else:
            return

        print(self.color_text(result, "green"))
        time.sleep(2)


# ==================== Ciclo do Dia ====================
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

    def get_durations_for_current_season(self) -> Dict[str, int]:
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
    def from_dict(cls, data: Dict[str, Any]):
        instance = cls(TimeSystem())
        instance.current_part_index = data["current_part_index"]
        instance.last_update_time = datetime.fromisoformat(data["last_update_time"])
        return instance


# ==================== Inicialização do Jogo ====================
def main():
    game_state = GameState()
    ui = TerminalUI(game_state)

    if not game_state.load():
        print("Starting new game...")
        time.sleep(1)

    try:
        print(">>> VERIFICANDO: start_game_loop existe")
        ui.start_game_loop()
    except KeyboardInterrupt:
        game_state.save()
        print("\nGame saved automatically!")
        sys.exit()


if __name__ == "__main__":
    main()

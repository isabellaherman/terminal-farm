from domain.player import Player
from domain.crop import Crop
from service.crop_system import CropSystem
from typing import Optional


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
                "fishing_rod": {"price": 6666, "unlocks": "fishing"},
                "golden_hat": {"price": 3333, "effect": "cosmetic", "narrative": True},
                "lucky_egg": {"price": 5000, "effect": "increase_event_chance"},
                "balatro_card": {"price": 7777, "effect": "increase_max_stamina"},
                "lantern": {"price": 5000, "effect": "unlock_night_work"},
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
        return "Item purchased."

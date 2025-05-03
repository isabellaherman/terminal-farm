import random
from domain.player import Player


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

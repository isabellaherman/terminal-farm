import random
from domain.player import Player
from domain.fish import Fish
from utils.constants import FishingConstants


class FishingSystem:
    def __init__(self, player: Player):
        self.player = player
        self.game = None
        self.caught_fish: list[Fish] = []

    def fish(self) -> str:
        if not self.player.has_stamina(FishingConstants.STAMINA_TO_FISH):
            return "Not enough stamina to fish."

        self.player.use_stamina(FishingConstants.STAMINA_TO_FISH)

        fish: Fish = FishingConstants.FISH_TYPES[random.choice(FishingConstants.FISHES)]
        self.caught_fish.append(fish)
        return f"You caught a {fish.name} worth ${fish.price}!"

    def sell_all_fish(self) -> str:
        if len(self.caught_fish) <= 0:
            return "You got no fish to sell!"

        bonus_multiplier = (
            1.5
            if getattr(self, "game", None)
            and getattr(self.game, "fishing_bonus", False)
            else 1.0
        )
        total = sum(int(fish.price * bonus_multiplier) for fish in self.caught_fish)
        self.player.earn_money(total)
        self.caught_fish = []
        return f"Sold all fish for ${total}!"

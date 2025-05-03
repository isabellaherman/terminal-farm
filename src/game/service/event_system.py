import random
from interfaces.game_system import IGameSystem
from service.farm_system import FarmSystem
from domain.player import Player


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

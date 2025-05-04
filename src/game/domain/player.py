from datetime import datetime
from typing import Any, Optional
from interfaces.serializable import ISerializable


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

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]) -> "Player":
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

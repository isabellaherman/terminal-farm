from typing import Any


from interfaces.serializable import ISerializable


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "cost": self.cost,
            "growth_time": self.growth_time,
            "value": self.value,
            "color": self.color,
            "stamina_cost": self.stamina_cost,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Crop":
        return cls(
            name=data["name"],
            cost=data["cost"],
            growth_time=data["growth_time"],
            value=data["value"],
            color=data["color"],
            stamina_cost=data["stamina_cost"],
        )

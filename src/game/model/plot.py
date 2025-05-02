from datetime import datetime
from typing import Optional, Any

from interfaces.serializable import ISerializable
from model.crop import Crop


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "crop": self.crop.to_dict() if self.crop else None,
            "planted_at": self.planted_at.isoformat() if self.planted_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Plot":
        crop_data = data["crop"]
        planted_at = data["planted_at"]

        return cls(
            crop=Crop.from_dict(crop_data) if crop_data else None,
            planted_at=datetime.fromisoformat(planted_at) if planted_at else None,
        )

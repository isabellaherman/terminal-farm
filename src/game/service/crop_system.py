from typing import Optional, Any, List
from model.crop import Crop
from interfaces.serializable import ISerializable


class CropSystem(ISerializable):
    def __init__(self):
        self.available_crops = self._load_default_crops()
        self.unlocked_crops = ["wheat"]

    def _load_default_crops(self) -> dict[str, Crop]:
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

    def to_dict(self) -> dict[str, Any]:
        return {"unlocked_crops": self.unlocked_crops}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CropSystem":
        system = cls()
        system.unlocked_crops = data["unlocked_crops"]
        return system

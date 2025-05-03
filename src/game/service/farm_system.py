from datetime import timedelta
import random
from typing import Optional, Tuple, Any
from domain.crop import Crop
from domain.plot import Plot
from interfaces.serializable import ISerializable


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

    def to_dict(self) -> dict[str, Any]:
        return {"plots": [plot.to_dict() for plot in self.plots]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FarmSystem":
        farm = cls(size=len(data["plots"]))
        farm.plots = [Plot.from_dict(plot_data) for plot_data in data["plots"]]
        return farm

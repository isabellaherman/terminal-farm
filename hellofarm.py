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
    def __init__(self, name: str, cost: int, growth_time: int, value: int, 
                 color: str, stamina_cost: float):
        self.name = name
        self.cost = cost
        self.growth_time = growth_time
        self.value = value
        self.color = color
        self.stamina_cost = stamina_cost
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'cost': self.cost,
            'growth_time': self.growth_time,
            'value': self.value,
            'color': self.color,
            'stamina_cost': self.stamina_cost
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Crop':
        return cls(
            name=data['name'],
            cost=data['cost'],
            growth_time=data['growth_time'],
            value=data['value'],
            color=data['color'],
            stamina_cost=data['stamina_cost']
        )

class Plot(ISerializable):
    def __init__(self, crop: Optional[Crop] = None, planted_at: Optional[datetime] = None):
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
            'crop': self.crop.to_dict() if self.crop else None,
            'planted_at': self.planted_at.isoformat() if self.planted_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Plot':
        crop_data = data['crop']
        planted_at = data['planted_at']
        
        return cls(
            crop=Crop.from_dict(crop_data) if crop_data else None,
            planted_at=datetime.fromisoformat(planted_at) if planted_at else None
        )

class Player(ISerializable):
    def __init__(self, money: int = 50, stamina: float = 5.0, 
                 max_stamina: int = 5, last_sleep_time: Optional[datetime] = None):
        self.money = money
        self.stamina = stamina
        self.max_stamina = max_stamina
        self.last_sleep_time = last_sleep_time or datetime.now()
    
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
            'money': self.money,
            'stamina': self.stamina,
            'max_stamina': self.max_stamina,
            'last_sleep_time': self.last_sleep_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        return cls(
            money=data['money'],
            stamina=data['stamina'],
            max_stamina=data['max_stamina'],
            last_sleep_time=datetime.fromisoformat(data['last_sleep_time'])
        )

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
        return {
            'plots': [plot.to_dict() for plot in self.plots]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FarmSystem':
        farm = cls(size=len(data['plots']))
        farm.plots = [Plot.from_dict(plot_data) for plot_data in data['plots']]
        return farm

class CropSystem(ISerializable):
    def __init__(self):
        self.available_crops = self._load_default_crops()
        self.unlocked_crops = ['wheat']
    
    def _load_default_crops(self) -> Dict[str, Crop]:
        return {
            'wheat': Crop('wheat', 10, 10, 20, 'yellow', 0.5),
            'corn': Crop('corn', 20, 20, 45, 'bright_yellow', 0.5),
            'pumpkin': Crop('pumpkin', 40, 40, 100, 'orange', 1.0)
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
        return {
            'unlocked_crops': self.unlocked_crops
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CropSystem':
        system = cls()
        system.unlocked_crops = data['unlocked_crops']
        return system

class WeatherSystem(IGameSystem):
    WEATHER_TYPES = ['sunny', 'rainy', 'cloudy', 'windy']
    
    def __init__(self):
        self.current_weather = 'sunny'
    
    def update(self):
        if random.random() < 0.2:
            self.current_weather = random.choice(self.WEATHER_TYPES)
    
    def get_weather(self) -> str:
        return self.current_weather
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_weather': self.current_weather
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeatherSystem':
        system = cls()
        system.current_weather = data['current_weather']
        return system

class TimeSystem(IGameSystem):
    def __init__(self):
        self.day = 1
    
    def update(self):
        self.day += 1
    
    def get_day(self) -> int:
        return self.day
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'day': self.day
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeSystem':
        system = cls()
        system.day = data['day']
        return system

class EventSystem(IGameSystem):
    def __init__(self, farm: FarmSystem, player: Player):
        self.farm = farm
        self.player = player
        self.last_event_day = -1
    
    def update(self, current_day: int):
        if random.random() < 0.8 and self.last_event_day != current_day:
            self.last_event_day = current_day
            event = random.choice([
                self._storm_event,
                self._sunny_bonus_event,
                self._found_money_event,
                self._found_energy_event
            ])
            return event()
        return None
    
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
    
    def next_day(self) -> Tuple[bool, Optional[str]]:
        """Advance to next day, returns (success, event_message)"""
        if not self.player.has_stamina(1.0):
            return False, None
        
        self.player.use_stamina(1.0)
        self.time_system.update()
        self.weather_system.update()
        self.day_cycle_system = DayCycleSystem(self.time_system)
        
        unlock_message = None
        if self.time_system.day == 3 and 'corn' not in self.crop_system.unlocked_crops:
            unlock_message = self.crop_system.unlock_crop('corn')
        elif self.time_system.day == 7 and 'pumpkin' not in self.crop_system.unlocked_crops:
            unlock_message = self.crop_system.unlock_crop('pumpkin')
        
        event_message = self.event_system.update(self.time_system.day)
        
        return True, unlock_message or event_message
    
    def save(self) -> bool:
        try:
            with open(self.SAVE_FILE, 'w') as f:
                json.dump(self.to_dict(), f)
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load(self) -> bool:
        try:
            if not os.path.exists(self.SAVE_FILE):
                return False
            
            with open(self.SAVE_FILE, 'r') as f:
                data = json.load(f)
                self.from_dict(data, fallback=True)
            
            time_passed = datetime.now() - self.player.last_sleep_time
            hours_passed = time_passed.total_seconds() / 3600
            stamina_to_restore = min(int(hours_passed / 2), 
                                   self.player.max_stamina - self.player.stamina)
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
            'player': self.player.to_dict(),
            'farm': self.farm.to_dict(),
            'crop_system': self.crop_system.to_dict(),
            'weather_system': self.weather_system.to_dict(),
            'time_system': self.time_system.to_dict(),
            'day_cycle_system': self.day_cycle_system.to_dict()
        }
    
    def from_dict(self, data: Dict[str, Any], fallback: bool = False):
        self.player = Player.from_dict(data['player'])
        self.farm = FarmSystem.from_dict(data['farm'])
        self.farm.game = self
        self.crop_system = CropSystem.from_dict(data['crop_system'])
        self.weather_system = WeatherSystem.from_dict(data['weather_system'])
        self.time_system = TimeSystem.from_dict(data['time_system'])
        if 'day_cycle_system' in data:
            self.day_cycle_system = DayCycleSystem.from_dict(data['day_cycle_system'])
        elif fallback:
            self.day_cycle_system = DayCycleSystem(self.time_system)
        self.event_system = EventSystem(self.farm, self.player)
        self.event_system.game = self

# ==================== Interface do Usuário ====================
class TerminalUI:
    def display_status(self):
        weather = self.game.weather_system.get_weather()
        weather_icon = self.WEATHER_ICONS.get(weather, '')
        money_text = f"💰 Money: ${self.game.player.money}"
        weather_text = f"Weather: {weather_icon} {weather.capitalize()}"

        header_width = self.last_box_width if hasattr(self, 'last_box_width') else 50
        content = f"{money_text}   {weather_text}"
        

        print(self.color_text('═' * header_width, 'bright_cyan'))
        print(content)
        print(self.color_text('═' * header_width, 'bright_cyan'))
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
                else:
                    bg_color = "orange"
                slot_text = str(plot_idx + 1).center(9)
                content_text = crop.name[:7].center(9) if crop else "Empty".center(9)
                spacer = " "

                row_lines[0] += self.bg_color_text(slot_text, "white", bg_color) + spacer
                row_lines[1] += self.bg_color_text(content_text, "white", bg_color) + spacer
                row_lines[2] += self.bg_color_text(" " * 9, "white", bg_color) + spacer

            for line in row_lines:
                print(line)
            print()
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
        "heart_red": "\033[38;5;161m"
    }
    # ==================== Cores de Fundo ====================
    BG_COLORS = {
        "reset": "\033[0m",
        "orange": "\033[48;5;94m",
        "yellow_pastel": "\033[48;5;187m",
        "gray": "\033[48;5;240m",
        "green": "\033[42m"
    }

    def bg_color_text(self, text: str, fg_color: str, bg_color: str) -> str:
        fg = self.COLORS.get(fg_color, "")
        bg = self.BG_COLORS.get(bg_color, "")
        return f"{bg}{fg}{text}{self.COLORS['reset']}"
    
    WEATHER_ICONS = {
        "sunny": "☀️",
        "rainy": "🌧️",
        "cloudy": "☁️",
        "windy": "🌬️"
    }
    
    def __init__(self, game_state: GameState):
        self.game = game_state
    
    def clear_screen(self):
        print("\033[H\033[J")
    
    def color_text(self, text: str, color: str) -> str:
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"

    def strip_ansi(self, text: str) -> str:
        import re
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)
    
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
        icons = {
            "spring": "🌸",
            "summer": "☀️",
            "autumn": "🍂",
            "winter": "❄️"
        }
        return icons.get(self.game.day_cycle_system.get_season(), "")
    
    def display_header(self):
        import getpass
        username = getpass.getuser()
        greeting = self.get_greeting()
        stamina_display = self.display_stamina(self.game.player.stamina, self.game.player.max_stamina)
        season = self.game.day_cycle_system.get_season().capitalize()
        current_part = self.game.day_cycle_system.get_current_part().capitalize()
        season_icon = self.get_season_icon()
        day = self.game.time_system.day

        TITLE_LINE_LEFT = "🌱 TERMINAL FARM"
        TITLE_LINE_RIGHT = f"Day {day} ({current_part}) {season_icon} {season}"
        GREETING_LINE = f"{greeting}, {username}!"
        STAMINA_LINE = f"Stamina: {stamina_display}"

        raw_title_left = TITLE_LINE_LEFT
        raw_title_right = TITLE_LINE_RIGHT
        raw_greeting = GREETING_LINE
        raw_stamina = STAMINA_LINE

        content_width = max(
            len(TITLE_LINE_LEFT) + len(TITLE_LINE_RIGHT) + 2,
            len(raw_greeting),
            len(self.strip_ansi(stamina_display)) + len("Stamina: ")
        ) + 6
        BOX_WIDTH = content_width
        BOX_BORDER_HORIZONTAL = "═" * BOX_WIDTH

        spacing = BOX_WIDTH - len(TITLE_LINE_LEFT) - len(TITLE_LINE_RIGHT) - 2
        TITLE_LINE = f"{TITLE_LINE_LEFT}{' ' * spacing}{TITLE_LINE_RIGHT}"

        centered_title = TITLE_LINE
        title_line = f"{self.color_text('║', 'bright_cyan')}{self.color_text(centered_title.ljust(BOX_WIDTH - 2), 'bright_green')}{self.color_text('║', 'bright_cyan')}"
        greeting_line = f"{self.color_text('║', 'bright_cyan')}  {self.color_text(raw_greeting.ljust(BOX_WIDTH - 4), 'green')}  {self.color_text('║', 'bright_cyan')}"
        stamina_text = f"Stamina: {stamina_display}"
        padding = (BOX_WIDTH - 4) - len(self.strip_ansi(stamina_text))
        stamina_line = f"{self.color_text('║', 'bright_cyan')}  {stamina_text}{' ' * padding}  {self.color_text('║', 'bright_cyan')}"

        print(self.color_text(f'╔{BOX_BORDER_HORIZONTAL}╗', 'bright_cyan'))
        print(title_line)
        print(self.color_text(f'╠{BOX_BORDER_HORIZONTAL}╣', 'bright_cyan'))
        print(greeting_line)
        print(stamina_line)
        self.last_box_width = BOX_WIDTH
        print(self.color_text(f'╚{BOX_BORDER_HORIZONTAL}╝', 'bright_cyan'))

    def plant_crop_menu(self):
        self.display_farm()
        unlocked_crops = self.game.crop_system.get_unlocked_crops()
        
        print(f"{self.color_text('Available Crops:', 'bright_blue')}")
        for i, crop in enumerate(unlocked_crops, 1):
            cost = self.color_text(f"${crop.cost}", "yellow")
            value = self.color_text(f"${crop.value}", "bright_yellow")
            stamina = self.color_text(f"{crop.stamina_cost}♥", "pink")
            print(f"{self.color_text(f'{i}.', 'white')} {self.color_text(crop.name.capitalize(), crop.color)} "
                  f"(Cost: {cost}, Value: {value}, Stamina: {stamina}, Time: {crop.growth_time}s)")
        
        try:
            choice = input(f"\n{self.color_text('Choose crop to plant', 'bright_cyan')} (0 to cancel): ")
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
                print(f"{self.color_text(f'{i+1}-{i+3}', 'cyan')} ", end="")
            print("\n")
            
            plot = int(input(f"{self.color_text('Choose plot', 'bright_cyan')} (1-9): ")) - 1
            if plot < 0 or plot > 8:
                return
            
            if not self.game.farm.plots[plot].is_empty:
                input(f"{self.color_text('Plot already occupied!', 'red')} Press Enter...")
                return
                
            self.game.player.spend_money(crop.cost)
            self.game.player.use_stamina(crop.stamina_cost)
            self.game.farm.plant_crop(plot, crop)
            print(f"\n{self.color_text(f'Planted {crop.name} in plot {plot+1}!', 'green')}")
            time.sleep(1)
            
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
            print(f"{self.color_text(f'Harvested crops worth ${harvested_value}!', 'green')}")
        else:
            print(f"{self.color_text('Nothing ready to harvest yet!', 'yellow')}")
        time.sleep(1)

    def sleep_menu(self):
        self.clear_screen()
        print(f"{self.color_text('Sleep Options:', 'bright_blue')}\n")
        print(f"1. {self.color_text('Sleep until next day', 'cyan')} (Recover all hearts)")
        print(f"2. {self.color_text('Take a nap (2 hours)', 'cyan')} (Recover 1 heart)")
        print(f"3. {self.color_text('Cancel', 'red')}")
        
        choice = input("\nChoose option: ")
        if choice == "1":
            success, message = self.game.next_day()
            self.game.player.full_restore()
            self.game.player.last_sleep_time = datetime.now()
            
            print(self.color_text("\nYou slept soundly and woke up refreshed the next day!", "bright_green"))
            if message:
                print(f"{self.color_text('EVENT:', 'bright_blue')} {message}")
            time.sleep(2)
        elif choice == "2":
            self.game.player.restore_stamina(1)
            self.game.player.last_sleep_time = datetime.now()
            print(self.color_text("\nYou took a refreshing nap and recovered 1 heart!", "green"))
            time.sleep(1)

    def start_game_loop(self):
        while True:
            self.display_farm()
            print(f"{self.color_text('Actions:', 'bright_blue')}\n")
            print(f"  {self.color_text('1.', 'cyan')} {self.color_text('Plant Crop', 'bright_green')}     "
                  f"{self.color_text('2.', 'cyan')} {self.color_text('Harvest Crops', 'grey')}     "
                  f"{self.color_text('3.', 'cyan')} {self.color_text('Next Day', 'grey')}")
            print(f"  {self.color_text('4.', 'cyan')} {self.color_text('Sleep/Rest', 'grey')}     "
                  f"{self.color_text('5.', 'cyan')} {self.color_text('Save & Quit', 'grey')}     "
                  f"{self.color_text('6.', 'cyan')} {self.color_text('Reset Game', 'red')}")
            
            choice = input(f"\n{self.color_text('Choose action:', 'bright_cyan')} ")
            
            if choice == "1":
                self.plant_crop_menu()
            elif choice == "2":
                self.harvest_menu()
            elif choice == "3":
                success, message = self.game.next_day()
                if success:
                    print(f"{self.color_text('Advanced to day', 'blue')} "
                          f"{self.color_text(self.game.time_system.day, 'bright_blue')}!")
                    if message:
                        print(f"{self.color_text('EVENT:', 'bright_blue')} {message}")
                    time.sleep(2)
                else:
                    input(f"{self.color_text('Not enough stamina!', 'red')} Press Enter...")
            elif choice == "4":
                self.sleep_menu()
            elif choice == "5":
                if self.game.save():
                    print(f"\n{self.color_text('Game saved!', 'green')}")
                    sys.exit()
            elif choice == "6":
                confirm = input(self.color_text("Are you sure you want to reset? (y/n): ", "red"))
                if confirm.lower() == 'y':
                    self.game.new_game()
                    print(self.color_text("Game reset!", "green"))
                    time.sleep(1)
            else:
                print(f"{self.color_text('Invalid choice!', 'red')}")
                time.sleep(1)
# ==================== Ciclo do Dia ====================
class DayCycleSystem(ISerializable):
    PARTS = ["morning", "afternoon", "evening"]

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
            return {"morning": 4, "afternoon": 4, "evening": 2}
        elif season == "winter":
            return {"morning": 3, "afternoon": 3, "evening": 4}
        else:
            return {"morning": 3, "afternoon": 3, "evening": 3}

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

    def to_dict(self):
        return {
            'current_part_index': self.current_part_index,
            'last_update_time': self.last_update_time.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        instance = cls(TimeSystem())
        instance.current_part_index = data['current_part_index']
        instance.last_update_time = datetime.fromisoformat(data['last_update_time'])
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
        print(f"\nGame saved automatically!")
        sys.exit()

if __name__ == "__main__":
    main()
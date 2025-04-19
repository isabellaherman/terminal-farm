import os
import json
import time
import random
import sys
from datetime import datetime, timedelta

class TerminalFarm:
    SAVE_FILE = "terminal_farmer_save.json"
    
    def __init__(self):
        self.colors = {
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
        
        # Sistema de stamina (corações)
        self.max_stamina = 5
        self.stamina = 5
        self.last_sleep_time = datetime.now()
        
        # Cultivos padrão (agora com custo de stamina)
        self.default_crops = {
            "wheat": {"cost": 10, "growth_time": 10, "value": 20, "color": "yellow", "stamina_cost": 0.5},
            "corn": {"cost": 20, "growth_time": 20, "value": 45, "color": "bright_yellow", "stamina_cost": 0.5},
            "pumpkin": {"cost": 40, "growth_time": 40, "value": 100, "color": "orange", "stamina_cost": 1}
        }
        
        if os.path.exists(self.SAVE_FILE):
            self.load_game()
        else:
            self.new_game()
    
    def new_game(self):
        self.money = 50
        self.farm = [None] * 9
        self.crops = self.default_crops.copy()
        self.unlocked_crops = ["wheat"]
        self.day = 1
        self.weather = "sunny"
        self.stamina = self.max_stamina
        self.last_sleep_time = datetime.now()
    
    def save_game(self):
        try:
            farm_data = []
            for plot in self.farm:
                if plot is None:
                    farm_data.append(None)
                else:
                    crop, planted_at = plot
                    farm_data.append({
                        "crop": crop,
                        "planted_at": planted_at.isoformat()
                    })
            
            save_data = {
                "money": self.money,
                "farm": farm_data,
                "unlocked_crops": self.unlocked_crops,
                "day": self.day,
                "weather": self.weather,
                "stamina": self.stamina,
                "last_sleep_time": self.last_sleep_time.isoformat(),
                "max_stamina": self.max_stamina
            }
            
            with open(self.SAVE_FILE, 'w') as f:
                json.dump(save_data, f)
            return True
        except Exception as e:
            print(self.color_text(f"Error saving game: {e}", "red"))
            return False
    
    def load_game(self):
        try:
            with open(self.SAVE_FILE, 'r') as f:
                save_data = json.load(f)
            
            self.money = save_data["money"]
            self.farm = []
            for plot in save_data["farm"]:
                if plot is None:
                    self.farm.append(None)
                else:
                    self.farm.append((
                        plot["crop"],
                        datetime.fromisoformat(plot["planted_at"])
                    ))
            self.unlocked_crops = save_data["unlocked_crops"]
            self.day = save_data["day"]
            self.weather = save_data["weather"]
            self.stamina = save_data.get("stamina", self.max_stamina)
            self.max_stamina = save_data.get("max_stamina", 5)
            self.last_sleep_time = datetime.fromisoformat(save_data.get("last_sleep_time", datetime.now().isoformat()))
            self.crops = self.default_crops.copy()
            
            # Restaurar stamina baseado no tempo passado
            self.restore_stamina_over_time()
            
        except Exception as e:
            print(self.color_text(f"Error loading save: {e}, starting new game", "red"))
            time.sleep(2)
            self.new_game()
    
    def restore_stamina_over_time(self):
        """Restaura stamina baseado no tempo desde o último jogo"""
        time_passed = datetime.now() - self.last_sleep_time
        hours_passed = time_passed.total_seconds() / 3600
        
        # Restaura 1 coração a cada 2 horas
        stamina_to_restore = min(int(hours_passed / 2), self.max_stamina - self.stamina)
        if stamina_to_restore > 0:
            self.stamina += stamina_to_restore
            print(self.color_text(f"\nVocê descansou e recuperou {stamina_to_restore} coração(s) enquanto estava fora!", "pink"))
            time.sleep(1)
    
    def color_text(self, text, color):
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
    
    def display_stamina(self):
        """Mostra a barra de stamina com corações"""
        full_hearts = int(self.stamina)
        half_heart = (self.stamina - full_hearts) >= 0.5
        empty_hearts = self.max_stamina - full_hearts - (1 if half_heart else 0)
        
        hearts = []
        hearts.extend([self.color_text("♥", "heart_red")] * full_hearts)
        if half_heart:
            hearts.append(self.color_text("♥", "pink"))
        hearts.extend([self.color_text("♡", "gray")] * empty_hearts)
        
        return " ".join(hearts)
    
    def clear_screen(self):
        print("\033[H\033[J")
    
    def get_greeting(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        else:
            return "Good night"
    
    def display_header(self):
        import getpass
        username = getpass.getuser()
        greeting = self.get_greeting()
        
        stamina_display = self.display_stamina()

        BOX_WIDTH = 44
        INNER_WIDTH = BOX_WIDTH - 2 
        BOX_BORDER_HORIZONTAL = "═" * BOX_WIDTH
        BOX_TITLE_SPACING = 20 
        GREETING_PADDING = 39  
        STAMINA_PADDING = 24  

        header = f"""
{self.color_text(f'╔{BOX_BORDER_HORIZONTAL}╗', 'bright_cyan')}
{self.color_text('║', 'bright_cyan')}  {self.color_text('🌱 TERMINAL FARM', 'bright_green')}{' ' * (BOX_TITLE_SPACING - len(str(self.day)))}{self.color_text(f'Day {self.day}', 'yellow')}  {self.color_text('║', 'bright_cyan')}
{self.color_text(f'╠{BOX_BORDER_HORIZONTAL}╣', 'bright_cyan')}
{self.color_text('║', 'bright_cyan')}  {self.color_text(f'{greeting}, {username}!', 'green')}{' ' * (GREETING_PADDING - len(greeting) - len(username))}{self.color_text('║', 'bright_cyan')}
{self.color_text('║', 'bright_cyan')}  Stamina: {stamina_display}{' ' * STAMINA_PADDING}{self.color_text('║', 'bright_cyan')}
{self.color_text(f'╚{BOX_BORDER_HORIZONTAL}╝', 'bright_cyan')}
"""
        print(header)
    
    def display_status(self):
        weather_icons = {
            "sunny": "☀️",
            "rainy": "🌧️",
            "cloudy": "☁️",
            "windy": "🌬️"
        }
        
        status = f"""
{self.color_text('══════════════════════════════════════════════', 'bright_cyan')}
{self.color_text('💰 Money:', 'bright_yellow')} {self.color_text(f'${self.money}', 'yellow')}   {self.color_text('Weather:', 'bright_blue')} {weather_icons.get(self.weather, '')} {self.color_text(self.weather.capitalize(), 'blue')}
{self.color_text('══════════════════════════════════════════════', 'bright_cyan')}
"""
        print(status)
    
    def display_farm(self):
        self.clear_screen()
        self.display_header()
        self.display_status()
        
        print(f"{self.color_text('🌱 Farm Layout:', 'bright_green')}\n")
        
        for i in range(0, 9, 3):
            row = []
            for j in range(3):
                plot = self.farm[i+j]
                if plot:
                    crop, planted_at = plot
                    crop_info = self.crops[crop]
                    growth_time = crop_info["growth_time"]
                    elapsed = (datetime.now() - planted_at).total_seconds()
                    growth_percent = min(100, int((elapsed / growth_time) * 100))
                    
                    if growth_percent < 33:
                        growth_color = "red"
                    elif growth_percent < 66:
                        growth_color = "yellow"
                    else:
                        growth_color = "green"
                    
                    if growth_percent < 100:
                        display_text = f"{self.color_text(crop[0].upper(), crop_info['color'])}:{self.color_text(f'{growth_percent}%', growth_color)}"
                    else:
                        display_text = f"{self.color_text(crop[0].upper(), crop_info['color'])}:{self.color_text('READY!', 'bright_green')}"
                else:
                    display_text = self.color_text("[Empty]", "gray")
                
                row.append(display_text)
            
            print("  ".join(row))
        
        print("\n")
    
    def use_stamina(self, amount):
        """Tenta usar stamina e retorna True se bem-sucedido"""
        if self.stamina >= amount:
            self.stamina -= amount
            return True
        print(self.color_text(f"\nVocê está muito cansado! Precisa de {amount} coração(ões) para esta ação.", "red"))
        time.sleep(1)
        return False
    
    def plant_crop(self):
        self.display_farm()
        print(f"{self.color_text('Available Crops:', 'bright_blue')}")
        for i, crop in enumerate(self.unlocked_crops, 1):
            crop_info = self.crops[crop]
            cost = self.color_text(f"${crop_info['cost']}", "yellow")
            value = self.color_text(f"${crop_info['value']}", "bright_yellow")
            stamina = self.color_text(f"{crop_info['stamina_cost']}♥", "pink")
            print(f"{self.color_text(f'{i}.', 'white')} {self.color_text(crop.capitalize(), crop_info['color'])} "
                  f"(Cost: {cost}, Value: {value}, Stamina: {stamina}, Time: {crop_info['growth_time']}s)")
        
        try:
            choice = input(f"\n{self.color_text('Choose crop to plant', 'bright_cyan')} (0 to cancel): ")
            if choice == "0":
                return
            choice = int(choice) - 1
            crop = self.unlocked_crops[choice]
            crop_info = self.crops[crop]
            
            if not self.use_stamina(crop_info["stamina_cost"]):
                return
                
            if self.money < crop_info["cost"]:
                input(f"{self.color_text('Not enough money!', 'red')} Press Enter...")
                return
                
            print(f"\n{self.color_text('Farm Layout:', 'bright_green')}")
            for i in range(0, 9, 3):
                print(f"{self.color_text(f'{i+1}-{i+3}', 'cyan')} ", end="")
            print("\n")
            
            plot = int(input(f"{self.color_text('Choose plot', 'bright_cyan')} (1-9): ")) - 1
            if plot < 0 or plot > 8:
                return
            if self.farm[plot]:
                input(f"{self.color_text('Plot already occupied!', 'red')} Press Enter...")
                return
                
            self.money -= crop_info["cost"]
            self.farm[plot] = (crop, datetime.now())
            print(f"\n{self.color_text(f'Planted {crop} in plot {plot+1}!', 'green')}")
            time.sleep(1)
            
        except (ValueError, IndexError):
            input(f"{self.color_text('Invalid choice!', 'red')} Press Enter...")
            return
    
    def harvest_crop(self):
        if not self.use_stamina(0.5):  # Custa meio coração para colher
            return
            
        harvested = False
        for i in range(len(self.farm)):
            if self.farm[i]:
                crop, planted_at = self.farm[i]
                growth_time = self.crops[crop]["growth_time"]
                elapsed = (datetime.now() - planted_at).total_seconds()
                if elapsed >= growth_time:
                    self.money += self.crops[crop]["value"]
                    self.farm[i] = None
                    harvested = True
                    print(f"{self.color_text('Harvested', 'green')} {self.color_text(crop, self.crops[crop]['color'])} "
                          f"for {self.color_text('$' + str(self.crops[crop]['value']), 'bright_yellow')}!")
        
        if not harvested:
            print(f"{self.color_text('Nothing ready to harvest yet!', 'yellow')}")
        time.sleep(1)
    
    def check_unlocks(self):
        if self.day == 3 and "corn" not in self.unlocked_crops:
            self.unlocked_crops.append("corn")
            print(f"\n{self.color_text('NEW CROP UNLOCKED: Corn!', 'bright_yellow')}")
            time.sleep(1)
        if self.day == 7 and "pumpkin" not in self.unlocked_crops:
            self.unlocked_crops.append("pumpkin")
            print(f"\n{self.color_text('NEW CROP UNLOCKED: Pumpkin!', 'bright_yellow')}")
            time.sleep(1)
        
    def next_day(self):
        if not self.use_stamina(1):  # Passar o dia custa 1 coração
            return
            
        self.day += 1
        self.change_weather()
        self.check_unlocks()
        
        if random.random() < 0.2:
            self.random_event()
    
    def change_weather(self):
        weather_types = ["sunny", "rainy", "cloudy", "windy"]
        self.weather = random.choice(weather_types)
    
    def random_event(self):
        events = [
            ("A storm came! Some crops were damaged.", lambda: self.damage_random_crop()),
            ("Sunny day bonus! Crops grow faster today.", lambda: self.growth_bonus()),
            ("You found money on the ground!", lambda: self.found_money()),
            ("You found an energy drink! +1 heart", lambda: self.found_energy())
        ]
        event_text, event_func = random.choice(events)
        print(f"\n{self.color_text('EVENT:', 'bright_blue')} {event_text}")
        event_func()
        time.sleep(2)
    
    def damage_random_crop(self):
        occupied_plots = [i for i, plot in enumerate(self.farm) if plot]
        if occupied_plots:
            plot = random.choice(occupied_plots)
            self.farm[plot] = None
    
    def growth_bonus(self):
        for i in range(len(self.farm)):
            if self.farm[i]:
                crop, planted_at = self.farm[i]
                new_planted_at = planted_at - timedelta(seconds=self.crops[crop]["growth_time"] * 0.2)
                self.farm[i] = (crop, new_planted_at)
    
    def found_money(self):
        amount = random.randint(10, 50)
        self.money += amount
        print(f"{self.color_text('Found', 'green')} {self.color_text(f'${amount}', 'bright_yellow')}!")
    
    def found_energy(self):
        self.stamina = min(self.max_stamina, self.stamina + 1)
    
    def sleep_options(self):
        self.clear_screen()
        print(f"{self.color_text('Sleep Options:', 'bright_blue')}\n")
        print(f"1. {self.color_text('Sleep until next day', 'cyan')} (Recupera todos os corações)")
        print(f"2. {self.color_text('Take a nap (2 hours)', 'cyan')} (Recupera 1 coração)")
        print(f"3. {self.color_text('Cancel', 'red')}")
        
        choice = input("\nChoose option: ")
        if choice == "1":
            self.day += 1
            self.stamina = self.max_stamina
            self.last_sleep_time = datetime.now()
            self.change_weather()
            self.check_unlocks()
            print(self.color_text("\nVocê dormiu profundamente e acordou renovado no próximo dia!", "bright_green"))
            time.sleep(1)
        elif choice == "2":
            # Restaura 1 coração por 2 horas de descanso
            self.stamina = min(self.max_stamina, self.stamina + 1)
            self.last_sleep_time = datetime.now()
            print(self.color_text("\nVocê tirou uma soneca revigorante e recuperou 1 coração!", "green"))
            time.sleep(1)
    
    def reset_game(self):
        try:
            if os.path.exists(self.SAVE_FILE):
                os.remove(self.SAVE_FILE)
            print(self.color_text("Game reset successfully!", "green"))
            time.sleep(1)
            self.new_game()
        except Exception as e:
            print(self.color_text(f"Error resetting game: {e}", "red"))
            time.sleep(1)
    
    def main_loop(self):
        while True:
            self.display_farm()
            print(f"{self.color_text('Actions:', 'bright_blue')}")
            print(f"  {self.color_text('1.', 'cyan')} {self.color_text('Plant Crop', 'bright_green')}")
            print(f"  {self.color_text('2.', 'cyan')} {self.color_text('Harvest Crops', 'yellow')}")
            print(f"  {self.color_text('3.', 'cyan')} {self.color_text('Next Day', 'bright_blue')}")
            print(f"  {self.color_text('4.', 'cyan')} {self.color_text('Sleep/Rest', 'pink')}")
            print(f"  {self.color_text('5.', 'cyan')} {self.color_text('Save & Quit', 'blue')}")
            print(f"  {self.color_text('6.', 'cyan')} {self.color_text('Reset Game', 'red')}")
            
            choice = input(f"\n{self.color_text('Choose action:', 'bright_cyan')} ")
            
            if choice == "1":
                self.plant_crop()
            elif choice == "2":
                self.harvest_crop()
            elif choice == "3":
                self.next_day()
            elif choice == "4":
                self.sleep_options()
            elif choice == "5":
                if self.save_game():
                    print(f"\n{self.color_text('Game saved!', 'green')}")
                    sys.exit()
            elif choice == "6":
                confirm = input(self.color_text("Are you sure you want to reset? (y/n): ", "red"))
                if confirm.lower() == 'y':
                    self.reset_game()
            else:
                print(f"{self.color_text('Invalid choice!', 'red')}")
                time.sleep(1)

if __name__ == "__main__":
    game = TerminalFarm()
    try:
        game.main_loop()
    except KeyboardInterrupt:
        game.save_game()
        print(f"\n{game.color_text('Game saved automatically!', 'green')}")
        sys.exit()
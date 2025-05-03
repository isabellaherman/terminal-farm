from datetime import datetime
from service.game_state import GameState
import time
import sys
from utils.constants import TUIConstants


class TerminalUI:
    MENU_COOLDOWN_TIME = 2.6

    def display_status(self):
        weather = self.game.weather_system.get_weather()
        weather_icon = TUIConstants.WEATHER_ICONS.get(weather, "")
        money_text = f"💰 Money: ${self.game.player.money}"
        weather_text = f"Weather: {weather_icon}  {weather.capitalize()}"

        header_width = self.last_box_width if hasattr(self, "last_box_width") else 50
        content = f"{money_text}   {weather_text}"

        print(self.color_text("═" * header_width, "bright_cyan"))
        print(content)
        print(self.color_text("═" * header_width, "bright_cyan"))

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
                    fg_color = "white" if progress >= 1.0 else "gray"
                else:
                    bg_color = "orange"
                    fg_color = "white"
                slot_text = str(plot_idx + 1).center(9)
                content_text = crop.name[:7].center(9) if crop else "Empty".center(9)
                spacer = " "

                row_lines[0] += (
                    self.bg_color_text(slot_text, fg_color, bg_color) + spacer
                )
                row_lines[1] += (
                    self.bg_color_text(content_text, fg_color, bg_color) + spacer
                )
                row_lines[2] += self.bg_color_text(" " * 9, fg_color, bg_color) + spacer

            for line in row_lines:
                print(line)
            print()

    def bg_color_text(self, text: str, fg_color: str, bg_color: str) -> str:
        fg = TUIConstants.COLORS.get(fg_color, "")
        bg = TUIConstants.BG_COLORS.get(bg_color, "")
        return f"{bg}{fg}{text}{TUIConstants.COLORS['reset']}"

    def __init__(self, game_state: GameState):
        self.game = game_state

    def clear_screen(self):
        print("\033[H\033[J")

    def color_text(self, text: str, color: str) -> str:
        return (
            f"{TUIConstants.COLORS.get(color, '')}{text}{TUIConstants.COLORS['reset']}"
        )

    def strip_ansi(self, text: str) -> str:
        import re

        ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", text)

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
        return TUIConstants.SEASON_ICONS.get(
            self.game.day_cycle_system.get_season(), ""
        )

    def display_action_message(
        self,
        cancellable: bool = False,
        message: str = "Choose action",
        cancel_message: str = "(0 to cancel): ",
    ) -> str:
        cancel_text = cancel_message if cancellable else ""
        return f"\n{self.color_text(message, 'bright_cyan')} {cancel_text}"

    def display_header(self):
        message = self.game.day_cycle_system.update()
        if message:
            print(self.color_text(message, "bright_cyan"))
        import getpass

        username = getpass.getuser()
        greeting = self.get_greeting()
        stamina_display = self.display_stamina(
            self.game.player.stamina, self.game.player.max_stamina
        )
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

        content_width = (
            max(
                len(TITLE_LINE_LEFT) + len(TITLE_LINE_RIGHT) + 2,
                len(raw_greeting),
                len(self.strip_ansi(stamina_display)) + len("Stamina: "),
            )
            + 6
        )
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

        print(self.color_text(f"╔{BOX_BORDER_HORIZONTAL}╗", "bright_cyan"))
        print(title_line)
        print(self.color_text(f"╠{BOX_BORDER_HORIZONTAL}╣", "bright_cyan"))
        print(greeting_line)
        print(stamina_line)
        self.last_box_width = BOX_WIDTH
        print(self.color_text(f"╚{BOX_BORDER_HORIZONTAL}╝", "bright_cyan"))

    def plant_crop_menu(self):
        self.display_farm()
        unlocked_crops = self.game.crop_system.get_unlocked_crops()

        print(f"{self.color_text('Available Crops:', 'bright_blue')}")
        for i, crop in enumerate(unlocked_crops, 1):
            cost = self.color_text(f"${crop.cost}", "yellow")
            value = self.color_text(f"${crop.value}", "bright_yellow")
            stamina = self.color_text(f"{crop.stamina_cost}♥", "pink")
            name = crop.name.capitalize()
            rare_tag = ""
            if "rare" in name.lower():
                name = name.replace(" [Rare]", "").replace(" [rare]", "")
                rare_tag = self.color_text(" [Rare]", "orange")
            name_display = self.color_text(name, crop.color)
            print(
                f"{self.color_text(f'{i}.', 'white')} {name_display} "
                f"(Cost: {cost}, Value: {value}, Stamina: {stamina}, Time: {crop.growth_time}s){rare_tag}"
            )

        try:
            choice = input(
                self.display_action_message(
                    message="Choose crop to plant", cancellable=True
                )
            )
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
                print(f"{self.color_text(f'{i + 1}-{i + 3}', 'cyan')} ", end="")
            print("\n")

            plot = (
                int(input(f"{self.color_text('Choose plot', 'bright_cyan')} (1-9): "))
                - 1
            )
            if plot < 0 or plot > 8:
                return

            if not self.game.farm.plots[plot].is_empty:
                input(
                    f"{self.color_text('Plot already occupied!', 'red')} Press Enter..."
                )
                return

            self.game.player.spend_money(crop.cost)
            self.game.player.use_stamina(crop.stamina_cost)
            self.game.farm.plant_crop(plot, crop)
            print(
                f"\n{self.color_text(f'Planted {crop.name} in plot {plot + 1}!', 'green')}"
            )
            time.sleep(self.MENU_COOLDOWN_TIME)

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
            print(
                f"{self.color_text(f'Harvested crops worth ${harvested_value}!', 'green')}"
            )
        else:
            print(f"{self.color_text('Nothing ready to harvest yet!', 'yellow')}")
        time.sleep(self.MENU_COOLDOWN_TIME)

    def sleep_menu(self):
        self.clear_screen()
        print(f"{self.color_text('Sleep Options:', 'bright_blue')}\n")
        print(
            f"{self.color_text('1.', 'cyan')} Sleep until next day {self.color_text(f'(Recover all {TUIConstants.EMOJI_HEART})', 'cyan')}"
        )
        print(
            f"{self.color_text('2.', 'cyan')} Take a nap (advance time) {self.color_text(f'(+1 {TUIConstants.EMOJI_HEART})', 'cyan')}"
        )

        choice = input(self.display_action_message(cancellable=True))
        if choice == "1":
            if not self.game.day_cycle_system.is_night():
                print(
                    self.color_text(
                        "\nYou can only sleep at night… try taking a nap.", "red"
                    )
                )
                time.sleep(self.MENU_COOLDOWN_TIME)
                return
            success, message = self.game.next_day()
            self.game.player.full_restore()
            self.game.player.last_sleep_time = datetime.now()

            print(
                self.color_text(
                    "\nYou slept soundly and woke up refreshed the next day!",
                    "bright_green",
                )
            )
            if message:
                print(f"{self.color_text('EVENT:', 'bright_blue')} {message}")
            time.sleep(self.MENU_COOLDOWN_TIME)
        elif choice == "2":
            self.game.player.restore_stamina(1)

            self.game.day_cycle_system.current_part_index = (
                self.game.day_cycle_system.current_part_index + 1
            ) % len(self.game.day_cycle_system.PARTS)
            self.game.day_cycle_system.last_update_time = datetime.now()
            print(
                self.color_text(
                    f"\nYou took a nap and time passed... (+1 {TUIConstants.EMOJI_HEART})",
                    "green",
                )
            )
            time.sleep(self.MENU_COOLDOWN_TIME)

    def start_game_loop(self):
        while True:
            self.display_farm()
            print(self.color_text("Actions:", "bright_blue"))

            actions = []
            actions.append(
                f"{self.color_text('1.', 'cyan')} {self.color_text('Plant Crop', 'bright_green')}"
            )
            actions.append(
                f"{self.color_text('2.', 'cyan')} {self.color_text('Harvest Crops', 'grey')}"
            )
            actions.append(
                f"{self.color_text('3.', 'cyan')} {self.color_text('Next Day', 'grey')}"
            )
            actions.append(
                f"{self.color_text('4.', 'cyan')} {self.color_text('Sleep/Rest', 'grey')}"
            )
            actions.append(
                f"{self.color_text('5.', 'cyan')} {self.color_text('Save & Quit', 'grey')}"
            )
            actions.append(
                f"{self.color_text('6.', 'cyan')} {self.color_text('Reset Game', 'red')}"
            )

            if self.game.merchant_system.is_available(
                self.game.day_cycle_system.get_current_part()
            ):
                actions.append(
                    f"{self.color_text('7.', 'cyan')} {self.color_text('Joji the Merchant', 'bright_yellow')}"
                )

            if self.game.merchant_system.fishing_unlocked:
                actions.append(
                    f"{self.color_text('8.', 'cyan')} {self.color_text('Go Fishing', 'grey')}"
                )

            if self.game.player.has_farmdex:
                actions.append(
                    f"{self.color_text('9.', 'cyan')} {self.color_text('Farmdex', 'grey')}"
                )

            max_widths = [0, 0, 0]
            for i, action in enumerate(actions):
                col = i % 3
                length = len(self.strip_ansi(action))
                if length > max_widths[col]:
                    max_widths[col] = length

            for i in range(0, len(actions), 3):
                row = actions[i : i + 3]
                padded_row = []
                for j, action in enumerate(row):
                    col_width = max_widths[j]
                    raw = self.strip_ansi(action)
                    pad = col_width - len(raw)
                    padded_row.append(action + (" " * pad))
                print(" | ".join(padded_row))

            choice = input(self.display_action_message())

            if choice == "1":
                if (
                    self.game.day_cycle_system.get_current_part() == "night"
                    and not getattr(self.game.player, "has_lantern", False)
                ):
                    input(
                        self.color_text(
                            "It's too dark to work without a lantern!", "red"
                        )
                        + " Press Enter..."
                    )
                    continue
                self.plant_crop_menu()
            elif choice == "2":
                if (
                    self.game.day_cycle_system.get_current_part() == "night"
                    and not getattr(self.game.player, "has_lantern", False)
                ):
                    input(
                        self.color_text(
                            "It's too dark to work without a lantern!", "red"
                        )
                        + " Press Enter..."
                    )
                    continue
                self.harvest_menu()
            elif choice == "3":
                success, message = self.game.next_day()
                if success:
                    print(
                        f"{self.color_text('Advanced to day', 'blue')} "
                        f"{self.color_text(self.game.time_system.day, 'bright_blue')}!"
                    )
                    if message:
                        print(f"{self.color_text('EVENT:', 'bright_blue')} {message}")
                    time.sleep(self.MENU_COOLDOWN_TIME)
                else:
                    input(
                        f"{self.color_text('Not enough stamina!', 'red')} Press Enter..."
                    )
            elif choice == "4":
                self.sleep_menu()
            elif choice == "5":
                if self.game.save():
                    print(f"\n{self.color_text('Game saved!', 'green')}")
                    sys.exit()
            elif choice == "6":
                confirm = input(
                    self.color_text("Are you sure you want to reset? (y/n): ", "red")
                )
                if confirm.lower() == "y":
                    self.game.new_game()
                    print(self.color_text("Game reset!", "green"))
                    time.sleep(1)
            elif choice == "7" and self.game.merchant_system.is_available(
                self.game.day_cycle_system.get_current_part()
            ):
                self.merchant_menu()
            elif choice == "8" and self.game.merchant_system.fishing_unlocked:
                if (
                    self.game.day_cycle_system.get_current_part() == "night"
                    and not getattr(self.game.player, "has_lantern", False)
                ):
                    input(
                        self.color_text(
                            "It's too dark to work without a lantern!", "red"
                        )
                        + " Press Enter..."
                    )
                    continue
                self.fishing_menu()
            elif choice == "9" and self.game.player.has_farmdex:
                self.farmdex_menu()
            else:
                print(f"{self.color_text('Invalid choice!', 'red')}")
                time.sleep(self.MENU_COOLDOWN_TIME)

    def farmdex_menu(self):
        self.clear_screen()
        print(self.color_text("🦖 Farmdex Collection", "bright_green"))
        print(
            self.color_text(
                f"Fossils Discovered: {len(self.game.player.fossils_found)}/50", "cyan"
            )
        )
        print()
        all_fossils = [
            "Tyrannosaurus",
            "Triceratops",
            "Velociraptor",
            "Brachiosaurus",
            "Stegosaurus",
            "Spinosaurus",
            "Ankylosaurus",
            "Parasaurolophus",
            "Allosaurus",
            "Diplodocus",
            "Iguanodon",
            "Archaeopteryx",
            "Pteranodon",
            "Deinonychus",
            "Megalosaurus",
            "Pachycephalosaurus",
            "Corythosaurus",
            "Oviraptor",
            "Plateosaurus",
            "Styracosaurus",
            "Suchomimus",
            "Troodon",
            "Carnotaurus",
            "Sauropelta",
            "Albertosaurus",
            "Mamenchisaurus",
            "Edmontosaurus",
            "Herrerasaurus",
            "Giganotosaurus",
            "Therizinosaurus",
            "Kentrosaurus",
            "Dilophosaurus",
            "Coelophysis",
            "Protoceratops",
            "Sinraptor",
            "Rugops",
            "Lambeosaurus",
            "Mononykus",
            "Torosaurus",
            "Rhabdodon",
            "Ouranosaurus",
            "Microceratus",
            "Zuniceratops",
            "Einiosaurus",
            "Dromaeosaurus",
            "Massospondylus",
            "Lesothosaurus",
            "Noasaurus",
            "Gasparinisaura",
            "Minmi",
        ]
        columns = 3
        rows = (len(all_fossils) + columns - 1) // columns
        fossil_entries = []

        for name in all_fossils:
            if name in self.game.player.fossils_found:
                fossil_entries.append(self.color_text(name, "bright_green"))
            else:
                fossil_entries.append(self.color_text("?????", "gray"))

        for row in range(rows):
            line = ""
            for col in range(columns):
                idx = row + col * rows
                if idx < len(fossil_entries):
                    entry = fossil_entries[idx]
                    entry_padded = entry + " " * (20 - len(self.strip_ansi(entry)))
                    line += entry_padded
            print(line)
        input(self.color_text("\n(Press Enter to return)", "white"))

    def merchant_menu(self):
        self.clear_screen()
        print(self.color_text("🧙‍♂️ Joji, the Morning Merchant", "bright_yellow"))
        print(self.color_text("═" * 40, "bright_cyan"))
        print(self.color_text("Welcome! Take a look at my goods:", "white"))
        print(self.color_text(f"\n💰 Money: ${self.game.player.money}", "white"))
        print()

        print(self.color_text("🌱 Seeds:", "bright_blue"))
        for key, seed in self.game.merchant_system.inventory["seeds"].items():
            already_unlocked = seed["crop"] in self.game.crop_system.unlocked_crops
            item_name = self.color_text(key, "gray" if already_unlocked else "cyan")
            unlock = self.color_text(f"(Unlocks {seed['crop'].capitalize()})", "grey")
            inflated = (
                hasattr(self.game, "market_inflated") and self.game.market_inflated
            )
            price_display = f"${seed['price'] * 2}" if inflated else f"${seed['price']}"
            inflated_tag = self.color_text(" [INFLATED]", "red") if inflated else ""
            print(f" - {item_name}: {price_display} {unlock}{inflated_tag}")

        print()
        print(self.color_text("🎁 Items:", "bright_blue"))
        for key, item in self.game.merchant_system.inventory["items"].items():
            already_owned = False
            if (
                item.get("unlocks") == "fishing"
                and self.game.merchant_system.fishing_unlocked
            ):
                already_owned = True
            elif (
                item.get("effect") == "increase_event_chance"
                and hasattr(self.game.player, "event_bonus")
                and self.game.player.event_bonus == "lucky_egg"
            ):
                already_owned = True
            elif (
                item.get("effect") == "increase_max_stamina"
                and self.game.player.max_stamina > 5
            ):
                already_owned = True
            elif item.get("effect") == "cosmetic":
                already_owned = (
                    hasattr(self.game.player, "bought_hat")
                    and self.game.player.bought_hat
                )

            item_name = self.color_text(key, "gray" if already_owned else "cyan")
            if "unlocks" in item:
                detail = self.color_text(
                    f"(Unlocks {item['unlocks'].capitalize()})", "grey"
                )
            elif "effect" in item:
                readable_effects = {
                    "cosmetic": "Visual cosmetic item",
                    "increase_event_chance": "Boosts daily events: 80% chance to occur each day!",
                    "increase_max_stamina": "Double your max stamina",
                    "unlock_night_work": "Allow you to work at night",
                }
                effect_description = readable_effects.get(item.get("effect", ""), "")
                detail = (
                    self.color_text(f"({effect_description})", "grey")
                    if effect_description
                    else ""
                )
            else:
                detail = ""
            inflated = (
                hasattr(self.game, "market_inflated") and self.game.market_inflated
            )
            price_display = f"${item['price'] * 2}" if inflated else f"${item['price']}"
            inflated_tag = self.color_text(" [INFLATED]", "red") if inflated else ""
            print(f" - {item_name}: {price_display} {detail}{inflated_tag}")

        choice = input(
            self.display_action_message(
                message="What would you like to buy?",
                cancellable=True,
                cancel_message=f"(type {self.color_text('item_key', 'cyan')} or '0' to cancel): ",
            )
        ).strip()

        if choice == "0":
            return
        narrative = False
        item = None
        if choice in self.game.merchant_system.inventory["seeds"]:
            msg = self.game.merchant_system.buy_seed(choice)
        elif choice in self.game.merchant_system.inventory["items"]:
            item = self.game.merchant_system.inventory["items"][choice]
            narrative = item.get("narrative", False)
            msg = self.game.merchant_system.buy_item(choice)
        else:
            msg = "Invalid option."

        error_keywords = ["invalid", "not enough"]
        is_error = msg is None or any(kw in msg.lower() for kw in error_keywords)

        if is_error:
            print(self.color_text(msg, "red"))
            time.sleep(self.MENU_COOLDOWN_TIME)
        elif narrative:
            print(self.color_text(msg, "green"))
            input(self.color_text("\n(Press Enter to continue)", "white"))
        else:
            print(self.color_text(msg, "green"))
            time.sleep(self.MENU_COOLDOWN_TIME)

    def fishing_menu(self):
        self.clear_screen()
        print(self.color_text("🎣 Fishing Spot", "bright_blue"))

        print(
            f"{self.color_text('1.', 'cyan')} Go fishing {self.color_text('(-2 ♥)', 'red')}"
        )
        print(f"{self.color_text('2.', 'cyan')} Sell all fish")

        choice = input(self.display_action_message(cancellable=True))
        if choice == "1":
            result = self.game.fishing_system.fish()
        elif choice == "2":
            result = self.game.fishing_system.sell_all_fish()
        else:
            return

        print(self.color_text(result, "green"))
        time.sleep(2)

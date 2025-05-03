import time
import sys
from service.game_state import GameState
from service.tui_system import TerminalUI


def main():
    game_state: GameState = GameState()
    ui: TerminalUI = TerminalUI(game_state)

    if not game_state.load():
        print("Starting new game...")
        time.sleep(1)

    try:
        ui.start_game_loop()
    except KeyboardInterrupt:
        game_state.save()
        print("\nGame saved automatically!")
        sys.exit()


if __name__ == "__main__":
    main()

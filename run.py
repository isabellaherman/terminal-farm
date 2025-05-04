import sys
from pathlib import Path

PYTHONPATH = str(Path(__file__).parent / "src" / "game")

sys.path.append(PYTHONPATH)

from main import main

if __name__ == "__main__":
    main()

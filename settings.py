from pathlib import Path

WIDTH, HEIGHT = 320, 180
WINDOW_SCALE = 4
FPS = 60
TITLE = "Green-Eye: All Tidy Now!"
ROOT = Path(__file__).parent
SAVE_PATH = ROOT / "save.json"
ASSET_ROOT = ROOT / "assets"
USER_ASSETS = ASSET_ROOT / "user"
FOUND_ASSETS = ASSET_ROOT / "found"
GENERATED_ASSETS = ASSET_ROOT / "generated"

COLORS = {
    "ink": (31, 27, 45), "night": (13, 10, 27), "cream": (255, 238, 194), "paper": (255, 246, 211),
    "pink": (242, 111, 142), "red": (211, 65, 85), "green": (67, 174, 117),
    "lime": (177, 224, 103), "teal": (41, 126, 132), "sky": (128, 199, 220),
    "blue": (61, 96, 164), "yellow": (255, 211, 92), "orange": (239, 137, 69),
    "brown": (117, 76, 63), "shadow": (69, 54, 76), "white": (255, 255, 255),
}

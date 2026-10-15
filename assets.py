from pathlib import Path
import pygame
from settings import GENERATED_ASSETS, USER_ASSETS, FOUND_ASSETS
from settings import COLORS

_cache: dict[str, pygame.Surface] = {}

def asset_path(name: str) -> Path | None:
    for root in (USER_ASSETS, FOUND_ASSETS, GENERATED_ASSETS):
        path = root / name
        if path.exists():
            return path
    return None

def load_image(name: str, size: tuple[int, int] | None = None) -> pygame.Surface | None:
    key = f"{name}:{size}"
    if key in _cache:
        return _cache[key]
    path = asset_path(name)
    if path is None:
        # Keep the game playable when an optional replacement asset is absent.
        image = pygame.Surface(size or (16, 16), pygame.SRCALPHA)
        image.fill(COLORS["pink"])
        pygame.draw.rect(image, COLORS["yellow"], image.get_rect(), 2)
        pygame.draw.line(image, COLORS["ink"], (0, 0), image.get_rect().bottomright, 1)
        _cache[key] = image
        return image
    image = pygame.image.load(str(path)).convert_alpha()
    if size:
        image = pygame.transform.scale(image, size)
    _cache[key] = image
    return image

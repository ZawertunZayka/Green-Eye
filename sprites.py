import pygame
from settings import COLORS
from assets import load_image

def draw_person(surface: pygame.Surface, x: int, y: int, facing: int = 1,
                kind: str = "girl", scale: int = 1, flash: bool = False,
                top_down: bool = False) -> None:
    # Characters are always sourced from the supplied walk pack.
    asset_kind = {"girl": "runner", "thug": "bruiser", "teen": "punk", "dealer": "businessman"}.get(kind)
    if asset_kind:
        frame = (pygame.time.get_ticks() // 130) % 4
        image = load_image(f"walk/{asset_kind}/south/{frame:02d}.png", (32 * scale, 32 * scale))
        if flash:
            image = image.copy(); image.fill((255, 255, 255, 190), special_flags=pygame.BLEND_RGBA_ADD)
        anchor_y = 16 if top_down else 31
        surface.blit(image, (x - 16 * scale, y - anchor_y * scale))

def star_burst(surface: pygame.Surface, x: int, y: int, tick: int) -> None:
    colors = [COLORS["yellow"], COLORS["pink"], COLORS["sky"], COLORS["lime"]]
    for i in range(8):
        dx = ((tick * (i + 2) * 3) % 31) - 15
        dy = ((tick * (i + 3) * 2) % 25) - 18
        pygame.draw.rect(surface, colors[i % len(colors)], (x + dx, y + dy, 2, 2))

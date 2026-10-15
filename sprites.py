import pygame
from settings import COLORS
from assets import load_image

def draw_person(surface: pygame.Surface, x: int, y: int, facing: int = 1,
                kind: str = "girl", scale: int = 1, flash: bool = False) -> None:
    c = COLORS
    ink = c["white"] if flash else c["ink"]
    # Use the supplied walk-pack when available; the procedural drawing below
    # remains the safe fallback for any missing frame or future character type.
    asset_kind = {"girl": "runner", "thug": "bruiser", "teen": "punk", "dealer": "businessman"}.get(kind)
    if asset_kind and not flash:
        frame = (pygame.time.get_ticks() // 130) % 4
        image = load_image(f"walk/{asset_kind}/south/{frame:02d}.png", (32 * scale, 32 * scale))
        if image:
            surface.blit(image, (x - 16 * scale, y - 31 * scale))
            return
    if kind == "girl":
        skin, hair, outfit = (255, 190, 145), c["brown"], c["pink"]
        pygame.draw.rect(surface, hair, (x-6*scale, y-12*scale, 12*scale, 8*scale))
        pygame.draw.rect(surface, c["cream"], (x-5*scale, y-14*scale, 10*scale, 4*scale))
        pygame.draw.rect(surface, skin, (x-4*scale, y-8*scale, 8*scale, 8*scale))
        pygame.draw.rect(surface, ink, (x-2*scale, y-5*scale, 1*scale, 1*scale))
        pygame.draw.rect(surface, ink, (x+2*scale, y-5*scale, 1*scale, 1*scale))
        pygame.draw.rect(surface, c["red"], (x-2*scale, y-2*scale, 4*scale, 1*scale))
        pygame.draw.rect(surface, outfit, (x-6*scale, y, 12*scale, 10*scale))
        pygame.draw.rect(surface, c["paper"], (x-4*scale, y+1*scale, 8*scale, 7*scale))
        pygame.draw.rect(surface, c["blue"], (x-5*scale, y+10*scale, 4*scale, 3*scale))
        pygame.draw.rect(surface, c["blue"], (x+1*scale, y+10*scale, 4*scale, 3*scale))
    else:
        outfit = c["blue"] if kind == "dealer" else c["brown"]
        pygame.draw.rect(surface, outfit, (x-6*scale, y-8*scale, 12*scale, 15*scale))
        pygame.draw.rect(surface, (195, 132, 101), (x-5*scale, y-14*scale, 10*scale, 7*scale))
        pygame.draw.rect(surface, ink, (x-3*scale, y-11*scale, 2*scale, 2*scale))
        pygame.draw.rect(surface, ink, (x+2*scale, y-11*scale, 2*scale, 2*scale))
        pygame.draw.rect(surface, c["red"], (x-3*scale, y-5*scale, 6*scale, 2*scale))
        pygame.draw.rect(surface, c["shadow"], (x-5*scale, y+7*scale, 4*scale, 3*scale))
        pygame.draw.rect(surface, c["shadow"], (x+1*scale, y+7*scale, 4*scale, 3*scale))

def star_burst(surface: pygame.Surface, x: int, y: int, tick: int) -> None:
    colors = [COLORS["yellow"], COLORS["pink"], COLORS["sky"], COLORS["lime"]]
    for i in range(8):
        dx = ((tick * (i + 2) * 3) % 31) - 15
        dy = ((tick * (i + 3) * 2) % 25) - 18
        pygame.draw.rect(surface, colors[i % len(colors)], (x + dx, y + dy, 2, 2))

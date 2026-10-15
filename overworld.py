import pygame
from settings import WIDTH, HEIGHT, COLORS
from sprites import draw_person
from assets import load_image

class OverworldState:
    def __init__(self, game) -> None:
        self.game, self.player = game, game.player
        self.pos = pygame.Vector2(90, 104)
        self.enemies = [{"type": "thug", "pos": pygame.Vector2(244, 96), "done": False},
                        {"type": "teen", "pos": pygame.Vector2(156, 48), "done": False},
                        {"type": "dealer", "pos": pygame.Vector2(276, 143), "done": False}]
        self.message, self.message_time = "", 0.0
    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e and self.player.active_quest is None:
                self.game.manager.change("QUEST_BOARD")
            elif event.key == pygame.K_e and self.player.active_quest and self.pos.distance_to((58, 35)) < 32:
                self.game.manager.change("QUEST_BOARD")
    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
                              int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))
        if move.length_squared():
            move = move.normalize() * 58 * dt
            self.pos.x = max(12, min(308, self.pos.x + move.x))
            self.pos.y = max(30, min(168, self.pos.y + move.y))
        for enemy in self.enemies:
            if not enemy["done"] and self.pos.distance_to(enemy["pos"]) < 13:
                self.game.start_fight(enemy["type"], enemy)
                break
        self.message_time = max(0, self.message_time - dt)
    def draw(self, surface: pygame.Surface) -> None:
        c = COLORS; surface.fill(c["teal"])
        pygame.draw.rect(surface, c["green"], (0, 24, WIDTH, HEIGHT-24))
        tiles = ("0002", "0003", "0004", "0010")
        for row, y in enumerate(range(24, HEIGHT, 16)):
            for col, x in enumerate(range(0, WIDTH, 16)):
                tile = load_image(f"urban/tiles/tile_{tiles[(row + col) % len(tiles)]}.png", (16, 16))
                if tile: surface.blit(tile, (x, y))
        pygame.draw.rect(surface, c["shadow"], (0, 78, WIDTH, 20)); pygame.draw.rect(surface, c["shadow"], (137, 24, 20, HEIGHT-24))
        for x in range(0, WIDTH, 16): pygame.draw.line(surface, (80, 155, 123), (x, 78), (x+8, 98))
        # Supplied Kenney City Kit preview sprites add readable city landmarks.
        for name, pos in (("city/building-wide-a.png", (4, 52)), ("city/building-a.png", (82, 52)),
                          ("city/building-c.png", (164, 52)), ("city/skyscraper-a.png", (270, 48))):
            prop = load_image(name, (32, 32))
            if prop: surface.blit(prop, pos)
        pygame.draw.rect(surface, c["orange"], (37, 27, 42, 22)); pygame.draw.rect(surface, c["cream"], (42, 31, 32, 14))
        pygame.draw.rect(surface, c["red"], (48, 22, 20, 8)); pygame.draw.rect(surface, c["ink"], (54, 9, 8, 14))
        pygame.draw.rect(surface, c["yellow"], (246, 27, 16, 30)); pygame.draw.rect(surface, c["ink"], (252, 11, 4, 18))
        self.game.text(surface, "GLIWICE • CLEANUP DISTRICT", (8, 6), 8, c["paper"])
        self.game.text(surface, "QUEST BOARD", (41, 34), 6, c["ink"])
        for enemy in self.enemies:
            if not enemy["done"]: draw_person(surface, int(enemy["pos"].x), int(enemy["pos"].y), kind=enemy["type"], scale=1)
        draw_person(surface, int(self.pos.x), int(self.pos.y), kind="girl", scale=1)
        self.game.draw_hud(surface)
        self.game.text(surface, "WASD / ARROWS move   E board", (8, 171), 7, c["paper"])

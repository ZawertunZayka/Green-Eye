import pygame
from settings import WIDTH, HEIGHT, COLORS
from sprites import draw_person
from assets import load_image

class OverworldState:
    """A compact, neon top-down map of Gliwice's recognizable city zones."""
    def __init__(self, game) -> None:
        self.game, self.player = game, game.player
        self.location_index = 0
        self.location_names = ["RYNEK", "UL. ZWYCIESTWA", "UL. DWORCOWA", "DOLNYCH WALOW", "UL. CHORZOWSKA"]
        self.location_notes = ["MARKET SQUARE", "CITY CENTRE", "STATION ROAD", "OLD WALLS", "EAST DISTRICT"]
        self.pos = pygame.Vector2(112, 112)
        self.enemies = []
        self.spawn_location()
        self.buildings = [pygame.Rect(5, 52, 40, 20), pygame.Rect(49, 52, 34, 20), pygame.Rect(178, 50, 34, 16),
                          pygame.Rect(218, 50, 30, 16), pygame.Rect(264, 52, 50, 18), pygame.Rect(4, 144, 40, 22),
                          pygame.Rect(250, 144, 64, 22)]
    def spawn_location(self) -> None:
        layouts = [[("thug", (70, 126)), ("teen", (213, 43)), ("dealer", (270, 126))],
                   [("teen", (70, 126)), ("thug", (212, 42)), ("dealer", (270, 126))],
                   [("thug", (70, 126)), ("thug", (212, 42)), ("teen", (270, 126))],
                   [("dealer", (70, 126)), ("teen", (212, 42)), ("thug", (270, 126))],
                   [("dealer", (70, 126)), ("thug", (212, 42)), ("dealer", (270, 126))]]
        self.enemies = [{"type": kind, "pos": pygame.Vector2(pos), "done": False} for kind, pos in layouts[self.location_index % len(layouts)]]
    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if self.pos.distance_to((58, 35)) < 30: self.game.manager.change("QUEST_BOARD")
            elif self.all_clear and self.pos.x > 265 and 78 < self.pos.y < 120: self.next_location()
    @property
    def all_clear(self) -> bool:
        return all(enemy["done"] for enemy in self.enemies)
    def next_location(self) -> None:
        if not self.all_clear: return
        self.location_index += 1
        self.pos = pygame.Vector2(36, 96)
        self.spawn_location()
    def blocked(self, pos: pygame.Vector2) -> bool:
        body = pygame.Rect(int(pos.x - 6), int(pos.y - 6), 12, 12)
        return any(body.colliderect(rect) for rect in self.buildings)
    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed(); move = pygame.Vector2(int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]), int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))
        if move.length_squared():
            move = move.normalize() * 58 * dt
            candidate = pygame.Vector2(max(12, min(308, self.pos.x + move.x)), max(30, min(168, self.pos.y + move.y)))
            x_try = pygame.Vector2(candidate.x, self.pos.y); y_try = pygame.Vector2(self.pos.x, candidate.y)
            if not self.blocked(x_try): self.pos.x = x_try.x
            if not self.blocked(y_try): self.pos.y = y_try.y
        for enemy in self.enemies:
            if not enemy["done"] and self.pos.distance_to(enemy["pos"]) < 13:
                self.game.start_fight(enemy["type"], enemy); break
    def label(self, surface, text, pos, color=(0, 222, 218)) -> None:
        self.game.text(surface, text, pos, 6, color)
    def building(self, surface, rect, accent) -> None:
        pygame.draw.rect(surface, (16, 12, 31), rect)
        pygame.draw.rect(surface, accent, rect, 1)
        for y in range(rect.y + 4, rect.bottom - 2, 6):
            for x in range(rect.x + 4, rect.right - 2, 8): pygame.draw.rect(surface, (255, 178, 71), (x, y, 3, 2))
    def draw(self, surface: pygame.Surface) -> None:
        c = COLORS; surface.fill(c["night"]); pygame.draw.rect(surface, (15, 13, 32), (0, 24, WIDTH, HEIGHT - 24))
        # Street grid and districts.
        pygame.draw.rect(surface, (23, 18, 43), (0, 86, WIDTH, 20)); pygame.draw.rect(surface, (23, 18, 43), (128, 24, 20, HEIGHT - 24))
        pygame.draw.line(surface, (255, 37, 116), (0, 85), (WIDTH, 85), 2); pygame.draw.line(surface, (0, 222, 218), (128, 24), (128, HEIGHT), 2)
        for x in range(7, WIDTH, 24): pygame.draw.line(surface, (255, 178, 71), (x, 95), (x + 10, 95), 1)
        # Rynek / market square.
        pygame.draw.rect(surface, (56, 29, 68), (87, 48, 38, 32)); pygame.draw.rect(surface, (255, 236, 105), (87, 48, 38, 32), 1)
        for x in range(91, 121, 8): pygame.draw.line(surface, (97, 51, 103), (x, 52), (x, 76), 1)
        self.label(surface, "RYNEK", (96, 62), (255, 236, 105))
        # Station: long platform, entrance and tracks.
        pygame.draw.rect(surface, (35, 33, 48), (5, 110, 73, 31)); pygame.draw.rect(surface, (255, 37, 116), (5, 110, 73, 31), 1)
        for y in (117, 127, 137): pygame.draw.line(surface, (104, 100, 125), (8, y), (74, y), 1)
        pygame.draw.rect(surface, (0, 222, 218), (26, 112, 26, 8)); self.label(surface, "DWORZEC", (13, 145), (0, 222, 218))
        # Park and radio tower landmarks.
        pygame.draw.rect(surface, (16, 58, 58), (178, 25, 70, 48)); pygame.draw.rect(surface, (0, 222, 218), (178, 25, 70, 48), 1)
        for x, y in ((187, 35), (205, 58), (229, 34), (240, 57)): pygame.draw.circle(surface, (41, 165, 107), (x, y), 5)
        self.label(surface, "PARK CHOPINA", (185, 69), (0, 222, 218))
        pygame.draw.line(surface, (255, 178, 71), (282, 71), (282, 27), 2); pygame.draw.line(surface, (255, 178, 71), (270, 55), (294, 55), 1); pygame.draw.line(surface, (255, 178, 71), (276, 43), (288, 43), 1)
        self.label(surface, "RADIO TOWER", (261, 20), (255, 178, 71))
        # Residential blocks plus 2D previews rendered from the supplied 3D city kit.
        for rect in self.buildings: self.building(surface, rect, (255, 37, 116))
        for name, pos in (("city/building-wide-a.png", (8, 48)), ("city/building-a.png", (50, 48)), ("city/building-c.png", (265, 48)), ("city/skyscraper-a.png", (274, 138))):
            prop = load_image(name, (30, 30))
            if prop: surface.blit(prop, pos)
        for name, pos, size in (("building-type-a", (12, 73), 30), ("building-type-f", (53, 73), 28), ("building-type-k", (183, 74), 30), ("building-type-p", (224, 74), 28), ("building-type-u", (267, 73), 34), ("building-type-d", (12, 137), 30), ("building-type-m", (258, 137), 30)):
            prop = load_image(f"3d_city/Previews/{name}.png", (size, size))
            if prop: surface.blit(prop, pos)
        pygame.draw.rect(surface, (255, 37, 116), (44, 25, 30, 18)); pygame.draw.rect(surface, (12, 9, 24), (48, 29, 22, 10)); self.label(surface, "CLEANUP HQ", (47, 32), (255, 236, 105))
        self.game.text(surface, f"GLIWICE // {self.location_names[self.location_index]}", (8, 6), 8, (0, 222, 218))
        self.game.text(surface, self.location_notes[self.location_index], (232, 6), 6, (255, 178, 71))
        pygame.draw.rect(surface, (255, 37, 116), (int(self.pos.x) - 12, int(self.pos.y) + 10, 24, 2))
        for enemy in self.enemies:
            if not enemy["done"]: draw_person(surface, int(enemy["pos"].x), int(enemy["pos"].y), kind=enemy["type"], scale=1)
        draw_person(surface, int(self.pos.x), int(self.pos.y), kind="girl", scale=1)
        if self.all_clear:
            pygame.draw.rect(surface, (255, 37, 116), (267, 78, 45, 30), 1)
            self.game.text(surface, "NEXT", (278, 82), 7, (255, 236, 105))
            self.game.text(surface, self.location_names[(self.location_index + 1) % len(self.location_names)], (269, 92), 5, (0, 222, 218))
            self.game.text(surface, "E", (286, 106), 8, (255, 236, 105))
        self.game.draw_hud(surface); self.game.text(surface, "WASD / ARROWS MOVE   E INTERACT", (8, 171), 7, (255, 236, 105))

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
    def draw(self, surface: pygame.Surface) -> None:
        # Streets use only the supplied tile textures and 3D-kit preview art.
        tiles = [load_image(f"urban/tiles/tile_{tile:04d}.png", (16, 16)) for tile in (2, 3, 4, 10)]
        for index, y in enumerate(range(24, HEIGHT, 16)):
            for x in range(0, WIDTH, 16):
                tile = tiles[(index + x // 16) % len(tiles)]
                if tile: surface.blit(tile, (x, y))
        # Road strips use the supplied 3D-pack path renders, not Python-drawn shapes.
        road = load_image("3d_city/Previews/path-long.png", (32, 18))
        road_edge = load_image("3d_city/Previews/path-stones-long.png", (32, 12))
        road_kit = load_image("3d_city/Models/Roads/Previews/road-straight.png", (32, 22))
        road_cross = load_image("3d_city/Models/Roads/Previews/road-intersection.png", (48, 32))
        if road:
            for x in range(0, WIDTH, 32):
                surface.blit(road, (x, 86))
            vertical = pygame.transform.rotate(road, 90)
            for y in range(24, HEIGHT, 18):
                surface.blit(vertical, (145, y))
        if road_edge:
            for x in range(0, WIDTH, 32):
                surface.blit(road_edge, (x, 78))
                surface.blit(road_edge, (x, 105))
        if road_kit:
            for x in range(0, WIDTH, 32): surface.blit(road_kit, (x, 82))
            for y in range(24, HEIGHT, 22): surface.blit(pygame.transform.rotate(road_kit, 90), (144, y))
        if road_cross: surface.blit(road_cross, (136, 76))
        for name, pos, size in (("sedan", (28, 87), (30, 18)), ("taxi", (92, 87), (30, 18)), ("police", (246, 87), (30, 18)), ("van", (151, 38), (18, 30)), ("delivery", (151, 139), (18, 30)), ("truck", (285, 88), (34, 20))):
            car = load_image(f"3d_city/Models/Cars/Previews/{name}.png", size)
            if car: surface.blit(car, pos)
        for name, pos, size in (("traffic-light", (132, 66), 24), ("light-square", (116, 42), 24), ("electricity-pole", (303, 28), 28)):
            prop = load_image(f"3d_city/Models/Roads/Previews/{name}.png", (size, size))
            if prop: surface.blit(prop, pos)
        for name, pos, size in (("building-type-a", (12, 42), 42), ("building-type-f", (53, 42), 38), ("building-type-k", (180, 42), 42), ("building-type-p", (222, 42), 38), ("building-type-u", (266, 42), 46), ("building-type-d", (10, 120), 42), ("building-type-m", (254, 120), 42), ("tree-large", (232, 28), 32), ("tree-small", (198, 70), 28), ("planter", (146, 28), 24), ("fence", (150, 120), 38)):
            prop = load_image(f"3d_city/Previews/{name}.png", (size, size))
            if prop: surface.blit(prop, pos)
        index = self.location_index % len(self.location_names)
        self.game.text(surface, f"GLIWICE // {self.location_names[index]}", (8, 6), 8, (0, 222, 218))
        self.game.text(surface, self.location_notes[index], (232, 6), 6, (255, 178, 71))
        for enemy in self.enemies:
            if not enemy["done"]: draw_person(surface, int(enemy["pos"].x), int(enemy["pos"].y), kind=enemy["type"], scale=1)
        draw_person(surface, int(self.pos.x), int(self.pos.y), kind="girl", scale=1)
        if self.all_clear:
            self.game.text(surface, "NEXT", (278, 82), 7, (255, 236, 105))
            self.game.text(surface, self.location_names[(self.location_index + 1) % len(self.location_names)], (269, 92), 5, (0, 222, 218))
            self.game.text(surface, "E", (286, 106), 8, (255, 236, 105))
        self.game.draw_hud(surface); self.game.text(surface, "WASD / ARROWS MOVE   E INTERACT", (8, 171), 7, (255, 236, 105))

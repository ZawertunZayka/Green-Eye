import random
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
        self.story_lines = ["The board called. The city needs a cheerful cleaner.", "Neon signs point east. Someone is making a mess.", "A station contact left one last clue.", "Old walls, new trouble. Keep moving.", "The radio tower is broadcasting the final job."]
        self.pos = pygame.Vector2(112, 112)
        self.tutorial = True
        self.enemies = []
        self.spawn_location()
        self.buildings = []
        self.building_accent = (255, 37, 116)
    def spawn_location(self) -> None:
        layouts = [[("thug", (70, 126)), ("teen", (213, 43)), ("dealer", (270, 126))],
                   [("teen", (70, 126)), ("thug", (212, 42)), ("dealer", (270, 126))],
                   [("thug", (70, 126)), ("thug", (212, 42)), ("teen", (270, 126))],
                   [("dealer", (70, 126)), ("teen", (212, 42)), ("thug", (270, 126))],
                   [("dealer", (70, 126)), ("thug", (212, 42)), ("dealer", (270, 126))]]
        building_layouts = [
            [(5, 52, 40, 20), (49, 52, 34, 20), (178, 50, 34, 16), (218, 50, 30, 16), (264, 52, 50, 18), (4, 144, 40, 22), (250, 144, 64, 22)],
            [(5, 45, 24, 28), (33, 45, 42, 17), (180, 49, 54, 18), (240, 45, 32, 24), (278, 45, 36, 24), (8, 145, 62, 20), (178, 145, 38, 20)],
            [(5, 50, 68, 15), (180, 48, 26, 24), (211, 48, 26, 24), (242, 48, 26, 24), (273, 48, 41, 24), (106, 145, 54, 20), (218, 145, 48, 20)],
            [(5, 49, 32, 18), (44, 49, 32, 18), (257, 48, 57, 18), (4, 145, 29, 21), (39, 145, 29, 21), (185, 145, 34, 21), (225, 145, 40, 21)],
            [(5, 46, 52, 25), (65, 46, 28, 25), (177, 45, 28, 25), (211, 45, 49, 25), (269, 45, 45, 25), (5, 145, 72, 20), (250, 145, 64, 20)],
        ]
        self.buildings = [pygame.Rect(*rect) for rect in building_layouts[self.location_index % len(building_layouts)]]
        self.building_accent = ((255, 37, 116), (0, 222, 218), (255, 178, 71), (96, 88, 180), (255, 72, 137))[self.location_index % 5]
        layout = list(layouts[self.location_index % len(layouts)])
        random.Random(100 + self.location_index).shuffle(layout)
        self.enemies = [{"type": kind, "pos": pygame.Vector2(pos), "done": False} for kind, pos in layout]
    def handle_event(self, event) -> None:
        if self.tutorial and (event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN):
            self.tutorial = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if self.pos.distance_to((58, 35)) < 30: self.game.manager.change("QUEST_BOARD")
            elif self.pos.distance_to((104, 35)) < 20: self.game.manager.change("SHOP")
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
    def bus(self, surface, x: int, y: int, color) -> None:
        pygame.draw.rect(surface, (8, 8, 18), (x, y, 31, 12)); pygame.draw.rect(surface, color, (x, y, 31, 8)); pygame.draw.rect(surface, (150, 222, 220), (x + 4, y + 2, 6, 3)); pygame.draw.rect(surface, (150, 222, 220), (x + 13, y + 2, 6, 3)); pygame.draw.rect(surface, (150, 222, 220), (x + 22, y + 2, 5, 3)); pygame.draw.circle(surface, (8, 8, 18), (x + 6, y + 11), 3); pygame.draw.circle(surface, (8, 8, 18), (x + 25, y + 11), 3)
    def tree(self, surface, x: int, y: int, large: bool = False) -> None:
        radius = 7 if large else 5; pygame.draw.rect(surface, (66, 37, 39), (x - 1, y + radius - 1, 3, 7)); pygame.draw.circle(surface, (20, 110, 76), (x, y), radius); pygame.draw.circle(surface, (53, 171, 104), (x - 2, y - 2), max(2, radius - 3))
    def draw_zone_details(self, surface, zone: int) -> None:
        if zone == 0:  # Rynek: fountain, stalls and café lights.
            pygame.draw.circle(surface, (0, 222, 218), (106, 63), 9, 2); pygame.draw.circle(surface, (255, 236, 105), (106, 63), 3)
            for x in (91, 119): pygame.draw.rect(surface, (255, 37, 116), (x, 39, 10, 6)); pygame.draw.line(surface, (255, 178, 71), (x + 2, 45), (x + 2, 51), 1)
            self.label(surface, "MARKET", (94, 76), (255, 236, 105))
        elif zone == 1:  # Zwycięstwa: bright storefront canyon.
            for x, color in ((6, (255, 37, 116)), (52, (0, 222, 218)), (173, (255, 178, 71)), (252, (255, 37, 116))):
                pygame.draw.rect(surface, color, (x, 73, 30, 5), 1); pygame.draw.line(surface, color, (x, 78), (x, 84), 1)
            self.label(surface, "NIGHT CENTRE", (121, 30), (255, 236, 105))
        elif zone == 2:  # Dworcowa: platforms and buses.
            for y in (112, 127, 142): pygame.draw.line(surface, (128, 128, 151), (4, y), (100, y), 1)
            self.bus(surface, 16, 102, (255, 37, 116)); self.bus(surface, 204, 104, (0, 222, 218)); self.label(surface, "BUS TERMINAL", (110, 118), (255, 236, 105))
        elif zone == 3:  # Dolnych Wałów: park, pond and trees.
            pygame.draw.rect(surface, (11, 65, 72), (172, 26, 77, 45)); pygame.draw.ellipse(surface, (0, 126, 145), (181, 32, 40, 23)); pygame.draw.ellipse(surface, (0, 222, 218), (181, 32, 40, 23), 1)
            for point in ((166, 38), (206, 74), (245, 38), (265, 75), (185, 27)): self.tree(surface, *point, large=True)
            self.label(surface, "PARK / POND", (183, 62), (0, 222, 218))
        else:  # Chorzowska: industrial road and freight yard.
            for x in (10, 58, 180, 230): pygame.draw.rect(surface, (78, 36, 57), (x, 35, 32, 14)); pygame.draw.rect(surface, (255, 37, 116), (x, 35, 32, 14), 1)
            self.bus(surface, 202, 76, (255, 178, 71)); pygame.draw.line(surface, (255, 178, 71), (8, 30), (312, 30), 1); self.label(surface, "FREIGHT YARD", (121, 32), (255, 178, 71))
    def draw(self, surface: pygame.Surface) -> None:
        c = COLORS; surface.fill(c["night"]); pygame.draw.rect(surface, (15, 13, 32), (0, 24, WIDTH, HEIGHT - 24))
        # Street grid and districts.
        pygame.draw.rect(surface, (23, 18, 43), (0, 86, WIDTH, 20)); pygame.draw.rect(surface, (23, 18, 43), (128, 24, 20, HEIGHT - 24))
        pygame.draw.line(surface, (255, 37, 116), (0, 85), (WIDTH, 85), 2); pygame.draw.line(surface, (0, 222, 218), (128, 24), (128, HEIGHT), 2)
        for x in range(7, WIDTH, 24): pygame.draw.line(surface, (255, 178, 71), (x, 95), (x + 10, 95), 1)
        zone = self.location_index % 5
        self.draw_zone_details(surface, zone)
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
        # Residential blocks and Kenney building sprites.
        for rect in self.buildings: self.building(surface, rect, self.building_accent)
        for name, pos in (("city/building-wide-a.png", (8, 48)), ("city/building-a.png", (50, 48)), ("city/building-c.png", (265, 48)), ("city/skyscraper-a.png", (274, 138))):
            prop = load_image(name, (30, 30))
            if prop: surface.blit(prop, pos)
        pygame.draw.rect(surface, (255, 37, 116), (44, 25, 30, 18)); pygame.draw.rect(surface, (12, 9, 24), (48, 29, 22, 10)); self.label(surface, "CLEANUP HQ", (47, 32), (255, 236, 105))
        pygame.draw.rect(surface, (0, 222, 218), (84, 18, 43, 27), 1)
        shop_prop = load_image("city/building-wide-a.png", (42, 38))
        if shop_prop: surface.blit(shop_prop, (84, 8))
        pygame.draw.rect(surface, (0, 222, 218), (91, 25, 27, 18)); pygame.draw.rect(surface, (12, 9, 24), (95, 29, 19, 10)); self.label(surface, "SHOP", (98, 32), (255, 236, 105))
        name_index = self.location_index % len(self.location_names)
        self.game.text(surface, f"GLIWICE // {self.location_names[name_index]}", (8, 6), 8, (0, 222, 218))
        self.game.text(surface, self.location_notes[name_index], (232, 6), 6, (255, 178, 71))
        pygame.draw.rect(surface, (255, 37, 116), (int(self.pos.x) - 12, int(self.pos.y) + 10, 24, 2))
        for enemy in self.enemies:
            if not enemy["done"]: draw_person(surface, int(enemy["pos"].x), int(enemy["pos"].y), kind=enemy["type"], scale=1)
        draw_person(surface, int(self.pos.x), int(self.pos.y), kind="girl", scale=1)
        if self.all_clear:
            pygame.draw.rect(surface, (255, 37, 116), (267, 78, 45, 30), 1)
            self.game.text(surface, "NEXT", (278, 82), 7, (255, 236, 105))
            self.game.text(surface, self.location_names[(self.location_index + 1) % len(self.location_names)], (269, 92), 5, (0, 222, 218))
            self.game.text(surface, "E", (286, 106), 8, (255, 236, 105))
        self.game.draw_hud(surface); self.game.text(surface, self.story_lines[name_index], (104, 158), 5, (255, 178, 71)); self.game.text(surface, "E HQ / SHOP / EXIT", (8, 160), 6, (0, 222, 218)); self.game.text(surface, "WASD / ARROWS MOVE", (8, 171), 7, (255, 236, 105))
        if self.tutorial:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); shade.fill((5, 4, 18, 185)); surface.blit(shade, (0, 0)); pygame.draw.rect(surface, (255, 37, 116), (36, 34, 248, 108), 2)
            self.game.text(surface, "NIGHT SHIFT // QUICK TUTORIAL", (62, 45), 9, (255, 236, 105)); self.game.text(surface, "WASD / ARROWS   MOVE", (72, 64), 7, COLORS["paper"]); self.game.text(surface, "E near HQ / SHOP / EXIT", (72, 78), 7, (0, 222, 218)); self.game.text(surface, "LMB shoot   J/K melee   L special", (54, 92), 7, COLORS["paper"]); self.game.text(surface, "Clear the street, then follow NEXT.", (62, 108), 7, (255, 178, 71)); self.game.text(surface, "PRESS ANY KEY", (111, 128), 7, (255, 37, 116))

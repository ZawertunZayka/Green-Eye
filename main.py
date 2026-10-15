import json
from dataclasses import dataclass, field, asdict
import pygame
from settings import WIDTH, HEIGHT, WINDOW_SCALE, FPS, TITLE, SAVE_PATH, COLORS
from quests import Quest, starter_quest, quest_to_dict, quest_from_dict
from overworld import OverworldState
from fight import FightState
from assets import load_image
from sprites import draw_person

@dataclass
class PlayerData:
    hp: int = 100; max_hp: int = 100; coins: int = 0; xp: int = 0
    upgrades: dict = field(default_factory=lambda: {"pan": 0, "health": 0})
    active_quest: Quest | None = None

class StateManager:
    def __init__(self, game) -> None: self.game, self.states, self.current = game, {}, "MENU"
    def add(self, name, state) -> None: self.states[name] = state
    def change(self, name) -> None: self.current = name
    def handle_event(self, event) -> None: self.states[self.current].handle_event(event)
    def update(self, dt) -> None: self.states[self.current].update(dt)
    def draw(self, surface) -> None: self.states[self.current].draw(surface)

class IntroState:
    def __init__(self, game): self.game, self.timer = game, 0.0
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN: self.game.manager.change("MENU")
    def update(self, dt):
        self.timer += dt
        if self.timer >= 4.5: self.game.manager.change("MENU")
    def draw(self, surface):
        t = self.timer; pulse = int(190 + 55 * ((pygame.time.get_ticks() // 180) % 2)); surface.fill((9, 7, 20)); pygame.draw.rect(surface, (22, 11, 43), (0, 88, WIDTH, 92))
        for x in range(-70, WIDTH + 70, 25): pygame.draw.line(surface, (63, 19, 75), (160, 88), (x, 180), 1)
        for y in range(96, 180, 12): pygame.draw.line(surface, (42, 17, 58), (0, y), (WIDTH, y), 1)
        pygame.draw.line(surface, (255, 178, 71), (266, 88), (266, 22), 2); pygame.draw.line(surface, (255, 178, 71), (256, 47), (276, 47), 1)
        for name, pos in (("city/building-a.png", (10, 53)), ("city/building-c.png", (62, 60)), ("city/skyscraper-a.png", (278, 40))):
            prop = load_image(name, (42, 42))
            if prop: surface.blit(prop, pos)
        runner_x = int(-25 + min(1.0, t / 2.2) * 130)
        draw_person(surface, runner_x, 135, kind="girl", scale=2, top_down=True)
        if t > 1.2: self.game.text(surface, "GREEN-EYE", (79, 49), 22, (255, 236, 105))
        if t > 1.8: self.game.text(surface, "ALL TIDY NOW!", (91, 80), 10, (0, 222, 218))
        if t > 2.5: self.game.text(surface, "A GLIWICE CLEANUP STORY", (80, 103), 7, COLORS["paper"])
        if t > 3.2: self.game.text(surface, "PRESS ANY KEY", (113, 143), 7, (pulse, 37, 116))
        self.game.text(surface, "15.10.2026 // NIGHT SHIFT", (89, 171), 6, (255, 178, 71))

class MenuState:
    def __init__(self, game): self.game, self.selected, self.controls = game, 0, False
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN: return
        if self.controls:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE): self.controls = False
            return
        if event.key in (pygame.K_UP, pygame.K_w): self.selected = (self.selected - 1) % 2
        elif event.key in (pygame.K_DOWN, pygame.K_s): self.selected = (self.selected + 1) % 2
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.selected == 0: self.game.manager.change("OVERWORLD")
            else: self.controls = True
    def update(self, dt): pass
    def draw(self, surface):
        surface.fill((10, 8, 21)); pygame.draw.rect(surface, (25, 12, 44), (0, 82, WIDTH, 98))
        for x in range(-80, WIDTH + 80, 24): pygame.draw.line(surface, (66, 20, 76), (160, 82), (x, 180), 1)
        for y in range(92, 180, 12): pygame.draw.line(surface, (43, 18, 61), (0, y), (WIDTH, y), 1)
        for name, pos in (("city/building-a.png", (8, 54)), ("city/building-c.png", (72, 61)), ("city/skyscraper-a.png", (274, 38))):
            prop = load_image(name, (44, 44))
            if prop: surface.blit(prop, pos)
        pygame.draw.line(surface, (255, 178, 71), (249, 82), (249, 25), 2); pygame.draw.line(surface, (255, 178, 71), (238, 44), (260, 44), 1)
        draw_person(surface, 247, 132, kind="girl", scale=2, top_down=True)
        pygame.draw.rect(surface, (11, 8, 23), (25, 20, 190, 142)); pygame.draw.rect(surface, (255, 37, 116), (25, 20, 190, 142), 2)
        self.game.text(surface, "GREEN-EYE", (44, 34), 21, (255, 236, 105)); self.game.text(surface, "GLIWICE AFTER DARK", (57, 67), 8, (0, 222, 218)); self.game.text(surface, "A CLEANUP STORY", (72, 80), 7, COLORS["paper"])
        if self.controls:
            pygame.draw.rect(surface, (11, 8, 23), (37, 93, 165, 52)); pygame.draw.rect(surface, (0, 222, 218), (37, 93, 165, 52), 1)
            self.game.text(surface, "CONTROLS", (83, 99), 9, (255, 236, 105)); self.game.text(surface, "WASD  MOVE", (52, 115), 7, COLORS["paper"]); self.game.text(surface, "J/K  HIT   L  SPECIAL", (52, 127), 7, COLORS["paper"]); self.game.text(surface, "ENTER / ESC  BACK", (52, 139), 7, COLORS["paper"])
        else:
            for i, label in enumerate(("START CLEANUP", "CONTROLS")):
                color = (255, 37, 116) if i == self.selected else (87, 76, 111)
                pygame.draw.rect(surface, color, (62, 100 + i * 19, 118, 14), 1); self.game.text(surface, label, (78, 103 + i * 19), 7, (255, 236, 105) if i == self.selected else COLORS["paper"])
        self.game.text(surface, "ENTER SELECT   UP/DOWN CHOOSE", (55, 171), 6, (255, 178, 71))

class QuestBoardState:
    def __init__(self, game): self.game = game
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_ESCAPE): self.game.manager.change("OVERWORLD")
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and self.game.player.active_quest is None:
            self.game.player.active_quest = starter_quest(); self.game.player.active_quest.active = True; self.game.manager.change("OVERWORLD")
    def update(self, dt): pass
    def draw(self, surface):
        surface.fill(COLORS["brown"]); pygame.draw.rect(surface, COLORS["paper"], (24, 19, 272, 135)); self.game.text(surface, "CLEANUP BOARD", (83, 30), 13, COLORS["red"]); self.game.text(surface, "JOB #001", (44, 57), 8, COLORS["ink"]); self.game.text(surface, "Clean the station corner", (44, 74), 10, COLORS["ink"]); self.game.text(surface, "One street thug is making a mess.", (44, 91), 7, COLORS["shadow"]); self.game.text(surface, "REWARD 30 COINS + 50 XP", (44, 111), 8, COLORS["green"]); self.game.text(surface, "ENTER accept   E close", (86, 137), 7, COLORS["red"])

class GameOverState:
    def __init__(self, game): self.game = game
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE): self.game.reset_player(); self.game.manager.change("OVERWORLD")
    def update(self, dt): pass
    def draw(self, surface): surface.fill(COLORS["shadow"]); self.game.text(surface, "CITY STILL MESSY!", (78, 60), 13, COLORS["pink"]); self.game.text(surface, "Press ENTER to tidy up again", (88, 95), 7, COLORS["paper"])

class Game:
    def __init__(self):
        pygame.init(); pygame.display.set_caption(TITLE); self.window = pygame.display.set_mode((WIDTH*WINDOW_SCALE, HEIGHT*WINDOW_SCALE)); self.canvas = pygame.Surface((WIDTH, HEIGHT)); self.fonts = {}; self.player = self.load_player(); self.manager = StateManager(self); self.overworld = OverworldState(self); self.manager.add("INTRO", IntroState(self)); self.manager.add("MENU", MenuState(self)); self.manager.add("OVERWORLD", self.overworld); self.manager.add("QUEST_BOARD", QuestBoardState(self)); self.manager.add("GAME_OVER", GameOverState(self)); self.manager.change("INTRO")
    def text(self, surface, value, pos, size, color):
        if size not in self.fonts: self.fonts[size] = pygame.font.Font(None, size*2)
        surface.blit(self.fonts[size].render(value, False, color), pos)
    def load_player(self):
        try:
            data = json.loads(SAVE_PATH.read_text()); data["active_quest"] = quest_from_dict(data["active_quest"]) if data.get("active_quest") else None; return PlayerData(**data)
        except (OSError, ValueError, TypeError): return PlayerData()
    def save(self):
        data = asdict(self.player); data["active_quest"] = quest_to_dict(self.player.active_quest) if self.player.active_quest else None; SAVE_PATH.write_text(json.dumps(data, indent=2))
    def reset_player(self): self.player = PlayerData(); self.overworld.pos = pygame.Vector2(90, 104)
    def start_fight(self, enemy_type, enemy_ref): self.manager.states["FIGHT"] = FightState(self, enemy_type, enemy_ref); self.manager.change("FIGHT")
    def complete_enemy(self, enemy_name):
        q = self.player.active_quest
        if q and not q.complete:
            q.progress += 1
            if q.progress >= q.required: q.complete = True; q.active = False; self.player.coins += q.reward_coins; self.player.xp += q.reward_xp
        self.player.coins += 5; self.save()
    def draw_hud(self, surface):
        self.text(surface, f"COINS {self.player.coins}  XP {self.player.xp}", (8, 25), 7, COLORS["paper"])
        if self.player.active_quest: self.text(surface, self.player.active_quest.label(), (180, 25), 6, COLORS["yellow"])
    def run(self):
        clock = pygame.time.Clock(); running = True
        while running:
            dt = min(clock.tick(FPS) / 1000.0, .05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                else: self.manager.handle_event(event)
            self.manager.update(dt); self.manager.draw(self.canvas); pygame.transform.scale(self.canvas, self.window.get_size(), self.window); pygame.display.flip()
        self.save(); pygame.quit()

if __name__ == "__main__": Game().run()

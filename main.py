import json
from dataclasses import dataclass, field, asdict
import pygame
from settings import WIDTH, HEIGHT, WINDOW_SCALE, FPS, TITLE, SAVE_PATH, COLORS
from quests import Quest, starter_quest, quest_to_dict, quest_from_dict
from overworld import OverworldState
from fight import FightState

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

class MenuState:
    def __init__(self, game): self.game = game
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE): self.game.manager.change("OVERWORLD")
    def update(self, dt): pass
    def draw(self, surface):
        surface.fill(COLORS["teal"]); pygame.draw.rect(surface, COLORS["green"], (18, 24, 284, 128)); self.game.text(surface, "GREEN-EYE", (87, 43), 22, COLORS["yellow"]); self.game.text(surface, "ALL TIDY NOW!", (91, 75), 10, COLORS["paper"]); self.game.text(surface, "A wholesome city cleanup adventure", (72, 103), 7, COLORS["paper"]); self.game.text(surface, "PRESS ENTER", (119, 135), 8, COLORS["pink"])

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
        pygame.init(); pygame.display.set_caption(TITLE); self.window = pygame.display.set_mode((WIDTH*WINDOW_SCALE, HEIGHT*WINDOW_SCALE)); self.canvas = pygame.Surface((WIDTH, HEIGHT)); self.fonts = {}; self.player = self.load_player(); self.manager = StateManager(self); self.overworld = OverworldState(self); self.manager.add("MENU", MenuState(self)); self.manager.add("OVERWORLD", self.overworld); self.manager.add("QUEST_BOARD", QuestBoardState(self)); self.manager.add("GAME_OVER", GameOverState(self))
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
            self.manager.update(dt)
            self.manager.draw(self.canvas)
            scaled = pygame.transform.scale(self.canvas, self.window.get_size())
            self.window.blit(scaled, (0, 0))
            pygame.display.flip()
        self.save(); pygame.quit()

if __name__ == "__main__": Game().run()

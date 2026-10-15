import random
import pygame
from settings import WIDTH, HEIGHT, COLORS
from sprites import draw_person, star_burst
from enemies import ENEMY_TYPES

class Fighter:
    def __init__(self, x: float, spec, player: bool) -> None:
        self.x, self.y, self.spec, self.player = x, 125.0, spec, player
        self.hp = 100 if player else spec.hp; self.max_hp = self.hp; self.vx = 0.0; self.hit_stun = 0.0
        self.attack = ""; self.attack_time = 0.0; self.block = False; self.facing = 1 if player else -1; self.combo = 0
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x-9), int(self.y-25), 18, 28)

class FightState:
    def __init__(self, game, enemy_type: str, enemy_ref) -> None:
        self.game, self.enemy_ref = game, enemy_ref; self.spec = ENEMY_TYPES[enemy_type]
        self.hero, self.foe = Fighter(85, self.spec, True), Fighter(235, self.spec, False)
        self.hero.max_hp = self.hero.hp = game.player.max_hp; self.rounds = [0, 0]; self.round_no = 1; self.timer = 45.0
        self.banner, self.banner_time, self.message = "FIGHT!", 1.1, ""; self.hit_stop = 0.0; self.shake = 0; self.finish_timer = 0.0; self.rng = random.Random()
    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and self.finish_timer <= 0:
            if event.key == pygame.K_j: self.hero.attack, self.hero.attack_time = "punch", .22
            elif event.key == pygame.K_k: self.hero.attack, self.hero.attack_time = "kick", .3
            elif event.key == pygame.K_l: self.hero.attack, self.hero.attack_time = "special", .42
    def update(self, dt: float) -> None:
        if self.finish_timer > 0:
            self.finish_timer -= dt
            if self.finish_timer <= 0: self.end_fight(self.rounds[0] >= 2)
            return
        if self.hit_stop > 0: self.hit_stop -= dt; return
        self.banner_time = max(0, self.banner_time-dt); self.timer -= dt
        keys = pygame.key.get_pressed(); direction = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        if self.hero.hit_stun <= 0:
            self.hero.x = max(28, min(292, self.hero.x + direction * 72 * dt)); self.hero.block = keys[pygame.K_SPACE]
            self.hero.y = 115.0 if keys[pygame.K_w] else 132.0 if keys[pygame.K_s] else 125.0
        self.hero.attack_time = max(0, self.hero.attack_time-dt); self.foe.attack_time = max(0, self.foe.attack_time-dt)
        self.hero.hit_stun = max(0, self.hero.hit_stun-dt); self.foe.hit_stun = max(0, self.foe.hit_stun-dt)
        if self.foe.hit_stun <= 0 and self.foe.attack_time <= 0:
            gap = self.hero.x - self.foe.x
            if abs(gap) > 34: self.foe.x += (1 if gap > 0 else -1) * self.spec.speed * dt
            elif self.rng.random() < .035: self.foe.attack, self.foe.attack_time = "attack", .25
        if self.hero.attack_time > 0 and self.hero.attack_time < .16: self.try_hit(self.hero, self.foe, self.hero.attack)
        if self.foe.attack_time > 0 and self.foe.attack_time < .16: self.try_hit(self.foe, self.hero, "enemy")
        if self.foe.hp <= 0: self.rounds[0] += 1; self.next_round(True)
        elif self.hero.hp <= 0: self.rounds[1] += 1; self.next_round(False)
        elif self.timer <= 0: self.rounds[1] += 1; self.next_round(False)
    def try_hit(self, attacker: Fighter, defender: Fighter, attack: str) -> None:
        if not attacker.rect().inflate(22, 10).colliderect(defender.rect()): return
        if defender.block or (not defender.player and self.rng.random() < self.spec.block_chance): return
        damage = 18 if attack == "punch" else 24 if attack == "kick" else 30 if attack == "special" else self.spec.damage
        defender.hp -= damage; defender.hit_stun = .22; self.hit_stop = .05; self.shake = 4
        if attacker.player: attacker.combo += 1; self.message = "TIDY HIT!" if attack != "special" else "SOUP SPLASH!"
        else: self.message = "Oof!"
    def next_round(self, won: bool) -> None:
        if max(self.rounds) >= 2:
            self.finish_timer = 1.25; self.banner = "FINISH HER!" if won else "OH NO!"; self.banner_time = 1.25; return
        self.round_no += 1; self.hero.hp = self.hero.max_hp; self.foe.hp = self.foe.max_hp; self.timer = 45; self.banner = "ROUND " + str(self.round_no); self.banner_time = 1
    def end_fight(self, won: bool) -> None:
        if won: self.enemy_ref["done"] = True; self.game.complete_enemy(self.spec.name); self.game.manager.change("OVERWORLD")
        else: self.game.manager.change("GAME_OVER")
    def draw(self, surface: pygame.Surface) -> None:
        c = COLORS
        surface.fill((20, 13, 35))
        pygame.draw.rect(surface, (45, 19, 67), (0, 45, WIDTH, 100))
        pygame.draw.rect(surface, (11, 9, 22), (0, 145, WIDTH, 35))
        for x in range(-20, WIDTH + 20, 24):
            pygame.draw.line(surface, (84, 26, 91), (x, 145), (x + 18, 180), 1)
        for y in range(148, 180, 8): pygame.draw.line(surface, (48, 22, 66), (0, y), (WIDTH, y), 1)
        pygame.draw.line(surface, (255, 48, 117), (0, 144), (WIDTH, 144), 2)
        pygame.draw.rect(surface, (0, 221, 217), (18, 62, 284, 2))
        self.bar(surface, 12, 12, 115, self.hero.hp/self.hero.max_hp, (0, 232, 190)); self.bar(surface, 193, 12, 115, self.foe.hp/self.foe.max_hp, (255, 52, 93))
        self.game.text(surface, "MAMA", (14, 25), 7, c["paper"]); self.game.text(surface, self.spec.name.upper(), (190, 25), 6, c["paper"]); self.game.text(surface, f"R{self.round_no}  {max(0,int(self.timer)):02d}", (145, 8), 7, c["ink"])
        draw_person(surface, int(self.hero.x), int(self.hero.y), facing=1, kind="girl", scale=2, flash=self.hit_stop > 0); draw_person(surface, int(self.foe.x), int(self.foe.y), facing=-1, kind=self.spec.color, scale=2, flash=self.hit_stop > 0)
        if self.shake: self.shake -= 1; star_burst(surface, int(self.foe.x), 105, self.shake)
        if self.banner_time:
            pygame.draw.rect(surface, (255, 41, 103), (84, 38, 152, 22), 2)
            self.game.text(surface, self.banner, (104, 40), 14, (255, 236, 105))
        if self.message: self.game.text(surface, self.message, (112, 157), 8, c["paper"])
        self.game.text(surface, "A/D move  J punch  K kick  L special  SPACE block", (16, 171), 6, c["paper"])
    @staticmethod
    def bar(surface, x, y, width, ratio, color) -> None:
        pygame.draw.rect(surface, COLORS["ink"], (x-2, y-2, width+4, 12)); pygame.draw.rect(surface, color, (x, y, max(0, int(width*ratio)), 8))

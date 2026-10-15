import random
import pygame
from settings import WIDTH, HEIGHT, COLORS
from sprites import draw_person, star_burst
from enemies import ENEMY_TYPES
from assets import load_image

class Fighter:
    def __init__(self, x: float, y: float, spec, player: bool) -> None:
        self.x, self.y, self.spec, self.player = x, y, spec, player
        self.hp = 100 if player else spec.hp; self.max_hp = self.hp
        self.hit_stun = 0.0; self.attack = ""; self.attack_time = 0.0; self.attack_hit = False
        self.block = False; self.facing = 1 if player else -1; self.combo = 0
    def rect(self) -> pygame.Rect: return pygame.Rect(int(self.x - 8), int(self.y - 8), 16, 16)

class FightState:
    """Top-down neon cleanup arena with fast, readable arcade combat."""
    def __init__(self, game, enemy_type: str, enemy_ref) -> None:
        self.game, self.enemy_ref, self.spec = game, enemy_ref, ENEMY_TYPES[enemy_type]
        self.hero, self.foe = Fighter(80, 104, self.spec, True), Fighter(240, 104, self.spec, False)
        self.hero.max_hp = self.hero.hp = game.player.max_hp; self.rounds = [0, 0]; self.round_no = 1; self.timer = 45.0
        self.banner, self.banner_time, self.message = "FIGHT!", 1.1, ""; self.hit_stop = 0.0; self.shake = 0; self.finish_timer = 0.0; self.rng = random.Random()
        self.bullets: list[dict] = []; self.shoot_cooldown = 0.0; self.aim = pygame.Vector2(1, 0)
    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and self.finish_timer <= 0:
            if event.key == pygame.K_j: self.start_attack(self.hero, "punch", .22)
            elif event.key == pygame.K_k: self.start_attack(self.hero, "kick", .30)
            elif event.key == pygame.K_l: self.start_attack(self.hero, "special", .42)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.finish_timer <= 0: self.shoot_player(event.pos)
    @staticmethod
    def start_attack(fighter: Fighter, attack: str, duration: float) -> None:
        if fighter.attack_time <= 0 and fighter.hit_stun <= 0: fighter.attack, fighter.attack_time, fighter.attack_hit = attack, duration, False
    def update(self, dt: float) -> None:
        if self.finish_timer > 0:
            self.finish_timer -= dt
            if self.finish_timer <= 0: self.end_fight(self.rounds[0] >= 2)
            return
        if self.hit_stop > 0: self.hit_stop -= dt; return
        self.banner_time = max(0, self.banner_time - dt); self.timer -= dt
        self.shoot_cooldown = max(0, self.shoot_cooldown - dt); self.update_bullets(dt)
        keys = pygame.key.get_pressed(); dx = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]); dy = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
        if self.hero.hit_stun <= 0:
            move = pygame.Vector2(dx, dy)
            if move.length_squared():
                move = move.normalize() * 76 * dt; self.hero.x = max(22, min(298, self.hero.x + move.x)); self.hero.y = max(52, min(136, self.hero.y + move.y))
                if abs(dx) >= abs(dy) and dx: self.hero.facing = 1 if dx > 0 else -1
            self.hero.block = keys[pygame.K_SPACE]
        else: self.hero.block = False
        self.hero.hit_stun = max(0, self.hero.hit_stun - dt); self.foe.hit_stun = max(0, self.foe.hit_stun - dt)
        self.hero.attack_time = max(0, self.hero.attack_time - dt); self.foe.attack_time = max(0, self.foe.attack_time - dt); self.enemy_ai(dt)
        if self.hero.attack_time > 0 and self.hero.attack_time < .14 and not self.hero.attack_hit: self.hero.attack_hit = True; self.try_hit(self.hero, self.foe, self.hero.attack)
        if self.foe.attack_time > 0 and self.foe.attack_time < .14 and not self.foe.attack_hit: self.foe.attack_hit = True; self.try_hit(self.foe, self.hero, "enemy")
        if self.foe.hp <= 0: self.rounds[0] += 1; self.next_round(True)
        elif self.hero.hp <= 0 or self.timer <= 0: self.rounds[1] += 1; self.next_round(False)
    def enemy_ai(self, dt: float) -> None:
        if self.foe.hit_stun > 0 or self.foe.attack_time > 0: return
        delta = pygame.Vector2(self.hero.x - self.foe.x, self.hero.y - self.foe.y); distance = delta.length()
        if distance > 24:
            step = delta.normalize() * self.spec.speed * dt; self.foe.x = max(22, min(298, self.foe.x + step.x)); self.foe.y = max(52, min(136, self.foe.y + step.y))
        elif self.rng.random() < .05:
            self.foe.facing = 1 if self.hero.x > self.foe.x else -1; self.foe.block = self.rng.random() < self.spec.block_chance; self.start_attack(self.foe, "enemy", .27)
            if self.spec.ranged and self.rng.random() < .35: self.shoot_enemy()
    def shoot_player(self, mouse_pos) -> None:
        if self.shoot_cooldown > 0: return
        target = pygame.Vector2(mouse_pos[0] * WIDTH / self.game.window.get_width(), mouse_pos[1] * HEIGHT / self.game.window.get_height())
        direction = target - pygame.Vector2(self.hero.x, self.hero.y)
        if not direction.length_squared(): return
        self.aim = direction.normalize(); self.hero.facing = 1 if self.aim.x >= 0 else -1; self.bullets.append({"pos": pygame.Vector2(self.hero.x, self.hero.y), "vel": self.aim * 230, "owner": "hero", "ttl": .7}); self.shoot_cooldown = .18; self.message = "BANG!"
    def shoot_enemy(self) -> None:
        direction = pygame.Vector2(self.hero.x - self.foe.x, self.hero.y - self.foe.y)
        if direction.length_squared(): self.bullets.append({"pos": pygame.Vector2(self.foe.x, self.foe.y), "vel": direction.normalize() * 150, "owner": "enemy", "ttl": 1.0})
    def update_bullets(self, dt: float) -> None:
        for bullet in self.bullets[:]:
            bullet["pos"] += bullet["vel"] * dt; bullet["ttl"] -= dt
            target = self.foe if bullet["owner"] == "hero" else self.hero
            if bullet["ttl"] <= 0 or not pygame.Rect(0, 45, WIDTH, 100).collidepoint(bullet["pos"]): self.bullets.remove(bullet); continue
            if target.rect().inflate(4, 4).collidepoint(bullet["pos"]):
                target.hp -= 35 if bullet["owner"] == "hero" else self.spec.damage; target.hit_stun = .24; self.hit_stop, self.shake = .05, 4; self.message = "CLEAN SHOT!" if bullet["owner"] == "hero" else "INCOMING!"; self.bullets.remove(bullet)
    def try_hit(self, attacker: Fighter, defender: Fighter, attack: str) -> None:
        if not attacker.rect().inflate(27 if attack == "special" else 20, 27 if attack == "special" else 20).colliderect(defender.rect()): return
        if defender.block or (not defender.player and self.rng.random() < self.spec.block_chance): self.message = "BLOCKED!"; return
        damage = 18 if attack == "punch" else 24 if attack == "kick" else 30 if attack == "special" else self.spec.damage; defender.hp -= damage; defender.hit_stun = .22; defender.x = max(20, min(300, defender.x + (7 if attacker.x < defender.x else -7))); self.hit_stop, self.shake = .05, 4
        self.message = ("TIDY HIT!" if attack != "special" else "SOUP SPLASH!") if attacker.player else "Oof!"
    def next_round(self, won: bool) -> None:
        if max(self.rounds) >= 2: self.finish_timer = 1.25; self.banner = "FINISH HER!" if won else "OH NO!"; self.banner_time = 1.25; return
        self.round_no += 1; self.hero.hp = self.hero.max_hp; self.foe.hp = self.foe.max_hp; self.hero.x, self.hero.y = 80, 104; self.foe.x, self.foe.y = 240, 104; self.timer = 45; self.banner = "ROUND " + str(self.round_no); self.banner_time = 1
    def end_fight(self, won: bool) -> None:
        if won: self.enemy_ref["done"] = True; self.game.complete_enemy(self.spec.name); self.game.manager.change("OVERWORLD")
        else: self.game.manager.change("GAME_OVER")
    def draw(self, surface: pygame.Surface) -> None:
        c = COLORS
        arena = load_image("city/gliwice_map.png", (WIDTH, HEIGHT))
        surface.blit(arena, (0, 0))
        pygame.draw.rect(surface, (10, 8, 23), (8, 48, 304, 92), 2)
        self.bar(surface, 12, 12, 115, self.hero.hp / self.hero.max_hp, (0, 232, 190)); self.bar(surface, 193, 12, 115, self.foe.hp / self.foe.max_hp, (255, 52, 93))
        self.game.text(surface, "MAMA", (14, 25), 7, c["paper"]); self.game.text(surface, self.spec.name.upper(), (190, 25), 6, c["paper"]); self.game.text(surface, f"R{self.round_no}  {max(0, int(self.timer)):02d}", (145, 8), 7, c["cream"])
        if self.hero.attack_time > 0:
            reach = 18 if self.hero.attack == "punch" else 24
            pygame.draw.circle(surface, (255, 236, 105), (int(self.hero.x + self.hero.facing * 10), int(self.hero.y)), reach, 2)
        if self.foe.attack_time > 0: pygame.draw.circle(surface, (255, 52, 93), (int(self.foe.x + self.foe.facing * 10), int(self.foe.y)), 18, 1)
        for bullet in self.bullets: pygame.draw.rect(surface, (255, 236, 105) if bullet["owner"] == "hero" else (255, 52, 93), (int(bullet["pos"].x) - 2, int(bullet["pos"].y) - 2, 4, 4))
        draw_person(surface, int(self.hero.x), int(self.hero.y), facing=self.hero.facing, kind="girl", flash=self.hit_stop > 0, top_down=True); draw_person(surface, int(self.foe.x), int(self.foe.y), facing=self.foe.facing, kind=self.spec.color, flash=self.hit_stop > 0, top_down=True)
        if self.shake: self.shake -= 1; star_burst(surface, int(self.foe.x), int(self.foe.y), self.shake)
        if self.banner_time: pygame.draw.rect(surface, (255, 41, 103), (84, 38, 152, 22), 2); self.game.text(surface, self.banner, (104, 40), 14, (255, 236, 105))
        if self.message: self.game.text(surface, self.message, (112, 147), 8, c["paper"])
        self.game.text(surface, "WASD MOVE  LMB SHOOT  J PUNCH  K KICK  L SPECIAL  SPACE BLOCK", (4, 171), 6, c["cream"])
    @staticmethod
    def bar(surface, x, y, width, ratio, color) -> None:
        pygame.draw.rect(surface, COLORS["ink"], (x - 2, y - 2, width + 4, 12)); pygame.draw.rect(surface, color, (x, y, max(0, int(width * ratio)), 8))

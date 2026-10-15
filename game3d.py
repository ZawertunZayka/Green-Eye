"""Reliable 3D vertical slice for Green-Eye."""
import json
from pathlib import Path
from ursina import *

ROOT = Path(__file__).parent
SAVE_PATH = ROOT / "save.json"
INK = color.rgb(9, 8, 20)
ROAD = color.rgb(29, 27, 48)
BUILDING = color.rgb(72, 47, 74)
CYAN = color.rgb(0, 225, 220)
PINK = color.rgb(255, 35, 120)
YELLOW = color.rgb(255, 225, 80)
GREEN = color.rgb(50, 180, 105)


class SaveData:
    def __init__(self, raw=None):
        raw = raw or {}
        upgrades = raw.get("upgrades", {})
        self.coins = int(raw.get("coins", 0))
        self.xp = int(raw.get("xp", 0))
        self.pan = int(raw.get("pan", upgrades.get("pan", 0)))
        self.quest = bool(raw.get("quest", False))
        self.quest_done = int(raw.get("quest_done", 0))

    def dump(self):
        return {"coins": self.coins, "xp": self.xp, "pan": self.pan,
                "quest": self.quest, "quest_done": self.quest_done}


class Enemy:
    def __init__(self, game, kind, position):
        self.game, self.kind = game, kind
        self.hp = {"THUG": 3, "TEEN": 2, "DEALER": 4}[kind]
        self.speed = {"THUG": 1.0, "TEEN": 1.7, "DEALER": .8}[kind]
        tint = {"THUG": PINK, "TEEN": color.azure, "DEALER": color.orange}[kind]
        self.entity = Entity(model="cube", position=position, scale=(.9, 1.5, .9), color=tint)
        Text(kind, parent=self.entity, y=1.1, origin=(0, 0), scale=4, color=YELLOW)
        self.cooldown = 0
        self.dead = False

    def update(self, dt):
        if self.dead:
            return
        delta = self.game.player.position - self.entity.position
        delta.y = 0
        if delta.length() > 1.8:
            self.entity.position += delta.normalized() * self.speed * dt
        else:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.cooldown = 1.0
                self.game.flash("OUCH!", PINK)

    def hit(self):
        if self.dead:
            return
        self.hp -= 1 + self.game.data.pan // 2
        tint = {"THUG": PINK, "TEEN": color.azure, "DEALER": color.orange}[self.kind]
        self.entity.color = YELLOW
        invoke(setattr, self.entity, "color", tint, delay=.12)
        if self.hp <= 0:
            self.dead = True
            self.entity.animate_scale(0, duration=.12)
            self.game.data.coins += 5
            self.game.data.xp += 10
            self.game.target_down()


class GreenEye:
    def __init__(self):
        self.state = "INTRO"
        self.intro_timer = 0
        self.location = 0
        self.data = self.load()
        self.world, self.enemies = [], []
        self.create_ui()
        self.build_level()

    def load(self):
        try:
            return SaveData(json.loads(SAVE_PATH.read_text()))
        except (OSError, ValueError, TypeError):
            return SaveData()

    def save(self):
        SAVE_PATH.write_text(json.dumps(self.data.dump(), indent=2))

    def create_ui(self):
        self.ui_bg = Entity(parent=camera.ui, model="quad", scale=(2, 2), color=INK, z=10)
        self.title = Text("GREEN-EYE", parent=camera.ui, origin=(0, 0), y=.16, scale=.11, color=YELLOW)
        self.subtitle = Text("GLIWICE // NIGHT CLEANUP", parent=camera.ui, origin=(0, 0), y=.03, scale=.045, color=CYAN)
        self.prompt = Text("ENTER  START CLEANUP", parent=camera.ui, origin=(0, 0), y=-.2, scale=.045, color=PINK)
        self.menu_info = Text("A cheerful city cleaner\nA very tidy night\n\nWASD MOVE   J PAN SWING   E INTERACT", parent=camera.ui, origin=(0, 0), y=-.05, scale=.032, color=color.white)
        self.hud = Text("", parent=camera.ui, position=(-.47, .43), scale=.9, color=YELLOW)
        self.help = Text("", parent=camera.ui, position=(-.47, -.46), scale=.8, color=color.white)
        self.message = Text("", parent=camera.ui, origin=(0, 0), y=-.25, scale=.05, color=PINK, enabled=False)
        self.quest_panel = Entity(parent=camera.ui, model="quad", scale=(.8, .62), color=color.rgb(19, 14, 33), z=1, enabled=False)
        self.quest_text = Text("", parent=camera.ui, origin=(0, 0), y=.03, scale=.045, color=YELLOW, enabled=False)
        self.shop_panel = Entity(parent=camera.ui, model="quad", scale=(.8, .62), color=color.rgb(19, 14, 33), z=1, enabled=False)
        self.shop_text = Text("", parent=camera.ui, origin=(0, 0), y=.03, scale=.045, color=YELLOW, enabled=False)
        self.show_menu()

    def build_level(self):
        for item in self.world:
            destroy(item)
        for enemy in self.enemies:
            destroy(enemy.entity)
        self.world.clear(); self.enemies.clear()
        self.world.append(Entity(model="plane", scale=(42, 1, 28), color=ROAD))
        self.world.append(Entity(model="cube", position=(0, .02, 0), scale=(42, .08, 3), color=color.rgb(52, 42, 70)))
        self.world.append(Entity(model="cube", position=(0, .03, 0), scale=(3, .09, 28), color=color.rgb(52, 42, 70)))
        layouts = [
            [(-14, 6, 5, 4), (-7, 6, 4, 4), (8, 6, 6, 4), (15, 6, 4, 4), (-13, -7, 7, 4), (12, -7, 7, 4)],
            [(-14, 6, 4, 7), (-7, 6, 5, 3), (9, 6, 8, 3), (-12, -7, 10, 3), (11, -7, 5, 4)],
            [(-14, 6, 10, 3), (8, 6, 3, 7), (14, 6, 3, 7), (-11, -7, 5, 3), (7, -7, 8, 3)],
            [(-14, 6, 5, 3), (-7, 6, 5, 3), (12, 6, 9, 3), (-14, -7, 4, 4), (10, -7, 4, 4)],
            [(-13, 6, 8, 5), (-3, 6, 4, 5), (8, 6, 8, 5), (-13, -7, 8, 3), (14, -7, 5, 3)],
        ][self.location % 5]
        accent = [PINK, CYAN, YELLOW, GREEN, color.orange][self.location % 5]
        for x, z, sx, sz in layouts:
            self.world.append(Entity(model="cube", position=(x, 1.5, z), scale=(sx, 3, sz), color=BUILDING))
            self.world.append(Entity(model="cube", position=(x, 3.05, z), scale=(sx + .1, .08, sz + .1), color=accent))
        self.world.append(Entity(model="cube", position=(5, .7, 8), scale=(2.5, 1.4, 2), color=CYAN))
        self.world.append(Text("SHOP", world_position=(5, 2, 8), billboard=True, scale=1.4, color=YELLOW))
        self.shop = Vec3(5, 0, 8)
        self.world.append(Entity(model="cube", position=(-5, .7, 8), scale=(2.7, 1.4, 1), color=PINK))
        self.world.append(Text("QUEST BOARD", world_position=(-5, 2, 8), billboard=True, scale=1.1, color=YELLOW))
        self.board = Vec3(-5, 0, 8)
        self.world.append(Entity(model="cube", position=(20, .5, 0), scale=(.8, 1, 3), color=YELLOW))
        self.world.append(Text("NEXT", world_position=(18, 1.5, 0), billboard=True, scale=1.1, color=YELLOW))
        self.player = Entity(model="cube", position=(-8, .8, 0), scale=(.9, 1.6, .9), color=YELLOW)
        self.world.append(self.player)
        positions = [(-11, .8, -5), (10, .8, 6), (14, .8, -5)]
        kinds = [["THUG", "TEEN", "DEALER"], ["TEEN", "THUG", "DEALER"], ["THUG", "THUG", "TEEN"], ["DEALER", "TEEN", "THUG"], ["DEALER", "THUG", "DEALER"]][self.location % 5]
        self.enemies = [Enemy(self, kind, pos) for kind, pos in zip(kinds, positions)]
        camera.position = (0, 24, -19); camera.rotation_x = 55

    def show_menu(self):
        self.state = "MENU"
        for item in (self.ui_bg, self.title, self.subtitle, self.prompt, self.menu_info): item.enabled = True
        self.hide_play_ui()

    def hide_play_ui(self):
        for item in (self.hud, self.help, self.message, self.quest_panel, self.quest_text, self.shop_panel, self.shop_text): item.enabled = False

    def start(self):
        self.state = "PLAY"
        for item in (self.ui_bg, self.title, self.subtitle, self.prompt, self.menu_info): item.enabled = False
        self.hud.enabled = True; self.help.enabled = True
        self.help.text = "WASD MOVE   J PAN   E INTERACT   CLEAR STREET -> NEXT"
        self.refresh_hud()

    def refresh_hud(self):
        alive = sum(not enemy.dead for enemy in self.enemies)
        self.hud.text = f"GLIWICE // STREET {self.location + 1}     COINS {self.data.coins}     XP {self.data.xp}     TARGETS {alive}"

    def flash(self, text, tint=PINK):
        self.message.enabled = True; self.message.color = tint; self.message.text = text
        invoke(self.message.disable, delay=.8)

    def target_down(self):
        if self.data.quest:
            self.data.quest_done += 1
            if self.data.quest_done >= 3:
                self.data.quest = False; self.data.coins += 30; self.data.xp += 50
                self.flash("ALL TIDY NOW!  +30 COINS +50 XP", YELLOW)
        self.save(); self.refresh_hud()

    def open_quest(self):
        self.state = "QUEST"; self.hide_play_ui()
        status = "COMPLETED" if self.data.quest_done >= 3 and not self.data.quest else ("ACTIVE" if self.data.quest else "PRESS ENTER TO ACCEPT")
        self.quest_text.text = f"CLEAN STREET {self.location + 1}\n\nREMOVE 3 TARGETS\nREWARD 30 COINS + 50 XP\n\n{status}\n\nENTER ACCEPT   E CLOSE"
        self.quest_panel.enabled = True; self.quest_text.enabled = True

    def open_shop(self):
        self.state = "SHOP"; self.hide_play_ui()
        self.shop_text.text = f"NIGHT SHOP\n\nP  UPGRADE PAN  30 COINS\n\nCOINS: {self.data.coins}\n\nE CLOSE"
        self.shop_panel.enabled = True; self.shop_text.enabled = True

    def attack(self):
        living = [enemy for enemy in self.enemies if not enemy.dead]
        target = min(living, key=lambda enemy: distance(self.player, enemy.entity), default=None)
        if target and distance(self.player, target.entity) < 3.2:
            target.hit(); self.flash("PAN BONK!", YELLOW)

    def update(self, dt):
        if self.state == "INTRO":
            self.intro_timer += dt
            if self.intro_timer > 1.6: self.show_menu()
            return
        if self.state != "PLAY": return
        move = Vec3(held_keys["d"] - held_keys["a"], 0, held_keys["s"] - held_keys["w"])
        if move.length(): self.player.position += move.normalized() * 6 * dt
        self.player.x = clamp(self.player.x, -19, 19); self.player.z = clamp(self.player.z, -12, 12)
        for enemy in self.enemies: enemy.update(dt)
        camera.position = lerp(camera.position, Vec3(self.player.x, 24, self.player.z - 19), dt * 3)
        self.refresh_hud()

    def input(self, key):
        if self.state == "INTRO": self.show_menu()
        elif self.state == "MENU" and key in ("enter", "left mouse down"): self.start()
        elif self.state == "PLAY":
            if key in ("j", "left mouse down"): self.attack()
            elif key == "e" and distance(self.player.position, self.shop) < 3: self.open_shop()
            elif key == "e" and distance(self.player.position, self.board) < 3: self.open_quest()
            elif key == "e" and self.player.x > 17 and all(enemy.dead for enemy in self.enemies):
                self.location += 1; self.data.quest = False; self.data.quest_done = 0; self.save(); self.build_level()
        elif self.state == "QUEST":
            if key in ("e", "escape"): self.start()
            elif key == "enter" and not self.data.quest and self.data.quest_done < 3:
                self.data.quest = True; self.data.quest_done = 0; self.save(); self.open_quest()
        elif self.state == "SHOP":
            if key in ("e", "escape"): self.start()
            elif key == "p" and self.data.coins >= 30:
                self.data.coins -= 30; self.data.pan += 1; self.save(); self.open_shop()


game = None
app = None


def update():
    if game: game.update(time.dt)


def input(key):
    if game: game.input(key)


def create_app():
    global app, game
    app = Ursina(borderless=False, development_mode=False)
    window.title = "Green-Eye // Gliwice Cleanup"; window.color = INK; window.fps_counter.enabled = True
    game = GreenEye(); app.run()


if __name__ == "__main__": create_app()

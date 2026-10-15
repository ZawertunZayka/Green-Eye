from __future__ import annotations

import json
from pathlib import Path
from ursina import *

ROOT = Path(__file__).parent
SAVE = ROOT / "save.json"
CITY = "assets/user/3d_city/Models/GLB"
CARS = "assets/user/3d_city/Models/Cars/GLB"
ROADS = "assets/user/3d_city/Models/Roads/GLB"
MAP = "assets/user/city/gliwice_map.png"
WALK = "assets/user/walk"
NIGHT = color.rgb(10, 12, 24)
CYAN = color.rgb(0, 225, 220)
PINK = color.rgb(255, 35, 120)
YELLOW = color.rgb(255, 225, 80)


def city(name):
    return f"{CITY}/{name}.glb"


def car(name):
    return f"{CARS}/{name}.glb"


def road(name):
    return f"{ROADS}/{name}.glb"


class HybridGame:
    """3D street layer with the project's 2D-style HUD and quest prompts."""
    def __init__(self):
        self.state = "INTRO"
        self.intro_time = 0.0
        self.street = 0
        self.coins, self.xp = self.load_progress()
        self.scene_entities: list[Entity] = []
        self.traffic: list[Entity] = []
        self.enemies: list[dict] = []
        self.avatar: Entity | None = None
        self.in_car = True
        self.create_ui()
        self.build_street()

    def load_progress(self):
        try:
            data = json.loads(SAVE.read_text())
            return int(data.get("coins", 0)), int(data.get("xp", 0))
        except (OSError, ValueError, TypeError):
            return 0, 0

    def save(self):
        SAVE.write_text(json.dumps({"coins": self.coins, "xp": self.xp}, indent=2))

    def create_ui(self):
        self.intro = Text("GREEN-EYE\n\nA GLIWICE CLEANUP STORY\n\nThe city needs a very cheerful cleaner.", parent=camera.ui, origin=(0, 0), y=.06, scale=.055, color=YELLOW)
        self.map_panel = Entity(parent=camera.ui, model="quad", texture=MAP, scale=(1.72, 1), color=color.rgba(255, 255, 255, 180), enabled=False)
        self.menu_card = Entity(parent=camera.ui, model="quad", color=color.rgba(8, 6, 18, 220), scale=(.62, .78), enabled=False)
        self.menu = Text("GLIWICE // RYNEK\n\nCLEANUP PROGRESS\n\nENTER  START STREET", parent=camera.ui, origin=(0, 0), y=.08, scale=.045, color=YELLOW, enabled=False)
        self.hud_bg = Entity(parent=camera.ui, model="quad", position=(0, .455), scale=(.98, .105), color=color.rgba(8, 12, 24, 235), enabled=False)
        self.hud = Text("", parent=camera.ui, position=(-.46, .465), scale=.82, color=YELLOW, enabled=False)
        self.help_bg = Entity(parent=camera.ui, model="quad", position=(0, -.455), scale=(1.08, .105), color=color.rgba(8, 12, 24, 235), enabled=False)
        self.help = Text("WASD  DRIVE / WALK     E  EXIT / ENTER / USE     J  CLEANUP HIT     ESC  MAP", parent=camera.ui, position=(-.51, -.465), scale=.68, color=color.white, enabled=False)
        self.notice_bg = Entity(parent=camera.ui, model="quad", position=(0, -.32), scale=(.7, .1), color=color.rgba(8, 12, 24, 235), enabled=False)
        self.notice = Text("", parent=camera.ui, origin=(0, 0), y=-.32, scale=.045, color=CYAN, enabled=False)
        self.quest_panel = Entity(parent=camera.ui, model="quad", color=color.rgb(18, 14, 32), scale=(.78, .58), enabled=False)
        self.quest_text = Text("", parent=camera.ui, origin=(0, 0), y=.03, scale=.045, color=YELLOW, enabled=False)
        self.shop_panel = Entity(parent=camera.ui, model="quad", color=color.rgb(18, 14, 32), scale=(.78, .58), enabled=False)
        self.shop_text = Text("", parent=camera.ui, origin=(0, 0), y=.03, scale=.045, color=CYAN, enabled=False)

    def add(self, entity):
        self.scene_entities.append(entity)
        return entity

    def build_street(self):
        for entity in self.scene_entities + self.traffic:
            destroy(entity)
        for enemy in self.enemies:
            destroy(enemy["entity"])
        self.scene_entities.clear(); self.traffic.clear()
        self.enemies.clear()
        # Continuous grass base and asphalt underlays keep the city readable even
        # where individual road-kit meshes have small tile gaps.
        self.add(Entity(model="cube", position=(0, -.35, 0), scale=(70, .5, 55), color=color.rgb(42, 112, 58), shader=unlit_shader))
        self.add(Entity(model="cube", position=(0, -.06, 0), scale=(66, .12, 8.2), color=color.rgb(48, 51, 61), shader=unlit_shader))
        self.add(Entity(model="cube", position=(0, -.05, 0), scale=(8.2, .12, 52), color=color.rgb(48, 51, 61), shader=unlit_shader))
        # Real road GLBs, not flat Python rectangles.
        for x in range(-24, 25, 4): self.add(Entity(model=road("road-straight"), position=(x, .03, 0), scale=2.2))
        for z in range(-20, 21, 4): self.add(Entity(model=road("road-straight"), position=(0, .04, z), rotation_y=90, scale=2.2))
        self.add(Entity(model=road("road-crossroad"), position=(0, .06, 0), scale=2.3))
        # Long, unbroken lane/curb lines instead of isolated decorative dashes.
        line = color.rgb(238, 209, 92)
        for z in (-3.7, 3.7): self.add(Entity(model="cube", position=(0, .16, z), scale=(64, .035, .09), color=line, shader=unlit_shader))
        for x in (-3.7, 3.7): self.add(Entity(model="cube", position=(x, .17, 0), scale=(.09, .035, 50), color=line, shader=unlit_shader))
        houses = [("building-type-a", (-16, 5), 2.4), ("building-type-c", (-9, 5), 2.3), ("building-type-f", (9, 5), 2.4), ("building-type-h", (16, 5), 2.2), ("building-type-k", (-15, -8), 2.4), ("building-type-m", (9, -8), 2.3), ("building-type-r", (16, -8), 2.3)]
        for name, pos, size in houses: self.add(Entity(model=city(name), position=(pos[0], 0, pos[1]), scale=size, collider="box"))
        for name, pos, size in (("tree-large", (-5, 0, 8), 1.5), ("tree-small", (12, 0, 2), 1.4), ("planter", (5, 0, 7), 1.5)):
            self.add(Entity(model=city(name), position=pos, scale=size))
        self.shop = self.add(Entity(model=city("building-type-b"), position=(5, 0, 10), scale=2.1, collider="box"))
        self.board = self.add(Entity(model=city("building-type-d"), position=(-5, 0, 10), scale=1.9, collider="box"))
        self.add(Text("SHOP [E]", world_position=(5, 3.5, 10), billboard=True, scale=1.0, color=CYAN))
        self.add(Text("QUEST BOARD [E]", world_position=(-5, 3.5, 10), billboard=True, scale=.9, color=YELLOW))
        self.car_entity = Entity(model=car("sedan"), position=(-7, .5, 0), scale=1.25, collider="box")
        self.add(self.car_entity)
        # The supplied packs contain city/vehicle models, but no humanoid GLBs.
        # Keep the character fully 3D with a small primitive body until a character
        # pack is added; the gameplay interface does not depend on the model.
        self.avatar = self.add(Entity(model="cube", position=(-5.5, .9, 0), scale=(.7, 1.6, .7), color=YELLOW))
        Entity(parent=self.avatar, model="sphere", y=.95, scale=.55, color=color.rgb(255, 205, 160))
        Entity(parent=self.avatar, model="cube", y=.48, scale=(1.05, .12, 1.05), color=CYAN)
        self.avatar.enabled = False
        self.in_car = True
        for name, pos, rotation in (("taxi", (-15, .45, 0), 0), ("police", (11, .45, 0), 0), ("van", (0, .45, 12), 90), ("delivery", (0, .45, -12), 90)):
            self.traffic.append(Entity(model=car(name), position=pos, rotation_y=rotation, scale=1.2))
        enemy_setup = (("bruiser", (11, 1.1, -5), PINK), ("punk", (14, 1.1, 6), CYAN), ("businessman", (-12, 1.1, -5), color.orange))
        for kind, pos, tint in enemy_setup:
            enemy = Entity(model="cube", position=pos, scale=(.8, 1.6, .8), color=tint)
            Entity(parent=enemy, model="sphere", y=.95, scale=.55, color=color.rgb(235, 175, 140))
            Entity(parent=enemy, model="cube", y=.48, scale=(1.05, .12, 1.05), color=color.rgb(35, 35, 48))
            self.enemies.append({"entity": enemy, "kind": kind, "hp": 2, "dead": False, "tint": tint})
        self.add(Text(f"UL. {['ZWYCIESTWA', 'DWORCOWA', 'DOLNYCH WALOW', 'CHORZOWSKA', 'RYNEK'][self.street % 5]}", world_position=(-2, 4, -1), billboard=True, scale=1.0, color=YELLOW))
        camera.position = (-7, 19, -18); camera.look_at(self.car_entity.position)

    def start(self):
        self.state = "PLAY"
        for item in (self.intro, self.map_panel, self.menu_card, self.menu, self.quest_panel, self.quest_text, self.shop_panel, self.shop_text): item.enabled = False
        self.hud_bg.enabled = True; self.help_bg.enabled = True; self.notice_bg.enabled = True
        self.hud.enabled = True; self.help.enabled = True; self.notice.enabled = True
        self.notice.text = "3D STREET READY // E EXIT CAR"

    def show_menu(self):
        self.state = "MENU"
        self.intro.enabled = False; self.map_panel.enabled = True; self.menu_card.enabled = True; self.menu.enabled = True
        self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False
        self.hud.enabled = False; self.help.enabled = False; self.notice.enabled = False

    def open_quest(self):
        self.state = "QUEST"
        self.map_panel.enabled = False; self.menu_card.enabled = False; self.hud.enabled = False; self.help.enabled = False
        self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False
        self.quest_panel.enabled = True; self.quest_text.enabled = True
        self.quest_text.text = f"QUEST BOARD\n\nCLEAN STREET {self.street + 1}\nREMOVE 3 TARGETS\nREWARD 30 COINS + 50 XP\n\nENTER ACCEPT   E CLOSE"

    def open_shop(self):
        self.state = "SHOP"
        self.shop_panel.enabled = True; self.shop_text.enabled = True; self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False; self.hud.enabled = False; self.help.enabled = False
        self.shop_text.text = f"NIGHT SHOP\n\nP  PAN UPGRADE  30 COINS\n\nCOINS {self.coins}\n\nE CLOSE"

    def update(self, dt):
        if self.state == "INTRO":
            self.intro_time += dt
            if self.intro_time > 3.0: self.show_menu()
            return
        if self.state != "PLAY": return
        if self.in_car:
            forward = held_keys["w"] - held_keys["s"]
            steer = held_keys["d"] - held_keys["a"]
            if forward: self.car_entity.position += self.car_entity.forward * forward * 8 * dt
            self.car_entity.rotation_y += steer * 100 * dt
            self.car_entity.x = clamp(self.car_entity.x, -28, 28); self.car_entity.z = clamp(self.car_entity.z, -22, 22)
            actor = self.car_entity
        else:
            actor = self.avatar
            direction = Vec3(held_keys["d"] - held_keys["a"], 0, held_keys["w"] - held_keys["s"])
            if direction.length() and actor:
                actor.position += direction.normalized() * 4.5 * dt
                actor.x = clamp(actor.x, -28, 28); actor.z = clamp(actor.z, -22, 22)
        camera.position = lerp(camera.position, actor.position + Vec3(0, 15 if not self.in_car else 19, -14 if not self.in_car else -18), dt * 4)
        camera.look_at(actor.position + Vec3(0, 0, 1))
        for enemy in self.enemies:
            if enemy["dead"]: continue
            delta = actor.position - enemy["entity"].position
            delta.y = 0
            if delta.length() > 3 and delta.length() < 16: enemy["entity"].position += delta.normalized() * 1.2 * dt
        mode = "DRIVING" if self.in_car else "ON FOOT"
        self.hud.text = f"GLIWICE // {['ZWYCIESTWA', 'DWORCOWA', 'DOLNYCH WALOW', 'CHORZOWSKA', 'RYNEK'][self.street % 5]}   COINS {self.coins}   XP {self.xp}   {mode}"

    def input(self, key):
        if self.state == "INTRO": self.show_menu()
        elif self.state == "MENU" and key in ("enter", "left mouse down"): self.start()
        elif self.state == "PLAY":
            if key == "escape": self.show_menu()
            elif key in ("j", "left mouse down"):
                if self.in_car:
                    self.notice.text = "E EXIT CAR TO START A CLEANUP FIGHT"
                    return
                target = min((e for e in self.enemies if not e["dead"]), key=lambda e: distance(self.avatar, e["entity"]), default=None)
                if target and distance(self.avatar, target["entity"]) < 3.2:
                    target["hp"] -= 1; self.notice.text = "PAN BONK!"
                    if target["hp"] <= 0:
                        target["dead"] = True; target["entity"].animate_scale(0, duration=.15); self.coins += 5; self.xp += 10; self.save()
            elif key == "e" and distance(self.avatar if not self.in_car else self.car_entity, self.shop) < 4: self.open_shop()
            elif key == "e" and distance(self.avatar if not self.in_car else self.car_entity, self.board) < 4: self.open_quest()
            elif key == "e" and self.in_car and self.car_entity.x > 20 and all(e["dead"] for e in self.enemies):
                self.street += 1; self.build_street(); self.start()
            elif key == "e" and self.in_car:
                self.in_car = False
                self.avatar.position = self.car_entity.position + Vec3(1.4, .4, 0)
                self.avatar.enabled = True
                self.notice.text = "ON FOOT // J CLEANUP PAN // E ENTER CAR"
            elif key == "e" and not self.in_car and distance(self.avatar, self.car_entity) < 2.5:
                self.in_car = True
                self.avatar.enabled = False
                self.notice.text = "BACK IN CAR // DRIVE TO THE NEXT STREET"
        elif self.state == "QUEST":
            if key in ("e", "escape"): self.start()
            elif key == "enter": self.quest_text.text = "QUEST ACTIVE\n\nREMOVE 3 TARGETS\n\nE CLOSE"; self.notice.text = "CLEANUP JOB ACCEPTED"
        elif self.state == "SHOP":
            if key in ("e", "escape"): self.start()
            elif key == "p" and self.coins >= 30: self.coins -= 30; self.save(); self.open_shop()

    def run(self): app.run()


app = None
game = None


def update():
    if game: game.update(time.dt)


def input(key):
    if game: game.input(key)


def create_app():
    global app, game
    app = Ursina(borderless=False, development_mode=False)
    window.title = "Green-Eye // Gliwice 3D Streets"; window.color = NIGHT; scene.fog_color = NIGHT
    Sky(color=color.rgb(16, 20, 35))
    AmbientLight(color=color.rgba(110, 110, 110, 1))
    DirectionalLight(rotation=(45, -45, 45), color=color.rgba(150, 150, 150, 1))
    game = HybridGame(); game.run()


if __name__ == "__main__": create_app()

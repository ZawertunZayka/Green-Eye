from __future__ import annotations

import json
from pathlib import Path
from ursina import *

ROOT = Path(__file__).parent
SAVE = ROOT / "save.json"
CITY = "assets/user/3d_city/Models/GLB"
CARS = "assets/user/3d_city/Models/Cars/GLB"
ROADS = "assets/user/3d_city/Models/Roads/GLB"
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
        self.state = "MENU"
        self.coins, self.xp = self.load_progress()
        self.scene_entities: list[Entity] = []
        self.traffic: list[Entity] = []
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
        self.menu = Text("GREEN-EYE\n\nGLIWICE // NIGHT CLEANUP\n\nENTER  START 3D STREET", parent=camera.ui, origin=(0, 0), y=.08, scale=.055, color=YELLOW)
        self.hud = Text("", parent=camera.ui, position=(-.48, .45), scale=.9, color=YELLOW, enabled=False)
        self.help = Text("WASD DRIVE   E SHOP / QUEST   SPACE BRAKE   ESC MENU", parent=camera.ui, position=(-.48, -.46), scale=.8, color=color.white, enabled=False)
        self.notice = Text("", parent=camera.ui, origin=(0, 0), y=-.28, scale=.05, color=CYAN, enabled=False)

    def add(self, entity):
        self.scene_entities.append(entity)
        return entity

    def build_street(self):
        for entity in self.scene_entities + self.traffic:
            destroy(entity)
        self.scene_entities.clear(); self.traffic.clear()
        self.add(Entity(model="cube", position=(0, -.35, 0), scale=(70, .5, 55), color=color.rgb(37, 52, 42)))
        # Real road GLBs, not flat Python rectangles.
        for x in range(-24, 25, 4): self.add(Entity(model=road("road-straight"), position=(x, .03, 0), scale=2.2))
        for z in range(-20, 21, 4): self.add(Entity(model=road("road-straight"), position=(0, .04, z), rotation_y=90, scale=2.2))
        self.add(Entity(model=road("road-crossroad"), position=(0, .06, 0), scale=2.3))
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
        for name, pos, rotation in (("taxi", (-15, .45, 0), 0), ("police", (11, .45, 0), 0), ("van", (0, .45, 12), 90), ("delivery", (0, .45, -12), 90)):
            self.traffic.append(Entity(model=car(name), position=pos, rotation_y=rotation, scale=1.2))
        camera.position = (-7, 19, -18); camera.look_at(self.car_entity.position)

    def start(self):
        self.state = "PLAY"
        self.menu.enabled = False; self.hud.enabled = True; self.help.enabled = True; self.notice.enabled = True
        self.notice.text = "3D STREET READY"

    def update(self, dt):
        if self.state != "PLAY": return
        forward = held_keys["w"] - held_keys["s"]
        steer = held_keys["d"] - held_keys["a"]
        if forward: self.car_entity.position += self.car_entity.forward * forward * 8 * dt
        self.car_entity.rotation_y += steer * 100 * dt
        self.car_entity.x = clamp(self.car_entity.x, -28, 28); self.car_entity.z = clamp(self.car_entity.z, -22, 22)
        camera.position = lerp(camera.position, self.car_entity.position + Vec3(0, 19, -18), dt * 4)
        camera.look_at(self.car_entity.position + Vec3(0, 0, 2))
        self.hud.text = f"GLIWICE // RYNEK     COINS {self.coins}     XP {self.xp}     SEDAN"

    def input(self, key):
        if self.state == "MENU" and key in ("enter", "left mouse down"): self.start()
        elif self.state == "PLAY":
            if key == "escape": self.state = "MENU"; self.menu.enabled = True; self.hud.enabled = False; self.help.enabled = False
            elif key == "e" and distance(self.car_entity, self.shop) < 4: self.notice.text = "SHOP // DRIVE-UP"
            elif key == "e" and distance(self.car_entity, self.board) < 4: self.notice.text = "QUEST BOARD // CLEAN THE STREET"

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
    AmbientLight(color=color.rgba(190, 190, 190, 1))
    DirectionalLight(rotation=(45, -45, 45), color=color.rgba(220, 220, 220, 1))
    game = HybridGame(); game.run()


if __name__ == "__main__": create_app()

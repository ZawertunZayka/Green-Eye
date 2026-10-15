from __future__ import annotations

import json
import math
from pathlib import Path
from ursina import *
from ursina.shaders import unlit_shader
from panda3d.core import NodePath
import gltf

ROOT = Path(__file__).parent
SAVE = ROOT / "save.json"
CITY = "assets/user/3d_city/Models/GLB"
CARS = "assets/user/3d_city/Models/Cars/GLB"
ROADS = "assets/user/3d_city/Models/Roads/GLB"
CHARACTERS = "assets/user/3d_arcade/Models/OBJ format"
NATURE = "assets/user/3d_nature/FULL_VERSION_ALL_MODELS/GLB"
SKELETONS = "assets/user/3d_skeletons/KayKit_Skeletons_1.1_FREE/characters/gltf"
MAP = "assets/user/city/gliwice_map.png"
WALK = "assets/user/walk"
NIGHT = color.rgb32(10, 12, 24)
CYAN = color.rgb32(0, 225, 220)
PINK = color.rgb32(255, 35, 120)
YELLOW = color.rgb32(255, 225, 80)


def city(name):
    return f"{CITY}/{name}.glb"


def car(name):
    return f"{CARS}/{name}.glb"


def road(name):
    return f"{ROADS}/{name}.glb"


def character(name):
    return f"{CHARACTERS}/{name}.obj"


def nature(name):
    return f"{NATURE}/{name}.glb"


def skeleton(name):
    # KayKit exports these models with Z as up; Ursina's street uses Y as up.
    return NodePath(gltf.load_model(f"{SKELETONS}/Skeleton_{name}.glb"))


class HybridGame:
    """3D street layer with the project's 2D-style HUD and quest prompts."""
    LEVEL_NAMES = ("ZWYCIESTWA", "DWORCOWA", "ZSTI SCHOOL")
    LEVELS = (
        (("bruiser", (11, 0, -5), PINK, "Warrior", 2), ("punk", (14, 0, 6), CYAN, "Rogue", 2)),
        (("punk", (11, 0, -5), CYAN, "Rogue", 2), ("businessman", (-12, 0, -5), color.orange, "Mage", 2), ("bruiser", (14, 0, 6), PINK, "Warrior", 3)),
        (("bruiser", (11, 0, -5), PINK, "Warrior", 3), ("punk", (14, 0, 6), CYAN, "Rogue", 3), ("zsti_boss", (7, 0, 2), YELLOW, "Mage", 5)),
    )
    def __init__(self):
        self.state = "INTRO"
        self.intro_time = 0.0
        self.street = 0
        self.coins, self.xp = self.load_progress()
        self.scene_entities: list[Entity] = []
        self.traffic: list[Entity] = []
        self.enemies: list[dict] = []
        self.attack_effects: list[Entity] = []
        self.projectiles: list[dict] = []
        self.avatar: Entity | None = None
        self.in_car = True
        self.attack_cooldown = 0.0
        self.fight_banner_time = 0.0
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
        self.map_panel = Entity(parent=camera.ui, model="quad", texture=MAP, scale=(1.72, 1), color=color.rgba32(255, 255, 255, 255), enabled=False)
        self.menu_card = Entity(parent=camera.ui, model="quad", color=color.rgba32(8, 6, 18, 248), scale=(.62, .78), enabled=False)
        self.menu = Text("GLIWICE // RYNEK\n\nCLEANUP PROGRESS\n\n3 STREET CAMPAIGN\n\nENTER / LEFT CLICK  START", parent=camera.ui, origin=(0, 0), y=.08, scale=.045, color=YELLOW, enabled=False)
        self.hud_bg = Entity(parent=camera.ui, model="quad", position=(0, .455), scale=(.98, .075), color=color.rgba32(8, 12, 24, 245), enabled=False)
        self.hud = Text("", parent=camera.ui, position=(-.46, .462), scale=.72, color=YELLOW, enabled=False)
        self.objective_bg = Entity(parent=camera.ui, model="quad", position=(-.33, .335), scale=(.48, .095), color=color.rgba32(8, 12, 24, 235), enabled=False)
        self.objective = Text("", parent=camera.ui, position=(-.55, .355), scale=.62, color=CYAN, enabled=False)
        self.help_bg = Entity(parent=camera.ui, model="quad", position=(0, -.46), scale=(1.08, .07), color=color.rgba32(8, 12, 24, 245), enabled=False)
        self.help = Text("W/S  DRIVE   A/D  STEER   E  EXIT / ENTER   J  CLEANUP   ESC  MENU", parent=camera.ui, position=(-.51, -.467), scale=.68, color=color.white, enabled=False)
        self.notice_bg = Entity(parent=camera.ui, model="quad", position=(0, -.32), scale=(.62, .07), color=color.rgba32(8, 12, 24, 245), enabled=False)
        self.notice = Text("", parent=camera.ui, origin=(0, 0), y=-.32, scale=.045, color=CYAN, enabled=False)
        self.fight_banner = Text("", parent=camera.ui, origin=(0, 0), y=.22, scale=.085, color=PINK, enabled=False)
        self.quest_panel = Entity(parent=camera.ui, model="quad", color=color.rgb32(18, 14, 32), scale=(.78, .58), enabled=False)
        self.quest_text = Text("", parent=camera.ui, origin=(0, 0), y=.03, scale=.045, color=YELLOW, enabled=False)
        self.shop_panel = Entity(parent=camera.ui, model="quad", color=color.rgb32(18, 14, 32), scale=(.78, .58), enabled=False)
        self.shop_text = Text("", parent=camera.ui, origin=(0, 0), y=.03, scale=.045, color=CYAN, enabled=False)
        self.win_panel = Entity(parent=camera.ui, model="quad", color=color.rgba32(8, 6, 18, 250), scale=(.72, .62), enabled=False)
        self.win_text = Text("", parent=camera.ui, origin=(0, 0), y=.04, scale=.055, color=YELLOW, enabled=False)

    def add(self, entity):
        self.scene_entities.append(entity)
        return entity

    def get_mouse_aim_point(self) -> Vec3:
        """Return the cursor's point on the street plane."""
        if mouse.collision and mouse.collision.world_point:
            point = Vec3(mouse.collision.world_point)
            point.y = 0
            return point
        return self.avatar.position + self.avatar.forward * 8

    def show_cleanup_hit(self, target: Entity | None, aim_point: Vec3 | None = None) -> None:
        """Show a short, readable cleanup beam instead of an invisible hit."""
        if not self.avatar:
            return
        start = self.avatar.position + Vec3(0, 1.1, 0)
        end = target.position + Vec3(0, 1.0, 0) if target else (aim_point or start + self.avatar.forward * 2.5)
        if not target:
            end.y = 1.0
        beam = Entity(
            model="cube",
            position=(start + end) / 2,
            scale=(.12, .12, max(.2, distance(start, end))),
            color=YELLOW,
            shader=unlit_shader,
            billboard=False,
        )
        beam.look_at(end)
        self.attack_effects.append(beam)
        invoke(self.remove_attack_effect, beam, delay=.12)
        if target:
            flash = Entity(model="quad", position=end, scale=1.0, color=color.rgba32(255, 246, 120, 230), billboard=True, double_sided=True)
            self.attack_effects.append(flash)
            invoke(self.remove_attack_effect, flash, delay=.16)

    def remove_attack_effect(self, effect: Entity) -> None:
        if effect in self.attack_effects:
            self.attack_effects.remove(effect)
        destroy(effect)

    def damage_enemy(self, target: dict) -> None:
        """Apply one hit after a cleanup projectile reaches its target."""
        entity = target["entity"]
        target["hp"] -= 1
        self.notice.text = "PAN BONK!"
        direction = entity.position - self.avatar.position
        direction.y = 0
        if direction.length():
            entity.animate_position(entity.position + direction.normalized() * 1.3, duration=.12)
        entity.animate_color(color.white, duration=.05)
        invoke(entity.animate_color, target["tint"], delay=.10, duration=.12)
        flash = Entity(model="quad", position=entity.position + Vec3(0, 1, 0), scale=.9, color=color.rgba32(255, 246, 120, 230), billboard=True, double_sided=True)
        self.attack_effects.append(flash)
        invoke(self.remove_attack_effect, flash, delay=.12)
        if target["hp"] <= 0:
            target["dead"] = True
            entity.animate_rotation_z(180, duration=.18)
            entity.animate_scale(0, duration=.2)
            self.coins += 5; self.xp += 10; self.save()
            if self.street == 2 and all(enemy["dead"] for enemy in self.enemies):
                invoke(self.win_game, delay=.35)

    def spawn_projectile(self, aim_point: Vec3) -> None:
        start = self.avatar.position + Vec3(0, 1.1, 0)
        direction = aim_point - start
        direction.y = 0
        if not direction.length():
            direction = self.avatar.forward
        direction = direction.normalized()
        shot = Entity(model="sphere", position=start, scale=.22, color=YELLOW, shader=unlit_shader)
        self.projectiles.append({"entity": shot, "velocity": direction * 15, "target": None, "life": 1.0})

    def update_projectiles(self, dt: float) -> None:
        for shot in self.projectiles[:]:
            projectile = shot["entity"]
            shot["life"] -= dt
            target = shot["target"]
            if target is None:
                nearby = [enemy for enemy in self.enemies if not enemy["dead"] and distance(projectile, enemy["entity"]) < 2.0]
                if nearby:
                    shot["target"] = min(nearby, key=lambda enemy: distance(projectile, enemy["entity"]))
                    target = shot["target"]
            if target and not target["dead"]:
                direction = target["entity"].position + Vec3(0, 1, 0) - projectile.position
                if direction.length():
                    shot["velocity"] = direction.normalized() * 15
                if distance(projectile, target["entity"].position + Vec3(0, 1, 0)) < .75:
                    self.damage_enemy(target)
                    self.projectiles.remove(shot)
                    destroy(projectile)
                    continue
            projectile.position += shot["velocity"] * dt
            if shot["life"] <= 0:
                self.projectiles.remove(shot)
                destroy(projectile)

    def build_street(self):
        for entity in self.scene_entities + self.traffic:
            destroy(entity)
        for effect in self.attack_effects:
            destroy(effect)
        self.attack_effects.clear()
        for shot in self.projectiles:
            destroy(shot["entity"])
        self.projectiles.clear()
        for enemy in self.enemies:
            destroy(enemy["entity"])
        self.scene_entities.clear(); self.traffic.clear()
        self.enemies.clear()
        # Continuous grass base and asphalt underlays keep the city readable even
        # where individual road-kit meshes have small tile gaps.
        # Thin horizontal cubes are used instead of planes: in Ursina this makes
        # the XZ orientation explicit, so the green field always fills the map.
        self.add(Entity(model="cube", position=(0, -.30, 0), scale=(120, .6, 120), texture="white_cube", shader=unlit_shader, color=color.rgb32(42, 112, 58)))
        self.add(Entity(model="cube", position=(0, -.08, 0), scale=(120, .04, 120), collider="box", visible=False))
        self.add(Entity(model="cube", position=(0, -.005, 0), scale=(66, .08, 8.2), texture="white_cube", shader=unlit_shader, color=color.rgb32(48, 51, 61)))
        self.add(Entity(model="cube", position=(0, 0, 0), scale=(8.2, .08, 52), texture="white_cube", shader=unlit_shader, color=color.rgb32(48, 51, 61)))
        # Real road GLBs, not flat Python rectangles.
        for x in range(-24, 25, 4): self.add(Entity(model=road("road-straight"), position=(x, .03, 0), scale=2.2))
        for z in range(-20, 21, 4): self.add(Entity(model=road("road-straight"), position=(0, .04, z), rotation_y=90, scale=2.2))
        self.add(Entity(model=road("road-crossroad"), position=(0, .06, 0), scale=2.3))
        # Long, unbroken lane/curb lines instead of isolated decorative dashes.
        line = color.rgb32(238, 209, 92)
        for z in (-3.7, 3.7): self.add(Entity(model="cube", position=(0, .16, z), scale=(64, .035, .09), color=line, shader=unlit_shader))
        for x in (-3.7, 3.7): self.add(Entity(model="cube", position=(x, .17, 0), scale=(.09, .035, 50), color=line, shader=unlit_shader))
        houses = [("building-type-a", (-16, 5), 2.4), ("building-type-c", (-9, 5), 2.3), ("building-type-f", (9, 5), 2.4), ("building-type-h", (16, 5), 2.2), ("building-type-k", (-15, -8), 2.4), ("building-type-m", (9, -8), 2.3), ("building-type-r", (16, -8), 2.3)]
        for name, pos, size in houses: self.add(Entity(model=city(name), position=(pos[0], 0, pos[1]), scale=size, collider="box"))
        for name, pos, size in (("tree-large", (-5, 0, 8), 1.5), ("tree-small", (12, 0, 2), 1.4), ("planter", (5, 0, 7), 1.5)):
            self.add(Entity(model=city(name), position=pos, scale=size))
        for name, pos, size in (("grass_1", (-8, 0, 8), 2.8), ("grass_2", (-3, 0, 8), 2.8), ("bush_1", (8, 0, 8), 2.4), ("flowers_1", (12, 0, 8), 2.2), ("fern", (-12, 0, 8), 2.0), ("grass_1", (18, 0, 5), 2.6)):
            self.add(Entity(model=nature(name), position=pos, scale=size))
        self.shop = self.add(Entity(model=city("building-type-b"), position=(5, 0, 10), scale=2.1, collider="box"))
        self.board = self.add(Entity(model=city("building-type-d"), position=(-5, 0, 10), scale=1.9, collider="box"))
        for label, pos, tint, width in (("SHOP [E]", (5, 3.5, 10), CYAN, 2.8), ("QUEST BOARD [E]", (-5, 3.5, 10), YELLOW, 4.0)):
            self.add(Entity(model="quad", position=pos, scale=(width, .7), color=color.rgba32(8, 12, 24, 230), billboard=True, double_sided=True))
            self.add(Text(label, world_position=(pos[0], pos[1], pos[2] - .05), billboard=True, scale=.8, color=tint))
        if self.street == 2:
            school_pos = (17, 0, 9)
            self.add(Entity(model=city("building-type-r"), position=school_pos, scale=2.8, collider="box"))
            self.add(Entity(model="quad", position=(17, 4.3, 9), scale=(4.6, .8), color=color.rgba32(8, 12, 24, 235), billboard=True, double_sided=True))
            self.add(Text("ZSTI SCHOOL // FINAL CLEANUP", world_position=(17, 4.25, 8.95), billboard=True, scale=.72, color=YELLOW))
        self.car_entity = Entity(model=car("sedan"), position=(-7, .5, 0), scale=1.25, collider="box")
        self.add(self.car_entity)
        # The OBJ loader is compatible with this Ursina/glTF version; provide the
        # shared Kenney colormap explicitly because the MTL uses a relative path.
        self.avatar = self.add(Entity(model=character("character-gamer"), texture=f"{CHARACTERS}/Textures/colormap.png", position=(-5.5, 0, 0), scale=2.25))
        self.avatar.enabled = False
        self.in_car = True
        for name, pos, rotation in (("taxi", (-15, .45, 0), 0), ("police", (11, .45, 0), 0), ("van", (0, .45, 12), 90), ("delivery", (0, .45, -12), 90)):
            self.traffic.append(Entity(model=car(name), position=pos, rotation_y=rotation, scale=1.2))
        for kind, pos, tint, model_name, hp in self.LEVELS[self.street]:
            enemy = Entity(model=skeleton(model_name), position=pos, rotation_x=0, scale=.65, color=tint)
            self.enemies.append({"entity": enemy, "kind": kind, "hp": hp, "dead": False, "tint": tint})
        self.add(Text(f"UL. {self.LEVEL_NAMES[self.street]}", world_position=(-2, 4, -1), billboard=True, scale=1.0, color=YELLOW))
        camera.position = (-7, 19, -18); camera.look_at(self.car_entity.position)

    def start(self):
        self.state = "PLAY"
        for item in (self.intro, self.map_panel, self.menu_card, self.menu, self.quest_panel, self.quest_text, self.shop_panel, self.shop_text, self.win_panel, self.win_text): item.enabled = False
        self.fight_banner.enabled = False
        self.hud_bg.enabled = True; self.help_bg.enabled = True; self.notice_bg.enabled = True
        self.hud.enabled = True; self.help.enabled = True; self.notice.enabled = True; self.objective_bg.enabled = True; self.objective.enabled = True
        self.notice.text = "READY // PRESS E TO LEAVE THE CAR"

    def show_menu(self):
        self.state = "MENU"
        self.intro.enabled = False; self.map_panel.enabled = True; self.menu_card.enabled = True; self.menu.enabled = True
        self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False
        self.hud.enabled = False; self.help.enabled = False; self.notice.enabled = False; self.objective_bg.enabled = False; self.objective.enabled = False

    def win_game(self):
        self.state = "WIN"
        self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False
        self.hud.enabled = False; self.help.enabled = False; self.notice.enabled = False; self.objective_bg.enabled = False; self.objective.enabled = False
        self.fight_banner.enabled = False
        self.win_panel.enabled = True; self.win_text.enabled = True
        self.win_text.text = "ZSTI CLEANUP COMPLETE!\n\nTHE CITY IS TIDY\n\nCOINS %d   XP %d\n\nENTER  PLAY AGAIN" % (self.coins, self.xp)

    def open_quest(self):
        self.state = "QUEST"
        self.map_panel.enabled = False; self.menu_card.enabled = False; self.hud.enabled = False; self.help.enabled = False
        self.objective_bg.enabled = False; self.objective.enabled = False
        self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False
        self.quest_panel.enabled = True; self.quest_text.enabled = True
        self.quest_text.text = f"QUEST BOARD\n\nLEVEL {self.street + 1}/3: {self.LEVEL_NAMES[self.street]}\nREMOVE TARGETS\nREWARD 30 COINS + 50 XP\n\nENTER ACCEPT   E CLOSE"

    def open_shop(self):
        self.state = "SHOP"
        self.shop_panel.enabled = True; self.shop_text.enabled = True; self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False; self.hud.enabled = False; self.help.enabled = False; self.objective_bg.enabled = False; self.objective.enabled = False
        self.shop_text.text = f"NIGHT SHOP\n\nP  PAN UPGRADE  30 COINS\n\nCOINS {self.coins}\n\nE CLOSE"

    def update(self, dt):
        if self.state == "INTRO":
            self.intro_time += dt
            if self.intro_time > 3.0: self.show_menu()
            return
        if self.state != "PLAY": return
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        if self.fight_banner_time > 0:
            self.fight_banner_time -= dt
            if self.fight_banner_time <= 0: self.fight_banner.enabled = False
        self.update_projectiles(dt)
        if self.in_car:
            forward = held_keys["s"] - held_keys["w"]
            steer = held_keys["a"] - held_keys["d"]
            if forward: self.car_entity.position += self.car_entity.forward * forward * 8 * dt
            self.car_entity.rotation_y += steer * 100 * dt
            self.car_entity.x = clamp(self.car_entity.x, -28, 28); self.car_entity.z = clamp(self.car_entity.z, -22, 22)
            actor = self.car_entity
            self.avatar.enabled = False
        else:
            actor = self.avatar
            direction = Vec3(held_keys["d"] - held_keys["a"], 0, held_keys["w"] - held_keys["s"])
            if direction.length() and actor:
                actor.position += direction.normalized() * 4.5 * dt
                actor.x = clamp(actor.x, -28, 28); actor.z = clamp(actor.z, -22, 22)
                # While walking, face the direction of travel.
                actor.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
            elif actor:
                # When idle, keep looking back at the car.
                to_car = self.car_entity.position - actor.position
                actor.rotation_y = math.degrees(math.atan2(to_car.x, to_car.z))
        camera.position = lerp(camera.position, actor.position + Vec3(0, 11 if not self.in_car else 17, -16 if not self.in_car else -18), dt * 4)
        camera.look_at(actor.position + Vec3(0, 1.2 if not self.in_car else 0, 1))
        for enemy in self.enemies:
            if enemy["dead"]: continue
            delta = actor.position - enemy["entity"].position
            delta.y = 0
            if delta.length() > 3 and delta.length() < 16: enemy["entity"].position += delta.normalized() * 1.2 * dt
        mode = "DRIVING" if self.in_car else "ON FOOT"
        self.hud.text = f"GLIWICE  |  LEVEL {self.street + 1}/3  |  UL. {self.LEVEL_NAMES[self.street]}  |  COINS {self.coins}  |  XP {self.xp}  |  {mode}"
        remaining = sum(not enemy["dead"] for enemy in self.enemies)
        objective = "DEFEAT THE ZSTI BOSS" if self.street == 2 else "CLEAR THE STREET"
        self.objective.text = f"OBJECTIVE\n{objective}  [{remaining} LEFT]"

    def input(self, key):
        if self.state == "INTRO": self.show_menu()
        elif self.state == "MENU" and key in ("enter", "left mouse down"): self.start()
        elif self.state == "PLAY":
            if key == "escape": self.show_menu()
            elif key in ("j", "left mouse down"):
                if self.in_car:
                    self.notice.text = "E EXIT CAR TO START A CLEANUP FIGHT"
                    return
                if self.attack_cooldown > 0: return
                self.attack_cooldown = .28
                aim_point = self.get_mouse_aim_point()
                aim = aim_point - self.avatar.position
                aim.y = 0
                if aim.length():
                    self.avatar.rotation_y = math.degrees(math.atan2(aim.x, aim.z))
                self.spawn_projectile(aim_point)
                self.notice.text = "CLEANUP SHOT // HOMING"
            elif key == "e" and distance(self.avatar if not self.in_car else self.car_entity, self.shop) < 4: self.open_shop()
            elif key == "e" and distance(self.avatar if not self.in_car else self.car_entity, self.board) < 4: self.open_quest()
            elif key == "e" and self.in_car and self.car_entity.x > 20 and all(e["dead"] for e in self.enemies):
                if self.street < 2:
                    self.street += 1; self.build_street(); self.start()
                else:
                    self.win_game()
            elif key == "e" and self.in_car:
                self.in_car = False
                self.avatar.position = self.car_entity.position + Vec3(1.4, -.5, 0)
                self.avatar.enabled = True
                self.fight_banner.text = "CLEANUP FIGHT!"
                self.fight_banner.enabled = True; self.fight_banner_time = 1.2
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
        elif self.state == "WIN":
            if key == "enter":
                self.street = 0; self.coins = 0; self.xp = 0; self.save(); self.build_street(); self.start()
            elif key == "escape": self.show_menu()

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
    window.title = "Green-Eye // Gliwice 3D Streets"; window.color = color.rgb32(28, 72, 38); scene.fog_color = color.rgb32(28, 72, 38)
    AmbientLight(color=color.rgb32(55, 55, 55))
    DirectionalLight(rotation=(45, -45, 45), color=color.rgb32(85, 85, 85))
    game = HybridGame(); game.run()


if __name__ == "__main__": create_app()

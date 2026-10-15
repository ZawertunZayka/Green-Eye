from __future__ import annotations

import json
import math
import random
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
    UPGRADES = (
        ("power", "HEAVY PAN", "+1 projectile damage"),
        ("vitality", "BIG LUNCH", "+20 maximum HP and heal 20"),
        ("speed", "QUICK SHOES", "+12% walking and running speed"),
        ("rapid", "FAST HANDS", "+15% firing speed"),
        ("armor", "THICK APRON", "Take 15% less damage"),
        ("heal", "WARM SOUP", "Restore 35 HP now"),
    )
    WEAPONS = (
        {"id": "pan", "name": "CLEANUP PAN", "price": 0, "damage": 1, "cooldown": .28, "speed": 15, "color": YELLOW},
        {"id": "pin", "name": "ROLLING PIN", "price": 45, "damage": 2, "cooldown": .38, "speed": 18, "color": color.orange},
        {"id": "soup", "name": "SOUP BLASTER", "price": 75, "damage": 3, "cooldown": .52, "speed": 20, "color": CYAN},
    )
    STORY = (
        "A cleanup call arrives. Clear the street and follow the road east.",
        "A dropped note points farther east: ZSTI. Someone is waiting there.",
        "ZSTI courtyard. The Principal of Disorder challenges the city's cleaner!",
    )
    LEVELS = (
        (("bruiser", (11, 0, -3), PINK, "Warrior", 2), ("punk", (16, 0, 3), CYAN, "Rogue", 2),
         ("punk", (-12, 0, 3), CYAN, "Rogue", 2), ("businessman", (-19, 0, -3), color.orange, "Mage", 2),
         ("bruiser", (3, 0, 13), PINK, "Warrior", 3), ("punk", (-3, 0, -14), CYAN, "Rogue", 2)),
        (("punk", (10, 0, -3), CYAN, "Rogue", 2), ("businessman", (-11, 0, -3), color.orange, "Mage", 2),
         ("bruiser", (17, 0, 3), PINK, "Warrior", 3), ("bruiser", (-19, 0, 3), PINK, "Warrior", 3),
         ("punk", (3, 0, 14), CYAN, "Rogue", 2), ("businessman", (-3, 0, -14), color.orange, "Mage", 2),
         ("punk", (3, 0, -12), CYAN, "Rogue", 2)),
        (("zsti_boss", (13, 0, 0), YELLOW, "Mage", 12),
         ("boss_guard", (6, 0, -6), PINK, "Warrior", 3), ("boss_guard", (6, 0, 6), CYAN, "Rogue", 3),
         ("boss_guard", (16, 0, -6), color.orange, "Mage", 3), ("boss_guard", (16, 0, 6), PINK, "Warrior", 3)),
    )
    def __init__(self):
        camera.fov = 65
        self.state = "INTRO"
        self.intro_time = 0.0
        self.street = 0
        self.weapon_level = 0
        self.unlocked_weapons = {"pan"}
        self.equipped_weapon = "pan"
        self.coins, self.xp = self.load_progress()
        self.scene_entities: list[Entity] = []
        self.building_bounds: list[tuple[float, float, float, float]] = []
        self.traffic: list[Entity] = []
        self.traffic_velocity: dict[int, Vec3] = {}
        self.car_speed = 0.0
        self.vehicle_time = 0.0
        self.car_collision_cooldown = 0.0
        self.animation_time = 0.0
        self.enemies: list[dict] = []
        self.attack_effects: list[Entity] = []
        self.projectiles: list[dict] = []
        self.enemy_projectiles: list[dict] = []
        self.locked_enemy: dict | None = None
        self.lock_marker: Entity | None = None
        self.east_exit_markers: list[Entity] = []
        self.intro_actors: list[dict] = []
        self.intro_hero: Entity | None = None
        self.avatar: Entity | None = None
        self.in_car = True
        self.max_hp = 100
        self.player_hp = self.max_hp
        self.damage_bonus = 0
        self.move_multiplier = 1.0
        self.attack_delay = .28
        self.damage_multiplier = 1.0
        self.upgrade_choices: list[tuple[str, str, str]] = []
        self.damage_cooldown = 0.0
        self.attack_cooldown = 0.0
        self.fight_banner_time = 0.0
        self.story_queue: list[str] = []
        self.story_time = 0.0
        self.create_ui()
        self.build_street()
        self.build_intro()

    def load_progress(self):
        try:
            data = json.loads(SAVE.read_text())
            if not isinstance(data, dict):
                return 0, 0
            self.weapon_level = max(0, min(3, int(data.get("weapon_level", 0))))
            saved_weapons = data.get("unlocked_weapons", ["pan"])
            if isinstance(saved_weapons, list):
                valid_ids = {weapon["id"] for weapon in self.WEAPONS}
                self.unlocked_weapons = {weapon for weapon in saved_weapons if weapon in valid_ids} | {"pan"}
            equipped = data.get("equipped_weapon", "pan")
            self.equipped_weapon = equipped if equipped in self.unlocked_weapons else "pan"
            return int(data.get("coins", 0)), int(data.get("xp", 0))
        except (OSError, ValueError, TypeError):
            return 0, 0

    def save(self):
        data = {}
        try:
            previous = json.loads(SAVE.read_text())
            if isinstance(previous, dict):
                data = previous
        except (OSError, ValueError):
            pass
        data.update(coins=self.coins, xp=self.xp, weapon_level=self.weapon_level,
                    unlocked_weapons=sorted(self.unlocked_weapons), equipped_weapon=self.equipped_weapon)
        temporary = SAVE.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2))
        temporary.replace(SAVE)

    def create_ui(self):
        self.intro_top_bar = Entity(parent=camera.ui, model="quad", position=(0, .46), scale=(2, .12), color=NIGHT)
        self.intro_bottom_bar = Entity(parent=camera.ui, model="quad", position=(0, -.43), scale=(2, .18), color=NIGHT)
        self.intro = Text("GLIWICE WAS QUIET...", parent=camera.ui, origin=(0, 0), y=-.39, z=-.1, scale=1.1, color=YELLOW)
        self.intro_skip = Text("PRESS ANY KEY TO SKIP", parent=camera.ui, origin=(.5, 0), x=.47, y=.455, z=-.1, scale=.55, color=color.rgba32(220, 225, 235, 190))
        self.map_panel = Entity(parent=camera.ui, model="quad", texture=MAP, scale=(1.72, 1), color=color.rgba32(255, 255, 255, 255), enabled=False)
        self.menu_card = Entity(parent=camera.ui, model="quad", color=color.rgba32(8, 6, 18, 248), scale=(.62, .78), enabled=False)
        self.menu = Text("", parent=camera.ui, origin=(0, 0), y=.02, z=-.1, scale=1, color=color.white, enabled=False)
        self.hud_bg = Entity(parent=camera.ui, model="quad", position=(0, .455), scale=(.98, .06), color=color.rgba32(8, 12, 24, 235), enabled=False)
        self.hud = Text("", parent=camera.ui, position=(-.46, .462), scale=.68, color=YELLOW, enabled=False)
        self.objective_bg = Entity(parent=camera.ui, model="quad", position=(-.33, .335), scale=(.48, .095), color=color.rgba32(8, 12, 24, 235), enabled=False)
        self.objective = Text("", parent=camera.ui, position=(-.55, .355), scale=.62, color=CYAN, enabled=False)
        self.help_bg = Entity(parent=camera.ui, model="quad", position=(0, -.46), scale=(1.08, .07), color=color.rgba32(8, 12, 24, 245), enabled=False)
        self.help = Text("WASD  MOVE   SHIFT  RUN   TAB  LOCK   J  CLEANUP   E  USE   ESC  MENU", parent=camera.ui, position=(-.51, -.467), scale=.61, color=color.white, enabled=False)
        self.notice_bg = Entity(parent=camera.ui, model="quad", position=(0, -.43), scale=(.68, .055), color=color.rgba32(8, 12, 24, 220), enabled=False)
        self.notice = Text("", parent=camera.ui, origin=(0, 0), y=-.43, z=-.1, scale=.9, color=color.white, enabled=False)
        self.story_bg = Entity(parent=camera.ui, model="quad", position=(0, -.31), scale=(.82, .105), color=color.rgba32(8, 12, 24, 235), enabled=False)
        self.story_text = Text("", parent=camera.ui, origin=(0, 0), y=-.31, z=-.1, scale=.82, color=YELLOW, enabled=False)
        self.boss_bar_bg = Entity(parent=camera.ui, model="quad", position=(0, .405), scale=(.54, .038), color=color.rgba32(20, 12, 24, 245), enabled=False)
        # The fill uses its centre as origin. Its position is recalculated with
        # its width, keeping its left edge fixed inside the background bar.
        self.boss_bar_fill = Entity(parent=camera.ui, model="quad", position=(0, .405), scale=(.52, .024), color=PINK, enabled=False)
        self.boss_name = Text("PRINCIPAL OF DISORDER", parent=camera.ui, origin=(0, 0), y=.437, z=-.1, scale=.72, color=YELLOW, enabled=False)
        self.fight_banner = Text("", parent=camera.ui, origin=(0, 0), y=.22, scale=.085, color=PINK, enabled=False)
        self.quest_panel = Entity(parent=camera.ui, model="quad", color=color.rgb32(18, 14, 32), scale=(.78, .58), enabled=False)
        self.quest_text = Text("", parent=camera.ui, origin=(0, 0), y=.03, z=-.1, scale=1, color=YELLOW, enabled=False)
        self.shop_panel = Entity(parent=camera.ui, model="quad", color=color.rgb32(18, 14, 32), scale=(.78, .58), enabled=False)
        self.shop_text = Text("", parent=camera.ui, origin=(0, 0), y=.03, z=-.1, scale=1, color=CYAN, enabled=False)
        self.win_panel = Entity(parent=camera.ui, model="quad", color=color.rgba32(8, 6, 18, 250), scale=(.72, .62), enabled=False)
        self.win_text = Text("", parent=camera.ui, origin=(0, 0), y=.04, z=-.1, scale=1, color=YELLOW, enabled=False)
        self.upgrade_overlay = Entity(parent=camera.ui, model="quad", scale=(2, 1), color=color.rgba32(5, 7, 15, 220), enabled=False)
        self.upgrade_title = Text("CHOOSE A CLEANUP BONUS", parent=camera.ui, origin=(0, 0), y=.32,
                                  z=-.2, scale=1.25, color=YELLOW, enabled=False)
        self.upgrade_cards: list[Button] = []
        for index, x in enumerate((-.34, 0, .34)):
            card = Button(parent=camera.ui, model="quad", position=(x, -.02, -.2), scale=(.29, .48),
                          color=color.rgb32(22, 30, 48), highlight_color=color.rgb32(35, 65, 78),
                          pressed_color=color.rgb32(18, 105, 105), text="", text_color=color.white,
                          enabled=False)
            card.on_click = Func(self.choose_upgrade, index)
            self.upgrade_cards.append(card)
        self.hp_bg = Entity(parent=camera.ui, model="quad", origin=(-.5, 0), position=(-.47, .425),
                            scale=(.25, .025), color=color.rgba32(20, 12, 24, 235), enabled=False)
        self.hp_fill = Entity(parent=camera.ui, model="quad", origin=(-.5, 0), position=(-.465, .425),
                              scale=(.24, .015), color=PINK, enabled=False)
        self.hp_text = Text("HP 100 / 100", parent=camera.ui, position=(-.465, .455), scale=.58,
                            color=color.white, enabled=False)
        # Minecraft-style quick bar: every owned weapon has a visible numbered slot.
        self.hotbar = Entity(parent=camera.ui, model="quad", position=(0, -.365, -.01), scale=(.62, .205),
                             color=color.rgba32(8, 12, 24, 235), enabled=False)
        self.hotbar_info = Text("", parent=self.hotbar, origin=(0, 0), y=.58, z=-.06, scale=.78, color=YELLOW)
        self.hotbar_slots: list[dict] = []
        labels = ("PAN", "PIN", "SOUP")
        for index, (x, weapon, label) in enumerate(zip((-.34, 0, .34), self.WEAPONS, labels)):
            # Every opaque UI layer gets a distinct depth. Without this, the
            # GPU alternates between the frame and its face (z-fighting).
            frame = Entity(parent=self.hotbar, model="quad", position=(x, 0, -.02), scale=(.29, .80), color=color.rgb32(65, 70, 85))
            face = Entity(parent=frame, model="quad", z=-.02, scale=(.84, .84), color=color.rgb32(20, 25, 38))
            Text(str(index + 1), parent=frame, x=-.38, y=.30, z=-.06, scale=.82, color=color.white)
            icon = self.make_weapon_icon(frame, index, weapon["color"])
            name = Text(label, parent=frame, origin=(0, 0), y=-.02, z=-.10, scale=.70, color=weapon["color"])
            state = Text("", parent=frame, origin=(0, 0), y=-.30, z=-.06, scale=.48, color=color.white)
            self.hotbar_slots.append({"frame": frame, "face": face, "icon": icon, "name": name, "state": state, "weapon": weapon})
        self.minimap = Entity(parent=camera.ui, model="quad", position=(.405, .33), scale=(.19, .24),
                              color=color.rgba32(8, 12, 24, 225), enabled=False)
        Entity(parent=self.minimap, model="quad", scale=(.94, .17), color=color.rgb32(62, 66, 78), z=-.02)
        Entity(parent=self.minimap, model="quad", scale=(.17, .94), color=color.rgb32(62, 66, 78), z=-.02)
        self.minimap_player = Entity(parent=self.minimap, model="circle", scale=.085, color=CYAN, z=-.05)
        self.minimap_exit = Entity(parent=self.minimap, model="quad", position=(.44, 0, -.04), scale=(.035, .18), color=YELLOW)
        self.minimap_enemy_dots: list[Entity] = []

    def make_weapon_icon(self, parent, index, tint):
        """Build a readable 3D weapon silhouette for the hotbar."""
        icon = Entity(parent=parent, position=(0, .17, -.08), scale=.18, color=tint)
        if index == 0:  # frying pan
            Entity(parent=icon, model="cube", scale=(1.35, .16, 1.35), rotation_x=90, color=tint)
            Entity(parent=icon, model="cube", position=(1.05, 0, 0), scale=(1.5, .22, .22), color=color.rgb32(120, 75, 45))
        elif index == 1:  # rolling pin
            Entity(parent=icon, model="cube", scale=(.35, 1.8, .35), rotation_z=90, color=tint)
            Entity(parent=icon, model="cube", position=(-1.15, 0, 0), scale=(.28, .55, .28), color=color.rgb32(160, 95, 55))
            Entity(parent=icon, model="cube", position=(1.15, 0, 0), scale=(.28, .55, .28), color=color.rgb32(160, 95, 55))
        else:  # soup blaster: body, barrel and grip
            Entity(parent=icon, model="cube", scale=(1.35, .62, .55), color=tint)
            Entity(parent=icon, model="cube", position=(1.0, .05, 0), scale=(1.25, .22, .22), color=color.white)
            Entity(parent=icon, model="cube", position=(-.25, -.75, 0), scale=(.28, .85, .28), color=color.rgb32(45, 55, 75))
        return icon

    def add(self, entity):
        self.scene_entities.append(entity)
        return entity

    def add_building(self, name, position, scale):
        entity = self.add(Entity(model=city(name), position=position, scale=scale, collider="box"))
        low, high = entity.get_tight_bounds(scene)
        self.building_bounds.append((low.x, high.x, low.z, high.z))
        return entity

    def blocked(self, position, radius, ignore=None):
        if abs(position.x) > 28 - radius or abs(position.z) > 22 - radius:
            return True
        if self.street < 2 and not all(enemy["dead"] for enemy in self.enemies) and position.x + radius > 21:
            return True
        for left, right, bottom, top in self.building_bounds:
            x = clamp(position.x, left, right)
            z = clamp(position.z, bottom, top)
            if (position.x - x) ** 2 + (position.z - z) ** 2 < radius ** 2:
                return True
        # Vehicles are solid while driving and on foot.  Use a simple radial
        # test here because imported GLB collider meshes are inconsistent.
        for vehicle in [getattr(self, "car_entity", None), *self.traffic]:
            if vehicle is None or vehicle is ignore or not vehicle.enabled:
                continue
            if distance(Vec3(position.x, 0, position.z), Vec3(vehicle.x, 0, vehicle.z)) < radius + 1.65:
                return True
        return False

    def move_actor(self, actor, movement, radius):
        # Small axis-separated steps prevent tunnelling and allow wall sliding.
        steps = max(1, math.ceil(movement.length() / .15))
        step = movement / steps
        for _ in range(steps):
            for offset in (Vec3(step.x, 0, 0), Vec3(0, 0, step.z)):
                candidate = actor.position + offset
                if not self.blocked(candidate, radius, actor):
                    actor.position = candidate

    def spawn_player(self, car_position=(-7, .5, 0)):
        self.car_entity = self.add(Entity(model=car("sedan"), position=car_position, scale=1.25, collider="box"))
        self.car_entity.y = .5
        self.avatar = self.add(Entity(
            model=character("character-gamer"),
            texture=f"{CHARACTERS}/Textures/colormap.png",
            position=(car_position[0] + 1.5, 0, car_position[2]),
            scale=2.25,
        ))
        self.avatar.enabled = False
        self.in_car = True

    def spawn_enemies(self):
        for kind, pos, tint, model_name, hp in self.LEVELS[self.street]:
            scale = 1.05 if kind == "zsti_boss" else .65
            enemy = Entity(model=skeleton(model_name), position=pos, rotation_x=0, scale=scale, color=tint)
            self.enemies.append({"entity": enemy, "kind": kind, "hp": hp, "max_hp": hp, "dead": False,
                                 "tint": tint, "shot_timer": random.uniform(2.0, 4.0)})

    def build_intro(self):
        """Stage a short undead invasion over the already-built city."""
        self.intro_time = 0.0
        self.intro_actors.clear()
        routes = (
            ("skeleton", "Warrior", (-23, 0, -2), (1, 0, .10), .68, color.rgb32(205, 215, 225)),
            ("skeleton", "Rogue", (19, 0, 2), (-1, 0, -.08), .65, color.rgb32(190, 210, 225)),
            ("skeleton", "Mage", (-2, 0, 19), (.08, 0, -1), .68, color.rgb32(190, 225, 215)),
            ("skeleton", "Minion", (3, 0, -19), (-.06, 0, 1), .68, color.rgb32(215, 205, 225)),
            ("zombie", "character-employee", (-17, 0, 2), (1, 0, -.06), 2.1, color.rgb32(92, 155, 82)),
            ("zombie", "character-gamer", (16, 0, -2), (-1, 0, .05), 2.1, color.rgb32(78, 145, 76)),
            ("zombie", "character-employee", (2, 0, 15), (-.04, 0, -1), 2.1, color.rgb32(105, 165, 88)),
        )
        for kind, model_name, position, direction, size, tint in routes:
            if kind == "skeleton":
                actor = Entity(model=skeleton(model_name), position=position, scale=size, color=tint)
            else:
                actor = Entity(model=character(model_name), texture=f"{CHARACTERS}/Textures/colormap.png",
                               position=position, scale=size, color=tint)
            vector = Vec3(*direction).normalized()
            actor.rotation_y = math.degrees(math.atan2(vector.x, vector.z))
            self.intro_actors.append({"entity": actor, "direction": vector, "phase": len(self.intro_actors) * .8})
        self.intro_hero = Entity(model=character("character-gamer"), texture=f"{CHARACTERS}/Textures/colormap.png",
                                 position=(-3, 0, -9), scale=2.35, color=color.white, enabled=False)
        # Keep a fixed isometric angle; only the focus point moves during the pan.
        intro_focus = Vec3(-8, 0, 0)
        camera.position = intro_focus + Vec3(0, 24, -22)
        camera.look_at(intro_focus)
        camera.rotation_z = 0

    def finish_intro(self):
        for actor in self.intro_actors:
            destroy(actor["entity"])
        self.intro_actors.clear()
        if self.intro_hero:
            destroy(self.intro_hero)
            self.intro_hero = None
        self.show_menu()

    def update_intro(self, dt):
        self.intro_time += dt
        for actor in self.intro_actors:
            entity = actor["entity"]
            entity.position += actor["direction"] * dt * (1.15 if entity.scale_y < 1 else .85)
            entity.y = abs(math.sin(self.intro_time * 5 + actor["phase"])) * .06
        progress = min(1.0, self.intro_time / 7.5)
        focus = lerp(Vec3(-8, 0, 0), Vec3(5, 0, 0), progress)
        camera.position = focus + Vec3(0, 24, -22)
        camera.look_at(focus)
        camera.rotation_z = 0
        if self.intro_time < 2.3:
            self.intro.text = "GLIWICE WAS QUIET..."
        elif self.intro_time < 5.2:
            self.intro.text = "THEN ZOMBIES AND SKELETONS FILLED THE STREETS"
        else:
            if self.intro_hero:
                self.intro_hero.enabled = True
                self.intro_hero.rotation_y = -25
            self.intro.text = "GREEN-EYE  //  TIME TO CLEAN UP!"
        if self.intro_time >= 7.5:
            self.finish_intro()

    def boss(self):
        return next((enemy for enemy in self.enemies if enemy["kind"] == "zsti_boss" and not enemy["dead"]), None)

    def refresh_boss_bar(self):
        boss = self.boss() if self.street == 2 else None
        visible = self.state == "PLAY" and boss is not None
        self.boss_bar_bg.enabled = visible
        self.boss_bar_fill.enabled = visible
        self.boss_name.enabled = visible
        if boss:
            ratio = max(0, boss["hp"]) / boss["max_hp"]
            width = .52 * ratio
            self.boss_bar_fill.scale_x = width
            self.boss_bar_fill.x = -(0.52 - width) / 2

    def refresh_player_hud(self):
        ratio = max(0, self.player_hp) / self.max_hp
        self.hp_fill.scale_x = .24 * ratio
        self.hp_fill.color = PINK if ratio > .3 else color.red
        self.hp_text.text = f"HP {max(0, self.player_hp)} / {self.max_hp}"

    def weapon(self):
        return next(weapon for weapon in self.WEAPONS if weapon["id"] == self.equipped_weapon)

    def refresh_inventory(self):
        active = self.weapon()
        self.hotbar_info.text = f"{active['name']}  //  DMG {active['damage'] + self.weapon_level + self.damage_bonus}"
        for slot in self.hotbar_slots:
            weapon = slot["weapon"]
            owned = weapon["id"] in self.unlocked_weapons
            selected = weapon["id"] == self.equipped_weapon
            slot["frame"].color = YELLOW if selected else color.rgb32(65, 70, 85)
            slot["face"].color = color.rgb32(20, 25, 38) if owned else color.rgb32(12, 14, 22)
            slot["icon"].color = weapon["color"] if owned else color.rgb32(80, 80, 90)
            slot["state"].text = "SELECTED" if selected else ("READY" if owned else "LOCKED")
            slot["state"].color = YELLOW if selected else (color.white if owned else color.rgb32(135, 135, 145))

    def equip_weapon(self, index):
        if not 0 <= index < len(self.WEAPONS):
            return
        weapon = self.WEAPONS[index]
        if weapon["id"] not in self.unlocked_weapons:
            self.notice.text = "BUY THIS WEAPON AT THE SHOP"
            return
        self.equipped_weapon = weapon["id"]
        self.save()
        self.refresh_inventory()
        self.notice.text = f"EQUIPPED: {weapon['name']}"

    def refresh_minimap(self):
        while len(self.minimap_enemy_dots) < len(self.enemies):
            self.minimap_enemy_dots.append(Entity(parent=self.minimap, model="circle", scale=.065, color=PINK, z=-.05))
        actor = self.car_entity if self.in_car else self.avatar
        self.minimap_player.position = (actor.x / 60, actor.z / 48, -.05)
        self.minimap_player.color = YELLOW if self.in_car else CYAN
        self.minimap_exit.enabled = self.street < 2 and all(enemy["dead"] for enemy in self.enemies)
        for index, dot in enumerate(self.minimap_enemy_dots):
            if index >= len(self.enemies):
                dot.enabled = False
                continue
            enemy = self.enemies[index]
            dot.enabled = not enemy["dead"]
            dot.position = (enemy["entity"].x / 60, enemy["entity"].z / 48, -.05)
            dot.color = YELLOW if enemy["kind"] == "zsti_boss" else PINK

    def damage_player(self, amount):
        if self.damage_cooldown > 0 or self.in_car or self.state != "PLAY":
            return
        self.player_hp = max(0, self.player_hp - max(1, round(amount * self.damage_multiplier)))
        self.damage_cooldown = .8
        self.avatar.animate_color(color.red, duration=.05)
        invoke(self.avatar.animate_color, color.white, delay=.12, duration=.12)
        self.refresh_player_hud()
        if self.player_hp <= 0:
            self.game_over()

    def game_over(self):
        self.hide_ui()
        self.state = "GAME_OVER"
        self.set_target_lock(None)
        self.win_panel.enabled = self.win_text.enabled = True
        self.win_text.color = PINK
        self.win_text.text = "THE CITY IS STILL MESSY...\n\nThe cleanup crew needs another try.\n\nENTER  RETRY THIS STREET\nESC  MENU"

    def show_story(self):
        if not self.story_queue:
            return
        self.story_text.text = self.story_queue.pop(0)
        self.story_bg.enabled = self.story_text.enabled = True
        self.story_time = 4.5

    def build_boss_arena(self):
        """Final ZSTI courtyard reached from the east road."""
        asphalt = color.rgb32(42, 45, 55)
        court = color.rgb32(91, 104, 114)
        self.add(Entity(model="cube", position=(-18, .01, 0), scale=(28, .10, 8), color=asphalt, shader=unlit_shader))
        self.add(Entity(model="cube", position=(7, .02, 0), scale=(24, .11, 22), color=court, shader=unlit_shader))
        # Painted court lines make the final battle space readable from above.
        for z in (-9.5, 9.5):
            self.add(Entity(model="cube", position=(7, .09, z), scale=(24, .025, .16), color=YELLOW, shader=unlit_shader))
        for x in (-5, 19):
            self.add(Entity(model="cube", position=(x, .09, 0), scale=(.16, .025, 19), color=YELLOW, shader=unlit_shader))
        self.add(Entity(model="cube", position=(7, .09, 0), scale=(.12, .025, 19), color=color.white, shader=unlit_shader))
        # Fences frame the arena but leave its western entrance open.
        for x in range(-3, 20, 3):
            self.add(Entity(model=city("fence-1x3"), position=(x, 0, -10.5), scale=1.2))
            self.add(Entity(model=city("fence-1x3"), position=(x, 0, 10.5), scale=1.2))
        self.building_bounds.extend([(-5.5, 20.5, -11.2, -10.0), (-5.5, 20.5, 10.0, 11.2)])
        self.shop = self.add(Entity(position=(999, 0, 999), enabled=False))
        self.board = self.add(Entity(position=(999, 0, 999), enabled=False))
        self.add_building("building-type-r", (23, 0, 0), 3.2)
        for name, pos, size in (("tree-large", (17, 0, -8), 1.5), ("tree-large", (17, 0, 8), 1.5),
                                ("planter", (2, 0, -8), 1.4), ("planter", (2, 0, 8), 1.4)):
            self.add(Entity(model=city(name), position=pos, scale=size))
        self.spawn_player((-20, .5, 0))
        self.spawn_enemies()
        camera.position = (-20, 19, -18)
        camera.look_at(self.car_entity.position)

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

    def set_target_lock(self, target: dict | None) -> None:
        if self.lock_marker:
            destroy(self.lock_marker)
            self.lock_marker = None
        self.locked_enemy = target
        if target:
            self.lock_marker = Entity(model="quad", position=target["entity"].position + Vec3(0, 2.1, 0), scale=.22, rotation_z=45, color=PINK, shader=unlit_shader, billboard=True, double_sided=True)

    def nearest_enemy(self) -> dict | None:
        alive = [enemy for enemy in self.enemies if not enemy["dead"]]
        return min(alive, key=lambda enemy: distance(self.avatar, enemy["entity"]), default=None)

    def damage_enemy(self, target: dict, base_damage: int = 1) -> None:
        """Apply one hit after a cleanup projectile reaches its target."""
        entity = target["entity"]
        if target["dead"]:
            return
        target["hp"] -= base_damage + self.weapon_level + self.damage_bonus
        direction = entity.position - self.avatar.position
        direction.y = 0
        if direction.length():
            self.move_actor(entity, direction.normalized() * 1.3, .4)
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
            level_cleared = all(enemy["dead"] for enemy in self.enemies)
            if level_cleared:
                if self.street == 2:
                    self.win_game()
                else:
                    self.offer_upgrades()

    def offer_upgrades(self):
        self.state = "UPGRADE"
        self.upgrade_choices = random.sample(self.UPGRADES, 3)
        self.upgrade_overlay.enabled = self.upgrade_title.enabled = True
        for index, (card, (_, title, description)) in enumerate(zip(self.upgrade_cards, self.upgrade_choices)):
            card.text = f"{index + 1}\n\n{title}\n\n{description}"
            card.enabled = True

    def choose_upgrade(self, index):
        if self.state != "UPGRADE" or not 0 <= index < len(self.upgrade_choices):
            return
        key = self.upgrade_choices[index][0]
        if key == "power":
            self.damage_bonus += 1
        elif key == "vitality":
            self.max_hp += 20
            self.player_hp = min(self.max_hp, self.player_hp + 20)
        elif key == "speed":
            self.move_multiplier *= 1.12
        elif key == "rapid":
            self.attack_delay = max(.11, self.attack_delay * .85)
        elif key == "armor":
            self.damage_multiplier = max(.4, self.damage_multiplier * .85)
        elif key == "heal":
            self.player_hp = min(self.max_hp, self.player_hp + 35)
        self.upgrade_choices.clear()
        self.start()

    def spawn_projectile(self, aim_point: Vec3) -> None:
        start = self.avatar.position + Vec3(0, 1.1, 0)
        direction = aim_point - start
        direction.y = 0
        if not direction.length():
            direction = self.avatar.forward
        direction = direction.normalized()
        weapon = self.weapon()
        shot = Entity(model="sphere", position=start, scale=.22 + weapon["damage"] * .025,
                      color=weapon["color"], shader=unlit_shader)
        muzzle = Entity(model="sphere", position=start, scale=.42, color=color.white, shader=unlit_shader)
        self.attack_effects.append(muzzle)
        invoke(self.remove_attack_effect, muzzle, delay=.07)
        self.avatar.animate_scale(Vec3(2.38, 2.12, 2.38), duration=.045)
        invoke(self.avatar.animate_scale, Vec3(2.25, 2.0, 2.25), duration=.08, delay=.05)
        target = self.locked_enemy if self.locked_enemy and not self.locked_enemy["dead"] else None
        self.projectiles.append({"entity": shot, "velocity": direction * weapon["speed"], "target": target,
                                 "damage": weapon["damage"], "speed": weapon["speed"], "life": 1.0})

    def update_projectiles(self, dt: float) -> None:
        for shot in self.projectiles[:]:
            projectile = shot["entity"]
            shot["life"] -= dt
            target = shot["target"]
            if target and target["dead"]:
                shot["target"] = target = None
            if target is None:
                nearby = [enemy for enemy in self.enemies if not enemy["dead"] and distance(projectile, enemy["entity"]) < 2.0]
                if nearby:
                    shot["target"] = min(nearby, key=lambda enemy: distance(projectile, enemy["entity"]))
                    target = shot["target"]
            if target and not target["dead"]:
                direction = target["entity"].position + Vec3(0, 1, 0) - projectile.position
                if direction.length():
                    shot["velocity"] = direction.normalized() * shot["speed"]
                if direction.length() <= .75 + shot["velocity"].length() * dt:
                    self.damage_enemy(target, shot["damage"])
                    self.projectiles.remove(shot)
                    destroy(projectile)
                    continue
            projectile.position += shot["velocity"] * dt
            if shot["life"] <= 0:
                self.projectiles.remove(shot)
                destroy(projectile)

    def fire_enemy_projectile(self, enemy: dict) -> None:
        """Slow, non-homing enemy projectile that leaves room for dodging."""
        start = enemy["entity"].position + Vec3(0, 1.0, 0)
        direction = self.avatar.position + Vec3(0, .7, 0) - start
        direction.y = 0
        if not direction.length():
            return
        boss = enemy["kind"] == "zsti_boss"
        shot = Entity(model="sphere", position=start, scale=.30 if boss else .22,
                      color=YELLOW if boss else PINK, shader=unlit_shader)
        self.enemy_projectiles.append({"entity": shot, "velocity": direction.normalized() * (4.2 if boss else 3.2),
                                       "damage": 12 if boss else 8, "life": 4.0})

    def update_enemy_projectiles(self, dt: float) -> None:
        for shot in self.enemy_projectiles[:]:
            projectile = shot["entity"]
            shot["life"] -= dt
            projectile.position += shot["velocity"] * dt
            if not self.in_car and distance(projectile, self.avatar) < .7:
                self.damage_player(shot["damage"])
                self.enemy_projectiles.remove(shot)
                destroy(projectile)
                continue
            if shot["life"] <= 0:
                self.enemy_projectiles.remove(shot)
                destroy(projectile)

    def resolve_car_collisions(self) -> None:
        """Stop the player car at traffic and bounce it away from impacts."""
        if not self.in_car:
            return
        car_pos = Vec3(self.car_entity.x, 0, self.car_entity.z)
        for vehicle in self.traffic:
            if distance(car_pos, Vec3(vehicle.x, 0, vehicle.z)) >= 2.7:
                continue
            away = car_pos - Vec3(vehicle.x, 0, vehicle.z)
            if not away.length():
                away = Vec3(1, 0, 0)
            away = away.normalized()
            impact = max(3.0, abs(self.car_speed) * 1.35)
            # Separate both bodies immediately, then give the parked car an
            # impulse so the collision is visible instead of a static bump.
            self.car_entity.position += away * .22
            self.car_speed *= -.42
            self.traffic_velocity[id(vehicle)] = self.traffic_velocity.get(id(vehicle), Vec3(0, 0, 0)) + away * impact
            vehicle.rotation_y += random.choice((-1, 1)) * min(16.0, impact * 1.8)
        if self.car_collision_cooldown > 0:
            return
        for enemy in self.enemies:
            if enemy["dead"] or distance(car_pos, enemy["entity"].position) >= 2.4:
                continue
            self.car_collision_cooldown = .35
            self.car_speed *= -.35
            # A moving car is a strong but non-gory cleanup tool.
            self.damage_enemy(enemy, 2)
            break

    def update_traffic_physics(self, dt: float) -> None:
        """Integrate impact impulses on traffic cars with friction and walls."""
        for vehicle in self.traffic:
            velocity = self.traffic_velocity.get(id(vehicle), Vec3(0, 0, 0))
            if velocity.length() <= .03:
                self.traffic_velocity[id(vehicle)] = Vec3(0, 0, 0)
                continue
            velocity *= max(0.0, 1.0 - 3.8 * dt)
            candidate = vehicle.position + velocity * dt
            candidate.y = vehicle.y
            if self.blocked(candidate, 1.5, vehicle):
                velocity *= -.25
            else:
                vehicle.position = candidate
            vehicle.rotation_y += velocity.length() * dt * 5.0
            self.traffic_velocity[id(vehicle)] = velocity

    def update_visual_animations(self, dt: float, actor: Entity) -> None:
        """Small readable motion layers that work with imported static GLBs."""
        self.animation_time += dt
        moving = actor is not self.car_entity and actor is not None and actor.position != getattr(self, "_last_actor_position", actor.position)
        if self.avatar and self.avatar.enabled:
            base_y = 0.0
            self.avatar.y = base_y + (abs(math.sin(self.animation_time * 10.0)) * .055 if moving else 0.0)
        for index, enemy in enumerate(self.enemies):
            if enemy["dead"]:
                continue
            enemy["entity"].y = abs(math.sin(self.animation_time * 4.0 + index)) * .035
        for index, vehicle in enumerate([self.car_entity, *self.traffic]):
            if vehicle and vehicle.enabled:
                vehicle.y = (.5 if vehicle is self.car_entity else .45) + math.sin(self.animation_time * 2.0 + index) * .008
        self._last_actor_position = Vec3(actor.position)

    def update_target_lock(self) -> None:
        if self.locked_enemy and self.locked_enemy["dead"]:
            self.set_target_lock(self.nearest_enemy())
        if self.locked_enemy and self.lock_marker:
            self.lock_marker.position = self.locked_enemy["entity"].position + Vec3(0, 2.1, 0)

    def build_street(self):
        self.car_speed = 0.0
        self.car_collision_cooldown = 0.0
        self.traffic_velocity.clear()
        for entity in self.scene_entities + self.traffic:
            destroy(entity)
        for effect in self.attack_effects:
            destroy(effect)
        self.attack_effects.clear()
        for shot in self.projectiles:
            destroy(shot["entity"])
        self.projectiles.clear()
        for shot in self.enemy_projectiles:
            destroy(shot["entity"])
        self.enemy_projectiles.clear()
        self.set_target_lock(None)
        for enemy in self.enemies:
            destroy(enemy["entity"])
        self.scene_entities.clear(); self.traffic.clear()
        self.east_exit_markers.clear()
        self.building_bounds.clear()
        self.enemies.clear()
        self.story_queue = [self.STORY[self.street]]
        self.story_time = 0
        # Continuous grass base and asphalt underlays keep the city readable even
        # where individual road-kit meshes have small tile gaps.
        # Thin horizontal cubes are used instead of planes: in Ursina this makes
        # the XZ orientation explicit, so the green field always fills the map.
        ground_color = color.rgb32(42, 112, 58) if self.street != 1 else color.rgb32(58, 94, 58)
        self.add(Entity(model="cube", position=(0, -.30, 0), scale=(120, .6, 120), texture="white_cube", shader=unlit_shader, color=ground_color))
        self.add(Entity(model="cube", position=(0, -.08, 0), scale=(120, .04, 120), collider="box", visible=False))
        if self.street == 2:
            self.build_boss_arena()
            return
        residential = self.street == 0
        road_width = 8.2 if residential else 10.5
        asphalt = color.rgb32(48, 51, 61) if residential else color.rgb32(38, 42, 50)
        self.add(Entity(model="cube", position=(0, -.005, 0), scale=(66, .08, road_width), texture="white_cube", shader=unlit_shader, color=asphalt))
        self.add(Entity(model="cube", position=(0, 0, 0), scale=(road_width, .08, 52), texture="white_cube", shader=unlit_shader, color=asphalt))
        if not residential:
            # Dworcowa has a broad station forecourt and a small construction site.
            self.add(Entity(model="cube", position=(17, .01, -14), scale=(20, .08, 10), color=asphalt, shader=unlit_shader))
        # Continuous asphalt, with lane markings stopping before the junction.
        line = color.rgb32(225, 221, 200)
        for x in range(-30, 31, 4):
            if abs(x) > 6:
                self.add(Entity(model="cube", position=(x, .06, 0), scale=(1.8, .02, .10), color=line, shader=unlit_shader))
        for z in range(-22, 23, 4):
            if abs(z) > 6:
                self.add(Entity(model="cube", position=(0, .07, z), scale=(.10, .02, 1.8), color=line, shader=unlit_shader))
        sidewalk = color.rgb32(145, 150, 162) if residential else color.rgb32(178, 174, 166)
        for side in (-1, 1):
            for bank in (-1, 1):
                self.add(Entity(model="cube", position=(side * 18.55, .10, bank * 4.85), scale=(28.9, .12, 1.5), color=sidewalk, shader=unlit_shader))
                self.add(Entity(model="cube", position=(bank * 4.85, .10, side * 16), scale=(1.5, .12, 20.8), color=sidewalk, shader=unlit_shader))
        if residential:
            houses = [
                ("building-type-a", (-25, 9), 2.5), ("building-type-c", (-18, 9), 2.2), ("building-type-e", (-10, 9), 2.4),
                ("building-type-f", (10, 9), 2.4), ("building-type-h", (18, 9), 2.2), ("building-type-j", (25, 9), 2.5),
                ("building-type-k", (-25, -9), 2.4), ("building-type-m", (-17, -9), 2.3), ("building-type-o", (-9, -9), 2.5),
                ("building-type-p", (10, -9), 2.3), ("building-type-r", (18, -9), 2.4), ("building-type-t", (25, -9), 2.2),
                ("building-type-g", (-24, 18), 1.8), ("building-type-i", (-15, 18), 1.7),
                ("building-type-l", (15, 18), 1.8), ("building-type-n", (24, 18), 1.7),
                ("building-type-q", (-24, -18), 1.8), ("building-type-s", (-15, -18), 1.7),
                ("building-type-u", (15, -18), 1.8), ("building-type-c", (24, -18), 1.7),
            ]
        else:
            houses = [
                ("building-type-u", (-24, 10), 2.8), ("building-type-t", (-15, 11), 2.5),
                ("building-type-p", (19, 13), 3.0), ("building-type-o", (26, 10), 2.4),
                ("building-type-n", (-25, -11), 2.7), ("building-type-l", (-16, -13), 2.5),
                ("building-type-j", (-9, -18), 1.9), ("building-type-i", (9, -10), 2.3),
                ("building-type-g", (25, -10), 2.6), ("building-type-f", (-24, 19), 1.8),
                ("building-type-d", (25, 19), 1.8), ("building-type-b", (-24, -19), 1.8),
            ]
        for name, pos, size in houses:
            if self.street == 2 and pos == (18, 9):
                continue
            self.add_building(name, (pos[0], 0, pos[1]), size)
        city_details = (("tree-large", (-6, 0, 7), 1.5), ("tree-small", (7, 0, 7), 1.4),
                        ("tree-large", (-7, 0, -7), 1.4), ("tree-small", (7, 0, -7), 1.4),
                        ("tree-small", (-21, 0, 14), 1.2), ("tree-large", (-11, 0, 14), 1.3),
                        ("tree-large", (11, 0, -14), 1.3), ("tree-small", (21, 0, -14), 1.2),
                        ("planter", (-13, 0, 6.8), 1.2), ("planter", (13, 0, -6.8), 1.2)) if residential else (
                        ("planter", (-7, 0, 7), 1.3), ("planter", (7, 0, 7), 1.3),
                        ("tree-small", (-20, 0, 16), 1.1), ("tree-small", (22, 0, 16), 1.1),
                        ("planter", (-18, 0, -7), 1.2), ("planter", (18, 0, 7), 1.2))
        for name, pos, size in city_details:
            self.add(Entity(model=city(name), position=pos, scale=size))
        # The optional nature pack contains several tree GLBs whose material
        # references are absent on some installations.  Those render white.
        # Use the city kit's textured trees for every tree; keep the nature
        # pack only for grass, bushes and flowers.
        tree_details = (
            ("tree-large", (-27, 0, 14), 1.5), ("tree-small", (27, 0, 14), 1.5),
            ("tree-large", (-27, 0, -14), 1.5), ("tree-small", (27, 0, -14), 1.5),
        ) if residential else (
            ("tree-small", (-27, 0, 16), 1.3), ("tree-large", (27, 0, 16), 1.3),
        )
        for name, pos, size in tree_details:
            self.add(Entity(model=city(name), position=pos, scale=size))
        nature_details = (
            ("grass_1", (-8, 0, 8), 2.8), ("grass_2", (-3, 0, 8), 2.8), ("bush_1", (8, 0, 8), 2.4),
            ("flowers_1", (12, 0, 8), 2.2), ("fern", (-12, 0, 8), 2.0), ("grass_1", (18, 0, 7), 2.6),
            ("bush_3", (-18, 0, 14), 1.8), ("flowers_1", (18, 0, 14), 1.8),
        ) if residential else (
            ("grass_1", (-7, 0, 8), 2.0), ("bush_2", (7, 0, 8), 1.8),
            ("bush_1", (-20, 0, -16), 1.5), ("grass_2", (22, 0, -17), 1.8),
        )
        for name, pos, size in nature_details:
            self.add(Entity(model=nature(name), position=pos, scale=size))
        for pos, rotation in (((-13, .1, 5.2), 0), ((13, .1, 5.2), 0), ((-13, .1, -5.2), 180), ((13, .1, -5.2), 180)):
            self.add(Entity(model=road("light-square"), position=pos, rotation_y=rotation, scale=1.15))
        for pos, rotation in (((-5.2, .1, 8), 90), ((5.2, .1, -8), -90)):
            self.add(Entity(model=road("traffic-light"), position=pos, rotation_y=rotation, scale=1.2))
        for pos in ((-20, .1, 5.3), (20, .1, -5.3)):
            self.add(Entity(model=road("road-sign-street"), position=pos, scale=1.2))
        for pos in ((-20, .1, 7), (20, .1, -7)):
            self.add(Entity(model=road("dumpster"), position=pos, scale=1.1))
        if not residential:
            for name, pos, rotation in (("construction-barrier", (12, .1, -9), 0),
                                        ("construction-barrier", (17, .1, -9), 0),
                                        ("construction-cone", (10, .1, -7), 0),
                                        ("construction-cone", (20, .1, -7), 0),
                                        ("electricity-pole", (-21, .1, 6), 0)):
                self.add(Entity(model=road(name), position=pos, rotation_y=rotation, scale=1.15))
        shop_pos, board_pos = ((8, 0, 17), (-8, 0, 17)) if residential else ((-8, 0, 16), (8, 0, 16))
        self.shop = self.add_building("building-type-b", shop_pos, 2.1)
        self.board = self.add_building("building-type-d", board_pos, 1.9)
        for z in (-2.2, 0, 2.2):
            marker = self.add(Entity(model="cube", position=(25, .22, z), scale=(2.4, .08, .16),
                                     rotation_y=-25, color=CYAN, shader=unlit_shader, enabled=False))
            self.east_exit_markers.append(marker)
        self.spawn_player()
        traffic = (("taxi", (-15, .45, 0), 0), ("police", (11, .45, 0), 0),
                   ("van", (0, .45, 12), 90), ("hatchback-sports", (-23, .45, 3), 0)) if residential else (
                   ("ambulance", (-17, .45, 0), 0), ("garbage-truck", (13, .45, 0), 180),
                   ("delivery", (0, .45, 13), 90), ("police", (0, .45, -15), 90),
                   ("taxi", (18, .45, -14), 0))
        for name, pos, rotation in traffic:
            vehicle = Entity(model=car(name), position=pos, rotation_y=rotation, scale=1.2, collider="box")
            vehicle.y = .45
            self.traffic.append(vehicle)
            self.traffic_velocity[id(vehicle)] = Vec3(0, 0, 0)
        self.spawn_enemies()
        camera.position = (-7, 19, -18); camera.look_at(self.car_entity.position)

    def start(self):
        self.hide_ui()
        self.state = "PLAY"
        for item in (self.intro, self.map_panel, self.menu_card, self.menu, self.quest_panel, self.quest_text, self.shop_panel, self.shop_text, self.win_panel, self.win_text): item.enabled = False
        self.fight_banner.enabled = False
        self.hp_bg.enabled = self.hp_fill.enabled = self.hp_text.enabled = True
        self.hotbar.enabled = True
        self.minimap.enabled = True
        self.refresh_player_hud()
        self.refresh_inventory()
        self.refresh_minimap()
        self.refresh_boss_bar()
        if self.story_queue:
            self.show_story()
        self.refresh_prompt()

    def hide_ui(self):
        for item in (self.intro_top_bar, self.intro_bottom_bar, self.intro, self.intro_skip,
                     self.map_panel, self.menu_card, self.menu,
                     self.hud_bg, self.hud, self.help_bg, self.help,
                     self.objective_bg, self.objective, self.notice_bg, self.notice,
                     self.story_bg, self.story_text, self.boss_bar_bg, self.boss_bar_fill, self.boss_name,
                     self.hp_bg, self.hp_fill, self.hp_text, self.hotbar, self.minimap,
                     self.upgrade_overlay, self.upgrade_title, *self.upgrade_cards,
                     self.fight_banner, self.quest_panel, self.quest_text,
                     self.shop_panel, self.shop_text, self.win_panel, self.win_text):
            item.enabled = False

    def interaction(self) -> str:
        actor = self.car_entity if self.in_car else self.avatar
        if distance(actor, self.shop) < 4:
            return "shop"
        if distance(actor, self.board) < 4:
            return "quest"
        if self.in_car and self.car_entity.x > 20 and all(e["dead"] for e in self.enemies):
            return "next"
        if self.in_car:
            return "exit"
        if distance(actor, self.car_entity) < 2.5:
            return "enter"
        return ""

    def refresh_prompt(self):
        prompts = {"shop": "E  Shop", "quest": "E  Job board", "next": "E  Continue",
                   "exit": "E  Leave car", "enter": "E  Enter car"}
        message = prompts.get(self.interaction(), "")
        if not message and all(e["dead"] for e in self.enemies):
            message = "Return to the car and drive east"
        self.notice.text = message
        self.notice.enabled = self.notice_bg.enabled = bool(message)
        open_exit = self.street < 2 and all(enemy["dead"] for enemy in self.enemies)
        for marker in self.east_exit_markers:
            marker.enabled = open_exit

    def show_menu(self):
        self.hide_ui()
        self.menu.text = (f"GREEN-EYE\n\nStage {self.street + 1}/3   Coins {self.coins}   XP {self.xp}"
                          "\n\nEnter  Continue\nWASD  Walk   Shift  Run\nS / W  Drive / Reverse\nA / D  Steer"
                          "\nMouse + J / Click  Shoot\nTab  Target lock\nE  Interact")
        self.state = "MENU"
        self.intro.enabled = False; self.map_panel.enabled = True; self.menu_card.enabled = True; self.menu.enabled = True
        self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False
        self.hud.enabled = False; self.help.enabled = False; self.notice.enabled = False; self.objective_bg.enabled = False; self.objective.enabled = False

    def win_game(self):
        self.hide_ui()
        self.state = "WIN"
        self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False
        self.hud.enabled = False; self.help.enabled = False; self.notice.enabled = False; self.objective_bg.enabled = False; self.objective.enabled = False
        self.fight_banner.enabled = False
        self.win_panel.enabled = True; self.win_text.enabled = True
        self.win_text.color = YELLOW
        self.win_text.text = "THE PRINCIPAL IS DEFEATED!\n\nGliwice can breathe again.\nEverything is tidy.\n\nCOINS %d   XP %d\n\nENTER  PLAY AGAIN" % (self.coins, self.xp)

    def open_quest(self):
        self.hide_ui()
        self.state = "QUEST"
        self.map_panel.enabled = False; self.menu_card.enabled = False; self.hud.enabled = False; self.help.enabled = False
        self.objective_bg.enabled = False; self.objective.enabled = False
        self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False
        self.quest_panel.enabled = True; self.quest_text.enabled = True
        remaining = sum(not e["dead"] for e in self.enemies)
        self.quest_text.text = f"JOB BOARD\n\nClear the area: {remaining} remaining\n5 coins + 10 XP per target\n\nE / Esc  Close"

    def open_shop(self):
        self.hide_ui()
        self.state = "SHOP"
        self.shop_panel.enabled = True; self.shop_text.enabled = True; self.hud_bg.enabled = False; self.help_bg.enabled = False; self.notice_bg.enabled = False; self.hud.enabled = False; self.help.enabled = False; self.objective_bg.enabled = False; self.objective.enabled = False
        weapon_lines = []
        for index, weapon in enumerate(self.WEAPONS, start=1):
            if weapon["id"] in self.unlocked_weapons:
                status = "OWNED"
            elif weapon["price"] <= self.coins:
                status = f"BUY {weapon['price']}"
            else:
                status = f"{weapon['price']} COINS"
            weapon_lines.append(f"{index}. {weapon['name']}  DMG {weapon['damage']}  {status}")
        offer = "P  Upgrade pan damage - 30 coins" if self.weapon_level < 3 else "Pan upgrade: maximum"
        self.shop_text.text = f"WEAPON SHOP\n\nCoins: {self.coins}\n\n" + "\n".join(weapon_lines) + f"\n\n{offer}\n\n1-3 Buy weapon   E / Esc Close"

    def update(self, dt):
        dt = max(0.0, min(dt, .05))
        if self.state == "INTRO":
            self.update_intro(dt)
            return
        if self.state != "PLAY": return
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.damage_cooldown = max(0.0, self.damage_cooldown - dt)
        self.car_collision_cooldown = max(0.0, self.car_collision_cooldown - dt)
        self.update_traffic_physics(dt)
        if self.fight_banner_time > 0:
            self.fight_banner_time -= dt
            if self.fight_banner_time <= 0: self.fight_banner.enabled = False
        self.update_projectiles(dt)
        self.update_enemy_projectiles(dt)
        if self.state != "PLAY":
            return
        self.update_target_lock()
        self.refresh_boss_bar()
        if self.story_time > 0:
            self.story_time -= dt
            if self.story_time <= 0:
                self.story_bg.enabled = self.story_text.enabled = False
        if self.in_car:
            throttle = held_keys["s"] - held_keys["w"]
            steer = held_keys["d"] - held_keys["a"]
            self.car_speed += throttle * 22 * dt
            if not throttle:
                self.car_speed *= max(0.0, 1.0 - 4.5 * dt)
            self.car_speed = clamp(self.car_speed, -9.0, 14.0)
            if abs(self.car_speed) > .08:
                self.car_entity.rotation_y += steer * 92 * dt * clamp(abs(self.car_speed) / 5.0, .2, 1.5)
                before = Vec3(self.car_entity.position)
                self.move_actor(self.car_entity, self.car_entity.forward * self.car_speed * dt, 1.9)
                if distance(before, self.car_entity.position) < abs(self.car_speed * dt) * .35:
                    self.car_speed *= -.25
            self.car_entity.x = clamp(self.car_entity.x, -28, 28); self.car_entity.z = clamp(self.car_entity.z, -22, 22)
            self.resolve_car_collisions()
            actor = self.car_entity
            self.avatar.enabled = False
        else:
            actor = self.avatar
            direction = Vec3(held_keys["d"] - held_keys["a"], 0, held_keys["w"] - held_keys["s"])
            if direction.length() and actor:
                running = held_keys["shift"] or held_keys["left shift"] or held_keys["right shift"]
                walk_speed = (7.2 if running else 4.5) * self.move_multiplier
                self.move_actor(actor, direction.normalized() * walk_speed * dt, .45)
                actor.x = clamp(actor.x, -28, 28); actor.z = clamp(actor.z, -22, 22)
                # While walking, face the direction of travel.
                actor.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
            if actor and self.locked_enemy and not self.locked_enemy["dead"]:
                to_target = self.locked_enemy["entity"].position - actor.position
                to_target.y = 0
                if to_target.length():
                    actor.rotation_y = math.degrees(math.atan2(to_target.x, to_target.z))
        camera.position = lerp(camera.position, actor.position + Vec3(0, 11 if not self.in_car else 17, -16 if not self.in_car else -18), dt * 4)
        camera.look_at(actor.position + Vec3(0, 1.2 if not self.in_car else 0, 1))
        for enemy in self.enemies:
            if enemy["dead"]: continue
            delta = actor.position - enemy["entity"].position
            delta.y = 0
            if delta.length() > 3 and delta.length() < 16: self.move_actor(enemy["entity"], delta.normalized() * 1.2 * dt, .4)
            elif not self.in_car and delta.length() < 1.25:
                self.damage_player(20 if enemy["kind"] == "zsti_boss" else 12)
                if self.state != "PLAY":
                    return
            if not self.in_car:
                enemy["shot_timer"] -= dt
                if 4.5 < delta.length() < 14 and enemy["shot_timer"] <= 0:
                    self.fire_enemy_projectile(enemy)
                    # Long cooldown keeps the street readable and projectiles avoidable.
                    enemy["shot_timer"] = random.uniform(4.5, 6.5)
        self.refresh_minimap()
        self.refresh_prompt()
        self.update_visual_animations(dt, actor)

    def input(self, key):
        if self.state == "INTRO": self.finish_intro()
        elif self.state == "MENU" and key in ("enter", "left mouse down"): self.start()
        elif self.state == "PLAY":
            if key == "escape": self.show_menu()
            elif key == "tab":
                if self.in_car:
                    self.notice.text = "EXIT THE CAR TO LOCK A TARGET"
                elif self.locked_enemy:
                    self.set_target_lock(None)
                    self.notice.text = "TARGET LOCK OFF"
                else:
                    target = self.nearest_enemy()
                    self.set_target_lock(target)
                    self.notice.text = "TARGET LOCK ON" if target else "NO TARGETS LEFT"
            elif key in ("j", "left mouse down"):
                if self.in_car:
                    self.notice.text = "E EXIT CAR TO START A CLEANUP FIGHT"
                    return
                if self.attack_cooldown > 0: return
                self.attack_cooldown = self.weapon()["cooldown"] * self.attack_delay / .28
                aim_point = self.locked_enemy["entity"].position if self.locked_enemy and not self.locked_enemy["dead"] else self.get_mouse_aim_point()
                aim = aim_point - self.avatar.position
                aim.y = 0
                if aim.length():
                    self.avatar.rotation_y = math.degrees(math.atan2(aim.x, aim.z))
                self.spawn_projectile(aim_point)
            elif key in ("1", "2", "3"):
                self.equip_weapon(int(key) - 1)
            elif key == "e" and distance(self.avatar if not self.in_car else self.car_entity, self.shop) < 4: self.open_shop()
            elif key == "e" and distance(self.avatar if not self.in_car else self.car_entity, self.board) < 4: self.open_quest()
            elif key == "e" and self.in_car and self.car_entity.x > 20 and all(e["dead"] for e in self.enemies):
                if self.street < 2:
                    self.street += 1; self.build_street(); self.start()
                else:
                    self.win_game()
            elif key == "e" and self.in_car:
                exit_position = None
                for offset in (self.car_entity.right, -self.car_entity.right,
                               self.car_entity.forward, -self.car_entity.forward):
                    candidate = self.car_entity.position + offset.normalized() * 2.2
                    candidate.y = 0
                    if not self.blocked(candidate, .45):
                        exit_position = candidate
                        break
                if exit_position is None:
                    return
                self.in_car = False
                self.car_speed = 0.0
                self.avatar.position = exit_position
                self.avatar.enabled = True
                self.notice.text = "ON FOOT // J CLEANUP PAN // E ENTER CAR"
            elif key == "e" and not self.in_car and distance(self.avatar, self.car_entity) < 2.5:
                self.set_target_lock(None)
                self.in_car = True
                self.car_speed = 0.0
                self.avatar.enabled = False
                self.notice.text = "BACK IN CAR // DRIVE TO THE NEXT STREET"
        elif self.state == "QUEST":
            if key in ("e", "escape"): self.start()
        elif self.state == "SHOP":
            if key in ("e", "escape"): self.start()
            elif key in ("1", "2", "3"):
                weapon = self.WEAPONS[int(key) - 1]
                if weapon["id"] in self.unlocked_weapons:
                    self.equipped_weapon = weapon["id"]
                    self.save()
                    self.open_shop()
                elif self.coins >= weapon["price"]:
                    self.coins -= weapon["price"]
                    self.unlocked_weapons.add(weapon["id"])
                    self.equipped_weapon = weapon["id"]
                    self.save()
                    self.open_shop()
                else:
                    self.shop_text.text += "\n\nNot enough coins"
            elif key == "p":
                if self.coins >= 30 and self.weapon_level < 3:
                    self.coins -= 30
                    self.weapon_level += 1
                    self.save()
                    self.open_shop()
                elif self.coins < 30:
                    self.open_shop()
                    self.shop_text.text += "\nNot enough coins"
        elif self.state == "UPGRADE" and key in ("1", "2", "3"):
            self.choose_upgrade(int(key) - 1)
        elif self.state == "WIN":
            if key == "enter":
                self.street = 0
                self.max_hp = 100; self.player_hp = 100; self.damage_bonus = 0
                self.move_multiplier = 1.0; self.attack_delay = .28; self.damage_multiplier = 1.0
                self.build_street(); self.start()
            elif key == "escape": self.show_menu()
        elif self.state == "GAME_OVER":
            if key == "enter":
                self.player_hp = self.max_hp
                self.damage_cooldown = 0
                self.build_street()
                self.start()
            elif key == "escape":
                self.player_hp = self.max_hp
                self.show_menu()

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
    camera.fov = 65
    window.title = "Green-Eye // Gliwice 3D Streets"; window.color = color.rgb32(28, 72, 38); scene.fog_color = color.rgb32(28, 72, 38)
    AmbientLight(color=color.rgb32(55, 55, 55))
    DirectionalLight(rotation=(45, -45, 45), color=color.rgb32(85, 85, 85))
    game = HybridGame(); game.run()


if __name__ == "__main__": create_app()

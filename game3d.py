import json
import random
from pathlib import Path

from ursina import *

ROOT = Path(__file__).parent
SAVE_PATH = ROOT / "save.json"
# Ursina resolves asset names relative to the project working directory.
# Keep these relative so Panda3D also finds them when launched from the repo.
MAP_TEXTURE = "assets/user/city/gliwice_map.png"
RUNNER_TEXTURE = "assets/user/walk/runner/south/00.png"
THUG_TEXTURE = "assets/user/walk/bruiser/south/00.png"
TEEN_TEXTURE = "assets/user/walk/punk/south/00.png"
DEALER_TEXTURE = "assets/user/walk/businessman/south/00.png"

NEON_PINK = color.rgb(255, 37, 116)
NEON_CYAN = color.rgb(0, 222, 218)
NEON_YELLOW = color.rgb(255, 236, 105)
NIGHT = color.rgb(10, 8, 21)

class PlayerData:
    def __init__(self, data=None):
        data = data or {}
        self.coins = int(data.get("coins", 0)); self.xp = int(data.get("xp", 0))
        self.max_hp = int(data.get("max_hp", 100)); self.upgrades = data.get("upgrades", {"pan": 0, "health": 0, "ammo": 0})
        self.quest_active = bool(data.get("quest_active", False)); self.quest_progress = int(data.get("quest_progress", 0)); self.quest_complete = bool(data.get("quest_complete", False))
        for key in ("pan", "health", "ammo"): self.upgrades.setdefault(key, 0)
    def to_dict(self): return {"hp": self.max_hp, "max_hp": self.max_hp, "coins": self.coins, "xp": self.xp, "upgrades": self.upgrades, "quest_active": self.quest_active, "quest_progress": self.quest_progress, "quest_complete": self.quest_complete}

class Enemy3D:
    def __init__(self, game, kind, position):
        self.game, self.kind, self.position = game, kind, Vec3(*position); self.hp = {"thug": 70, "teen": 45, "dealer": 95}[kind]
        self.dead = False
        texture = {"thug": THUG_TEXTURE, "teen": TEEN_TEXTURE, "dealer": DEALER_TEXTURE}[kind]
        self.entity = Entity(model="quad", texture=texture, billboard=True, position=self.position + Vec3(0, 1.2, 0), scale=2.2, double_sided=True)
        self.marker = Entity(model="quad", color=NEON_PINK, position=self.position + Vec3(0, .03, 0), scale=(1.5, .05), rotation_x=90)
    def update(self, dt):
        if self.hp <= 0: return
        delta = self.game.player.position - self.position; distance = delta.length()
        if distance > 3: self.position += delta.normalized() * (1.2 if self.kind == "teen" else .7) * dt
        self.entity.position = self.position + Vec3(0, 1.2, 0); self.marker.position = self.position + Vec3(0, .03, 0)
    def hit(self, damage):
        if self.dead: return
        self.hp -= damage
        if self.hp <= 0:
            self.dead = True; self.entity.animate_scale(0, duration=.12); self.marker.disable(); self.game.spawn_sparks(self.position); self.game.player_data.coins += 5; self.game.player_data.xp += 10; self.game.enemy_defeated()

class GreenEye3D:
    def __init__(self):
        self.state = "INTRO"; self.intro_time = 0; self.location = 0; self.player_data = self.load_save(); self.enemies = []; self.bullets = []; self.entities = []; self.story = ["The board called. Gliwice needs a cleaner.", "Neon signs point east. Keep moving.", "A station contact left one last clue.", "The old walls hide a new mess.", "The radio tower is broadcasting the final job."]
        self.locations = ["RYNEK", "UL. ZWYCIESTWA", "UL. DWORCOWA", "DOLNYCH WALOW", "UL. CHORZOWSKA"]
        self.menu_ui = []; self.shop_ui = []; self.tutorial = True; self.create_ui(); self.build_world()
    def load_save(self):
        try: return PlayerData(json.loads(SAVE_PATH.read_text()))
        except (OSError, ValueError, TypeError): return PlayerData()
    def save(self): SAVE_PATH.write_text(json.dumps(self.player_data.to_dict(), indent=2))
    def create_ui(self):
        # Ursina can use a white clear color on some Wayland/OpenGL setups;
        # keep an explicit UI backdrop behind every screen.
        self.backdrop = Entity(parent=camera.ui, model="quad", color=NIGHT, scale=(2, 2), z=1)
        self.title = Text("GREEN-EYE", origin=(0, 0), scale=.08, color=NEON_YELLOW, enabled=False)
        self.subtitle = Text("GLIWICE // NIGHT CLEANUP", origin=(0, 0), scale=.035, color=NEON_CYAN, enabled=False)
        self.hud = Text("", position=(-.86, .45), scale=.025, color=NEON_YELLOW, enabled=False)
        self.help = Text("", position=(-.86, -.46), scale=.022, color=color.white, enabled=False)
        self.message = Text("", origin=(0, 0), y=-.2, scale=.04, color=NEON_PINK, enabled=False)
        self.map_panel = Entity(parent=camera.ui, model="quad", texture=MAP_TEXTURE, scale=(1.72, 1), color=color.rgba(255,255,255,190), z=.5, enabled=False)
        self.menu_card = Entity(parent=camera.ui, model="quad", color=color.rgba(8,6,18,220), scale=(.64,.86), z=.2, enabled=False)
        self.start_text = Text("START CLEANUP", parent=camera.ui, origin=(0,0), y=-.05, scale=.045, color=NEON_YELLOW, enabled=False)
        self.controls_text = Text("CONTROLS", parent=camera.ui, origin=(0,0), y=-.15, scale=.038, color=color.white, enabled=False)
        self.menu_prompt = Text("ENTER / CLICK  TO START 3D CITY", parent=camera.ui, origin=(0,0), y=-.38, scale=.028, color=NEON_PINK, enabled=False)
        self.shop_title = Text("NIGHT SHOP", parent=camera.ui, origin=(0,0), y=.3, scale=.055, color=NEON_YELLOW, enabled=False)
        self.shop_text = Text("", parent=camera.ui, origin=(0,0), y=.05, scale=.035, color=color.white, enabled=False)
        self.quest_title = Text("QUEST BOARD", parent=camera.ui, origin=(0,0), y=.3, scale=.055, color=NEON_YELLOW, enabled=False)
        self.quest_text = Text("", parent=camera.ui, origin=(0,0), y=.05, scale=.035, color=color.white, enabled=False)
    def clear_world(self):
        for entity in self.entities: destroy(entity)
        self.entities.clear()
        for enemy in self.enemies: destroy(enemy.entity); destroy(enemy.marker)
        self.enemies.clear()
        for bullet in self.bullets: destroy(bullet["entity"])
        self.bullets.clear()
    def add_box(self, position, scale, tint, label=None):
        entity = Entity(model="cube", position=position, scale=scale, color=tint, collider="box"); self.entities.append(entity)
        if label: self.entities.append(Text(label, world_position=Vec3(position[0], position[1] + scale[1] + .1, position[2]), billboard=True, scale=.45, color=NEON_YELLOW))
        return entity
    def build_world(self):
        self.clear_world(); zone = self.location % 5
        self.ground = self.add_box((0, -0.2, 0), (42, .3, 28), color.rgb(21, 16, 39))
        self.add_box((0, .01, 0), (42, .05, 3.2), color.rgb(30, 22, 48)); self.add_box((0, .02, 0), (3.2, .06, 28), color.rgb(30, 22, 48))
        for x in range(-19, 20, 4): self.add_box((x, .07, 0), (1.5, .04, .08), NEON_YELLOW)
        layouts = [[(-15,3,5,3),(-10,3,4,3),(8,3,5,3),(14,3,4,3),(-15,-10,5,3),(12,-10,8,3)], [(-16,5,4,5),(-10,5,5,3),(9,5,8,3),(16,5,4,5),(-12,-10,10,3),(10,-10,5,3)], [(-16,5,10,3),(8,5,3,5),(14,5,3,5),(-12,-10,5,3),(6,-10,8,3)], [(-16,5,5,3),(-8,5,5,3),(13,5,9,3),(-15,-10,4,3),(10,-10,4,3)], [(-15,5,8,5),(-4,5,4,5),(8,5,8,5),(16,-10,8,3),(-15,-10,8,3)]][zone]
        self.obstacles = []
        accents = [NEON_PINK, NEON_CYAN, color.orange, color.rgb(100,90,190), color.rgb(255,80,140)]
        for x,z,w,d in layouts: self.add_box((x,1.5,z), (w,3,d), color.rgb(25,18,42)); self.add_box((x,3.05,z), (w+.05,.04,d+.05), accents[zone]); self.obstacles.append((x-w/2-.5,x+w/2+.5,z-d/2-.5,z+d/2+.5))
        if zone == 2: self.add_bus((-3, .6, -6), NEON_CYAN); self.add_bus((8, .6, 7), NEON_PINK)
        if zone == 3: self.add_park()
        if zone == 4: self.add_box((0,1,-8),(9,2,3),color.rgb(85,40,50)); self.add_bus((11,.6,-4),color.orange)
        self.add_box((0,.4,11),(4,.8,2),color.rgb(55,30,70)); self.add_text_label("RYNEK" if zone == 0 else self.locations[zone], (0,1.2,11), NEON_YELLOW)
        self.shop = self.add_box((5,.8,8),(2.4,1.6,2.0),color.rgb(20,100,106)); self.obstacles.append((3.3,6.7,7,9)); self.add_text_label("SHOP  [E]", (5,2.0,8), NEON_CYAN)
        shop_sprite = Entity(model="quad", texture="assets/user/city/building-wide-a.png", billboard=True, position=(5, 2.0, 8), scale=2.8, double_sided=True); self.entities.append(shop_sprite)
        self.board = self.add_box((-5,.8,8),(2.8,1.6,1.0),color.rgb(125,35,75)); self.add_text_label("QUEST BOARD  [E]", (-5,2.0,8), NEON_YELLOW)
        self.exit = self.add_box((19,.2,0),(1,.25,3),NEON_PINK); self.add_text_label("NEXT STREET", (17,1,0), NEON_YELLOW)
        self.player = Entity(model="quad", texture=RUNNER_TEXTURE, billboard=True, position=(-8,1.2,0), scale=2.1, collider="box"); self.entities.append(self.player)
        enemy_positions = [(-12,0,-5),(10,0,6),(15,0,-5)]
        kinds = [["thug","teen","dealer"],["teen","thug","dealer"],["thug","thug","teen"],["dealer","teen","thug"],["dealer","thug","dealer"]][zone]
        for kind,pos in zip(kinds,enemy_positions): self.enemies.append(Enemy3D(self,kind,pos))
        camera.position = (0, 25, -20); camera.rotation_x = 55; camera.rotation_y = 0
    def add_text_label(self, text, position, tint): self.entities.append(Text(text, world_position=Vec3(*position), billboard=True, scale=.45, color=tint))
    def add_bus(self, position, tint): self.add_box(position,(4,1.2,1.5),tint); self.add_box((position[0],position[1]+.5,position[2]),(3,.45,1.2),color.rgb(150,220,220))
    def add_park(self):
        self.add_box((12,.05,7),(7,.1,7),color.rgb(15,80,68)); self.add_box((12,.08,7),(3,.1,2),color.rgb(0,126,145))
        for x,z in ((9,5),(15,5),(9,9),(15,9)): self.add_box((x,1,z),(.5,2,.5),color.rgb(40,150,85))
    def spawn_sparks(self, position):
        for i in range(6): Entity(model="sphere", position=position+Vec3(random.uniform(-.5,.5),1,random.uniform(-.5,.5)), scale=.1, color=NEON_YELLOW, add_to_scene_entities=True)
    def show_menu(self):
        self.state="MENU"; self.map_panel.enabled=True; self.menu_card.enabled=True; self.start_text.enabled=True; self.controls_text.enabled=True; self.menu_prompt.enabled=True; self.title.enabled=False; self.subtitle.enabled=False; self.hud.enabled=False; self.help.enabled=False
    def hide_menu(self):
        for ui in (self.map_panel,self.menu_card,self.start_text,self.controls_text,self.menu_prompt): ui.enabled=False
    def show_shop(self):
        self.state="SHOP"; self.shop_title.enabled=True; self.shop_text.enabled=True; self.shop_text.text="PAN POWER  $30  (P)\nHEART +20 HP  $25  (H)\nAMMO +10  $40  (A)\n\nP / H / A buy    E close"; self.hide_hud()
    def show_quest(self):
        self.state="QUEST"; self.quest_title.enabled=True; self.quest_text.enabled=True
        status = "COMPLETED" if self.player_data.quest_complete else (f"PROGRESS {self.player_data.quest_progress}/3" if self.player_data.quest_active else "PRESS ENTER TO ACCEPT")
        self.quest_text.text = f"CLEAN THE {self.locations[self.location]} BLOCK\nREMOVE 3 TARGETS   //   REWARD 30C + 50XP\n\n{status}\n\nENTER accept    E close"
        self.hide_hud()
    def hide_hud(self): self.hud.enabled=False; self.help.enabled=False
    def show_hud(self):
        self.hud.enabled=True; self.help.enabled=True; self.shop_title.enabled=False; self.shop_text.enabled=False; self.quest_title.enabled=False; self.quest_text.enabled=False; self.message.enabled=True
        self.hud.text = f"{self.locations[self.location]}  |  COINS {self.player_data.coins}  |  XP {self.player_data.xp}  |  TARGETS {sum(enemy.hp > 0 for enemy in self.enemies)}"
        self.help.text = "WASD MOVE   LMB SHOOT   J/K/L PAN ATTACKS   E INTERACT   CLEAR ALL -> NEXT STREET"
    def buy(self,key):
        prices={"pan":30,"health":25,"ammo":40}; price=prices[key]
        if self.player_data.coins < price: self.message.text="NOT ENOUGH COINS"; invoke(setattr,self.message,"text", "", delay=1.2); return
        self.player_data.coins -= price; self.player_data.upgrades[key] += 1
        if key == "health": self.player_data.max_hp += 20
        self.save(); self.message.text="UPGRADE BOUGHT!"; invoke(setattr,self.message,"text", "", delay=1.2)
    def shoot(self):
        if self.state != "PLAY": return
        direction = (mouse.world_point - self.player.world_position).normalized() if mouse.world_point else Vec3(0,0,1)
        bullet = Entity(model="sphere", position=self.player.position + Vec3(0,1,0), scale=.16, color=NEON_YELLOW); self.bullets.append({"entity":bullet,"direction":direction,"ttl":1.2})
    def melee(self, damage, label):
        living = [enemy for enemy in self.enemies if enemy.hp > 0]
        target = min(living, key=lambda enemy: distance(self.player, enemy.entity), default=None)
        if target and distance(self.player, target.entity) < 3.2: target.hit(damage); self.message.enabled=True; self.message.text=label; invoke(setattr,self.message,"text", "", delay=.45)
    def enemy_defeated(self):
        if self.player_data.quest_active:
            self.player_data.quest_progress = min(3, self.player_data.quest_progress + 1)
            if self.player_data.quest_progress >= 3:
                self.player_data.quest_active = False; self.player_data.quest_complete = True; self.player_data.coins += 30; self.player_data.xp += 50
                self.message.enabled=True; self.message.text="ALL TIDY NOW!  +30 COINS  +50 XP"; invoke(setattr,self.message,"text", "", delay=2.0)
        self.save()
    def update_bullets(self, dt):
        for bullet in self.bullets[:]:
            bullet["entity"].position += bullet["direction"] * 22 * dt; bullet["ttl"] -= dt
            hit = next((enemy for enemy in self.enemies if enemy.hp > 0 and distance(bullet["entity"], enemy.entity) < 1.2), None)
            if hit: hit.hit(35 + self.player_data.upgrades["ammo"]*10); bullet["ttl"] = 0
            if bullet["ttl"] <= 0: destroy(bullet["entity"]); self.bullets.remove(bullet)
    def update(self, dt):
        if self.state == "INTRO":
            self.intro_time += dt
            if self.intro_time > 3.5: self.show_menu()
            return
        if self.state != "PLAY": return
        movement = Vec3(held_keys["d"] - held_keys["a"], 0, held_keys["s"] - held_keys["w"])
        if movement.length():
            step = movement.normalized() * 7 * dt
            candidate = self.player.position + step
            blocked = any(left < candidate.x < right and front < candidate.z < back for left, right, front, back in self.obstacles)
            if not blocked: self.player.position = candidate
        self.player.x = clamp(self.player.x,-19,19); self.player.z = clamp(self.player.z,-12,12); camera.position = lerp(camera.position, Vec3(self.player.x,25,self.player.z-20), dt*3)
        for enemy in self.enemies: enemy.update(dt)
        self.update_bullets(dt)
        if all(enemy.hp <= 0 for enemy in self.enemies): self.exit.color=NEON_YELLOW
        self.hud.text = f"{self.locations[self.location]}  |  COINS {self.player_data.coins}  |  XP {self.player_data.xp}  |  TARGETS {sum(enemy.hp > 0 for enemy in self.enemies)}"
    def input(self,key):
        if self.state == "INTRO" and key not in ("mouse left",): self.show_menu(); return
        if self.state == "MENU" and key in ("enter", "left mouse down"): self.hide_menu(); self.state="PLAY"; self.show_hud(); return
        if self.state == "MENU" and key == "c": self.message.enabled=True; self.message.text="WASD move | LMB shoot | J/K/L pan attacks | E shop/quest/exit"; invoke(setattr,self.message,"text", "", delay=3); return
        if self.state == "PLAY":
            if key == "left mouse down": self.shoot()
            elif key == "j": self.melee(18 + self.player_data.upgrades["pan"] * 6, "PAN SWING!")
            elif key == "k": self.melee(25 + self.player_data.upgrades["pan"] * 8, "ROLLING PIN!")
            elif key == "l": self.melee(35 + self.player_data.upgrades["pan"] * 10, "SOUP SPLASH!")
            elif key == "e" and distance(self.player,self.shop) < 3: self.show_shop()
            elif key == "e" and distance(self.player,self.board) < 3: self.show_quest()
            elif key == "e" and self.player.x > 17 and all(enemy.hp <= 0 for enemy in self.enemies):
                self.location += 1; self.player_data.quest_active=False; self.player_data.quest_progress=0; self.player_data.quest_complete=False; self.save(); self.build_world(); self.show_hud()
        elif self.state == "SHOP":
            if key == "escape" or key == "e": self.state="PLAY"; self.show_hud()
            elif key == "p": self.buy("pan")
            elif key == "h": self.buy("health")
            elif key == "a": self.buy("ammo")
        elif self.state == "QUEST":
            if key in ("escape", "e"): self.state="PLAY"; self.show_hud()
            elif key == "enter" and not self.player_data.quest_active and not self.player_data.quest_complete:
                self.player_data.quest_active=True; self.player_data.quest_progress=0; self.save(); self.show_quest()
    def run(self):
        self.state="INTRO"; self.hide_menu(); self.title.enabled=True; self.title.text="GREEN-EYE"; self.title.position=(0,.15); self.subtitle.enabled=True; self.subtitle.text="GLIWICE // NIGHT CLEANUP"; self.subtitle.position=(0,-.02)
        app.run()

game = None
def update():
    if game: game.update(time.dt)
def input(key):
    if game: game.input(key)

app = None
def create_app():
    global app, game
    app = Ursina(borderless=False, development_mode=False)
    window.title = "Green-Eye 3D // Gliwice Night Cleanup"; window.color = NIGHT; camera.overlay.color = color.clear; window.fps_counter.enabled = True
    game = GreenEye3D(); game.run()

if __name__ == "__main__": create_app()

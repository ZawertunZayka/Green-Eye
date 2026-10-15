# Green-Eye: All Tidy Now! 3D

A neon top-down 3D cleanup action game set in a stylized Gliwice. The cheerful heroine treats cartoon bad guys as city trash: defeated opponents pop into stars, with no blood or gore.

## Run

    python3 -m pip install -r requirements.txt
    python main.py

The current build uses Ursina/Panda3D for the 3D migration. It keeps the top-down neon action loop while adding real 3D buildings, streets, shop, enemies, and camera.

## Controls

- Menu: Enter
- 3D city: WASD to move, left mouse to shoot, J/K/L for pan, rolling-pin and soup attacks
- Quest board: walk to the pink board and press E, then Enter to accept a cleanup job
- Shop: walk to the cyan shop and press E; P buys pan power, H buys health, A buys ammo
- E at the glowing exit advances to the next unique street after all targets are cleared
- Shop/quest screens: E or Escape closes
- Menu: Enter starts, C shows controls

The Ursina migration includes a 3D city scene, camera, map-driven menu, quest board, shop building, upgrades, three enemy types, shooting, melee specials, procedural street scenes, and street-to-street progression. Progress is saved to save.json. The earlier Pygame modules remain in the repository as legacy reference modules; `main.py` now launches the Ursina build.

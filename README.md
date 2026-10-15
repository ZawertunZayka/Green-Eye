# Green-Eye: All Tidy Now! 3D

A neon top-down 3D cleanup action game set in a stylized Gliwice. The cheerful heroine treats cartoon bad guys as city trash: defeated opponents pop into stars, with no blood or gore.

## Run

    python3 -m pip install -r requirements.txt
    python main.py

The current build uses Ursina/Panda3D for the 3D migration. It keeps the top-down neon action loop while adding real 3D buildings, streets, shop, enemies, and camera.

## Controls

- Menu: Enter
- 3D city: WASD to move, left mouse to shoot, E at the shop or exit
- Shop: P buys pan power, H buys health, A buys ammo, Escape closes
- Menu: Enter starts, C shows controls

The Ursina migration includes a 3D city scene, camera, map-driven menu, shop building, upgrades, three enemy types, shooting, procedural street scenes, and street-to-street progression. Progress is saved to save.json. The earlier Pygame modules remain in the repository as legacy reference modules; `main.py` now launches the Ursina build.

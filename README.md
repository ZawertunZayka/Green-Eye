# Green-Eye: All Tidy Now!

A 3D cartoon cleanup game using Ursina, with three stages and a fictional final boss at ZSTI. Asset credits are in CREDITS.md.

The city stages contain dense residential blocks, greenery, street furniture, parked traffic and larger enemy groups. The final boss is protected by four guards.

At launch, a short skippable 3D cinematic shows zombies and skeletons taking over the streets of Gliwice before the main menu appears.

## Run

    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python main.py

The current entry point is main.py → game3d.py. Other Python modules are retained legacy 2D code, not imported by the 3D game.

## Controls

- Esc: pause/menu with controls and progress; Enter: continue.
- WASD: walk; hold Shift to run. S/W: drive forward/reverse; A/D: steer.
- Mouse: aim; J or left click: shoot; Tab: toggle nearest-enemy lock.
- E: nearby shop/board, enter or leave the car.
- Clear the stage, drive east past x=20 and press E to continue.
- Shop: P buys a damage upgrade for 30 coins (maximum three upgrades).

The gameplay view keeps only useful information visible: health, minimap, contextual interaction prompt and target marker. Brief story cards introduce each stage and disappear automatically. The final ZSTI arena shows the boss name and health bar. Statistics and controls are in the pause menu; there are no permanent city/street labels or shot notifications.

The gameplay HUD includes player health and a compact minimap. Enemies damage the player at close range while on foot; after defeat, Enter restarts the current street with full health.

Coins, XP and upgrades are saved to save.json. Replaying retains these rewards. Existing unrelated save fields are preserved. The job board reports remaining enemies and the per-target reward.

# Green-Eye: All Tidy Now!

A 3D cartoon cleanup game using Ursina, with three stages and a fictional final boss at ZSTI. Asset credits are in CREDITS.md.

## Run

    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python main.py

The current entry point is main.py → game3d.py. Other Python modules are retained legacy 2D code, not imported by the 3D game.

## Controls

- Esc: pause/menu with controls and progress; Enter: continue.
- WASD: walk. S/W: drive forward/reverse; A/D: steer.
- Mouse: aim; J or left click: shoot; Tab: toggle nearest-enemy lock.
- E: nearby shop/board, enter or leave the car.
- Clear the stage, drive east past x=20 and press E to continue.
- Shop: P buys a damage upgrade for 30 coins (maximum three upgrades).

The gameplay view has only a contextual interaction prompt and a small target marker. Statistics and controls are in the pause menu. There are no permanent city/street labels or shot notifications.

Coins, XP and upgrades are saved to save.json. Replaying retains these rewards. Existing unrelated save fields are preserved. The job board reports remaining enemies and the per-target reward.

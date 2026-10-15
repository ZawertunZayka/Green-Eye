# Green-Eye: All Tidy Now!

A tiny 2D pixel-art cleanup comedy game set in a stylized Gliwice. The cheerful apron-wearing heroine treats cartoon bad guys as city trash: defeated opponents pop into stars, with no blood or gore.

## Run

    python3 -m pip install -r requirements.txt
    python main.py

`pygame-ce` is used because it provides the normal `pygame` import and prebuilt wheels for current Python versions, avoiding a local SDL source build.

## Controls

- Menu: Enter
- Overworld: WASD / arrow keys to move, E at the board to accept a job
- Fight: WASD / arrow keys move, left mouse shoots, J punch, K kick, L cooking special, Space block

The current vertical slice includes the quest board, a Gliwice-inspired overworld with Rynek, station, park, blocks and radio tower landmarks, and best-of-three fights against three enemy types. Progress is saved to save.json.

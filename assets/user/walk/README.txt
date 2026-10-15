GEGX FREE WALK PACK - PIXEL STYLE v1.1

19 top-down characters, walking, in all four directions. Free.

CONTENT
  biker
  bruiser
  businessman
  butcher
  child
  cook
  firefighter
  heavyset
  jogger
  mechanic
  nurse
  old_man
  police_officer
  priest
  punk
  runner
  soldier
  student
  teacher

FOLDERS
  <character>/<direction>/00.png ...      the single frames, in order
  <character>/strips/<direction>.png      the same frames as one horizontal strip
  README.txt                              this file

  Directions are south, north, east and west. South means the character is facing the
  camera - the pose you want for a menu or a portrait.

FRAME SIZE AND ANCHOR (new in v1.1)
  Every frame of every character is 192 x 192 px. One size, one pivot:
    - the feet stand on row 164 (0-based), i.e. the ground line sits at
      0.859 of the frame height, for EVERY character and EVERY direction
    - the character is horizontally centred on x = 96
  Within one animation the frames still bob up and down a few pixels - that is the
  step itself, not a cropping artefact. Set your pivot once (x 96, y 165 - or
  0.5 / 0.859 in normalised coordinates) and every character in this pack, and
  in the other GegX walk packs, drops in without per-character offsets.
  In a strip the frame size is the image height (192), the frame count is width / 192.

FRAME COUNT
  12 frames per direction, except for a few (8, 9 frames) where single broken
  frames were dropped instead of re-rolling the whole animation.
  The looping frame (a repeat of the first one) has been removed, so the frames can be
  played start to end on repeat without a stutter.

CHANGELOG
  v1.1: all frames re-padded to one square size (192) with a shared foot line and a
        shared centre - one pivot for the whole pack and for every other GegX walk pack.
        v1.0 used a per-character frame size and a per-direction pivot.

LICENCE
  Use these assets in any project, commercial or free, no credit required.
  Reselling or redistributing the assets themselves as assets is not allowed.

THIS PACK IS A VOTE
  This is a free sample, and what comes next is up to you. If you want ATTACK, RUN or
  IDLE animations for particular characters, say so in the itch comments - the names
  that get asked for most are the ones that get animated next.

Made by GegX - gegx.itch.io

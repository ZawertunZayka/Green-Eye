# Asset scan

assets/user/city/ contains four 64x64 transparent PNG preview sprites copied from the supplied kenney_city-kit-commercial_2.1 pack. They are loaded through assets.py, nearest-neighbor scaled to 32x32, and used as city landmark props in the overworld.

assets/user/walk/ contains four frames each for runner, bruiser, punk, and businessman from the supplied GegX Free Walk Pixel Pack. These animate the player and three enemy types. assets/user/urban/tiles/ contains four 16x16 tiles from the supplied Kenney RPG Urban Pack and they are tiled across the overworld ground.

assets/user/city/gliwice_map.png is the user-supplied 1674x940 map image. It is scaled with nearest-neighbor to the 320x180 menu canvas and used as the menu's progress map with district markers, coins, XP, and completed/current/locked routes.

assets/user/3d_city/ contains the newly supplied 3D city set: GLB buildings,
roads, fences, planters and trees, plus the matching colormap and preview PNGs.
The 2D overworld uses the supplied preview PNGs as pixel-art landmark sprites;
the original GLB files are preserved for a future true-3D renderer.

assets/user/3d_city/Models/Cars/ contains the supplied Kenney Car Kit in GLB
and preview PNG formats. The street scene uses sedan, taxi, police, van,
delivery and truck previews as traffic props.

assets/user/3d_city/Models/Roads/ contains the supplied Kenney City Kit Roads
GLB models and previews. The street uses road-straight/intersection pieces,
traffic lights and an electricity pole from this kit.

assets/user/3d_arcade/ contains the supplied Kenney Mini Arcade assets. The
static OBJ character-gamer model is the player and character-employee/gamer
models are used for 3D cleanup targets. The GLB character files are retained,
but the current Ursina loader uses the static OBJ versions because its GLB
skinning loader cannot import the animated character files.

assets/user/3d_nature/ contains the supplied vegetation GLBs. grass_1,
grass_2, bush_1, flowers_1 and fern are placed around the park section of
each street.

assets/user/3d_kaykit/ contains the selected KayKit Prototype Bits
Dummy_Base OBJ and texture. It is kept as a swappable character asset; the
runtime currently uses the verified Mini Arcade OBJ models because this KayKit
OBJ export is not accepted by the installed Ursina model loader.

assets/user/3d_skeletons/ contains the KayKit Skeletons character GLBs. The
street uses Skeleton_Warrior for the bruiser, Skeleton_Rogue for the fast
target and Skeleton_Mage for the dealer. They are loaded through the glTF
loader and rotated from the pack's Z-up coordinates into the game's Y-up
coordinates.

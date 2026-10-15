from dataclasses import dataclass

@dataclass(frozen=True)
class EnemySpec:
    name: str
    hp: int
    speed: float
    damage: int
    color: str
    block_chance: float
    ranged: bool = False

ENEMY_TYPES = {
    "thug": EnemySpec("Street Thug", 70, 36.0, 8, "brown", 0.08),
    "teen": EnemySpec("Knife Teenager", 48, 58.0, 6, "red", 0.16),
    "dealer": EnemySpec("Dealer Boss", 95, 31.0, 10, "dealer", 0.38, True),
}

from dataclasses import dataclass, asdict

@dataclass
class Quest:
    title: str
    target_type: str
    required: int
    progress: int = 0
    reward_coins: int = 30
    reward_xp: int = 50
    active: bool = False
    complete: bool = False
    def label(self) -> str:
        return f"{self.title} ({self.progress}/{self.required})"

def starter_quest() -> Quest:
    return Quest("Clean the station corner", "thug", 1)

def quest_to_dict(q: Quest) -> dict:
    return asdict(q)

def quest_from_dict(data: dict) -> Quest:
    return Quest(**data)

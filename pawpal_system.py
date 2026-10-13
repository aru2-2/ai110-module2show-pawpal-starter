from dataclasses import dataclass, field
from datetime import date, time
from typing import Dict, List, Optional


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: str = "medium"
    scheduled_time: Optional[time] = None
    recurrence: Optional[str] = None
    completed: bool = False

    def mark_complete(self) -> None:
        pass

    def is_due(self, on_date: date) -> bool:
        pass


@dataclass
class Pet:
    name: str
    species: str
    breed: str = ""
    age: int = 0
    special_needs: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_pending_tasks(self) -> List[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> List[Task]:
        pass


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self, on_date: date) -> List[Task]:
        pass

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        pass

    def filter_by_time(self, tasks: List[Task]) -> List[Task]:
        pass

    def detect_conflicts(self, tasks: List[Task]) -> List[Task]:
        pass

    def explain_plan(self) -> str:
        pass

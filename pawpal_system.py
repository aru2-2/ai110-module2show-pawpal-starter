from dataclasses import dataclass, field
from datetime import date, time, timedelta
from enum import IntEnum
from typing import Dict, List, Optional

DAY_START = time(8, 0)
DAY_END = time(21, 0)


def _to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _to_time(minutes: int) -> time:
    return time(minutes // 60, minutes % 60)


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    scheduled_time: Optional[time] = None
    recurrence: Optional[str] = None  # None (one-off), "daily" or "weekly"
    completed: bool = False
    last_completed: Optional[date] = None
    # Back-reference to the owning Pet; excluded from repr/eq to avoid infinite recursion.
    pet: Optional["Pet"] = field(default=None, repr=False, compare=False)

    def mark_complete(self, on_date: Optional[date] = None) -> None:
        """Mark the task done and record the completion date."""
        self.completed = True
        self.last_completed = on_date or date.today()

    def is_due(self, on_date: date) -> bool:
        """Return True if the task needs doing on the given date."""
        if self.recurrence is None:
            return not self.completed
        if self.last_completed is None:
            return True
        if self.recurrence == "daily":
            return self.last_completed < on_date
        if self.recurrence == "weekly":
            return (on_date - self.last_completed) >= timedelta(days=7)
        raise ValueError(f"Unknown recurrence: {self.recurrence!r}")


@dataclass
class Pet:
    name: str
    species: str
    breed: str = ""
    age: int = 0
    special_needs: str = ""
    tasks: List[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Link any tasks passed to the constructor back to this pet."""
        for task in self.tasks:
            task.pet = self

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and set the task's pet reference."""
        task.pet = self
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet and clear its pet reference."""
        self.tasks.remove(task)
        task.pet = None

    def get_pending_tasks(self) -> List[Task]:
        """Return the tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every task from all of the owner's pets in one list."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class ScheduledItem:
    task: Task
    start_time: time
    reason: str = ""

    @property
    def start_minutes(self) -> int:
        return _to_minutes(self.start_time)

    @property
    def end_minutes(self) -> int:
        return self.start_minutes + self.task.duration_minutes

    def overlaps(self, other: "ScheduledItem") -> bool:
        """Return True if this item's time window overlaps the other's."""
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans for the given owner's pets."""
        self.owner = owner
        self.skipped: List[Task] = []

    def generate_plan(self, on_date: date) -> List[ScheduledItem]:
        """Build a time-ordered plan of due tasks that fit the owner's day."""
        # Read across every pet through the Owner, not from a single pet.
        due = [t for t in self.owner.get_all_tasks() if t.is_due(on_date)]
        ordered = self.sort_tasks(due)
        fitting = self.filter_by_time(ordered)

        plan: List[ScheduledItem] = []
        busy: List[tuple] = []  # (start, end) minutes already taken

        # Tasks with a fixed time go in first so floating tasks can work around them.
        for task in fitting:
            if task.scheduled_time is not None:
                item = ScheduledItem(
                    task, task.scheduled_time,
                    f"{task.priority.name.capitalize()} priority; fixed at {task.scheduled_time:%H:%M}",
                )
                plan.append(item)
                busy.append((item.start_minutes, item.end_minutes))

        # Floating tasks take the earliest open gap in the day.
        day_end = _to_minutes(DAY_END)
        placed = {id(i.task) for i in plan}
        for task in fitting:
            if task.scheduled_time is not None:
                continue
            start = self._find_gap(busy, task.duration_minutes, _to_minutes(DAY_START), day_end)
            if start is None:
                continue
            item = ScheduledItem(
                task, _to_time(start),
                f"{task.priority.name.capitalize()} priority; placed in first open slot",
            )
            plan.append(item)
            busy.append((start, start + task.duration_minutes))
            placed.add(id(task))

        self.skipped = [t for t in due if id(t) not in placed]
        return sorted(plan, key=lambda i: i.start_minutes)

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority, then fixed time, then duration."""
        # Highest priority first, then fixed-time tasks, then shortest first.
        return sorted(
            tasks,
            key=lambda t: (-t.priority, t.scheduled_time or time.max, t.duration_minutes),
        )

    def filter_by_time(self, tasks: List[Task]) -> List[Task]:
        """Keep tasks, in order, until the owner's daily time budget runs out."""
        budget = self.owner.available_minutes_per_day
        kept: List[Task] = []
        for task in tasks:
            if task.duration_minutes <= budget:
                kept.append(task)
                budget -= task.duration_minutes
        return kept

    def detect_conflicts(self, plan: List[ScheduledItem]) -> List[ScheduledItem]:
        """Return the plan items that overlap another item."""
        return [
            item for i, item in enumerate(plan)
            if any(item.overlaps(other) for j, other in enumerate(plan) if i != j)
        ]

    def explain_plan(self, plan: List[ScheduledItem]) -> str:
        """Describe the plan as text, including conflicts and skipped tasks."""
        if not plan:
            return "No tasks to schedule."
        lines = []
        for item in plan:
            pet = item.task.pet.name if item.task.pet else "?"
            lines.append(
                f"{item.start_time:%H:%M} - {item.task.title} for {pet} "
                f"({item.task.duration_minutes} min) [{item.reason}]"
            )
        conflicts = self.detect_conflicts(plan)
        if conflicts:
            names = ", ".join(i.task.title for i in conflicts)
            lines.append(f"Warning: overlapping tasks: {names}")
        if self.skipped:
            names = ", ".join(t.title for t in self.skipped)
            lines.append(f"Skipped (not enough time): {names}")
        return "\n".join(lines)

    @staticmethod
    def _find_gap(busy: List[tuple], duration: int, day_start: int, day_end: int) -> Optional[int]:
        """Return the earliest start minute with a free gap of the given length, or None."""
        candidate = day_start
        for start, end in sorted(busy):
            if candidate + duration <= start:
                break
            candidate = max(candidate, end)
        return candidate if candidate + duration <= day_end else None

from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from enum import IntEnum
from typing import Dict, List, Optional

DAY_START = time(8, 0)
DAY_END = time(21, 0)

# Days between occurrences of each supported recurrence.
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}


def _to_minutes(t: time) -> int:
    """Convert a time of day to minutes since midnight."""
    return t.hour * 60 + t.minute


def _to_time(minutes: int) -> time:
    """Convert minutes since midnight to a time of day (must be under 24 hours)."""
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
    due_date: Optional[date] = None  # None means "due whenever"; set on auto-created repeats
    # Back-reference to the owning Pet; excluded from repr/eq to avoid infinite recursion.
    pet: Optional["Pet"] = field(default=None, repr=False, compare=False)

    def mark_complete(self, on_date: Optional[date] = None) -> Optional["Task"]:
        """Mark the task done and record the completion date.

        A daily or weekly task also spawns a fresh copy due on its next occurrence
        (completion date + 1 or + 7 days). The copy is added to the same pet and
        returned; one-off tasks, and tasks that were already complete, return None.
        """
        if self.recurrence is not None and self.recurrence not in RECURRENCE_DAYS:
            raise ValueError(f"Unknown recurrence: {self.recurrence!r}")

        already_done = self.completed
        done_on = on_date or date.today()
        self.completed = True
        if already_done:
            return None
        self.last_completed = done_on

        if self.recurrence is None:
            return None
        next_task = replace(
            self,
            completed=False,
            last_completed=None,
            due_date=done_on + timedelta(days=RECURRENCE_DAYS[self.recurrence]),
        )
        if self.pet is not None:
            self.pet.add_task(next_task)
        return next_task

    def is_due(self, on_date: date) -> bool:
        """Return True if the task is unfinished and its due date has arrived.

        A task with no `due_date` is always due. Auto-created repeats of recurring
        tasks carry a `due_date`, so they stay hidden until their next occurrence.
        Raises ValueError if `recurrence` is not None, "daily" or "weekly".
        """
        if self.recurrence is not None and self.recurrence not in RECURRENCE_DAYS:
            raise ValueError(f"Unknown recurrence: {self.recurrence!r}")
        if self.completed:
            return False
        return self.due_date is None or self.due_date <= on_date


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
        """Start time as minutes since midnight."""
        return _to_minutes(self.start_time)

    @property
    def end_minutes(self) -> int:
        """End time as minutes since midnight (may pass 1440 for late tasks)."""
        return self.start_minutes + self.task.duration_minutes

    def overlaps(self, other: "ScheduledItem") -> bool:
        """Return True if this item's time window overlaps the other's.

        Windows are half-open [start, end), so back-to-back items (one ends exactly
        when the next starts) do not count as overlapping.
        """
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans for the given owner's pets."""
        self.owner = owner
        self.skipped: List[Task] = []

    def generate_plan(self, on_date: date) -> List[ScheduledItem]:
        """Build a time-ordered plan of due tasks that fit the owner's day.

        Steps:
          1. Collect tasks due on `on_date` across all pets.
          2. Sort by priority and keep those within the daily time budget.
          3. Place fixed-time tasks at their requested time (overlaps are allowed
             here and only reported later by `conflict_warnings`).
          4. Place each floating task in the earliest free gap between DAY_START
             and DAY_END; tasks with no gap are skipped.

        Side effect: sets `self.skipped` to the due tasks that were not scheduled.
        Returns the plan sorted by start time.
        """
        # Read across every pet through the Owner, not from a single pet.
        due = [t for t in self.owner.get_all_tasks() if t.is_due(on_date)]
        fitting = self.filter_by_time(self.sort_tasks(due))
        fixed = [t for t in fitting if t.scheduled_time is not None]
        floating = [t for t in fitting if t.scheduled_time is None]

        # Tasks with a fixed time go in first so floating tasks can work around them.
        plan = [
            ScheduledItem(t, t.scheduled_time, self._reason(t, f"fixed at {t.scheduled_time:%H:%M}"))
            for t in fixed
        ]
        busy = [(i.start_minutes, i.end_minutes) for i in plan]

        # Floating tasks take the earliest open gap in the day.
        day_start, day_end = _to_minutes(DAY_START), _to_minutes(DAY_END)
        for task in floating:
            start = self._find_gap(busy, task.duration_minutes, day_start, day_end)
            if start is None:
                continue
            plan.append(ScheduledItem(task, _to_time(start), self._reason(task, "placed in first open slot")))
            busy.append((start, start + task.duration_minutes))

        placed = {id(i.task) for i in plan}
        self.skipped = [t for t in due if id(t) not in placed]
        return sorted(plan, key=lambda i: i.start_minutes)

    @staticmethod
    def _reason(task: Task, detail: str) -> str:
        """Build the 'why' text shown next to a scheduled item."""
        return f"{task.priority.name.capitalize()} priority; {detail}"

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority, then fixed time, then duration.

        Order: highest priority first; ties go to the earlier fixed time (tasks
        without one sort after those with one); remaining ties go to the shorter task.
        Returns a new list and leaves the input unchanged.
        """
        # Highest priority first, then fixed-time tasks, then shortest first.
        return sorted(
            tasks,
            key=lambda t: (-t.priority, t.scheduled_time or time.max, t.duration_minutes),
        )

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by scheduled time, earliest first; unscheduled tasks go last.

        Unlike `sort_tasks`, priority is ignored. The sort is stable, so tasks with
        the same time (or none) keep their original relative order. Returns a new list.
        """
        return sorted(tasks, key=lambda t: t.scheduled_time or time.max)

    def filter_tasks(
        self,
        tasks: List[Task],
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        """Keep tasks matching the given completion status and/or pet name (None means any).

        Args:
            tasks: the tasks to filter; the list itself is not modified.
            completed: True keeps finished tasks, False keeps unfinished ones.
            pet_name: keeps tasks belonging to the pet with this name; tasks not
                attached to any pet never match a name.

        Pet names are compared case-insensitively, ignoring surrounding whitespace.
        Both filters must match when both are given. Returns a new list in the
        original order.
        """
        wanted = pet_name.strip().casefold() if pet_name is not None else None
        return [
            t for t in tasks
            if (completed is None or t.completed == completed)
            and (wanted is None or (t.pet is not None and t.pet.name.strip().casefold() == wanted))
        ]

    def filter_by_time(self, tasks: List[Task]) -> List[Task]:
        """Keep tasks, in order, until the owner's daily time budget runs out.

        Greedy: walks the list once and keeps each task whose duration still fits in
        the remaining minutes; a task that is too long is skipped but later, shorter
        ones can still be kept. It does not search for the best-fitting combination.
        """
        budget = self.owner.available_minutes_per_day
        kept: List[Task] = []
        for task in tasks:
            if task.duration_minutes <= budget:
                kept.append(task)
                budget -= task.duration_minutes
        return kept

    def detect_conflicts(self, plan: List[ScheduledItem]) -> List[ScheduledItem]:
        """Return the plan items that overlap at least one other item.

        Compares every pair (O(n^2)), so each conflicting item appears once,
        in plan order, however many items it collides with.
        """
        return [
            item for i, item in enumerate(plan)
            if any(item.overlaps(other) for j, other in enumerate(plan) if i != j)
        ]

    def conflict_warnings(self, plan: List[ScheduledItem]) -> List[str]:
        """Return one warning message per pair of overlapping items (empty if none).

        Lightweight check: it never raises or changes the plan. Items are sorted by
        start time, so each item is only compared with the ones that start before it ends.
        The inner loop stops at the first item that starts after the current one ends,
        which keeps the check close to O(n log n) when few items overlap.
        Each message comes from `_describe_conflict` and names both tasks, their
        times, and whether they belong to the same pet.
        """
        ordered = sorted(plan, key=lambda i: i.start_minutes)
        warnings: List[str] = []
        for i, first in enumerate(ordered):
            for second in ordered[i + 1:]:
                if second.start_minutes >= first.end_minutes:
                    break  # sorted by start, so nothing later can overlap either
                warnings.append(self._describe_conflict(first, second))
        return warnings

    def warn_for_task(self, task: Task, on_date: Optional[date] = None) -> List[str]:
        """Warn if a fixed-time task overlaps another fixed-time task due the same day.

        Meant to be called when a task is added, before building a full plan.

        Args:
            task: the task being added; floating tasks (no `scheduled_time`) return [].
            on_date: the day to check; defaults to the task's due date, then today.

        Returns one warning per overlapping fixed-time task. Never raises on a
        conflict and never changes any task.
        """
        if task.scheduled_time is None:
            return []
        day = on_date or task.due_date or date.today()
        mine = ScheduledItem(task, task.scheduled_time)
        return [
            self._describe_conflict(mine, theirs)
            for other in self.owner.get_all_tasks()
            if other is not task and other.scheduled_time is not None and other.is_due(day)
            for theirs in [ScheduledItem(other, other.scheduled_time)]
            if mine.overlaps(theirs)
        ]

    def explain_plan(self, plan: List[ScheduledItem], show_conflicts: bool = True) -> str:
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
        if show_conflicts:
            lines.extend(self.conflict_warnings(plan))
        if self.skipped:
            names = ", ".join(t.title for t in self.skipped)
            lines.append(f"Skipped (not enough time): {names}")
        return "\n".join(lines)

    @staticmethod
    def _describe_conflict(a: ScheduledItem, b: ScheduledItem) -> str:
        """Build the warning text for two overlapping items.

        The message shows each task's title, pet and time range, and says whether the
        overlap is for the same pet or different pets.
        """
        def label(item: ScheduledItem) -> str:
            pet = item.task.pet.name if item.task.pet else "?"
            # Plain arithmetic, not time(), so a task running past midnight can't raise.
            end = item.end_minutes
            return (f"'{item.task.title}' ({pet}, {item.start_time:%H:%M}-"
                    f"{end // 60:02d}:{end % 60:02d})")

        same_pet = a.task.pet is not None and a.task.pet is b.task.pet
        scope = f"same pet ({a.task.pet.name})" if same_pet else "different pets"
        return f"Warning: {label(a)} overlaps {label(b)} - {scope}"

    @staticmethod
    def _find_gap(busy: List[tuple], duration: int, day_start: int, day_end: int) -> Optional[int]:
        """Return the earliest start minute with a free gap of the given length, or None.

        Args:
            busy: (start, end) minute ranges already taken; need not be sorted.
            duration: minutes the new task needs.
            day_start, day_end: minute bounds the task must stay within.

        Sweeps the busy ranges in start order, moving a candidate start past each
        range it would collide with, and stops at the first gap that is long enough.
        Returns None if the task would run past `day_end`.
        """
        candidate = day_start
        for start, end in sorted(busy):
            if candidate + duration <= start:
                break
            candidate = max(candidate, end)
        return candidate if candidate + duration <= day_end else None

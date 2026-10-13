import os
import sys
from datetime import date, time

from pawpal_system import Owner, Pet, Priority, ScheduledItem, Scheduler, Task
from typing import List

from tabulate import tabulate

try:
    import colorama
except ImportError:  # colour on Windows is optional
    colorama = None


TYPE_EMOJI = {
    "exercise": "🦮",
    "feeding": "🍖",
    "meds": "💊",
    "health": "🩺",
    "grooming": "🛁",
    "enrichment": "🎾",
    "general": "🐾",
}
ESC = chr(27)
RED, GREEN, YELLOW = (f"{ESC}[{c}m" for c in (91, 92, 93))
RESET = f"{ESC}[0m"
PRIORITY_STYLE = {
    Priority.HIGH: ("🔴", RED),
    Priority.MEDIUM: ("🟡", YELLOW),
    Priority.LOW: ("🟢", GREEN),
}

if colorama:
    colorama.just_fix_windows_console()
# Only emit colour codes on a real terminal so piped output and tests stay plain text.
USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def paint(text: str, code: str) -> str:
    return f"{code}{text}{RESET}" if USE_COLOR else text


def task_icon(task: Task) -> str:
    return TYPE_EMOJI.get(task.category, TYPE_EMOJI["general"])


def priority_label(priority: Priority) -> str:
    emoji, code = PRIORITY_STYLE[priority]
    return f"{emoji} {paint(priority.name, code)}"


def status_label(task: Task) -> str:
    return paint("✅ done", GREEN) if task.completed else paint("⏳ pending", YELLOW)


def table(rows, headers) -> str:
    return tabulate(rows, headers=headers, tablefmt="rounded_grid")


def format_schedule(owner: Owner, scheduler: Scheduler, plan: List[ScheduledItem], on_date: date) -> str:
    used = sum(i.task.duration_minutes for i in plan)
    lines = [
        f"🐾 Today's Schedule for {owner.name} - {on_date:%A, %B %d}",
        f"⏱️  Budget: {used} of {owner.available_minutes_per_day} min used",
        "",
    ]

    rows = []
    for item in plan:
        # Plain arithmetic, not time(), so a task ending at or past midnight can't raise.
        end_min = item.end_minutes
        pet = item.task.pet.name if item.task.pet else "?"
        fixed = "📌" if item.task.scheduled_time is not None else ""
        rows.append((
            f"{item.start_time:%H:%M}-{end_min // 60:02d}:{end_min % 60:02d}",
            pet,
            f"{task_icon(item.task)} {item.task.title}",
            priority_label(item.task.priority),
            fixed,
        ))

    lines.append(table(rows, ("Time", "Pet", "Task", "Priority", "Fixed")))
    lines.append("📌 = fixed time")

    if scheduler.skipped:
        lines.append("")
        lines.append(paint("⏭️  Skipped (not enough time):", YELLOW))
        lines.extend(f"  - {task_icon(t)} {t.title} ({t.pet.name if t.pet else '?'}, {t.duration_minutes} min)"
                     for t in scheduler.skipped)

    warnings = scheduler.conflict_warnings(plan)
    if warnings:
        lines.append("")
        lines.extend(paint(f"⚠️  {w}", RED) for w in warnings)

    return "\n".join(lines)


def print_tasks(heading: str, tasks: List[Task]) -> None:
    print(f"📋 {heading}")
    if not tasks:
        print("  (none)\n")
        return
    rows = []
    for t in tasks:
        rows.append((
            f"{t.due_date:%b %d}" if t.due_date else "any day",
            f"{t.scheduled_time:%H:%M}" if t.scheduled_time else "flexible",
            t.pet.name if t.pet else "?",
            f"{task_icon(t)} {t.title}",
            f"🔁 {t.recurrence}" if t.recurrence else "-",
            status_label(t),
        ))
    print(table(rows, ("Due", "When", "Pet", "Task", "Repeats", "Status")))
    print()


def main() -> None:
    owner = Owner(name="Jordan", available_minutes_per_day=120)

    biscuit = Pet(name="Biscuit", species="Dog", breed="Golden Retriever", age=4)
    mia = Pet(name="Mia", species="Cat", breed="Siamese", age=2)
    owner.add_pet(biscuit)
    owner.add_pet(mia)

    # Added deliberately out of chronological order, and interleaved across pets.
    mia.add_task(Task("Medication", "meds", 5, Priority.HIGH,
                      scheduled_time=time(12, 30)))
    biscuit.add_task(Task("Grooming", "grooming", 45, Priority.LOW))
    biscuit.add_task(Task("Evening walk", "exercise", 25, Priority.MEDIUM,
                          scheduled_time=time(18, 0)))
    mia.add_task(Task("Play session", "enrichment", 20, Priority.MEDIUM))
    mia.add_task(Task("Feeding", "feeding", 10, Priority.HIGH,
                      scheduled_time=time(9, 0), recurrence="daily"))
    biscuit.add_task(Task("Morning walk", "exercise", 30, Priority.HIGH,
                          scheduled_time=time(8, 0), recurrence="daily"))

    biscuit.add_task(Task("Nail trim", "grooming", 15, Priority.LOW, recurrence="weekly"))

    scheduler = Scheduler(owner)

    # --- Conflict detection demo -------------------------------------------------
    # "Evening walk" (Biscuit) already runs 18:00-18:25. Adding each task below should
    # warn if it overlaps, and must never stop the program.
    print("🔍 Adding fixed-time tasks (checking for conflicts)")
    clashes = [
        # (pet, task, should it warn?)
        (biscuit, Task("Dinner", "feeding", 10, Priority.HIGH, scheduled_time=time(18, 0)), True),   # same time, same pet
        (mia, Task("Vet call", "health", 10, Priority.HIGH, scheduled_time=time(18, 0)), True),      # same time, different pets
        (biscuit, Task("Bath", "grooming", 15, Priority.HIGH, scheduled_time=time(18, 10)), True),   # partial overlap
        (mia, Task("Cuddles", "enrichment", 10, Priority.HIGH, scheduled_time=time(18, 25)), False), # starts as walk ends
    ]
    for pet, task, should_warn in clashes:
        pet.add_task(task)
        warnings = scheduler.warn_for_task(task)
        print(f"Added '{task.title}' for {pet.name} at {task.scheduled_time:%H:%M}:")
        for warning in warnings or ["(no conflict)"]:
            print(f"  {warning}")
        ok = bool(warnings) == should_warn
        verdict = paint("✅ OK", GREEN) if ok else paint("❌ UNEXPECTED", RED)
        print(f"  [{verdict}] expected {'a warning' if should_warn else 'no warning'}")
    print()

    print_tasks("Before completing anything", owner.get_all_tasks())

    # Complete a few tasks. Daily/weekly ones automatically spawn their next occurrence.
    for pet, title in [(mia, "Feeding"), (biscuit, "Morning walk"), (biscuit, "Nail trim")]:
        task = next(t for t in pet.tasks if t.title == title and not t.completed)
        follow_up = task.mark_complete()
        if follow_up:
            print(f"Completed '{title}' ({task.recurrence}) -> new one due {follow_up.due_date:%A, %b %d}")
        else:
            print(f"Completed '{title}' (one-off, nothing new)")
    print()

    # Completing a one-off task creates nothing.
    next(t for t in mia.tasks if t.title == "Medication").mark_complete()

    all_tasks = owner.get_all_tasks()

    print_tasks("All tasks, as added (out of order)", all_tasks)
    print_tasks("sort_by_time: all tasks", scheduler.sort_by_time(all_tasks))
    print_tasks("filter_tasks: pet_name='Mia'",
                scheduler.filter_tasks(all_tasks, pet_name="Mia"))
    print_tasks("filter_tasks: completed=True",
                scheduler.filter_tasks(all_tasks, completed=True))
    print_tasks("filter_tasks: completed=False, then sort_by_time",
                scheduler.sort_by_time(scheduler.filter_tasks(all_tasks, completed=False)))
    print_tasks("filter_tasks: pet_name='Biscuit', completed=False, then sort_by_time",
                scheduler.sort_by_time(
                    scheduler.filter_tasks(all_tasks, completed=False, pet_name="Biscuit")))
    print_tasks("filter_tasks: pet_name='Nobody' (expect none)",
                scheduler.filter_tasks(all_tasks, pet_name="Nobody"))

    today = date.today()
    plan = scheduler.generate_plan(today)
    print(format_schedule(owner, scheduler, plan, today))


if __name__ == "__main__":
    main()

from datetime import date, time

from pawpal_system import Owner, Pet, Priority, ScheduledItem, Scheduler, Task, _to_time
from typing import List


def format_schedule(owner: Owner, scheduler: Scheduler, plan: List[ScheduledItem], on_date: date) -> str:
    used = sum(i.task.duration_minutes for i in plan)
    lines = [
        f"Today's Schedule for {owner.name} - {on_date:%A, %B %d}",
        f"Budget: {used} of {owner.available_minutes_per_day} min used",
        "",
    ]

    rows = []
    for item in plan:
        end = _to_time(item.end_minutes)
        pet = item.task.pet.name if item.task.pet else "?"
        fixed = "*" if item.task.scheduled_time is not None else ""
        rows.append((
            f"{item.start_time:%H:%M}-{end:%H:%M}",
            pet,
            item.task.title,
            item.task.priority.name,
            fixed,
        ))

    headers = ("TIME", "PET", "TASK", "PRIORITY", "")
    widths = [max(len(str(r[c])) for r in [headers] + rows) for c in range(4)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths) + "  {}"
    lines.append(fmt.format(*headers).rstrip())
    lines.extend(fmt.format(*r).rstrip() for r in rows)
    lines.append("")
    lines.append("* = fixed time")

    if scheduler.skipped:
        lines.append("")
        lines.append("Skipped (not enough time):")
        lines.extend(f"  - {t.title} ({t.pet.name if t.pet else '?'}, {t.duration_minutes} min)"
                     for t in scheduler.skipped)

    conflicts = scheduler.detect_conflicts(plan)
    if conflicts:
        lines.append("")
        lines.append("Conflicts (overlapping times):")
        lines.extend(f"  - {i.task.title} at {i.start_time:%H:%M}" for i in conflicts)

    return "\n".join(lines)


def main() -> None:
    owner = Owner(name="Jordan", available_minutes_per_day=120)

    biscuit = Pet(name="Biscuit", species="Dog", breed="Golden Retriever", age=4)
    mia = Pet(name="Mia", species="Cat", breed="Siamese", age=2)
    owner.add_pet(biscuit)
    owner.add_pet(mia)

    biscuit.add_task(Task("Morning walk", "exercise", 30, Priority.HIGH,
                          scheduled_time=time(8, 0), recurrence="daily"))
    biscuit.add_task(Task("Grooming", "grooming", 45, Priority.LOW))
    mia.add_task(Task("Feeding", "feeding", 10, Priority.HIGH,
                      scheduled_time=time(9, 0), recurrence="daily"))
    mia.add_task(Task("Medication", "meds", 5, Priority.HIGH,
                      scheduled_time=time(12, 30)))
    mia.add_task(Task("Play session", "enrichment", 20, Priority.MEDIUM))

    scheduler = Scheduler(owner)
    today = date.today()
    plan = scheduler.generate_plan(today)

    print(format_schedule(owner, scheduler, plan, today))


if __name__ == "__main__":
    main()

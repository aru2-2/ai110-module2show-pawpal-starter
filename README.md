# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

The core logic lives in `pawpal_system.py`. `main.py` is a command-line demo that builds an owner with two pets and prints a formatted schedule. `tests/test_pawpal.py` holds the first tests. The design is in `diagrams/uml_draft.mmd`.

**Classes**

- **`Task`** (dataclass): one care activity with a title, category, duration, `Priority`, optional fixed time, optional recurrence (`daily` or `weekly`) and completion status. `mark_complete()` records the date, and `is_due(date)` decides whether the task applies on a given day.
- **`Pet`** (dataclass): pet details plus a list of tasks. `add_task()` also sets `task.pet`, so every task knows which pet it belongs to.
- **`Owner`** (dataclass): holds the pets and the daily time budget. `get_all_tasks()` returns every pet's tasks in one list.
- **`ScheduledItem`** (dataclass): one entry in the plan, made of a task, a start time and the reason it was placed there. It can check whether it overlaps another item.
- **`Priority`**: an `IntEnum` (`LOW`, `MEDIUM`, `HIGH`) so priorities sort correctly.
- **`Scheduler`**: the planner. It reads tasks through `Owner.get_all_tasks()`, so one plan covers all pets.

**How they work together**

1. `Owner` holds many `Pet`s, and each `Pet` holds many `Task`s.
2. `Scheduler.generate_plan(date)` collects all tasks through the owner and keeps the ones that are due that day.
3. It sorts them by priority, then fixed time, then shortest first.
4. It trims the list to fit the owner's daily minutes. A task that no longer fits is skipped, and smaller ones can still fit.
5. Tasks with a fixed time are placed first. The rest take the earliest open gap between 08:00 and 21:00.
6. The result is a time-ordered list of `ScheduledItem`s. `detect_conflicts()` flags overlapping items, and `explain_plan()` describes the plan along with conflicts and skipped tasks.

**Run it**

```bash
python main.py          # print a sample schedule
python -m pytest        # run the tests
```

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Today's Schedule for Jordan - Monday, October 12
Budget: 110 of 120 min used

TIME         PET      TASK          PRIORITY
08:00-08:30  Biscuit  Morning walk  HIGH      *
08:30-08:50  Mia      Play session  MEDIUM
09:00-09:10  Mia      Feeding       HIGH      *
09:10-09:55  Biscuit  Grooming      LOW
12:30-12:35  Mia      Medication    HIGH      *
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()`, `Scheduler.sort_by_time()` | Priority order for planning; clock order for display |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.filter_by_time()` | By completion status or pet name; by daily time budget |
| Conflict handling | `Scheduler.conflict_warnings()`, `Scheduler.warn_for_task()`, `Scheduler.detect_conflicts()` | Overlapping time windows are warned about, never auto-fixed |
| Recurring tasks | `Task.mark_complete()`, `Task.is_due()` | Daily and weekly tasks spawn their next occurrence |

### Sorting

- **`Scheduler.sort_tasks(tasks)`** orders tasks for planning: highest priority first, then earlier fixed time (tasks without one come after), then shortest duration. `generate_plan()` uses it before placing anything.
- **`Scheduler.sort_by_time(tasks)`** orders tasks by `scheduled_time`, earliest first, with unscheduled tasks last. It ignores priority and is stable, so tied tasks keep their original order. Use it to show a pet's tasks in clock order.

Both return a new list and leave the input unchanged.

### Filtering

- **`Scheduler.filter_tasks(tasks, completed=None, pet_name=None)`** keeps tasks that match the given completion status and/or pet name. `None` means "any". Pet names are matched case-insensitively and ignore surrounding whitespace. When both filters are given, a task must match both.
- **`Scheduler.filter_by_time(tasks)`** is the budget filter used inside `generate_plan()`. It walks the sorted list and keeps each task that still fits in the owner's remaining daily minutes. A task that is too long is dropped, but later shorter ones can still fit. It is greedy and does not search for the best combination.

### Conflict detection

Two items conflict when their time windows overlap. `ScheduledItem.overlaps()` compares half-open windows `[start, end)`, so back-to-back tasks do not conflict, and it checks duration, not only matching start times.

- **`Scheduler.conflict_warnings(plan)`** returns one message per overlapping pair, naming both tasks, their times, and whether they belong to the same pet or different pets. It sorts by start time and stops comparing early, so it is cheap on a typical day.
- **`Scheduler.warn_for_task(task, on_date)`** is a lightweight check for use when a task is added. It compares a fixed-time task with the other fixed-time tasks due that day. Floating tasks return no warnings.
- **`Scheduler.detect_conflicts(plan)`** returns the plan items that overlap at least one other item, for code that needs the items rather than messages.

**Tradeoff:** the scheduler warns but does not resolve. Fixed-time tasks stay where the user put them, even if they overlap, and `explain_plan()` prints the warnings. Floating tasks are placed by `_find_gap()` into free time only, so they never overlap anything.

### Recurring tasks

- **`Task.mark_complete(on_date)`** marks the task done and records the date. For a `daily` or `weekly` task it also creates a copy with `completed=False` and a `due_date` of the completion date plus 1 or 7 days. The copy is added to the same pet and returned. One-off tasks, and tasks that were already complete, return `None`, so completing twice does not create duplicates.
- **`Task.is_due(on_date)`** returns `True` only for unfinished tasks whose `due_date` has arrived (or is unset). The new copy therefore stays out of the plan until its next occurrence.

An unknown `recurrence` value raises `ValueError` rather than being ignored. The supported values and their intervals are in `RECURRENCE_DAYS`.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

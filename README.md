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

## Features

- **Priority-based ordering.** `sort_tasks` ranks tasks by priority (high to low), then by earlier fixed time, then by shorter duration. This ordering decides which tasks get scheduled first when time is tight.
- **Sorting by time.** `sort_by_time` orders tasks by their scheduled time, earliest first, with flexible tasks last. The sort is stable, so tasks with equal times keep their original order. The task table in the app uses it.
- **Filtering by pet and status.** `filter_tasks` filters by pet name (case-insensitive, whitespace-trimmed) and by completed or pending status. The two filters can be combined.
- **Daily and weekly recurrence.** Completing a daily or weekly task creates a new copy for the same pet, due 1 day (daily) or 7 days (weekly) after the completion date. The copy stays out of the plan until its due date. One-off tasks create nothing, completing an already-completed task does not create a duplicate, and an unknown recurrence value raises a `ValueError`.
- **Daily time budget.** `filter_by_time` walks the priority-sorted list and keeps each task that still fits in the owner's available minutes. It is greedy: a task that is too long is skipped, but later, shorter tasks can still fit. It does not search for the best combination.
- **Fixed-time and flexible scheduling.** Tasks with a fixed start time are placed at that time first. Flexible tasks go into the earliest free gap between 08:00 and 21:00, found by sweeping the busy ranges. A flexible task with no gap is skipped.
- **Conflict warnings.** `conflict_warnings` reports each overlapping pair using half-open time windows, so back-to-back tasks are not flagged. Each warning names both tasks, their time ranges, and whether they belong to the same pet or to different pets. The check sorts by start time and stops comparing early, so it is fast when few tasks overlap (worst case, if everything overlaps, it is still O(n²)). It only warns and never blocks or changes the plan.
- **Conflict check on task entry.** `warn_for_task` checks a new fixed-time task against other fixed-time tasks due that day. The app shows a warning with fix suggestions, and the task is still added.
- **Plan explanations.** Each scheduled item includes a reason, such as its priority and whether it was fixed or placed in the first open slot. Tasks that did not fit are listed as skipped.
- **Multi-pet support.** An owner can have several pets, and the scheduler plans across all of their tasks together.

**Current limits:** the Streamlit app does not yet let you set a recurrence (daily and weekly recurrence is exercised in `main.py` and the tests). Fixed-time tasks are not restricted to the 08:00-21:00 window, and they can overlap each other, which is only reported as a warning.

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

Run the full test suite from the project root:

```bash
python -m pytest
```

### What the tests cover

The 50 tests in `tests/test_pawpal.py` exercise the scheduling logic in `pawpal_system.py` (plus `format_schedule` in `main.py`). Each area has happy-path and edge-case tests:

- **Sorting correctness:** `sort_by_time` returns tasks in chronological order (unscheduled tasks last, midnight first, stable for equal times). `sort_tasks` orders by priority, then fixed time, then duration. Neither sort changes its input, and both handle an empty list. `generate_plan` output is always in chronological order.
- **Recurrence logic:** completing a daily task creates a new task for the next day, and a weekly task creates one 7 days later. Edge cases: one-off tasks spawn nothing, double-completion doesn't duplicate or overwrite the completion date, chains of completions, month/year rollover, late completion, tasks with no pet, and unknown recurrence values.
- **Conflict detection:** tasks at the exact same time are flagged, for the same pet and across pets. Edge cases: back-to-back tasks are not conflicts, a one-minute overlap is, containment and three-way overlaps give the right number of warnings, and tasks running past midnight don't crash.
- **Planning and filtering:** the daily time budget (an over-budget task is skipped, shorter ones still fit), floating tasks placed around fixed ones, filtering by completion status and pet name (case and whitespace insensitive), and empty cases such as a pet with no tasks or an owner with no pets.

### Sample test output

```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Arushi\Downloads\ai110-module2show-pawpal-starter
collected 50 items

tests\test_pawpal.py ..................................................  [100%]

============================= 50 passed in 0.07s ==============================
```

### Confidence Level: ⭐⭐⭐⭐ (4 out of 5)

All 50 tests pass, and writing them found and fixed two real bugs (a crash for tasks ending at midnight, and an overwritten completion date). I'm confident in sorting, recurrence and conflict detection. I stopped at 4 stars because some areas are still untested: the Streamlit UI in `app.py`, input validation (zero or negative durations), fixed-time tasks outside the 08:00-21:00 day window, and the fact that recurrence is counted from the completion date rather than the original due date.

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

Start the app with `streamlit run app.py`. It is a single page that runs top to bottom.

### Main UI features

- **Owner and pet setup:** enter the owner's name, the minutes available per day, and a pet's name and species, then click **Add pet**. Adding the same pet name twice shows a warning. Several pets can be added.
- **Add a task:** choose a pet, then enter a title, duration (1-240 min) and priority (low, medium, high). Tick **Fix this task at a specific time** to pick a start time, or leave it unticked to let PawPal+ place the task.
- **Instant conflict feedback:** if a new fixed-time task overlaps another fixed-time task, a warning lists the clash and suggests a fix. The task is still added.
- **Mark complete:** pick a pending task and click **Mark complete**. Completed tasks are kept and shown as completed.
- **Task table with filters:** filter by pet and by status (all, pending, completed). The table is sorted by time, with flexible tasks last.
- **Generate schedule:** builds today's plan and shows a table of time range, pet, task, minutes, priority and the reason each task was placed. It also lists any conflicts and any tasks that were skipped for lack of time.

### Example workflow

1. Set the owner to "Jordan" with 120 minutes per day, enter the pet "Mochi", and click **Add pet**.
2. Add "Morning walk" (30 min, high) fixed at 08:00. The success message appears.
3. Add "Brush teeth" (10 min, medium) as a flexible task, then add "Vet call" (10 min, high) fixed at 08:15. The second fixed task overlaps the walk, so a conflict warning appears.
4. Use **Filter by pet** and **Filter by status** to narrow the task table, which stays in clock order.
5. Click **Generate schedule**. The table shows each task with its reason, the "Brush teeth" task in the first free slot, and a conflict warning for the walk and the vet call.
6. Mark "Morning walk" complete, then generate the schedule again. The walk is no longer due, so it leaves the plan and the conflict warning disappears.

### Scheduler behaviors on display

- **Sorting:** the task table is in clock order (`sort_by_time`), while the plan picks tasks in priority order (`sort_tasks`).
- **Filtering:** by pet and status, and by the daily time budget, where a task that does not fit is listed as skipped.
- **Conflict warnings:** overlapping fixed-time tasks are reported at entry and again in the plan. Back-to-back tasks are not conflicts.
- **Flexible placement:** floating tasks fill the earliest free gap between 08:00 and 21:00.
- **Recurring tasks:** completing a daily or weekly task creates the next one, due 1 or 7 days later. This is not selectable in the app yet, so it is shown in the CLI demo below.

### Sample CLI output

Excerpts from `python main.py` (run on Tuesday, October 13; long task listings are shortened with `...`):

```
== Adding fixed-time tasks (checking for conflicts) ==
Added 'Dinner' for Biscuit at 18:00:
  Warning: 'Dinner' (Biscuit, 18:00-18:10) overlaps 'Evening walk' (Biscuit, 18:00-18:25) - same pet (Biscuit)
  [OK] expected a warning
Added 'Vet call' for Mia at 18:00:
  Warning: 'Vet call' (Mia, 18:00-18:10) overlaps 'Evening walk' (Biscuit, 18:00-18:25) - different pets
  Warning: 'Vet call' (Mia, 18:00-18:10) overlaps 'Dinner' (Biscuit, 18:00-18:10) - different pets
  [OK] expected a warning
Added 'Bath' for Biscuit at 18:10:
  Warning: 'Bath' (Biscuit, 18:10-18:25) overlaps 'Evening walk' (Biscuit, 18:00-18:25) - same pet (Biscuit)
  [OK] expected a warning
Added 'Cuddles' for Mia at 18:25:
  (no conflict)
  [OK] expected no warning

Completed 'Feeding' (daily) -> new one due Wednesday, Oct 14
Completed 'Morning walk' (daily) -> new one due Wednesday, Oct 14
Completed 'Nail trim' (weekly) -> new one due Tuesday, Oct 20

== filter_tasks: completed=False, then sort_by_time ==
  Oct 14   08:00     Biscuit   Morning walk    daily    pending
  Oct 14   09:00     Mia       Feeding         daily    pending
  any day  18:00     Biscuit   Evening walk    -        pending
  ...
  any day  flexible  Biscuit   Grooming        -        pending
  Oct 20   flexible  Biscuit   Nail trim       weekly   pending
  any day  flexible  Mia       Play session    -        pending

== filter_tasks: pet_name='Nobody' (expect none) ==
  (none)

Today's Schedule for Jordan - Tuesday, October 13
Budget: 90 of 120 min used

TIME         PET      TASK          PRIORITY
08:00-08:20  Mia      Play session  MEDIUM
18:00-18:10  Biscuit  Dinner        HIGH      *
18:00-18:10  Mia      Vet call      HIGH      *
18:00-18:25  Biscuit  Evening walk  MEDIUM    *
18:10-18:25  Biscuit  Bath          HIGH      *
18:25-18:35  Mia      Cuddles       HIGH      *

* = fixed time

Skipped (not enough time):
  - Grooming (Biscuit, 45 min)

Warning: 'Dinner' (Biscuit, 18:00-18:10) overlaps 'Vet call' (Mia, 18:00-18:10) - different pets
Warning: 'Dinner' (Biscuit, 18:00-18:10) overlaps 'Evening walk' (Biscuit, 18:00-18:25) - same pet (Biscuit)
Warning: 'Vet call' (Mia, 18:00-18:10) overlaps 'Evening walk' (Biscuit, 18:00-18:25) - different pets
Warning: 'Evening walk' (Biscuit, 18:00-18:25) overlaps 'Bath' (Biscuit, 18:10-18:25) - same pet (Biscuit)
```

In this run, "Cuddles" starts exactly as the evening walk ends, so it is not flagged. The daily and weekly tasks that were completed today are not in the plan, and their next occurrences are not due yet. "Grooming" is skipped because 45 minutes no longer fits in the remaining budget.

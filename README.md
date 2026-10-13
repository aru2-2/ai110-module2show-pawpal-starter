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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

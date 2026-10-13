from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")


TYPE_EMOJI = {
    "exercise": "🦮", "feeding": "🍖", "meds": "💊", "health": "🩺",
    "grooming": "🛁", "enrichment": "🎾", "general": "🐾",
}
PRIORITY_EMOJI = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}


def task_label(task):
    return f"{TYPE_EMOJI.get(task.category, TYPE_EMOJI['general'])} {task.title}"


def priority_label(task):
    return f"{PRIORITY_EMOJI[task.priority.name]} {task.priority.name.lower()}"


def status_label(task):
    return "✅ completed" if task.completed else "⏳ pending"


def show_conflicts(warnings):
    """Show all conflicts in one warning: what clashes, then how to fix it."""
    count = len(warnings)
    lines = "\n".join(f"- {w.removeprefix('Warning: ')}" for w in warnings)
    st.warning(
        f"**{count} scheduling conflict{'s' if count != 1 else ''} found**\n\n"
        f"{lines}\n\n"
        "**To fix:** move one of the tasks to a different start time, or make it "
        "flexible so PawPal+ can place it in a free slot. Tasks for different pets "
        "can overlap if you can care for both at once.",
        icon="⚠️",
    )

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner and Pet")
owner_name = st.text_input("Owner name", value="Jordan")
available = st.number_input("Minutes available per day", min_value=10, max_value=600, value=120)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# The session_state "vault": only create the Owner on the first run of this session.
# On every later rerun the key already exists, so the same Owner (with its pets) is reused.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes_per_day=int(available))
owner = st.session_state.owner
owner.name = owner_name
owner.available_minutes_per_day = int(available)

if st.button("Add pet"):
    if any(p.name == pet_name for p in owner.pets):
        st.warning(f"{pet_name} is already added.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species))

if owner.pets:
    st.write("Pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))

st.markdown("### Tasks")

if not owner.pets:
    st.info("Add a pet before adding tasks.")
else:
    task_pet_name = st.selectbox("Pet for this task", [p.name for p in owner.pets])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        category = st.selectbox(
            "Type", list(TYPE_EMOJI), format_func=lambda c: f"{TYPE_EMOJI[c]} {c}"
        )
    with col3:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col4:
        priority = st.selectbox(
            "Priority", ["low", "medium", "high"], index=2,
            format_func=lambda p: f"{PRIORITY_EMOJI[p.upper()]} {p}",
        )
    fixed_time = st.checkbox("Fix this task at a specific time")
    start_at = st.time_input("Start time", value=time(8, 0), disabled=not fixed_time)

if owner.pets and st.button("Add task"):
    pet = next(p for p in owner.pets if p.name == task_pet_name)
    new_task = Task(
        title=task_title,
        category=category,
        duration_minutes=int(duration),
        priority=Priority[priority.upper()],
        scheduled_time=start_at if fixed_time else None,
    )
    pet.add_task(new_task)
    # Warn about clashes with other fixed-time tasks; the task is still added.
    clashes = Scheduler(owner).warn_for_task(new_task)
    if clashes:
        show_conflicts(clashes)
    else:
        st.success(f"Added '{new_task.title}' for {pet.name}.")

all_tasks = owner.get_all_tasks()
if all_tasks:
    # Runs before the table is built so a click is reflected on the same rerun.
    pending = [t for t in all_tasks if not t.completed]
    if pending:
        ccol1, ccol2 = st.columns([3, 1], vertical_alignment="bottom")
        with ccol1:
            to_complete = st.selectbox(
                "Mark a task complete",
                pending,
                format_func=lambda t: f"{t.pet.name}: {task_label(t)}",
            )
        with ccol2:
            if st.button("Mark complete"):
                # Daily/weekly tasks add their next occurrence to the pet automatically.
                to_complete.mark_complete()
                st.rerun()

    fcol1, fcol2 = st.columns(2)
    with fcol1:
        pet_filter = st.selectbox("Filter by pet", ["All pets"] + [p.name for p in owner.pets])
    with fcol2:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])

    scheduler = Scheduler(owner)
    shown_tasks = scheduler.filter_tasks(
        all_tasks,
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
        pet_name=None if pet_filter == "All pets" else pet_filter,
    )

    st.write("Current tasks (earliest first, unscheduled last):")
    if not shown_tasks:
        st.info("No tasks match these filters.")
    st.table(
        [
            {
                "pet": t.pet.name,
                "due": f"{t.due_date:%b %d}" if t.due_date else "any day",
                "time": f"{t.scheduled_time:%H:%M}" if t.scheduled_time else "flexible",
                "title": task_label(t),
                "duration_minutes": t.duration_minutes,
                "priority": priority_label(t),
                "status": status_label(t),
            }
            for t in scheduler.sort_by_time(shown_tasks)
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())
    warnings = scheduler.conflict_warnings(plan)

    if not plan:
        st.info("Nothing is due today, so there is nothing to schedule.")
    else:
        total = sum(i.task.duration_minutes for i in plan)
        if warnings:
            show_conflicts(warnings)
        else:
            st.success(
                f"Schedule ready: {len(plan)} task(s), {total} of "
                f"{owner.available_minutes_per_day} available minutes, no conflicts."
            )
        st.table(
            [
                {
                    "time": f"{i.start_time:%H:%M}-{i.end_minutes // 60:02d}:{i.end_minutes % 60:02d}",
                    "pet": i.task.pet.name if i.task.pet else "?",
                    "task": task_label(i.task),
                    "minutes": i.task.duration_minutes,
                    "priority": priority_label(i.task),
                    "why": i.reason,
                }
                for i in plan
            ]
        )
    if scheduler.skipped:
        st.warning(
            "Not enough time today for: "
            + ", ".join(f"{task_label(t)} ({t.pet.name if t.pet else '?'})" for t in scheduler.skipped)
            + ". Raise the daily minutes or lower another task's priority."
        )

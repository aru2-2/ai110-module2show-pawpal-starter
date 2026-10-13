from datetime import time

from pawpal_system import Owner, Pet, ScheduledItem, Scheduler, Task


def test_mark_complete_changes_task_status():
    task = Task(title="Morning walk", category="exercise", duration_minutes=30)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Biscuit", species="Dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Feeding", category="feeding", duration_minutes=10))

    assert len(pet.tasks) == 1


def test_sort_by_time_orders_earliest_first_with_unscheduled_last():
    scheduler = Scheduler(Owner(name="Sam", available_minutes_per_day=120))
    evening = Task("Evening walk", "exercise", 20, scheduled_time=time(18, 0))
    floating = Task("Brush fur", "grooming", 10)
    morning = Task("Feeding", "feeding", 10, scheduled_time=time(8, 30))

    result = scheduler.sort_by_time([evening, floating, morning])

    assert result == [morning, evening, floating]


def test_sort_by_time_keeps_original_order_for_equal_times():
    scheduler = Scheduler(Owner(name="Sam", available_minutes_per_day=120))
    first = Task("Meds", "health", 5, scheduled_time=time(9, 0))
    second = Task("Water", "feeding", 5, scheduled_time=time(9, 0))

    assert scheduler.sort_by_time([first, second]) == [first, second]


def _owner_with_two_pets():
    owner = Owner(name="Sam", available_minutes_per_day=120)
    biscuit, mochi = Pet("Biscuit", "Dog"), Pet("Mochi", "Cat")
    walk = Task("Walk", "exercise", 30)
    feed = Task("Feed", "feeding", 10)
    brush = Task("Brush", "grooming", 15)
    biscuit.add_task(walk)
    biscuit.add_task(feed)
    mochi.add_task(brush)
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    feed.mark_complete()
    return owner, walk, feed, brush


def test_filter_tasks_by_completion_status():
    owner, walk, feed, brush = _owner_with_two_pets()
    scheduler = Scheduler(owner)
    tasks = owner.get_all_tasks()

    assert scheduler.filter_tasks(tasks, completed=True) == [feed]
    assert scheduler.filter_tasks(tasks, completed=False) == [walk, brush]


def test_filter_tasks_by_pet_name_and_combined():
    owner, walk, feed, brush = _owner_with_two_pets()
    scheduler = Scheduler(owner)
    tasks = owner.get_all_tasks()

    assert scheduler.filter_tasks(tasks, pet_name="Biscuit") == [walk, feed]
    assert scheduler.filter_tasks(tasks, completed=False, pet_name="Biscuit") == [walk]
    assert scheduler.filter_tasks(tasks, pet_name="Nobody") == []


def test_filter_tasks_without_criteria_returns_everything():
    owner, *_ = _owner_with_two_pets()
    tasks = owner.get_all_tasks()

    assert Scheduler(owner).filter_tasks(tasks) == tasks


def test_filter_tasks_pet_name_ignores_case():
    owner, walk, feed, brush = _owner_with_two_pets()
    scheduler = Scheduler(owner)
    tasks = owner.get_all_tasks()

    assert scheduler.filter_tasks(tasks, pet_name="biscuit") == [walk, feed]
    assert scheduler.filter_tasks(tasks, pet_name="MOCHI") == [brush]


def test_filter_tasks_pet_name_ignores_surrounding_whitespace():
    owner, walk, feed, brush = _owner_with_two_pets()
    scheduler = Scheduler(owner)
    tasks = owner.get_all_tasks()

    assert scheduler.filter_tasks(tasks, pet_name="  Biscuit ") == [walk, feed]
    assert scheduler.filter_tasks(tasks, pet_name="\tmochi\n") == [brush]


# ---- recurring tasks ----
from datetime import date, timedelta


def _recurring(recurrence, **kwargs):
    pet = Pet("Biscuit", "Dog")
    task = Task("Walk", "exercise", 30, recurrence=recurrence, **kwargs)
    pet.add_task(task)
    return pet, task


def test_completing_daily_task_creates_next_day_instance():
    pet, task = _recurring("daily", scheduled_time=time(8, 0))

    new = task.mark_complete(on_date=date(2026, 10, 13))

    assert task.completed is True
    assert new is not task
    assert new.due_date == date(2026, 10, 14)
    assert new.completed is False and new.last_completed is None
    assert (new.title, new.duration_minutes, new.recurrence, new.scheduled_time) == \
        ("Walk", 30, "daily", time(8, 0))
    assert new.pet is pet and pet.tasks == [task, new]


def test_completing_weekly_task_creates_instance_seven_days_later():
    pet, task = _recurring("weekly")

    new = task.mark_complete(on_date=date(2026, 10, 13))

    assert new.due_date == date(2026, 10, 20)
    assert len(pet.tasks) == 2


def test_completing_one_off_task_creates_nothing():
    pet = Pet("Biscuit", "Dog")
    task = Task("Vet visit", "health", 60)
    pet.add_task(task)

    assert task.mark_complete() is None
    assert pet.tasks == [task]


def test_completing_a_recurring_task_twice_does_not_duplicate_it():
    pet, task = _recurring("daily")

    task.mark_complete(on_date=date(2026, 10, 13))
    assert task.mark_complete(on_date=date(2026, 10, 13)) is None

    assert len(pet.tasks) == 2


def test_recurring_task_without_a_pet_still_returns_next_instance():
    task = Task("Walk", "exercise", 30, recurrence="daily")

    new = task.mark_complete(on_date=date(2026, 10, 13))

    assert new.due_date == date(2026, 10, 14) and new.pet is None


def test_next_instance_is_not_due_until_its_date():
    pet, task = _recurring("daily")
    new = task.mark_complete(on_date=date(2026, 10, 13))

    assert task.is_due(date(2026, 10, 14)) is False
    assert new.is_due(date(2026, 10, 13)) is False
    assert new.is_due(date(2026, 10, 14)) is True
    assert new.is_due(date(2026, 10, 20)) is True  # still due if left undone


def test_plan_skips_future_occurrence_and_includes_it_when_due():
    owner = Owner("Sam", 120)
    pet, task = _recurring("daily")
    owner.add_pet(pet)
    today = date(2026, 10, 13)
    task.mark_complete(on_date=today)
    scheduler = Scheduler(owner)

    assert scheduler.generate_plan(today) == []
    assert [i.task.title for i in scheduler.generate_plan(today + timedelta(days=1))] == ["Walk"]


def test_unknown_recurrence_is_rejected():
    task = Task("Walk", "exercise", 30, recurrence="monthly")

    for call in (task.mark_complete, lambda: task.is_due(date(2026, 10, 13))):
        try:
            call()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---- conflict warnings ----
def _plan_item(pet, title, start, minutes):
    task = Task(title, "general", minutes, scheduled_time=start)
    pet.add_task(task)
    return ScheduledItem(task, start)


def test_conflict_warnings_same_pet_and_different_pets():
    scheduler = Scheduler(Owner("Sam", 120))
    biscuit, mia = Pet("Biscuit", "Dog"), Pet("Mia", "Cat")
    walk = _plan_item(biscuit, "Walk", time(9, 0), 30)
    bath = _plan_item(biscuit, "Bath", time(9, 15), 20)
    feed = _plan_item(mia, "Feed", time(9, 0), 10)  # ends 09:10, before Bath starts

    warnings = scheduler.conflict_warnings([bath, feed, walk])  # order shouldn't matter

    assert len(warnings) == 2
    assert any("'Walk'" in w and "'Feed'" in w and "different pets" in w for w in warnings)
    assert any("'Walk'" in w and "'Bath'" in w and "same pet (Biscuit)" in w for w in warnings)


def test_back_to_back_and_separate_items_do_not_conflict():
    scheduler = Scheduler(Owner("Sam", 120))
    pet = Pet("Biscuit", "Dog")
    first = _plan_item(pet, "Walk", time(9, 0), 30)
    second = _plan_item(pet, "Feed", time(9, 30), 10)  # starts exactly when Walk ends

    assert scheduler.conflict_warnings([first, second]) == []
    assert scheduler.conflict_warnings([]) == []


def test_conflict_warning_does_not_raise_for_task_running_past_midnight():
    scheduler = Scheduler(Owner("Sam", 120))
    pet = Pet("Biscuit", "Dog")
    late = _plan_item(pet, "Late walk", time(23, 50), 30)
    later = _plan_item(pet, "Late feed", time(23, 55), 5)

    (warning,) = scheduler.conflict_warnings([late, later])

    assert "23:50-24:20" in warning


def test_generate_plan_reports_clashing_fixed_tasks_without_crashing():
    owner = Owner("Sam", 120)
    biscuit, mia = Pet("Biscuit", "Dog"), Pet("Mia", "Cat")
    owner.add_pet(biscuit)
    owner.add_pet(mia)
    biscuit.add_task(Task("Walk", "exercise", 30, scheduled_time=time(9, 0)))
    mia.add_task(Task("Meds", "meds", 5, scheduled_time=time(9, 0)))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(date(2026, 10, 13))

    assert len(plan) == 2
    assert len(scheduler.conflict_warnings(plan)) == 1
    assert "Warning:" in scheduler.explain_plan(plan)
    assert "Warning:" not in scheduler.explain_plan(plan, show_conflicts=False)


def test_warn_for_task_flags_overlap_with_existing_fixed_task():
    owner = Owner("Sam", 120)
    pet = Pet("Biscuit", "Dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", "exercise", 30, scheduled_time=time(9, 0)))
    scheduler = Scheduler(owner)
    day = date(2026, 10, 13)

    clash = Task("Bath", "grooming", 15, scheduled_time=time(9, 20))
    clear = Task("Dinner", "feeding", 10, scheduled_time=time(18, 0))
    floating = Task("Play", "enrichment", 20)

    assert len(scheduler.warn_for_task(clash, day)) == 1
    assert scheduler.warn_for_task(clear, day) == []
    assert scheduler.warn_for_task(floating, day) == []


def test_warn_for_task_ignores_completed_and_future_tasks():
    owner = Owner("Sam", 120)
    pet = Pet("Biscuit", "Dog")
    owner.add_pet(pet)
    done = Task("Walk", "exercise", 30, scheduled_time=time(9, 0))
    future = Task("Brush", "grooming", 30, scheduled_time=time(9, 0), due_date=date(2026, 10, 20))
    pet.add_task(done)
    pet.add_task(future)
    done.mark_complete(on_date=date(2026, 10, 12))
    new = Task("Bath", "grooming", 15, scheduled_time=time(9, 10))

    assert Scheduler(owner).warn_for_task(new, date(2026, 10, 13)) == []

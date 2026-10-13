from datetime import time

from pawpal_system import Owner, Pet, Priority, ScheduledItem, Scheduler, Task


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


# ---- sorting: happy paths and edge cases ----
def test_sort_tasks_orders_by_priority_then_fixed_time_then_duration():
    scheduler = Scheduler(Owner("Sam", 120))
    low = Task("Brush", "grooming", 5, Priority.LOW, scheduled_time=time(7, 0))
    high_floating = Task("Meds", "meds", 5, Priority.HIGH)
    high_fixed = Task("Feed", "feeding", 20, Priority.HIGH, scheduled_time=time(9, 0))
    med_long = Task("Walk", "exercise", 40, Priority.MEDIUM)
    med_short = Task("Play", "enrichment", 10, Priority.MEDIUM)

    result = scheduler.sort_tasks([low, med_long, high_floating, med_short, high_fixed])

    assert result == [high_fixed, high_floating, med_short, med_long, low]


def test_sorting_does_not_mutate_input_and_handles_empty_list():
    scheduler = Scheduler(Owner("Sam", 120))
    later = Task("Walk", "exercise", 30, scheduled_time=time(18, 0))
    earlier = Task("Feed", "feeding", 10, scheduled_time=time(8, 0))
    original = [later, earlier]

    assert scheduler.sort_by_time(original) == [earlier, later]
    assert scheduler.sort_tasks(original) == [earlier, later]
    assert original == [later, earlier]
    assert scheduler.sort_by_time([]) == [] and scheduler.sort_tasks([]) == []


def test_sort_by_time_puts_midnight_first():
    scheduler = Scheduler(Owner("Sam", 120))
    midnight = Task("Night meds", "meds", 5, scheduled_time=time(0, 0))
    morning = Task("Feed", "feeding", 10, scheduled_time=time(8, 0))
    floating = Task("Play", "enrichment", 20)

    assert scheduler.sort_by_time([floating, morning, midnight]) == [midnight, morning, floating]


def test_sort_by_time_works_across_pets():
    owner, walk, feed, brush = _owner_with_two_pets()
    walk.scheduled_time = time(17, 0)
    brush.scheduled_time = time(7, 30)

    result = Scheduler(owner).sort_by_time(owner.get_all_tasks())

    assert result == [brush, walk, feed]  # feed has no time, so it goes last


def test_generate_plan_is_in_chronological_order():
    owner = Owner("Sam", 240)
    pet = Pet("Biscuit", "Dog")
    owner.add_pet(pet)
    pet.add_task(Task("Dinner", "feeding", 10, Priority.LOW, scheduled_time=time(18, 0)))
    pet.add_task(Task("Brush", "grooming", 15, Priority.HIGH))
    pet.add_task(Task("Walk", "exercise", 30, Priority.MEDIUM, scheduled_time=time(9, 0)))
    pet.add_task(Task("Play", "enrichment", 20, Priority.MEDIUM))

    plan = Scheduler(owner).generate_plan(date(2026, 10, 13))

    starts = [i.start_minutes for i in plan]
    assert len(plan) == 4
    assert starts == sorted(starts)


# ---- pets with no tasks ----
def test_pet_with_no_tasks_produces_empty_plan():
    owner = Owner("Sam", 120)
    owner.add_pet(Pet("Biscuit", "Dog"))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(date(2026, 10, 13))

    assert owner.get_all_tasks() == []
    assert plan == [] and scheduler.skipped == []
    assert scheduler.explain_plan(plan) == "No tasks to schedule."
    assert scheduler.conflict_warnings(plan) == []


def test_owner_with_no_pets_produces_empty_plan():
    scheduler = Scheduler(Owner("Sam", 120))

    assert scheduler.generate_plan(date(2026, 10, 13)) == []


# ---- recurrence: happy path and edge cases ----
def test_marking_daily_task_complete_creates_task_for_following_day():
    pet = Pet("Biscuit", "Dog")
    task = Task("Feed", "feeding", 10, recurrence="daily")
    pet.add_task(task)

    new = task.mark_complete(on_date=date(2026, 10, 13))

    assert new.due_date == date(2026, 10, 14)
    assert new in pet.tasks and not new.completed


def test_daily_recurrence_chains_one_pending_task_at_a_time():
    pet, task = _recurring("daily")
    current = task
    for day in (13, 14, 15):
        current = current.mark_complete(on_date=date(2026, 10, day))
        assert current.due_date == date(2026, 10, day + 1)

    assert len(pet.tasks) == 4
    assert pet.get_pending_tasks() == [current]


def test_recurrence_rolls_over_month_and_year():
    _, task = _recurring("daily")
    assert task.mark_complete(on_date=date(2026, 12, 31)).due_date == date(2027, 1, 1)

    _, weekly = _recurring("weekly")
    assert weekly.mark_complete(on_date=date(2027, 2, 28)).due_date == date(2027, 3, 7)


def test_late_completion_schedules_next_from_completion_date():
    _, task = _recurring("daily", due_date=date(2026, 10, 10))

    new = task.mark_complete(on_date=date(2026, 10, 13))

    assert new.due_date == date(2026, 10, 14)  # counted from completion, not the old due date


def test_recompleting_a_task_keeps_original_completion_date():
    _, task = _recurring("daily")
    task.mark_complete(on_date=date(2026, 10, 13))

    task.mark_complete(on_date=date(2026, 10, 20))

    assert task.last_completed == date(2026, 10, 13)


def test_unknown_recurrence_leaves_task_unchanged():
    task = Task("Walk", "exercise", 30, recurrence="monthly")

    try:
        task.mark_complete(on_date=date(2026, 10, 13))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

    assert task.completed is False and task.last_completed is None


# ---- conflict detection: duplicate times ----
def test_scheduler_flags_two_tasks_at_the_exact_same_time():
    scheduler = Scheduler(Owner("Sam", 120))
    pet = Pet("Biscuit", "Dog")
    walk = _plan_item(pet, "Walk", time(9, 0), 30)
    feed = _plan_item(pet, "Feed", time(9, 0), 30)  # identical start and duration

    warnings = scheduler.conflict_warnings([walk, feed])

    assert len(warnings) == 1
    assert "'Walk'" in warnings[0] and "'Feed'" in warnings[0]
    assert "09:00" in warnings[0] and "same pet (Biscuit)" in warnings[0]
    assert scheduler.detect_conflicts([walk, feed]) == [walk, feed]


def test_duplicate_times_across_different_pets_are_flagged():
    scheduler = Scheduler(Owner("Sam", 120))
    walk = _plan_item(Pet("Biscuit", "Dog"), "Walk", time(9, 0), 30)
    meds = _plan_item(Pet("Mia", "Cat"), "Meds", time(9, 0), 5)

    (warning,) = scheduler.conflict_warnings([walk, meds])

    assert "different pets" in warning


def test_warn_for_task_flags_duplicate_time_when_adding():
    owner = Owner("Sam", 120)
    pet = Pet("Biscuit", "Dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", "exercise", 30, scheduled_time=time(9, 0)))
    dupe = Task("Feed", "feeding", 10, scheduled_time=time(9, 0))
    pet.add_task(dupe)

    warnings = Scheduler(owner).warn_for_task(dupe, date(2026, 10, 13))

    assert len(warnings) == 1 and "'Walk'" in warnings[0]


def test_conflict_count_for_contained_and_three_way_overlaps():
    scheduler = Scheduler(Owner("Sam", 240))
    pet = Pet("Biscuit", "Dog")

    big = _plan_item(pet, "Groom", time(9, 0), 180)
    inner_a = _plan_item(pet, "Feed", time(9, 30), 10)
    inner_b = _plan_item(pet, "Meds", time(10, 0), 10)  # inside Groom, apart from Feed
    assert len(scheduler.conflict_warnings([big, inner_a, inner_b])) == 2

    a = _plan_item(pet, "A", time(14, 0), 30)
    b = _plan_item(pet, "B", time(14, 0), 30)
    c = _plan_item(pet, "C", time(14, 0), 30)
    assert len(scheduler.conflict_warnings([a, b, c])) == 3


def test_generate_plan_keeps_duplicate_time_tasks_and_warns():
    owner = Owner("Sam", 120)
    pet = Pet("Biscuit", "Dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", "exercise", 30, scheduled_time=time(9, 0)))
    pet.add_task(Task("Feed", "feeding", 10, scheduled_time=time(9, 0)))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(date(2026, 10, 13))

    assert [i.start_time for i in plan] == [time(9, 0), time(9, 0)]
    assert len(scheduler.conflict_warnings(plan)) == 1


# ---- planning: budget and floating tasks ----
def test_floating_tasks_are_placed_around_fixed_tasks():
    owner = Owner("Sam", 240)
    pet = Pet("Biscuit", "Dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", "exercise", 60, Priority.HIGH, scheduled_time=time(8, 0)))
    pet.add_task(Task("Brush", "grooming", 30, Priority.LOW))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(date(2026, 10, 13))

    assert [(i.task.title, i.start_time) for i in plan] == [("Walk", time(8, 0)), ("Brush", time(9, 0))]
    assert scheduler.conflict_warnings(plan) == []


def test_over_budget_task_is_skipped_but_shorter_ones_still_fit():
    owner = Owner("Sam", 30)
    pet = Pet("Biscuit", "Dog")
    owner.add_pet(pet)
    long_high = Task("Long walk", "exercise", 60, Priority.HIGH)
    short_low = Task("Brush", "grooming", 15, Priority.LOW)
    pet.add_task(long_high)
    pet.add_task(short_low)
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(date(2026, 10, 13))

    assert [i.task for i in plan] == [short_low]
    assert scheduler.skipped == [long_high]
    assert "Skipped" in scheduler.explain_plan(plan)


def test_format_schedule_handles_task_ending_at_or_after_midnight():
    from main import format_schedule

    owner = Owner("Sam", 120)
    pet = Pet("Biscuit", "Dog")
    owner.add_pet(pet)
    pet.add_task(Task("Late walk", "exercise", 30, scheduled_time=time(23, 30)))  # ends 24:00
    pet.add_task(Task("Late feed", "feeding", 30, scheduled_time=time(23, 50)))   # ends 24:20
    scheduler = Scheduler(owner)
    day = date(2026, 10, 13)

    text = format_schedule(owner, scheduler, scheduler.generate_plan(day), day)

    assert "Late walk" in text and "Late feed" in text


# ---- extra coverage: sorting, recurrence, conflicts ----
def test_sort_tasks_keeps_original_order_when_all_keys_tie():
    scheduler = Scheduler(Owner("Sam", 120))
    first = Task("Walk", "exercise", 20, Priority.MEDIUM, scheduled_time=time(9, 0))
    second = Task("Play", "enrichment", 20, Priority.MEDIUM, scheduled_time=time(9, 0))
    third = Task("Brush", "grooming", 20, Priority.MEDIUM, scheduled_time=time(9, 0))

    assert scheduler.sort_tasks([second, third, first]) == [second, third, first]


def test_filter_pending_tasks_then_sort_by_time():
    owner, walk, feed, brush = _owner_with_two_pets()  # feed is already completed
    walk.scheduled_time = time(17, 0)
    feed.scheduled_time = time(8, 0)
    brush.scheduled_time = time(7, 30)
    scheduler = Scheduler(owner)

    pending = scheduler.filter_tasks(owner.get_all_tasks(), completed=False)

    assert scheduler.sort_by_time(pending) == [brush, walk]


def test_next_instance_keeps_priority_and_category():
    pet = Pet("Biscuit", "Dog")
    task = Task("Meds", "meds", 5, Priority.HIGH, scheduled_time=time(8, 0), recurrence="daily")
    pet.add_task(task)

    new = task.mark_complete(on_date=date(2026, 10, 13))

    assert (new.priority, new.category) == (Priority.HIGH, "meds")
    assert new is not task and new.pet is pet


def test_mark_complete_without_a_date_uses_today():
    _, task = _recurring("daily")

    new = task.mark_complete()

    assert task.last_completed == date.today()
    assert new.due_date == date.today() + timedelta(days=1)


def test_detect_conflicts_returns_only_overlapping_items_once_each():
    scheduler = Scheduler(Owner("Sam", 240))
    pet = Pet("Biscuit", "Dog")
    groom = _plan_item(pet, "Groom", time(9, 0), 30)   # overlaps both Feed and Meds
    feed = _plan_item(pet, "Feed", time(9, 10), 10)
    meds = _plan_item(pet, "Meds", time(9, 20), 10)    # starts as Feed ends
    dinner = _plan_item(pet, "Dinner", time(12, 0), 30)

    assert scheduler.detect_conflicts([groom, feed, meds, dinner]) == [groom, feed, meds]
    assert scheduler.detect_conflicts([feed, dinner]) == []


def test_warn_for_task_boundary_touching_is_ok_but_one_minute_overlap_warns():
    owner = Owner("Sam", 120)
    pet = Pet("Biscuit", "Dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", "exercise", 30, scheduled_time=time(9, 0)))
    scheduler = Scheduler(owner)
    day = date(2026, 10, 13)

    touching = Task("Brush", "grooming", 30, scheduled_time=time(8, 30))   # ends 09:00 exactly
    overlapping = Task("Bath", "grooming", 31, scheduled_time=time(8, 30)) # ends 09:01

    assert scheduler.warn_for_task(touching, day) == []
    assert len(scheduler.warn_for_task(overlapping, day)) == 1

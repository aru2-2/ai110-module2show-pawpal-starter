# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Three core actions a user should be able to perform is adding their pet, scheduling a walk, and viewing today's tasks.

The main objects for the system are Owner, Pet, Task, and Scheduler. Owner has Pets. Owner can schedule Tasks for Pets. The Scheduler considers constraints provided by the Owner and plans Tasks based on their priority, with an explanation of why each task was chosen.

Owner: Holds the owner's info (name, available time per day, preferences) and owns one or more pets.
Pet: Holds basic pet info (name, species/breed, age, special needs) and has its own list of care tasks.
Task: A single care activity (walk, feeding, meds, grooming) with a duration, priority, and optional time or recurrence.
Scheduler: Takes the owner's constraints and the tasks, sorts and filters them by priority and time available, handles conflicts, and produces the daily plan with an explanation of why each task was chosen.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, my design changed during implementation. I added a Pet attribute to Tasks, so that each Task could be mapped back to the Pet it is meant for, which is especially important when it is combined into a big list in Scheduler. I also included a Priority enum so that the priority values could be sorted by their meaning rather than their alphabetical order. Additionally, I added a ScheduledItem class to include characteristics of a task, such as when it happens and its priority level, to determine a reason for why it was chosen.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers the daily time budget, priority, fixed times, day window, task due date, duration, and overlaps. The time constraint was the most important because the tasks must fit within the allotted time slot for the PawPal+ system to work. Fixed times for certain tasks also stayed because they cannot be moved, such as feeding. Additionally, some tasks have a higher priority than others, which was considered in scheduling the order of these tasks for the pets. If a task needs to be cut due to time constraints, the lowest priority items will leave rather than important items such as medication.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff my scheduler makes is warning about overlapping fixed-time tasks but not fixing them. Fixed tasks stay exactly where the user set them, even when they collide, and the plan only prints a warning. This tradeoff is reasonable for this scenario because it respects the user's chosen times and keeps the logic simple, but the schedule can end up impossible to follow if the owner ignores the warnings. Only floating tasks are guaranteed not to overlap, because they're placed into free gaps.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI for design brainstorming, such as deciding which classes the system needed and how they should go together in the UML diagram and final project. I also used it to debug the logic as I was building PawPal+ and help write tests to ensure the code worked as expected. The most helpful prompts were specific and provided details, such as the exact files and methods, to modify or add to a different section.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One moment where AI suggested a more complicated method was during the creation of the generate_plan function in Scheduler. Instead of accepting the provided function instantly, I looked over the code and asked the AI agent to explain each part to me so that I could improve the readability and functionality of the methodology. Then, I verified the simplified function by using tests to confirm the behavior matched what was expected for PawPal+.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested task sorting by time, filtering by pet and completion status, conflict detection, and basic scheduling behavior. These test were important because the scheduler's purpose is giving the owner a correct daily plan for their pets. A bug in sorting or conflict detection would produce a bad schedule without any visible error, which is not favorable for the PawPal+ system.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm mostly confident in the core behavior because the automated tests pass and cover the main paths, but I'm less sure about edge cases. If I had more time, I would test tasks that cross midnight, tasks with identical start times, an empty schedule, pets with no tasks, and invalid durations or times.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the sorting, filtering, and conflict-detection logic and how it connects to the Streamlit UI. I think the system feels like a usable app. I am also proud of using AI as a helper to make processes more efficient while still remaining in charge of the final PawPal+ product. The test cases also gave me confidence that the code works as intended, even if some code was refactored during the development process.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If I had another iteration, I would add recurring tasks, task priorities that influence the schedule, and smarter conflict resolution. Currently, conflicts are detected but not automatically fixed. I would also clean up the UI and revisit the class design so scheduling logic is more separate from the data models.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

I learned that AI is a strong collaborator that can help me save time and catch mistakes, but it is prone to errors as well. I learned that I need to verify AI output every time to ensure that it is functional as well as logical. Additionally, I noticed that planning the UML design first also made working with AI much more productive, because I could give it clear context for tasks.

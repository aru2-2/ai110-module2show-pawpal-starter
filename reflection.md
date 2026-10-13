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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

# How this project is planned

The work is planned the way a small team plans software: a written backlog, a size on every item, two-week sprints and a definition of done, all kept in GitHub next to the code. LLMFAO is still at the design stage, so what follows is a plan and not a record of shipped work.

- **The board:** the [llmfao project](https://github.com/users/ChiefGyk3D/projects/6), with Sprint board, Sprint plan, Roadmap, Backlog and Agents at work views.
- **The backlog:** this repository's [issues](https://github.com/ChiefGyk3D/LLMFAO/issues), grouped into twelve epics.
- **The ordering and the reasoning:** [Roadmap](Roadmap.md) is the product roadmap, and `docs/ROADMAP.md` in the repository is the sprint-by-sprint ordering.
- **The board as code:** `board.yaml` in the repository root. [Scrum Around and Find Out](https://github.com/ChiefGyk3D/scrum-around-and-find-out) (SAFO) creates and checks the board from it.

## The shape of the plan

| Level | What it is | Where |
|---|---|---|
| Epic | One theme, labelled `epic`, with sub-issues. Its start and target dates draw its bar on the Roadmap view | Issue |
| Issue | One piece of work with a reason, a "done when" list and what it waits on | Sub-issue of an epic |
| Sprint | A two-week slice, Tuesday to Monday | Board field |

The twelve epics are foundation, engine core, Twitch, safety gate, LLM routing, persona and recaps, Discord and the bridge, tips, deployment, viewer identity and memory, stream automation (later), and docs, wiki and process.

## Sprints and what "scheduled" means

Sprint 1 starts on Tuesday 2026-11-03 and eight are defined, through 2027-02-22. Anything with a sprint is scheduled, and anything without one is backlog: wanted, ordered by priority, not promised. Right now the second half of the memory and roasting work, the cloud variant and stream automation are all unscheduled on purpose, because they would overload the agents or depend on parts that do not exist yet.

## Capacity

The maintainer has a day job, works on this in the evenings and at weekends, and shares that time with other boards. The sprint load counts his own hours, which are the items whose Agent is **You**, and it stays at about 3 to 7 hours a sprint. Agent items are limited by agent budgets and review time, with at most three in flight and each on its own branch and worktree. Sizes are **S** about 2 hours, **M** about 5, **L** about 12 and **XL** about 30, and an XL gets split before it is scheduled (there are none right now).

## The flow of an issue

| Status | Meaning |
|---|---|
| Backlog | Not scheduled |
| Next | Scheduled for a sprint |
| In progress | Being worked, or a draft pull request is open |
| In review | A pull request is open and checks and reviews are running |
| Blocked | Needs the maintainer or an answer from outside |
| Done | Closed or merged, with the date in **Done on** |

The board is a user-owned project, so no GitHub App can write it, and that means there is no project-sync workflow here. It is kept current by `safo --board board.yaml reconcile`, run from the maintainer's own `gh` login, which holds the only credential. Sprint, size, area, priority and agent are set by hand when an issue is planned.

## Definition of ready

An issue goes into a sprint when it has a reason, a "done when" checklist, a size, an owner (the maintainer or an agent) and what it waits on. An issue that cannot say what done looks like is a question, not a task.

## Definition of done

1. Checks are green, including the `CI green` gate and the secret scan.
2. Tests exist for what changed, and a test that should fail without the change was shown to fail.
3. The docs and the roadmap say what is now true, in the same pull request.
4. Anything that touches the safety gate, auth, the action allowlist or stored viewer data gets a Codex adversarial review before merge, even when CI and the Sonnet review are green.
5. A change that touches the live bot says how it is deployed and how it rolls back.

# AI Lab - Logical Reasoning for Planning

**Logic + Search = Planning.** A warehouse robot planner written in Python (STRIPS-style actions, BFS), with an independent plan validator and an optional Prolog verifier.

## Files

| File | Purpose |
|------|---------|
| `planner.py` | Actions, applicability, effects, BFS planner, independent `validate_plan()` |
| `test_planner.py` | Tests A, B, C and extra tests (9 in total) |
| `planner.pl` | Prolog facts/rules for Tasks 6-8 (optional extension) |
| `verify_with_prolog.py` | Python plan checked by SWI-Prolog (generate -> verify) |
| `prompts.txt` | Prompts used with the LLM (Appendix) |

## How to run

```bash
python planner.py                # solve the warehouse problem and validate the plan
python test_planner.py           # run all tests
swipl planner.pl                 # Prolog (optional); then type queries, e.g.  ?- can_move(a,b).
python verify_with_prolog.py     # needs SWI-Prolog installed
```

---

## Task 0 - The planning problem

- **(a) Initial state:** `I = {At(Robot,A), At(Package,A)}`
- **(b) Goal:** `G = {At(Package,C)}`
- **(c) Actions:** `Move(A,B)`, `Move(B,A)`, `Move(B,C)`, `Move(C,B)`, `PickUp(Package,loc)`, `Drop(Package,loc)`

| Action | Preconditions | Effects |
|--------|---------------|---------|
| `Move(x,y)` | `At(Robot,x)` | `¬At(Robot,x)`, `At(Robot,y)` |
| `PickUp(Package,l)` | `At(Robot,l)`, `At(Package,l)` | `¬At(Package,l)`, `Holding(Package)` |
| `Drop(Package,l)` | `At(Robot,l)`, `Holding(Package)` | `¬Holding(Package)`, `At(Package,l)` |

**Is `PickUp(Package,A)` applicable in I?** **Yes.** Both preconditions, `At(Robot,A)` and `At(Package,A)`, are in I.
**Is `Drop(Package,C)` applicable?** **No.** It needs `At(Robot,C)` (false: the robot is at A) and `Holding(Package)` (false). Being in the list of available actions is not enough; all preconditions must hold.

## Task 1 - Plan constructed by hand

| State | Facts | Action that produced it |
|-------|-------|-------------------------|
| S0 | At(Robot,A), At(Package,A) | - |
| S1 | At(Robot,A), Holding(Package) | PickUp(Package,A) |
| S2 | At(Robot,B), Holding(Package) | Move(A,B) |
| S3 | At(Robot,C), Holding(Package) | Move(B,C) |
| S4 | At(Robot,C), At(Package,C) | Drop(Package,C) |

S4 satisfies G, so the plan is valid.

> **Note on the lab sheet's hint.** The sheet suggests reasoning about `Move(A,B)`, `PickUp(Package,B)`, `Move(B,C)`, `Drop(Package,C)`. That sequence is **not valid**: the package is at A, not B, so `PickUp(Package,B)` has an unsatisfied precondition. The package must be picked up at A *before* moving. This is exactly the "looks reasonable but isn't valid" trap; `test_plausible_but_invalid_plan` demonstrates it, and the validator reports `step 2 PickUp(Package,B): FAIL - precondition At(Package,B) is false`.

## Task 2 - LLM prompt and generated program

Prompt: see `prompts.txt` (Prompt 1). The program is `planner.py`.

**Where the ideas from the specification appear:**

| Idea | Where |
|------|-------|
| Preconditions -> when is an action applicable? | `applicable()`: `pos_pre <= state` and `neg_pre` disjoint from `state` |
| Effects -> how does the state change? | `apply_action()`: `(state - neg_eff) \| pos_eff` |
| Goal -> when does planning terminate? | `satisfies_goal()`, tested when a state is dequeued; or the frontier empties ("No plan found") |
| BFS -> alternative plans | `plan_bfs()`: FIFO `deque`, `parent` dict doubling as the visited set |

**Output:**
```
Plan found (4 actions, 7 states expanded):
  S0: ['At(Package,A)', 'At(Robot,A)']
  1. PickUp(Package,A)   S1: ['At(Robot,A)', 'Holding(Package)']
  2. Move(A,B)           S2: ['At(Robot,B)', 'Holding(Package)']
  3. Move(B,C)           S3: ['At(Robot,C)', 'Holding(Package)']
  4. Drop(Package,C)     S4: ['At(Package,C)', 'At(Robot,C)']
```

**Assumptions made:** a state is the set of true propositions (closed-world: anything absent is false); actions are deterministic; the robot can carry one package; while the package is held its location is not tracked (it moves with the robot); BFS gives the plan with the fewest actions.

## Task 3 - Test results

| Test | Initial state | Goal | Plan found? | Plan | Valid? |
|------|---------------|------|-------------|------|--------|
| **A** Solvable | `{At(Robot,A), At(Package,A)}` | `At(Package,C)` | Yes | PickUp(Package,A), Move(A,B), Move(B,C), Drop(Package,C) | **Yes** (every step checked by `validate_plan`) |
| **B** Impossible (PickUp removed) | same | `At(Package,C)` | **No** - prints "No plan found" | none | n/a (nothing invented) |
| **C** Irrelevant action: robot-only `Shortcut(A,C)` | same | `At(Robot,C)` | Yes, 1 action (`Shortcut(A,C)`) | - | Yes |
| **C** same domain | same | `At(Package,C)` | Yes | still contains `PickUp(Package,A)` and `Drop(Package,C)` | **Yes** |
| **C** Shortcut, PickUp removed | same | `At(Package,C)` | **No** | none | n/a |

**Conclusion for Test C:** the robot reaching C is *not* treated as the package reaching C. The goal is a statement about `At(Package,C)`, so only actions that change the package's location can achieve it.

**Extra tests (all pass):** the lab's hint plan is rejected; a planner with the precondition check removed returns the bogus one-step plan `Drop(Package,C)` (rejected by the validator); goal already true gives an empty plan; disconnected map gives no plan; plan length is minimal (4).

## Task 4 - Logic and search

```
Current state
   |
Check action preconditions         <- LOGIC: S |= Pre(a)?
   |
Keep only the applicable actions   <- the "?" step
   |
Generate successor state           <- LOGIC: S' = (S - neg effects) + pos effects
   |
Search over alternatives           <- SEARCH: BFS queue, visited set
   |
Goal?                              <- LOGIC: S |= G ?   yes: return plan / no: continue
```

**In my own words:** logic decides *what is possible* from a given state: which actions' preconditions are satisfied and what the world looks like afterwards. Search decides *what to try*: it manages the queue of states, explores the alternatives systematically, avoids repeats, and stops when the goal is entailed. Without logic, search would try impossible actions; without search, logic could tell us what is possible but not which sequence reaches the goal.

## Task 5 - Can the LLM verify its own plan?

Asking an LLM to justify each step yields a fluent explanation, but the explanation is only text. The independent trace from `validate_plan()` re-runs the transitions and checks each precondition mechanically (see the output of `python planner.py`).

**Which to trust more: (b), the independently executed transitions.** It is deterministic, repeatable and actually computes the states; an LLM explanation can sound convincing while containing a wrong step (as the lab's own hint plan shows). *A generated explanation is not the same as an independent verification.* The LLM's explanation is still useful as a guide for understanding, and as something to check against the trace.

## Task 6 - Prolog as a verifier (verified in SWI-Prolog 9.0.4)

| Query | Result |
|-------|--------|
| `?- can_move(a,b).` | `true` |
| `?- can_move(a,c).` | `false` |

- **(a)** `connected(a,b)` is a fact, and the rule `can_move(X,Y) :- connected(X,Y)` lets Prolog derive `can_move(a,b)`.
- **(b)** There is no `connected(a,c)` fact and no other rule that could derive it, so `can_move(a,c)` cannot be proven. (Prolog uses the closed-world assumption: what cannot be proven is treated as false.)
- **(c)** The rule is the implication `Connected(X,Y) -> CanMove(X,Y)`: `:-` reads "if", the head is the conclusion and the body the condition.

## Task 7 - Prolog checks a proposed plan

| Query | Result |
|-------|--------|
| `?- valid_move(a,b).` | `true` |
| `?- valid_move(b,c).` | `true` |
| `?- valid_move(a,c).` | `false` |

**Challenge:** if the Python planner proposed `Move(a,c)`, Prolog's `valid_move(a,c)` fails, so the action is **not supported** by the warehouse knowledge and should be rejected. `verify_with_prolog.py` runs this pipeline: Python generates the plan, Prolog checks each `Move`. (Extra rule `valid_route([a,b,c])` checks a whole route: `true`; `valid_route([a,c])`: `false`.)

## Task 8 - Chaining rules

Query `?- reduce_speed.` succeeds. Prolog proves `reduce_speed` by needing `slippery`, which needs `wet_road`, which is a fact.

```
wet_road (fact)  =>  slippery (rule: wet_road -> slippery)  =>  reduce_speed (rule: slippery -> reduce_speed)
```
Fact => Rule => Rule => Conclusion.

---

## Reflection questions

> The answers below are drafts - adapt them to your own experience, and state which parts of the code you generated or modified with an LLM.

1. **Why specify preconditions/effects first?** They define what "correct" means. With a precise specification the LLM translates it into code, and I can check the code against the specification. A vague request makes the LLM guess the domain rules.
2. **Error if preconditions are not checked:** the planner would "deliver" the package with the single action `Drop(Package,C)` even though the robot is not at C and is not holding anything (shown in `test_without_precondition_check_gives_bogus_plan`).
3. **Why "reasonable-looking" is not valid:** validity depends on each action's preconditions holding in the state where it is executed. The lab's hint plan reads naturally but picks up the package at B while it is at A.
4. **LLM contribution:** a fast first implementation (data structures, BFS loop, trace output), explanation of its assumptions, and the Prolog boilerplate.
5. **Verified independently:** that every action's preconditions hold when executed (separate `validate_plan()`), that "no plan" is reported rather than invented, that robot-at-C is not package-at-C, that BFS terminates and returns the shortest plan, and that Prolog rejects `Move(a,c)`.
6. **Where logical reasoning is used:** deciding applicability (`S |= Pre(a)`), computing successor states from effects, testing the goal (`S |= G`), and in Prolog deriving `can_move`/`valid_move` from facts and rules.
7. **Relation to search:** planning is search over the state space: states are nodes, applicable actions are edges, the initial state is the start, and any state entailing G is a goal. BFS here is the same algorithm as in the previous module, with logic generating the successors instead of a grid.

### Prolog reflection

1. A **fact** is an unconditional statement (`connected(a,b).`); a **rule** says something follows if conditions hold (`can_move(X,Y) :- connected(X,Y).`).
2. A **query** asks whether a statement follows from the facts and rules (the knowledge base); `true` means it can be derived.
3. A plan from Python can contain mistakes; a separate Prolog description of the world can check each step against the domain facts.
4. An independent verifier does not share the generator's blind spots or mistakes, so errors by an LLM that "sounds right" can be caught.

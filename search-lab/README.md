# AI Lab - Search and A\* (Warehouse Robot Navigation)

Implementation of A\* and BFS for a grid warehouse, with tests, experiments and the lab report answers.

## Files

| File | Purpose |
|------|---------|
| `search_agent.py` | Search problem, A\* (with swappable heuristic), BFS, reporting |
| `test_search.py` | Tests 1-4 from Task 3 (+ heuristic optimality check) |
| `experiments.py` | Task 5 (BFS vs A\*) and Task 6 (heuristics) on the lab map |
| `experiments_open.py` | Supplementary experiment on an open map where heuristics differ |
| `prompts.txt` | Prompts used with the LLM (Appendix) |

## How to run

```bash
python search_agent.py        # solve the lab map with A* and BFS
python test_search.py         # run all tests
python experiments.py         # Task 5 + Task 6 tables
python experiments_open.py    # supplementary open-map experiment
```
Python 3 only; standard library only.

---

## Task 0 - Search problem formulation

| Component | Specification |
|-----------|---------------|
| State (S) | Robot position `(row, col)` of any free cell |
| Actions (A) | Up, Down, Left, Right |
| Transition (T) | `T((r,c), a) = (r+dr, c+dc)` using the action's offset, if that cell is valid |
| Initial state (s0) | Position of `S` = `(1, 1)` |
| Goal (G) | `{ (7, 15) }`, the position of `G` |
| Cost (c) | 1 per move |

**(a)** Only the robot's position `(row, col)` is needed. The map is fixed, so it is part of the problem, not the state.
**(b)** An action is invalid if the resulting cell is outside the grid or is an obstacle `#`.
**(c)** Yes, deterministic: an action in a given state always leads to exactly one next state.
**(d)** A solution is a sequence of valid actions leading from `S` to `G`. An optimal solution has the minimum number of moves (minimum total cost).

## Task 1 - Agent design (done before prompting)

1. **State:** a Python tuple `(row, col)`.
2. **Warehouse:** list of strings converted to a 2-D list of characters, held in a `GridProblem` class that also finds `S` and `G`.
3. **Valid actions:** a dictionary mapping action name to `(dr, dc)`; `successors(state)` yields only moves where `is_valid` is true.
4. **Goal test:** `state == problem.goal`.
5. **Frontier contents:** priority-queue entries `(f, h, tie_counter, state)`. Separate dictionaries store `g[state]` and `parent[state] = (previous_state, action)`.
6. **Path reconstruction:** follow `parent` links from the goal back to `None`, then reverse.

**Reported on termination:** solution found (yes/no), path, path length, states expanded.

## Task 2 - Prompts

See `prompts.txt`. The generated code was refined by me: the problem/environment split, a `SearchResult` object, swappable heuristics, and the tie-breaking rule (Prompt 4).

## Task 3 - Test results

| Test | Map | Expected | Result |
|------|-----|----------|--------|
| 1 Original warehouse | lab map | path found | **PASS**, path length 40, 63 states expanded |
| 2 Trivial | `#SG##` | 1 move (`Right`) | **PASS** |
| 3 No solution | goal walled off | reports failure, terminates | **PASS** (`found = False`, `path = None`) |
| 4 Alternative paths | two routes (4 and 8 moves) | returns the 4-move path | **PASS**; A\* length equals BFS length |

**Test 1 path found (`*`):**
```
#################
#S****#*********#
#.###*#*#######*#
#...#*#*******#*#
###.#*#######*#*#
#...#*********#*#
#.###########.#*#
#.............#G#
#################
```

## Task 4 - Where each concept appears in `search_agent.py`

| Concept | Where |
|---------|-------|
| State | `(row, col)` tuples, e.g. `problem.start` |
| Action | `ACTIONS` dictionary (`Up/Down/Left/Right`) |
| Transition | `GridProblem.successors()` |
| Goal test | `GridProblem.is_goal()`, called after popping from the frontier |
| g(n) | dictionary `g` in `astar` (`new_g = g[s] + cost`) |
| h(n) | heuristic functions `manhattan`, etc., called as `h(nxt, problem.goal)` |
| f(n) | `new_g + h_n`, the first element of each heap entry |
| Frontier | list `frontier` managed with `heapq` (a binary-heap priority queue) |
| Visited states | `closed` set (plus `g` dict used to detect cheaper routes) |
| Path reconstruction | `_reconstruct()` following the `parent` dictionary |

**(a)** A priority queue (min-heap via `heapq`).
**(b)** `heappop` returns the entry with the smallest `f(n)`; ties go to smaller `h`, then to the oldest entry.
**(c)** When a successor is generated: `h_n = h(nxt, problem.goal)`.
**(d)** Yes: `new_g + h_n`.
**(e)** The `closed` set: a state popped a second time is skipped (`if s in closed: continue`), and a successor is only pushed if it gives a lower `g` than previously known.

## Task 5 - BFS vs A\* on the lab map

| Measure | BFS | A\* (Manhattan) |
|---------|-----|-----------------|
| Solution found | Yes | Yes |
| Path length | 40 | 40 |
| States expanded | 63 | 63 |

**(a)** Yes, both. **(b)** Yes, both give 40, because both are optimal for unit costs. **(c)** Neither: both expanded 63. **(d)** In general A\* expands fewer states because the heuristic steers it towards the goal and avoids regions with high `f`. Here it cannot, because the lab map is essentially a single winding corridor: only one cell `(5,13)` has more than two free neighbours, and the route to `G` is forced. There is nothing for a heuristic to prune, and Manhattan distance is actively misleading (the goal looks close in a straight line, but the path must zig-zag 40 moves). This is an important result: **A\* is not automatically better; its advantage depends on the map and on the quality of the heuristic.**

### Supplementary: open map (`experiments_open.py`)

To see where A\*'s advantage appears, I ran both on a 25 x 10 map with large open areas and several alternative routes (same program, only the map differs):

| Algorithm | Found | Length | Expanded |
|-----------|-------|--------|----------|
| BFS | Yes | 29 | 129 |
| A\* Manhattan | Yes | 29 | **71** |

Here A\* finds the same optimal length while expanding about 45% fewer states.

## Task 6 - Heuristic investigation

**Why Manhattan is appropriate:** with 4-directional moves of cost 1, any path from `n` to the goal needs at least `|dr| + |dc|` moves, so Manhattan never overestimates (admissible). It also satisfies `h(n) <= 1 + h(n')` for neighbours (consistent), so A\* with a closed set stays optimal.

**Lab map:**

| Heuristic | Found | Length | Expanded |
|-----------|-------|--------|----------|
| Manhattan | Yes | 40 | 63 |
| h(n) = 0 | Yes | 40 | 63 |
| Euclidean | Yes | 40 | 63 |
| 2 x Manhattan | Yes | 40 | 63 |

All identical, for the corridor reason above: the heuristic cannot change the order of exploration when there is only one way to go.

**Open map (where the heuristic matters):**

| Heuristic | Found | Length | Expanded |
|-----------|-------|--------|----------|
| h(n) = 0 | Yes | 29 | 129 |
| Euclidean | Yes | 29 | 110 |
| Manhattan | Yes | 29 | 71 |
| 2 x Manhattan | Yes | **33** (not optimal) | 63 |

Observations:
1. **h = 0** removes all guidance: A\* becomes uniform-cost search (equivalent to BFS here). Still optimal, but expands the most states.
2. **Euclidean** is admissible but always <= Manhattan, so it is *less informed*: still optimal, but expands more states (110 vs 71).
3. **2 x Manhattan** is *inadmissible* (it can overestimate, e.g. an obstacle-free step costs 1 but the estimate drops by 2). A\* becomes greedier and faster (63 states) but returned a **non-optimal path** (33 instead of 29).

**Conclusion:** the closer an admissible heuristic is to the true cost, the fewer states A\* expands. A heuristic that over-estimates the true cost (inadmissible) trades optimality for speed.

## Task 7 - Evaluation of the LLM-generated agent

> **Edit these to reflect your own experience** - the lab asks for *your* reflection. The answers below are a starting draft based on what happened while building this solution.

1. **Correct immediately:** the grid representation, successors, `heapq` frontier, `closed` set and path reconstruction.
2. **Problems found:** (i) with FIFO tie-breaking A\* behaved exactly like BFS on open maps (129 vs 129 states), so the heuristic seemed to do nothing; (ii) on the lab map all methods gave identical numbers, which initially looked like a bug.
3. **How discovered:** by running BFS and A\* side by side (Task 5), the open-map experiment, and by inspecting the map's branching structure (only one branching cell).
4. **Unfamiliar terms:** admissible/consistent heuristics, "stale" heap entries, tie-breaking.
5. **Modified:** yes, added `(f, h, counter)` ordering; split environment from algorithm; added `SearchResult`.
6. **Most useful tests:** the no-solution test (checks termination) and the A\*-vs-BFS length comparison (checks optimality).
7. **Trusted without testing?** No. The program printed a plausible path from the start, but only the tests and comparisons showed whether the *behaviour* (optimality, termination, efficiency) was right.
8. **Learned about A\*:** the heuristic only helps if the map offers choices; it must be admissible to guarantee optimality; and it is `f = g + h` ordering plus the closed set, not "intelligence", that gives A\* its behaviour.

## Final reflection

**1. Why formulate the problem first?** The formulation fixes what a state, action, cost and goal are, which determines what the algorithm manipulates and how to tell if the result is correct. Without it there is nothing to test the program against, and an LLM can only guess the intent.

**2. In what sense is A\* "informed"?** It uses problem-specific knowledge, the heuristic `h(n)`, to rank frontier states by estimated total cost `g + h`, whereas BFS ranks only by depth.

**3. Why does the heuristic matter?** It controls both efficiency and correctness. A better-informed admissible heuristic (Manhattan over Euclidean over zero) expands fewer states; an inadmissible one (2 x Manhattan) can return suboptimal paths, as the open-map experiment showed.

**4. What did the LLM contribute?** Fast translation of the design into working code, boilerplate such as the heap and path reconstruction, and explanations of terms. The problem formulation, tests, experiments and judgement remained the engineer's job.

**5. What could go wrong without testing?** The code might loop forever on unsolvable maps, return non-shortest paths, miscount expansions, or silently misbehave on edge cases. A plausible-looking path is not proof of a correct algorithm: *working output is not a validated algorithm.*

Lab 2: A* and BFS search on a warehouse grid.

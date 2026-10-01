"""
Warehouse Robot Navigation: A* and BFS search agents
====================================================

Search problem  P = (S, A, T, s0, G, c)
  S  : all free cells (row, col)
  A  : Up, Down, Left, Right
  T  : (row, col) + action offset, valid only if the cell is inside the map
       and not '#'
  s0 : position of 'S'
  G  : {position of 'G'}
  c  : 1 per move

Both algorithms share the same environment class and return a SearchResult
so they can be compared fairly (same map, same counting rules).

Counting rule: a state is "expanded" when it is removed from the frontier and
its successors are generated. The goal is tested when a state is removed from
the frontier, for both A* and BFS.
"""

import heapq
import math
from collections import deque
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

State = Tuple[int, int]

WAREHOUSE_MAP = [
    "#################",
    "#S....#.........#",
    "#.###.#.#######.#",
    "#...#.#.......#.#",
    "###.#.#######.#.#",
    "#...#.........#.#",
    "#.###########.#.#",
    "#.............#G#",
    "#################",
]

# Action name -> (row change, column change)
ACTIONS = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}


# --------------------------------------------------------------------------
# Environment / problem definition
# --------------------------------------------------------------------------
class GridProblem:
    def __init__(self, layout: List[str]):
        self.grid = [list(row) for row in layout]
        self.rows, self.cols = len(self.grid), len(self.grid[0])
        self.start = self._find("S")
        self.goal = self._find("G")

    def _find(self, symbol: str) -> State:
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                if cell == symbol:
                    return (r, c)
        raise ValueError(f"'{symbol}' not found in map")

    def is_valid(self, s: State) -> bool:
        r, c = s
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] != "#"

    def successors(self, s: State):
        """Transition function T: yields (action, next_state, step_cost)."""
        for name, (dr, dc) in ACTIONS.items():
            nxt = (s[0] + dr, s[1] + dc)
            if self.is_valid(nxt):
                yield name, nxt, 1

    def is_goal(self, s: State) -> bool:
        return s == self.goal

    def render(self, path: Optional[List[State]] = None) -> str:
        out = [row[:] for row in self.grid]
        for r, c in path or []:
            if out[r][c] == ".":
                out[r][c] = "*"
        return "\n".join("".join(row) for row in out)


# --------------------------------------------------------------------------
# Heuristics   h(n) = estimated cost from n to the goal
# --------------------------------------------------------------------------
def manhattan(s: State, goal: State) -> float:
    return abs(s[0] - goal[0]) + abs(s[1] - goal[1])

def euclidean(s: State, goal: State) -> float:
    return math.hypot(s[0] - goal[0], s[1] - goal[1])

def zero(s: State, goal: State) -> float:
    return 0

def double_manhattan(s: State, goal: State) -> float:
    return 2 * manhattan(s, goal)


# --------------------------------------------------------------------------
# Result container
# --------------------------------------------------------------------------
@dataclass
class SearchResult:
    found: bool
    path: Optional[List[State]]
    actions: Optional[List[str]]
    cost: Optional[int]
    expanded: int


def _reconstruct(parent, state):
    """Walk parent links back from the goal to the start."""
    path, actions = [], []
    while state is not None:
        path.append(state)
        p = parent[state]
        if p is not None:
            actions.append(p[1])
        state = p[0] if p else None
    return path[::-1], actions[::-1]


# --------------------------------------------------------------------------
# A* search
# --------------------------------------------------------------------------
def astar(problem: GridProblem, h: Callable[[State, State], float] = manhattan) -> SearchResult:
    start = problem.start
    g = {start: 0}                       # g(n): best known cost from start
    parent = {start: None}               # (parent_state, action) for path rebuild
    counter = 0                          # final tie-breaker so heap never compares states
    h0 = h(start, problem.goal)
    # heap entries: (f, h, counter, state). Ties on f are broken in favour of
    # the smaller h, i.e. the state that looks closer to the goal.
    frontier = [(h0, h0, counter, start)]
    closed = set()                       # states already expanded
    expanded = 0

    while frontier:
        f, _, _, s = heapq.heappop(frontier)     # lowest f(n) = g(n) + h(n)
        if s in closed:                          # stale duplicate entry
            continue
        if problem.is_goal(s):
            path, actions = _reconstruct(parent, s)
            return SearchResult(True, path, actions, g[s], expanded)
        closed.add(s)
        expanded += 1

        for action, nxt, cost in problem.successors(s):
            new_g = g[s] + cost
            if nxt not in g or new_g < g[nxt]:   # found a cheaper way to nxt
                g[nxt] = new_g
                parent[nxt] = (s, action)
                counter += 1
                h_n = h(nxt, problem.goal)
                heapq.heappush(frontier, (new_g + h_n, h_n, counter, nxt))

    return SearchResult(False, None, None, None, expanded)


# --------------------------------------------------------------------------
# Breadth-first search (blind baseline)
# --------------------------------------------------------------------------
def bfs(problem: GridProblem) -> SearchResult:
    start = problem.start
    frontier = deque([start])                    # FIFO queue
    parent = {start: None}                       # doubles as the visited set
    expanded = 0

    while frontier:
        s = frontier.popleft()
        if problem.is_goal(s):
            path, actions = _reconstruct(parent, s)
            return SearchResult(True, path, actions, len(actions), expanded)
        expanded += 1
        for action, nxt, _ in problem.successors(s):
            if nxt not in parent:
                parent[nxt] = (s, action)
                frontier.append(nxt)

    return SearchResult(False, None, None, None, expanded)


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
def report(name: str, problem: GridProblem, res: SearchResult) -> None:
    print(f"=== {name} ===")
    print(f"Solution found : {res.found}")
    if res.found:
        print(f"Path length    : {res.cost}")
        print(f"States expanded: {res.expanded}")
        print("Actions        :", ", ".join(res.actions))
        print("Path           :", " -> ".join(map(str, res.path)))
        print(problem.render(res.path))
    else:
        print(f"States expanded: {res.expanded}")
        print("No path exists from S to G.")
    print()


if __name__ == "__main__":
    problem = GridProblem(WAREHOUSE_MAP)
    print("Warehouse map:\n" + problem.render() + "\n")
    report("A* (Manhattan)", problem, astar(problem, manhattan))
    report("BFS", problem, bfs(problem))

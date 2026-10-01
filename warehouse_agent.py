"""
Goal-Based Agent for the Warehouse Navigation Problem
=====================================================

Agent type : Goal-based agent (explicit goal, searches ahead for a plan)
Algorithm  : Breadth-First Search (BFS) on a grid graph
Why BFS    : Every move has the same cost (one grid square), so BFS is
             complete (finds a path if one exists) and optimal (the path
             it returns has the fewest moves).

Map legend:  S = start,  G = goal,  # = obstacle,  . = free space
"""

from collections import deque

WAREHOUSE_MAP = [
    "#####################",
    "#S....#............G#",
    "#.##....##########..#",
    "#....##.............#",
    "#.######.###.#.###..#",
    "#........#..........#",
    "#####################",
]

# Available actions: name -> (row change, column change)
ACTIONS = {
    "Up":    (-1, 0),
    "Down":  (1, 0),
    "Left":  (0, -1),
    "Right": (0, 1),
}


class WarehouseEnvironment:
    """The environment: a 2-D grid of cells."""

    def __init__(self, layout):
        self.grid = [list(row) for row in layout]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.start = self._find("S")
        self.goal = self._find("G")

    def _find(self, symbol):
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                if cell == symbol:
                    return (r, c)
        raise ValueError(f"Symbol '{symbol}' not found in the map")

    def is_free(self, pos):
        """True if pos is inside the grid and not an obstacle."""
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] != "#"

    def successors(self, pos):
        """Yield (action_name, new_position) for every legal move from pos."""
        for name, (dr, dc) in ACTIONS.items():
            new_pos = (pos[0] + dr, pos[1] + dc)
            if self.is_free(new_pos):
                yield name, new_pos

    def render(self, path=None):
        """Return the map as text, with the path drawn as '*'."""
        out = [row[:] for row in self.grid]
        for (r, c) in (path or []):
            if out[r][c] == ".":
                out[r][c] = "*"
        return "\n".join("".join(row) for row in out)


class GoalBasedAgent:
    """
    Goal-based agent. It keeps:
      - current state (its position)
      - goal (target position)
      - a model of the environment (the grid and its transitions)
    and uses BFS to look ahead and build a plan (sequence of actions).
    """

    def __init__(self, environment):
        self.env = environment
        self.state = environment.start
        self.goal = environment.goal
        self.nodes_expanded = 0

    def goal_test(self, state):
        return state == self.goal

    def plan(self):
        """
        Breadth-First Search.
        Returns (positions, actions) or (None, None) if no path exists.
        """
        frontier = deque([self.state])            # FIFO queue
        came_from = {self.state: None}            # explored set + parent links
        action_taken = {}                         # position -> action that reached it

        while frontier:
            current = frontier.popleft()
            self.nodes_expanded += 1

            if self.goal_test(current):
                return self._reconstruct(came_from, action_taken, current)

            for action, nxt in self.env.successors(current):
                if nxt not in came_from:          # avoid revisiting states
                    came_from[nxt] = current
                    action_taken[nxt] = action
                    frontier.append(nxt)

        return None, None                         # frontier empty: no path

    @staticmethod
    def _reconstruct(came_from, action_taken, node):
        positions, actions = [], []
        while node is not None:
            positions.append(node)
            if node in action_taken:
                actions.append(action_taken[node])
            node = came_from[node]
        positions.reverse()
        actions.reverse()
        return positions, actions

    def execute(self, actions):
        """Carry out the plan, one action at a time."""
        for a in actions:
            dr, dc = ACTIONS[a]
            self.state = (self.state[0] + dr, self.state[1] + dc)


def main():
    env = WarehouseEnvironment(WAREHOUSE_MAP)
    agent = GoalBasedAgent(env)

    print("Warehouse map:")
    print(env.render())
    print(f"\nStart (row, col): {env.start}")
    print(f"Goal  (row, col): {env.goal}")

    print("\nAlgorithm: Breadth-First Search (BFS)")
    print("Reason   : all moves cost 1, so BFS guarantees the shortest path.")

    positions, actions = agent.plan()

    if positions is None:
        print("\nNo collision-free path exists from S to G.")
        return

    print(f"\nPath found! Length: {len(actions)} moves "
          f"({agent.nodes_expanded} nodes expanded)")
    print("\nPath drawn on map (* = path):")
    print(env.render(positions))
    print("\nSequence of positions (row, col):")
    print(" -> ".join(map(str, positions)))
    print("\nSequence of actions:")
    print(", ".join(actions))

    agent.execute(actions)
    print(f"\nAgent final position: {agent.state} "
          f"(goal reached: {agent.goal_test(agent.state)})")


if __name__ == "__main__":
    main()

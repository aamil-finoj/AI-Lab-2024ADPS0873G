"""Simple tests for the warehouse agent (run: python test_agent.py)."""
from warehouse_agent import WarehouseEnvironment, GoalBasedAgent, WAREHOUSE_MAP


def test_path_found_and_valid():
    env = WarehouseEnvironment(WAREHOUSE_MAP)
    agent = GoalBasedAgent(env)
    path, actions = agent.plan()
    assert path is not None
    assert path[0] == env.start and path[-1] == env.goal
    assert all(env.is_free(p) for p in path)                       # no obstacles
    assert all(abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1                # one step each
               for a, b in zip(path, path[1:]))
    assert len(actions) == 20                                      # shortest path


def test_no_path():
    blocked = [
        "#######",
        "#S.#.G#",
        "#######",
    ]
    agent = GoalBasedAgent(WarehouseEnvironment(blocked))
    path, actions = agent.plan()
    assert path is None and actions is None


def test_start_equals_goal_neighbour():
    env = WarehouseEnvironment(["####", "#SG#", "####"])
    path, actions = GoalBasedAgent(env).plan()
    assert actions == ["Right"]


if __name__ == "__main__":
    test_path_found_and_valid()
    test_no_path()
    test_start_equals_goal_neighbour()
    print("All tests passed.")

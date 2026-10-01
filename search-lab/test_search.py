"""Tests for the search agents.  Run:  python test_search.py"""
from search_agent import (GridProblem, astar, bfs, WAREHOUSE_MAP,
                          manhattan, euclidean, zero, double_manhattan)

def check_valid_path(p, res):
    path = res.path
    assert path[0] == p.start and path[-1] == p.goal
    assert all(p.is_valid(s) for s in path)
    assert all(abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1 for a, b in zip(path, path[1:]))
    assert len(path) - 1 == res.cost

def test1_original():
    p = GridProblem(WAREHOUSE_MAP)
    for algo in (astar, bfs):
        r = algo(p)
        assert r.found; check_valid_path(p, r)
    assert astar(p).cost == bfs(p).cost

def test2_trivial():
    p = GridProblem(["#####", "#SG##", "#####"])
    for algo in (astar, bfs):
        r = algo(p)
        assert r.found and r.cost == 1 and r.actions == ["Right"]

def test3_no_solution():
    p = GridProblem(["#######", "#S....#", "###.###", "#...#G#", "#######"])
    for algo in (astar, bfs):
        r = algo(p)
        assert not r.found and r.path is None

def test4_alternative_paths():
    # Two routes: short (top row, 4 moves) and long (bottom detour, 8 moves)
    p = GridProblem([
        "#######",
        "#S...G#",
        "#.###.#",
        "#.....#",
        "#######",
    ])
    r = astar(p); assert r.found and r.cost == 4; check_valid_path(p, r)
    assert bfs(p).cost == 4

def test4b_cheaper_route_not_straight():
    # Straight line is blocked, optimal path must go around
    p = GridProblem([
        "#######",
        "#S#..G#",
        "#.#.###",
        "#.....#",
        "#######",
    ])
    r = astar(p); b = bfs(p)
    assert r.found and r.cost == b.cost; check_valid_path(p, r)

def test_admissible_heuristics_optimal():
    p = GridProblem(WAREHOUSE_MAP)
    opt = bfs(p).cost
    for h in (manhattan, euclidean, zero):
        assert astar(p, h).cost == opt

if __name__ == "__main__":
    for t in (test1_original, test2_trivial, test3_no_solution,
              test4_alternative_paths, test4b_cheaper_route_not_straight,
              test_admissible_heuristics_optimal):
        t(); print("PASS", t.__name__)
    print("All tests passed.")

"""Reproduces Task 5 (BFS vs A*) and Task 6 (heuristic investigation)."""
from search_agent import (GridProblem, astar, bfs, WAREHOUSE_MAP,
                          manhattan, euclidean, zero, double_manhattan)

p = GridProblem(WAREHOUSE_MAP)

print("Task 5: BFS vs A*")
print(f"{'Algorithm':<22}{'Found':<8}{'Length':<8}{'Expanded'}")
for name, res in [("BFS", bfs(p)), ("A* (Manhattan)", astar(p, manhattan))]:
    print(f"{name:<22}{str(res.found):<8}{res.cost!s:<8}{res.expanded}")

print("\nTask 6: heuristic investigation (A*)")
print(f"{'Heuristic':<22}{'Found':<8}{'Length':<8}{'Expanded'}")
for name, h in [("Manhattan", manhattan), ("h(n) = 0", zero),
                ("Euclidean", euclidean), ("2 x Manhattan", double_manhattan)]:
    res = astar(p, h)
    print(f"{name:<22}{str(res.found):<8}{res.cost!s:<8}{res.expanded}")

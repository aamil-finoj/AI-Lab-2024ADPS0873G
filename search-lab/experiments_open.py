"""
Supplementary experiment: an OPEN map with many alternative routes.
On the lab map (a single winding corridor) every algorithm behaves the same.
Here the heuristic can actually matter.
"""
from search_agent import (GridProblem, astar, bfs, manhattan, euclidean,
                          zero, double_manhattan)

OPEN_MAP = [
    "#########################",
    "#S......................#",
    "#.......................#",
    "#.......#########.......#",
    "#.......#.......#.......#",
    "#.......#.......#.......#",
    "#.......#...#...#.......#",
    "#.......#...#...#.......#",
    "#.......#...#...#......G#",
    "#########################",
]
p = GridProblem(OPEN_MAP)
print(p.render(), "\n")
print(f"{'Algorithm / heuristic':<24}{'Found':<8}{'Length':<8}{'Expanded'}")
rows = [("BFS", bfs(p)),
        ("A* Manhattan", astar(p, manhattan)),
        ("A* h=0", astar(p, zero)),
        ("A* Euclidean", astar(p, euclidean)),
        ("A* 2 x Manhattan", astar(p, double_manhattan))]
for name, r in rows:
    print(f"{name:<24}{str(r.found):<8}{r.cost!s:<8}{r.expanded}")

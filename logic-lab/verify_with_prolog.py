"""
Generate -> Independent verification.
Python (planner.py) generates the plan; SWI-Prolog (planner.pl) checks that
every Move(x,y) in it is supported by the warehouse facts.
Requires SWI-Prolog (`swipl`) on the PATH.   Run: python verify_with_prolog.py
"""
import re
import shutil
import subprocess

from planner import INITIAL, GOAL, warehouse_actions, plan_bfs


def prolog_says_valid_move(x: str, y: str) -> bool:
    goal = f"(valid_move({x},{y}) -> halt(0) ; halt(1))"
    r = subprocess.run(["swipl", "-q", "-g", goal, "planner.pl"],
                       capture_output=True, text=True)
    return r.returncode == 0


def check_moves(action_names):
    for name in action_names:
        m = re.fullmatch(r"Move\((\w),(\w)\)", name)
        if m:
            x, y = m.group(1).lower(), m.group(2).lower()
            ok = prolog_says_valid_move(x, y)
            print(f"  {name:<22} -> Prolog valid_move({x},{y}): {ok}")


if __name__ == "__main__":
    if shutil.which("swipl") is None:
        raise SystemExit("SWI-Prolog (swipl) not found; install it to run this check.")
    res = plan_bfs(INITIAL, GOAL, warehouse_actions())
    print("Plan from Python planner:", [a.name for a in res.plan])
    print("Prolog check of the Move actions:")
    check_moves([a.name for a in res.plan])
    print("\nChallenge: proposed action Move(a,c)")
    check_moves(["Move(A,C)"])

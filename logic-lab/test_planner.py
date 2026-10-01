"""Tests for the logical planner.   Run:  python test_planner.py"""
from collections import deque
from planner import (INITIAL, GOAL, warehouse_actions, plan_bfs, validate_plan,
                     applicable, apply_action, make_action, action_by_name,
                     satisfies_goal)


def names(res):
    return [a.name for a in res.plan]


# ---- Task 0: applicability --------------------------------------------------
def test_task0_applicability():
    acts = warehouse_actions()
    assert applicable(INITIAL, action_by_name(acts, "PickUp(Package,A)"))
    assert not applicable(INITIAL, action_by_name(acts, "Drop(Package,C)"))   # not at C, not holding
    assert not applicable(INITIAL, action_by_name(acts, "PickUp(Package,B)")) # robot/package not at B


# ---- Test A: solvable ------------------------------------------------------
def test_A_solvable():
    res = plan_bfs(INITIAL, GOAL, warehouse_actions())
    assert res.found
    assert names(res) == ["PickUp(Package,A)", "Move(A,B)", "Move(B,C)", "Drop(Package,C)"]
    ok, _ = validate_plan(INITIAL, GOAL, res.plan)
    assert ok


# ---- Test B: impossible (no PickUp action) ---------------------------------
def test_B_impossible_no_pickup():
    res = plan_bfs(INITIAL, GOAL, warehouse_actions(include_pickup=False))
    assert not res.found and res.plan is None


# ---- Test C: robot reaching C is not the package reaching C ----------------
def test_C_irrelevant_actions():
    # Robot-only shortcut A->C that does NOT move the package.
    shortcut = make_action("Shortcut(A,C)", pos_pre=["At(Robot,A)"],
                           pos_eff=["At(Robot,C)"], neg_eff=["At(Robot,A)"])
    acts = warehouse_actions() + [shortcut]
    # (i) robot goal is reachable in one step ...
    robot_goal = frozenset({"At(Robot,C)"})
    r1 = plan_bfs(INITIAL, robot_goal, acts)
    assert r1.found and len(r1.plan) == 1
    # (ii) ... but the package goal still needs PickUp and Drop
    r2 = plan_bfs(INITIAL, GOAL, acts)
    assert r2.found
    assert "PickUp(Package,A)" in names(r2) and "Drop(Package,C)" in names(r2)
    assert validate_plan(INITIAL, GOAL, r2.plan)[0]
    # (iii) without PickUp the shortcut cannot deliver the package
    acts_no_pick = warehouse_actions(include_pickup=False) + [shortcut]
    assert not plan_bfs(INITIAL, GOAL, acts_no_pick).found
    # (iv) robot at C does not satisfy the package goal
    assert not satisfies_goal(frozenset({"At(Robot,C)", "At(Package,A)"}), GOAL)


# ---- "Looks reasonable" is not "valid" (the lab's example plan) ------------
def test_plausible_but_invalid_plan():
    acts = warehouse_actions()
    bad = [action_by_name(acts, n) for n in
           ["Move(A,B)", "PickUp(Package,B)", "Move(B,C)", "Drop(Package,C)"]]
    ok, trace = validate_plan(INITIAL, GOAL, bad)
    assert not ok
    assert "PickUp(Package,B)" in trace[2] and "FAIL" in trace[2]   # package is at A, not B


# ---- What if preconditions were NOT checked? (Reflection Q2) ----------------
def test_without_precondition_check_gives_bogus_plan():
    def broken_planner(initial, goal, actions):
        frontier, seen = deque([(initial, [])]), {initial}
        while frontier:
            s, plan = frontier.popleft()
            if goal <= s:
                return plan
            for a in actions:                       # BUG: no applicable() check
                n = apply_action(s, a)
                if n not in seen:
                    seen.add(n); frontier.append((n, plan + [a]))
    acts = warehouse_actions()
    bogus = broken_planner(INITIAL, GOAL, acts)
    assert [a.name for a in bogus] == ["Drop(Package,C)"]          # "delivers" instantly
    assert not validate_plan(INITIAL, GOAL, bogus)[0]               # but it is invalid


# ---- Extra edge cases -------------------------------------------------------
def test_goal_already_true():
    res = plan_bfs(INITIAL | {"At(Package,C)"}, GOAL, warehouse_actions())
    assert res.found and res.plan == []


def test_disconnected_map_no_plan():
    acts = warehouse_actions(connections=[("A", "B"), ("B", "A")])   # C unreachable
    assert not plan_bfs(INITIAL, GOAL, acts).found


def test_plan_is_shortest():
    res = plan_bfs(INITIAL, GOAL, warehouse_actions())
    assert len(res.plan) == 4


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print("All tests passed.")

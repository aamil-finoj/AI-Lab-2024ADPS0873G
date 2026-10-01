"""
Logical Planning: warehouse robot (Logic + Search = Planning)
=============================================================

Planning problem (I, A, G)
  I : initial state  {At(Robot,A), At(Package,A)}
  A : actions with preconditions and effects
  G : goal           {At(Package,C)}

Representation
  * A state is a frozenset of ground propositions, e.g. "At(Robot,A)".
  * An Action has positive/negative preconditions and positive/negative effects.

Logic  : applicable(state, action)   <=>  state |= Preconditions(action)
         apply_action(state, action) =  (state - neg_effects) | pos_effects
Search : plan_bfs() explores applicable actions breadth-first (shortest plan).

validate_plan() is an INDEPENDENT checker: it re-executes a plan step by step
from the initial state and checks every precondition and the final goal. It
does not reuse the planner's search code.
"""

from collections import deque
from dataclasses import dataclass
from typing import FrozenSet, List, Optional, Tuple

State = FrozenSet[str]


# ---------------------------------------------------------------------------
# Action schema
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Action:
    name: str
    pos_pre: FrozenSet[str] = frozenset()   # must be TRUE in the state
    neg_pre: FrozenSet[str] = frozenset()   # must be FALSE in the state
    pos_eff: FrozenSet[str] = frozenset()   # added
    neg_eff: FrozenSet[str] = frozenset()   # deleted

    def __str__(self):
        return self.name


def make_action(name, pos_pre=(), neg_pre=(), pos_eff=(), neg_eff=()):
    return Action(name, frozenset(pos_pre), frozenset(neg_pre),
                  frozenset(pos_eff), frozenset(neg_eff))


# ---------------------------------------------------------------------------
# Logic: applicability and effects
# ---------------------------------------------------------------------------
def applicable(state: State, action: Action) -> bool:
    """state |= Preconditions(action)"""
    return action.pos_pre <= state and not (action.neg_pre & state)


def apply_action(state: State, action: Action) -> State:
    """S' = (S minus negative effects) plus positive effects."""
    return (state - action.neg_eff) | action.pos_eff


def satisfies_goal(state: State, goal: FrozenSet[str]) -> bool:
    return goal <= state


# ---------------------------------------------------------------------------
# The warehouse domain
# ---------------------------------------------------------------------------
CONNECTIONS = [("A", "B"), ("B", "A"), ("B", "C"), ("C", "B")]
LOCATIONS = ["A", "B", "C"]


def warehouse_actions(connections=CONNECTIONS, locations=LOCATIONS,
                      include_pickup=True) -> List[Action]:
    acts = []
    for x, y in connections:                                   # Move(x, y)
        acts.append(make_action(
            f"Move({x},{y})",
            pos_pre=[f"At(Robot,{x})"],
            pos_eff=[f"At(Robot,{y})"],
            neg_eff=[f"At(Robot,{x})"]))
    for loc in locations:
        if include_pickup:                                     # PickUp(Package, loc)
            acts.append(make_action(
                f"PickUp(Package,{loc})",
                pos_pre=[f"At(Robot,{loc})", f"At(Package,{loc})"],
                pos_eff=["Holding(Package)"],
                neg_eff=[f"At(Package,{loc})"]))
        acts.append(make_action(                               # Drop(Package, loc)
            f"Drop(Package,{loc})",
            pos_pre=[f"At(Robot,{loc})", "Holding(Package)"],
            pos_eff=[f"At(Package,{loc})"],
            neg_eff=["Holding(Package)"]))
    return acts


INITIAL = frozenset({"At(Robot,A)", "At(Package,A)"})
GOAL = frozenset({"At(Package,C)"})


# ---------------------------------------------------------------------------
# Search: breadth-first planner
# ---------------------------------------------------------------------------
@dataclass
class PlanResult:
    found: bool
    plan: Optional[List[Action]]
    states: Optional[List[State]]    # S0, S1, ..., Sn
    expanded: int


def plan_bfs(initial: State, goal: FrozenSet[str], actions: List[Action]) -> PlanResult:
    frontier = deque([initial])
    parent = {initial: None}                 # state -> (previous_state, action); also 'visited'
    expanded = 0

    while frontier:
        state = frontier.popleft()
        if satisfies_goal(state, goal):                       # goal test
            plan, states, s = [], [], state
            while parent[s] is not None:
                prev, act = parent[s]
                plan.append(act)
                states.append(s)
                s = prev
            states.append(initial)
            return PlanResult(True, plan[::-1], states[::-1], expanded)
        expanded += 1
        for act in actions:
            if applicable(state, act):                        # LOGIC: S |= Pre(a)
                nxt = apply_action(state, act)                # LOGIC: effects
                if nxt not in parent:                         # SEARCH: no repeats
                    parent[nxt] = (state, act)
                    frontier.append(nxt)

    return PlanResult(False, None, None, expanded)            # frontier empty: no plan


# ---------------------------------------------------------------------------
# Independent plan validator (does not use plan_bfs / applicable / apply_action)
# ---------------------------------------------------------------------------
def validate_plan(initial, goal, plan) -> Tuple[bool, List[str]]:
    """Execute `plan` from `initial`; return (is_valid, human-readable trace)."""
    facts = set(initial)
    trace = [f"S0 = {sorted(facts)}"]
    for i, a in enumerate(plan, start=1):
        for p in sorted(a.pos_pre):
            if p not in facts:
                trace.append(f"step {i} {a.name}: FAIL - precondition {p} is false")
                return False, trace
        for p in sorted(a.neg_pre):
            if p in facts:
                trace.append(f"step {i} {a.name}: FAIL - {p} must be false")
                return False, trace
        for p in a.neg_eff:
            facts.discard(p)
        for p in a.pos_eff:
            facts.add(p)
        trace.append(f"step {i} {a.name}: preconditions OK -> S{i} = {sorted(facts)}")
    ok = all(g in facts for g in goal)
    trace.append("Goal satisfied." if ok else f"FAIL - goal {sorted(goal)} not reached")
    return ok, trace


def action_by_name(actions, name):
    for a in actions:
        if a.name == name:
            return a
    raise KeyError(name)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
def print_result(res: PlanResult):
    if not res.found:
        print("No plan found")
        print(f"(states expanded: {res.expanded})")
        return
    print(f"Plan found ({len(res.plan)} actions, {res.expanded} states expanded):")
    print(f"  S0: {sorted(res.states[0])}")
    for i, (a, s) in enumerate(zip(res.plan, res.states[1:]), start=1):
        print(f"  {i}. {a}")
        print(f"  S{i}: {sorted(s)}")


if __name__ == "__main__":
    acts = warehouse_actions()
    print("Initial state:", sorted(INITIAL))
    print("Goal         :", sorted(GOAL), "\n")
    res = plan_bfs(INITIAL, GOAL, acts)
    print_result(res)
    ok, trace = validate_plan(INITIAL, GOAL, res.plan)
    print("\nIndependent validation:", "VALID" if ok else "INVALID")
    print("\n".join(trace))

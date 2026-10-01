"""
Tests that the programs implement the intended probabilistic model.
Run:  python test_models.py
"""
import random

from data import START, END, training_data, tokenise
from first_order import FirstOrderModel
from second_order import SecondOrderModel

DATA = training_data()
M1 = FirstOrderModel().fit(DATA)
M2 = SecondOrderModel().fit(DATA)
TOL = 1e-9


# ---- counts and CPT values (hand-computed from the 6 sentences) -----------
def test_hand_computed_counts_first_order():
    assert M1.counts["the"]["cat"] == 3 and M1.counts["the"]["dog"] == 3
    assert M1.counts["the"]["mat"] == 2 and M1.counts["the"]["rug"] == 2
    assert M1.counts["the"]["park"] == 2
    assert abs(M1.probs["the"]["cat"] - 3 / 12) < TOL
    assert abs(M1.probs["cat"]["sat"] - 2 / 3) < TOL
    assert abs(M1.probs["cat"]["ran"] - 1 / 3) < TOL
    assert abs(M1.probs["sat"]["on"] - 1.0) < TOL


def test_hand_computed_counts_second_order():
    assert M2.counts[("the", "cat")]["sat"] == 2 and M2.counts[("the", "cat")]["ran"] == 1
    assert abs(M2.probs[("on", "the")]["mat"] - 0.5) < TOL
    assert abs(M2.probs[("the", "park")][END] - 1.0) < TOL


# ---- invariant: every distribution sums to 1 ------------------------------
def test_normalisation():
    for m in (M1, M2):
        for ctx, dist in m.probs.items():
            assert abs(sum(dist.values()) - 1.0) < TOL, ctx
            assert all(p > 0 for p in dist.values())


# ---- invariant: probability over ALL complete sentences sums to 1 ----------
def test_second_order_sentence_probabilities_sum_to_one():
    # Enumerate every sentence the model can produce (finite for this data).
    total, stack = 0.0, [((START, START), [START], 1.0)]
    while stack:
        ctx, toks, p = stack.pop()
        for w, pw in M2.distribution(ctx).items():
            if w == END:
                total += p * pw
            else:
                stack.append(((ctx[1], w), toks + [w], p * pw))
    assert abs(total - 1.0) < 1e-9


def test_first_order_terminates_with_probability_one():
    # DP over the Markov chain: mass absorbed in <END> within n steps -> 1.
    mass, ended = {START: 1.0}, 0.0
    for _ in range(300):
        nxt = {}
        for w, p in mass.items():
            for v, pv in M1.distribution(w).items():
                if v == END:
                    ended += p * pv
                else:
                    nxt[v] = nxt.get(v, 0.0) + p * pv
        mass = nxt
    assert abs(ended - 1.0) < 1e-6


# ---- chain rule on a concrete sentence ------------------------------------
def test_chain_rule_sentence_probability():
    toks = tokenise("the cat sat on the mat")
    # P1 = P(the|S) P(cat|the) P(sat|cat) P(on|sat) P(the|on) P(mat|the) P(END|mat)
    expected1 = 1.0 * (3 / 12) * (2 / 3) * 1.0 * 1.0 * (2 / 12) * 1.0
    assert abs(M1.probability(toks) - expected1) < TOL
    # P2 = 1 * 1/2 * 2/3 * 1 * 1 * 1/2 * 1
    expected2 = 1.0 * (3 / 6) * (2 / 3) * 1.0 * 1.0 * 0.5 * 1.0
    assert abs(M2.probability(toks) - expected2) < TOL


def test_unseen_transition_has_probability_zero():
    assert M1.distribution("the").get("sat", 0.0) == 0.0
    assert M1.probability(tokenise("the sat")) == 0.0


# ---- unseen context (Question 7) ------------------------------------------
def test_unseen_context_handled():
    assert M1.distribution("zebra") == {}
    assert M1.most_probable("zebra") is None
    assert M1.sample_next("zebra", random.Random(0)) is None
    assert M2.distribution(("zebra", "the")) == {}
    # <END> is never a context, so generation from it cannot continue:
    assert M1.distribution(END) == {}


# ---- sampling really samples from the CPT (not argmax) ---------------------
def test_sampling_matches_distribution():
    rng, n = random.Random(1), 30000
    freq = {}
    for _ in range(n):
        w = M1.sample_next("the", rng)
        freq[w] = freq.get(w, 0) + 1
    for w, p in M1.distribution("the").items():
        assert abs(freq[w] / n - p) < 0.01, (w, freq[w] / n, p)


# ---- greedy vs sampling ----------------------------------------------------
def test_greedy_is_deterministic():
    a = M1.generate("greedy"); b = M1.generate("greedy")
    assert a == b
    a = M2.generate("greedy"); b = M2.generate("greedy")
    assert a == b


def test_first_order_greedy_cycles_and_hits_max_len():
    words, status = M1.generate("greedy", max_len=20)
    assert status == "MAX_LEN"                    # the cat sat on the cat sat on ...
    assert words[:8] == ["the", "cat", "sat", "on", "the", "cat", "sat", "on"]


def test_second_order_greedy_terminates():
    words, status = M2.generate("greedy")
    assert status == "END" and words == "the cat sat on the mat".split()


def test_seeded_sampling_reproducible():
    a = [M1.generate("sample", random.Random(5)) for _ in range(3)]
    b = [M1.generate("sample", random.Random(5)) for _ in range(3)]
    assert a == b


# ---- second-order model only produces sentences supported by its CPT ------
def test_second_order_generates_only_supported_transitions():
    rng = random.Random(3)
    for _ in range(200):
        words, status = M2.generate("sample", rng)
        assert status == "END"
        assert M2.probability([START] + words + [END]) > 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print("All tests passed.")

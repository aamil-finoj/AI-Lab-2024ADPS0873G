"""
First-order autoregressive language model  (Bayesian network  X1 -> X2 -> ... -> XT)

    P(X1,...,XT) = P(X1 | <START>) * prod_{t>=2} P(Xt | X_{t-1})

Parameters are the conditional probability table (CPT)
    P(w_j | w_i) = C(w_i, w_j) / sum_k C(w_i, w_k)
estimated purely by counting. No ML library, no pretrained model.
"""

import random
from collections import Counter, defaultdict

from data import START, END, training_data


class FirstOrderModel:
    def __init__(self):
        self.counts = defaultdict(Counter)   # counts[prev][next] = C(prev, next)
        self.probs = {}                      # probs[prev][next]  = P(next | prev)

    # ---- learning: counting, then normalising --------------------------
    def fit(self, sentences):
        for tokens in sentences:                       # tokens include <START>, <END>
            for prev, nxt in zip(tokens, tokens[1:]):
                self.counts[prev][nxt] += 1            # transition counts stored here
        for prev, cnt in self.counts.items():          # P(next|prev) computed here
            total = sum(cnt.values())
            self.probs[prev] = {w: c / total for w, c in sorted(cnt.items())}
        return self

    # ---- querying -----------------------------------------------------
    def distribution(self, prev):
        """P(. | prev); empty dict if `prev` was never seen as a context."""
        return self.probs.get(prev, {})

    def most_probable(self, prev):
        """arg max_w P(w | prev); ties broken alphabetically (deterministic)."""
        dist = self.distribution(prev)
        if not dist:
            return None
        return max(sorted(dist), key=lambda w: dist[w])

    def sample_next(self, prev, rng):
        """Draw w ~ P(. | prev)."""
        dist = self.distribution(prev)
        if not dist:
            return None
        words = sorted(dist)
        return rng.choices(words, weights=[dist[w] for w in words], k=1)[0]

    def probability(self, tokens):
        """Chain rule: product of P(t_i | t_{i-1}) over a <START>...<END> sequence."""
        p = 1.0
        for prev, nxt in zip(tokens, tokens[1:]):
            p *= self.distribution(prev).get(nxt, 0.0)
        return p

    # ---- generation ---------------------------------------------------
    def generate(self, mode="sample", rng=None, max_len=20):
        """
        mode = 'sample' : X_t ~ P(. | X_{t-1})      (probabilistic)
        mode = 'greedy' : X_t = arg max P(. | X_{t-1})   (deterministic)
        Returns (words, status) with status in {'END', 'MAX_LEN', 'UNSEEN'}.
        """
        rng = rng or random.Random()
        prev, words = START, []
        for _ in range(max_len):
            nxt = self.sample_next(prev, rng) if mode == "sample" else self.most_probable(prev)
            if nxt is None:
                return words, "UNSEEN"          # no observed transition from `prev`
            if nxt == END:
                return words, "END"
            words.append(nxt)
            prev = nxt
        return words, "MAX_LEN"                 # safety stop (e.g. greedy cycles)


def check_normalisation(model, tol=1e-9):
    """Property that must hold: sum_v P(v | w) = 1 for every context w."""
    ok = True
    for ctx, dist in sorted(model.probs.items()):
        total = sum(dist.values())
        flag = "ok" if abs(total - 1.0) < tol else "NOT NORMALISED"
        ok &= flag == "ok"
        print(f"  {ctx:<10} sum = {total:.6f}  {flag}")
    return ok


if __name__ == "__main__":
    model = FirstOrderModel().fit(training_data())
    print("P(next | the):", model.distribution("the"))
    print("Most probable after 'the':", model.most_probable("the"))
    print("\nNormalisation check:")
    check_normalisation(model)
    rng = random.Random(0)
    print("\nSampled sentences:")
    for _ in range(5):
        words, status = model.generate("sample", rng)
        print("  ", " ".join(words), f"[{status}]")

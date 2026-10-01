"""
Second-order autoregressive language model (Bayesian network  X_{t-2} -> X_t <- X_{t-1})

    P(Xt | X_{t-2}, X_{t-1}) = C(w_a, w_b, w_c) / sum_k C(w_a, w_b, w_k)

Each sentence is padded with TWO <START> tokens so the first word has a
two-token context:  (<START>,<START>) -> X1,  (<START>,X1) -> X2, ...
"""

import random
from collections import Counter, defaultdict

from data import START, END, training_data


class SecondOrderModel:
    def __init__(self):
        self.counts = defaultdict(Counter)   # counts[(a, b)][c] = C(a, b, c)
        self.probs = {}                      # probs[(a, b)][c]  = P(c | a, b)

    def fit(self, sentences):
        for tokens in sentences:
            padded = [START] + tokens                       # <START> <START> w1 ... <END>
            for a, b, c in zip(padded, padded[1:], padded[2:]):
                self.counts[(a, b)][c] += 1                 # triple counts stored here
        for ctx, cnt in self.counts.items():                # P(c | a, b) computed here
            total = sum(cnt.values())
            self.probs[ctx] = {w: n / total for w, n in sorted(cnt.items())}
        return self

    def distribution(self, ctx):
        return self.probs.get(ctx, {})

    def most_probable(self, ctx):
        dist = self.distribution(ctx)
        if not dist:
            return None
        return max(sorted(dist), key=lambda w: dist[w])     # alphabetical tie-break

    def sample_next(self, ctx, rng):
        dist = self.distribution(ctx)
        if not dist:
            return None
        words = sorted(dist)
        return rng.choices(words, weights=[dist[w] for w in words], k=1)[0]

    def probability(self, tokens):
        padded = [START] + tokens
        p = 1.0
        for a, b, c in zip(padded, padded[1:], padded[2:]):
            p *= self.distribution((a, b)).get(c, 0.0)
        return p

    def generate(self, mode="sample", rng=None, max_len=20):
        rng = rng or random.Random()
        ctx, words = (START, START), []
        for _ in range(max_len):
            nxt = self.sample_next(ctx, rng) if mode == "sample" else self.most_probable(ctx)
            if nxt is None:
                return words, "UNSEEN"
            if nxt == END:
                return words, "END"
            words.append(nxt)
            ctx = (ctx[1], nxt)
        return words, "MAX_LEN"


def check_normalisation(model, tol=1e-9):
    ok = True
    for ctx, dist in sorted(model.probs.items()):
        total = sum(dist.values())
        flag = "ok" if abs(total - 1.0) < tol else "NOT NORMALISED"
        ok &= flag == "ok"
        print(f"  {str(ctx):<24} sum = {total:.6f}  {flag}")
    return ok


if __name__ == "__main__":
    model = SecondOrderModel().fit(training_data())
    print("P(next | the, cat):", model.distribution(("the", "cat")))
    print("\nNormalisation check:")
    check_normalisation(model)
    rng = random.Random(0)
    print("\nSampled sentences:")
    for _ in range(5):
        words, status = model.generate("sample", rng)
        print("  ", " ".join(words), f"[{status}]")

"""
Produces the lab deliverables and the model comparison (Parts VIII-XIII).
Run:  python compare.py
Writes: cpt_first_order.txt, cpt_second_order.txt, generated_sentences.txt
"""
import random

from data import START, END, RAW_SENTENCES, training_data
from first_order import FirstOrderModel, check_normalisation as norm1
from second_order import SecondOrderModel, check_normalisation as norm2

DATA = training_data()
M1 = FirstOrderModel().fit(DATA)
M2 = SecondOrderModel().fit(DATA)
TRAIN_SET = set(RAW_SENTENCES)

WORDS = sorted({t for s in DATA for t in s if t not in (START, END)})
NEXT_TOKENS = WORDS + [END]                    # tokens that can follow a context
FIRST_CONTEXTS = [START] + WORDS               # 11 possible contexts
SECOND_CONTEXTS = ([(START, START)] + [(START, w) for w in WORDS]
                   + [(a, b) for a in WORDS for b in WORDS])   # 111 possible contexts


def fmt(dist):
    return ", ".join(f"{w}: {p:.3f}" for w, p in sorted(dist.items()))


def cpt_text(model, contexts, title):
    lines = [title, "=" * len(title)]
    for ctx in contexts:
        dist = model.distribution(ctx)
        zero = [w for w in NEXT_TOKENS if w not in dist]
        lines.append(f"P(next | {ctx}) = {{{fmt(dist)}}}" if dist else f"P(next | {ctx}) = (unseen context)")
        if dist:
            lines.append(f"    zero-probability next tokens: {', '.join(zero)}")
    return "\n".join(lines)


# ---- Part IV / Question 3: CPT for selected contexts --------------------------
cpt1 = cpt_text(M1, ["<START>", "the", "cat", "dog", "sat", "ran", "on", "to", "mat", "rug", "park"],
                "First-order CPT:  P(next | current)")
cpt2 = cpt_text(M2, [(START, START), (START, "the"), ("the", "cat"), ("the", "dog"), ("cat", "sat"),
                     ("dog", "sat"), ("cat", "ran"), ("dog", "ran"), ("sat", "on"), ("on", "the"),
                     ("ran", "to"), ("to", "the"), ("the", "mat"), ("the", "rug"), ("the", "park")],
                "Second-order CPT:  P(next | prev2, prev1)")
open("cpt_first_order.txt", "w").write(cpt1 + "\n")
open("cpt_second_order.txt", "w").write(cpt2 + "\n")
print(cpt1, "\n")

# ---- Part VII: normalisation ---------------------------------------------------
print("Normalisation (first-order):")
ok1 = norm1(M1)
print("Normalisation (second-order):")
ok2 = norm2(M2)
print("All distributions sum to 1:", ok1 and ok2, "\n")

# ---- Part VIII / Question 9: predictions --------------------------------------
print("Next-word predictions (first-order):")
for w in ["the", "cat", "dog", "sat", "ran", "on", "to"]:
    print(f"  P(. | {w:<4}) = {{{fmt(M1.distribution(w))}}}   argmax = {M1.most_probable(w)}")
print()

# ---- Part IX: 20 sampled sentences ---------------------------------------------
def gen_many(model, mode, n, seed):
    rng = random.Random(seed)
    return [model.generate(mode, rng) for _ in range(n)]

lines = []
for name, model in (("FIRST-ORDER", M1), ("SECOND-ORDER", M2)):
    lines.append(f"--- {name}: 20 sampled sentences (seed 42) ---")
    for words, status in gen_many(model, "sample", 20, 42):
        lines.append("  " + " ".join(words) + ("" if status == "END" else f"   [{status}]"))
    lines.append("")

# ---- Part X: greedy vs sampling (5 each) -----------------------------------------
for name, model in (("FIRST-ORDER", M1), ("SECOND-ORDER", M2)):
    g = model.generate("greedy")
    lines.append(f"--- {name}: greedy (5 runs, identical) ---")
    for _ in range(5):
        words, status = model.generate("greedy")
        lines.append("  " + " ".join(words) + ("" if status == "END" else f"   [{status}]"))
    lines.append(f"--- {name}: sampling (5 sentences, seed 7) ---")
    for words, status in gen_many(model, "sample", 5, 7):
        lines.append("  " + " ".join(words) + ("" if status == "END" else f"   [{status}]"))
    lines.append("")
open("generated_sentences.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

# ---- Part XIII: model comparison ------------------------------------------------------
def stats(model, contexts, n=1000, seed=0):
    nonzero = sum(len(d) for d in model.probs.values())
    table = len(contexts) * len(NEXT_TOKENS)
    seen = sum(1 for c in contexts if model.distribution(c))
    runs = gen_many(model, "sample", n, seed)
    sents = [" ".join(w) for w, _ in runs]
    distinct = set(sents)
    novel = {s for s in distinct if s not in TRAIN_SET}
    return dict(nonzero=nonzero, table=table, zero_entries=table - nonzero,
                contexts=len(contexts), unseen=len(contexts) - seen,
                distinct=len(distinct), novel=len(novel), novel_examples=sorted(novel)[:6],
                runs=runs)

s1, s2 = stats(M1, FIRST_CONTEXTS), stats(M2, SECOND_CONTEXTS)
print("MODEL COMPARISON (1000 sampled sentences each)")
print(f"{'Measure':<44}{'First-order':>14}{'Second-order':>14}")
rows = [
    ("Non-zero parameters (observed entries)", "nonzero"),
    ("Full CPT size (contexts x next tokens)", "table"),
    ("Zero-probability CPT entries", "zero_entries"),
    ("Possible contexts", "contexts"),
    ("Unseen contexts (no data at all)", "unseen"),
    ("Distinct sentences generated", "distinct"),
    ("Distinct sentences NOT in training data", "novel"),
]
for label, key in rows:
    print(f"{label:<44}{s1[key]:>14}{s2[key]:>14}")
print("\nNovel first-order sentences (examples):", s1["novel_examples"])
print("Novel second-order sentences (examples):", s2["novel_examples"])
trunc1 = sum(1 for _, st in s1["runs"] if st != "END")
print("First-order samples that hit max length:", trunc1)

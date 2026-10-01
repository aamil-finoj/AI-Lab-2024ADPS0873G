# AI Lab - Bayesian Networks and Autoregressive Language Models

A first-order and a second-order autoregressive language model built from counts (no ML libraries), viewed as Bayesian networks, with probabilistic tests and a comparison.

## Files

| File | Purpose |
|------|---------|
| `data.py` | Training sentences, tokenisation, `<START>`/`<END>` |
| `first_order.py` | First-order model: `P(Xt \| Xt-1)` |
| `second_order.py` | Second-order model: `P(Xt \| Xt-2, Xt-1)` |
| `test_models.py` | 14 tests of probabilistic invariants (normalisation, chain rule, sampling, ...) |
| `compare.py` | Generates the deliverables below and the model comparison |
| `cpt_first_order.txt`, `cpt_second_order.txt` | CPTs for selected contexts |
| `generated_sentences.txt` | 20 sampled sentences per model + greedy vs sampling |
| `prompts.txt` | Prompts used with the LLM (Appendix) |

## How to run

```bash
python first_order.py     # CPT for 'the', normalisation check, 5 samples
python second_order.py
python test_models.py     # all invariants
python compare.py         # CPTs, predictions, generation, comparison table
```
Python 3 only, standard library only.

---

## Part I - Chain rule (Question 1)

`P(X1..X6) = P(X1) P(X2|X1) P(X3|X1,X2) ... P(X6|X1..X5)` holds exactly, with no assumptions.

**Q1. Why useful for generating text?** It turns the hard problem "generate a whole sentence" into a repeated easy one: "given the words so far, choose the next word". We sample X1, then X2 given X1, then X3 given X1,X2, and so on, and the product of the sampled conditionals is exactly the probability of the finished sentence. It also means a model only has to learn *next-token* distributions, and the same machinery works for sequences of any length.

## Part II - Bayesian network (Question 2)

`X1 -> X2 -> X3 -> X4` encodes `P(X1,X2,X3,X4) = P(X1) P(X2|X1) P(X3|X2) P(X4|X3)`.

**Q2. Independence assumption:**
`P(Xt | X1, ..., Xt-1) = P(Xt | Xt-1)`, i.e. `Xt ⊥ {X1..Xt-2} | Xt-1`: given the previous word, earlier words add no information about the next one (the first-order Markov property).

## Part III-IV - Data and CPT (Question 3)

Vocabulary: 10 words (`the cat sat on mat rug dog ran to park`) plus `<START>`, `<END>`. Counts for `the`: cat 3, dog 3, mat 2, rug 2, park 2 (total 12).

**Q3. CPT `P(next | current)`** (computed by `compare.py`, saved in `cpt_first_order.txt`):

| Current | Non-zero transitions | Zero-probability transitions |
|---------|---------------------|------------------------------|
| `<START>` | the = 1.000 | everything else |
| `the` | cat 0.250, dog 0.250, mat 0.167, rug 0.167, park 0.167 | on, sat, ran, the, to, `<END>` |
| `cat` | sat 0.667, ran 0.333 | cat, dog, mat, on, park, rug, the, to, `<END>` |
| `dog` | sat 0.667, ran 0.333 | same pattern as `cat` |
| `sat` | on 1.000 | all others |
| `ran` | to 1.000 | all others |

Examples of zero-probability transitions: `P(sat | the) = 0`, `P(park | sat) = 0`, `P(the | cat) = 0`. They are not impossible in English; they are just unobserved in six sentences. Overall, 104 of the 121 CPT entries are zero (17 non-zero).

## Part V-VI - LLM prompt and code inspection (Questions 4-7)

Prompt: `prompts.txt`, Prompt 1. Code: `first_order.py`.

- **Q4. Where are transition counts stored?** In `self.counts`, a `defaultdict(Counter)`: `counts[prev][next] = C(prev, next)`, filled in the loop in `fit()`.
- **Q5. Where is `P(Xt | Xt-1)` computed?** In `fit()`, second loop: `probs[prev][w] = count / total`, where `total = sum(counts[prev].values())`. Stored in `self.probs`.
- **Q6. How is the next word chosen?** Depends on mode: `sample_next()` **samples** from the distribution (`rng.choices` with the CPT as weights); `most_probable()` is **greedy** (arg max). *Greedy* always returns the single most likely word, so it is deterministic and gives the same sentence every time. *Sampling* picks each word with its probability (e.g. `cat` 25% of the time after `the`, `park` 16.7%), so output varies while still following the model's statistics.
- **Q7. Unseen word?** `distribution()` uses `probs.get(prev, {})`, so it returns an empty dictionary; `most_probable()`/`sample_next()` return `None`, and `generate()` stops with status `UNSEEN` instead of crashing. (A naive `probs[prev]` would raise `KeyError`.) `<END>` is the one such token in this data, since nothing is observed after it. Fixing this properly needs smoothing or back-off, which is beyond this lab.

## Part VII - Testing the probability model (Question 8)

`check_normalisation()` prints `sum_v P(v|w)` for every context: all totals are 1.000000 for both models (see `python first_order.py` output).

**Q8. If a total were 0.87:** the implementation does not match the intended model. Typical causes: a wrong denominator (dividing by too large a number, e.g. the total count of *all* transitions instead of the context's), transitions silently dropped (e.g. `<END>` not counted or a token skipped), or a stray filter on tokens. A distribution that sums to 0.87 is not a probability distribution, and sampling from it would be biased. The check catches errors that "looks plausible" output would hide.

Additional invariant tests in `test_models.py`: hand-computed counts and probabilities; chain-rule probability of `the cat sat on the mat` (first-order = 1/36 ≈ 0.0278, second-order = 1/6 ≈ 0.1667); the second-order model's sentence probabilities sum to 1 over all six sentences it can produce; the first-order chain terminates with probability 1; sampling frequencies match the CPT within 1%.

## Part VIII - Predicting the next word (Question 9)

| Context | Distribution | arg max |
|---------|--------------|---------|
| `the` | cat .250, dog .250, mat .167, park .167, rug .167 | cat (tie with dog, broken alphabetically) |
| `cat` | sat .667, ran .333 | sat |
| `dog` | sat .667, ran .333 | sat |
| `sat` | on 1.0 | on |
| `ran` | to 1.0 | to |
| `on` | the 1.0 | the |
| `to` | the 1.0 | the |

**Q9. Same as human expectation?** Mostly for the deterministic words (`sat -> on`, `ran -> to`), but not always. After `the`, `cat` and `dog` are tied, so "most probable" is arbitrary; and `P(mat | the) = 0.167` is as likely as `park`, because the model cannot know that after `sat on the` a surface is expected. A human uses world knowledge and the whole sentence; the model knows only counts from six sentences and one word of context. A probability model reports *what the data and the model structure support*, not what is linguistically natural.

## Part IX - Generated text

See `generated_sentences.txt` (20 sampled sentences per model, seed 42). First-order examples:
```
the cat ran to the park
the mat
the cat sat on the cat sat on the park
the dog ran to the cat ran to the cat sat on the park
```
Second-order examples: `the dog sat on the rug`, `the cat ran to the park`, ...

## Part X - Greedy vs sampling (Question 10)

First-order greedy (identical every run, hits the 20-token limit):
`the cat sat on the cat sat on the cat sat on ...`   (a cycle: `on -> the -> cat -> sat -> on`)
First-order sampling (5 sentences): `the mat`, `the dog sat on the dog ran to the park`, ...

**Q10.** **Sampling** produces much more variation. Greedy always picks the arg max, so after the first step it has no randomness: all five sentences are identical, and in the first-order model it can get stuck in a loop (the program needs a `max_len` guard). Sampling follows the whole distribution, so lower-probability words still appear in proportion to their probability.

## Part XI - Second-order model (Question 11)

Code: `second_order.py` (counts of triples; sentences padded with two `<START>` tokens).

**Q11.**
1. **Graph:** each `Xt` gains a second parent: `Xt-2 -> Xt <- Xt-1` (an extra edge `Xt-2 -> Xt`), instead of only `Xt-1 -> Xt`.
2. **CPT:** rows are indexed by *pairs* of words, so there are up to V² contexts instead of V (111 vs 11 here); each row is still a distribution over the next token.
3. **Context:** two words. The model can now distinguish `on the -> mat/rug` from `to the -> park`, which the first-order model cannot (it only sees `the`).
4. **Data:** many more parameters, so each context is observed far less often; much more data is needed to estimate it reliably.

## Part XIII - Comparison (Question 12)

Computed by `compare.py` (1000 sampled sentences per model):

| Measure | First-order | Second-order |
|---------|-------------|--------------|
| Non-zero parameters (observed entries) | 17 | 19 |
| Full CPT size (contexts × next tokens) | 121 | 1221 |
| Zero-probability CPT entries | 104 | 1202 |
| Possible contexts | 11 | 111 |
| Unseen contexts (no data at all) | 0 | 96 |
| Distinct sentences generated | 162 | 6 |
| Distinct sentences not in the training data | 156 | 0 |

**Qualitative coherence:**
- First-order: `the mat`, `the park`, `the rug` (ungrammatical), and cycles like `the cat sat on the cat sat on the park`, because it forgets the earlier context. 27 of 1000 samples hit the length limit.
- Second-order: only `the cat/dog sat on the mat/rug` and `the cat/dog ran to the park`: all grammatical, but they are exactly the 6 training sentences, so the model has **memorised** the data and generates nothing new.

**Q12.** More context makes predictions sharper because the conditioning set contains information the shorter context lacks (e.g. `to the -> park` vs `on the -> mat/rug`). But the CPT size grows exponentially with context length: V^k contexts for k tokens of context. Here the table grows 10× (121 → 1221 entries), while the training data stays the same size, so almost every context is unseen (96 of 111) or seen only once, and probabilities are estimated from very few samples. This is the trade-off between expressiveness and estimability (a bias-variance trade-off): the second-order model is more accurate on seen contexts but overfits and cannot generalise.

## Part XIV-XV - Modern LMs and the LLM's role (Question 13)

**Q13. Why is Approach B better?** "Implement P(Xt|Xt-1) from transition counts with sampling-based generation" gives a *specification* the generated code can be judged against:
- **Specifying behaviour:** the request fixes the model class, how it is estimated and how text is generated; a vague "write a language model" could return a neural network, a pretrained model or something unrelated.
- **Understanding the representation:** I know the data structure to look for (counts → CPT) and can find it in the code (Q4/Q5).
- **Validating the implementation:** I can compute the expected values by hand (e.g. `P(cat|the) = 3/12`) and compare.
- **Testing probabilistic invariants:** rows must sum to 1, sentence probabilities must sum to 1, sampling frequencies must match the CPT; none of these can be tested without a clear model.
- **Distinguishing implementation from model:** working code that prints plausible sentences is not evidence that it implements `P(Xt|Xt-1)`; the specification lets us check the model, not just the program.

## Final question (Question 14)

**Q14. What did the Bayesian network view give?**
1. **A factorisation of the joint distribution:** `P(X1..XT)` = a product of local conditionals, which tells us exactly what the CPTs must be and how to compute the probability of a sentence (tested in `test_chain_rule_sentence_probability`).
2. **A way to reason about independence assumptions:** the first-order graph says `Xt ⊥ X1..Xt-2 | Xt-1`; adding the edge `Xt-2 -> Xt` relaxes it. This explains the loops and nonsense of the first-order model.
3. **Understanding the effect of more context:** more parents means a larger CPT (V^k rows), directly explaining the data-hungriness result (Q12).
4. **A principled method for generation:** ancestral sampling, i.e. sampling each node from its CPT given its parents, in topological order.
5. **A way to test an implementation against its specification:** the CPT rows must be distributions, and the model's joint distribution must sum to 1.

## Reflection on the use of the LLM

> **Edit this part to reflect what happened in your own LLM session.** The lab requires at least one example of LLM-generated code you inspected or corrected, and which parts you generated or modified with an LLM. The points below are examples that came up building this solution; replace or add your own.

- **Specification first:** I wrote the probabilistic specification (variables, `P(Xt|Xt-1)`, counts, sampling) before asking for code (`prompts.txt`).
- **Code inspected and corrected - tie-breaking:** a typical first version uses `max(dist, key=dist.get)` for the "most probable word". For `the`, `cat` and `dog` are tied (3 each), so the result depended on dictionary insertion order. I changed it to an explicit, documented alphabetical tie-break so greedy generation is reproducible.
- **Code inspected and corrected - greedy loop:** the first greedy generation ran forever (`the cat sat on the cat sat on ...`) because the loop only stopped on `<END>`. I added `max_len` and a returned status (`END`, `MAX_LEN`, `UNSEEN`), and wrote a test that asserts this behaviour.
- **Code inspected and corrected - unseen context:** `probs[prev]` would raise `KeyError`; replaced with `probs.get(prev, {})`.
- **What I validated independently:** hand-computed counts and CPT values; normalisation of every row; the sum of all sentence probabilities for the second-order model; sampling frequencies versus the CPT; that sampling is not secretly arg max.

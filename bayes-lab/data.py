"""Training data and tokenisation shared by both models."""

START, END = "<START>", "<END>"

RAW_SENTENCES = [
    "the cat sat on the mat",
    "the cat sat on the rug",
    "the dog sat on the mat",
    "the dog ran to the park",
    "the cat ran to the park",
    "the dog sat on the rug",
]


def tokenise(sentence):
    """Lower-case, split into word tokens, add <START> and <END> markers."""
    return [START] + sentence.lower().split() + [END]


def training_data():
    return [tokenise(s) for s in RAW_SENTENCES]

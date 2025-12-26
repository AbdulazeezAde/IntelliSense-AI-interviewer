"""STT evaluation metrics helpers (e.g., WER)."""
from typing import List


def wer(ref: str, hyp: str) -> float:
    """Compute Word Error Rate (WER) between reference and hypothesis.
    Returns ratio (0.0 = perfect, 1.0 = all wrong, >1 = more errors than words).
    """
    r = ref.split()
    h = hyp.split()
    # compute Levenshtein distance
    n = len(r)
    m = len(h)
    # initialize matrix
    d = [[0] * (m+1) for _ in range(n+1)]
    for i in range(n+1):
        d[i][0] = i
    for j in range(m+1):
        d[0][j] = j
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = 0 if r[i-1] == h[j-1] else 1
            d[i][j] = min(
                d[i-1][j] + 1,      # deletion
                d[i][j-1] + 1,      # insertion
                d[i-1][j-1] + cost  # substitution
            )
    edits = d[n][m]
    return edits / max(1, n)

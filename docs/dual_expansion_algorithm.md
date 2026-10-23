# The Dual-Expansion Value Area Algorithm

## 1. The Mathematical Challenge

Given an empirical discrete distribution of market activity (either TPO counts $C_i$ or trade volume $V_i$) across sorted price rows $i \in \{0, 1, \dots, N-1\}$, we must identify a price interval $[\text{VAL}, \text{VAH}]$ such that:

$$
\sum_{i = \text{lower}}^{\text{upper}} C_i \ge \alpha \cdot \sum_{i = 0}^{N-1} C_i, \quad \text{with } \alpha = 0.70
$$

While keeping the interval **strictly contiguous** and centered dynamically around the **Point of Control (POC)**.

---

## 2. Why Naive Sorting Fails

A common mistake in quantitative implementations is sorting price rows by count in descending order and accumulating until 70% is reached:
- **Discontinuity Artifact ("Swiss Cheese")**: High-frequency rows may be non-adjacent (e.g., in a double distribution profile). Naive sorting produces a disjointed set of price levels with holes in between.
- **Violation of Auction Logic**: In economic terms, value cannot exist at $105 and $115 while being nonexistent at $110. Value Area must represent a **connected topological interval**.

---

## 3. The Dual-Expansion Solution

The **Dual-Expansion Algorithm** solves this problem by expanding outward from the mode of the distribution ($i_{\text{POC}}$) in discrete steps:

```text
               [ upper frontier ]  (up = upper + 1)
                      ▲
                      │  Compare C[up] vs C[down]
              [ upper boundary ]
                      ▲
               ... rows in VA ...
                      ▲
            [ Point of Control (POC) ] ── Seed (lower = upper = poc)
                      ▼
               ... rows in VA ...
                      ▼
              [ lower boundary ]
                      ▼
                      │  Compare C[down] vs C[up]
               [ lower frontier ]  (down = lower - 1)
```

### Pseudo-code Specification:

```python
def dual_expansion(counts, target_fraction=0.70):
    # 1. Seed at Point of Control
    poc = argmax(counts)
    lower = poc
    upper = poc
    accumulated = counts[poc]
    target = sum(counts) * target_fraction

    # 2. Dual Expansion Loop
    while accumulated < target and (lower > 0 or upper < len(counts) - 1):
        down = lower - 1 if lower > 0 else None
        up = upper + 1 if upper < len(counts) - 1 else None

        if down is None:
            choose_up = True
        elif up is None:
            choose_up = False
        else:
            if counts[up] != counts[down]:
                choose_up = counts[up] > counts[down]
            else:
                # Tie-breaker: choose side closer to POC
                choose_up = (up - poc) <= (poc - down)

        if choose_up:
            upper += 1
            accumulated += counts[upper]
        else:
            lower -= 1
            accumulated += counts[lower]

    return lower, upper, accumulated
```

---

## 4. Key Mathematical Invariants

1. **Spatial Contiguity**:
   The resulting Value Area is strictly contiguous:
   $$
   \forall p \in [\text{VAL}, \text{VAH}], \quad p \text{ is in Value Area}
   $$
2. **Minimal Asymmetric Distortion**:
   By greedily taking the frontier row with the strictly greater activity, the algorithm guarantees the shortest possible interval containing the required 70% mass around the mode.
3. **Exact Boundary Alignment**:
   $$
   \text{VAL} = \text{Price}_{\text{lower}} - \frac{\text{row\_size}}{2}
   $$
   $$
   \text{VAH} = \text{Price}_{\text{upper}} + \frac{\text{row\_size}}{2}
   $$

# Normalized scoring model

Every dimension uses a 0-10 scale where a higher value is better. Do not mix
benefit and cost directions in the matrix.

| Dimension | Weight | 10 means |
|---|---:|---|
| Repository fit | 0.25 | Uses verified existing capabilities with minimal mismatch |
| Delivery confidence | 0.20 | Clear dependencies, owners, and executable path |
| Maintainability | 0.15 | Low long-term drift and understandable ownership |
| Reversibility | 0.15 | Fast, tested, low-loss rollback |
| Safety | 0.15 | Narrow permissions and strong approval/validation gates |
| Efficiency | 0.10 | Low implementation and operating cost for the delivered value |

Compute:

```text
score =
  0.25 * repository_fit +
  0.20 * delivery_confidence +
  0.15 * maintainability +
  0.15 * reversibility +
  0.15 * safety +
  0.10 * efficiency
```

Round only the final score to two decimals. The weights sum to 1.00, so the
result stays within 0-10.

If evidence is expressed as a cost from 0 (free) to 10 (prohibitive), convert it
before scoring: `efficiency = 10 - cost`. Record both values so the conversion is
auditable. Never enter raw cost directly in the higher-is-better matrix.

## Scoring discipline

- Cite repository evidence for each value.
- Mark unsupported values `[ASSUMPTION]` and include a confidence note.
- Treat a difference below 0.30 as a near tie unless one flow violates a hard
  constraint.
- Explain any override of the numerical winner.
- Recalculate when the user changes a constraint.

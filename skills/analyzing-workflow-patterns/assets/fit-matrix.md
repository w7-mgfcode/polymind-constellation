# Fit matrix

Use 0-10 values where higher is always better. Copy one row per candidate flow.

| Flow | Repository fit 25% | Delivery confidence 20% | Maintainability 15% | Reversibility 15% | Safety 15% | Efficiency 10% | Weighted score | Confidence |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| {{WORKFLOW_NAME}} | 0 | 0 | 0 | 0 | 0 | 0 | 0.00 | low/medium/high |

Formula:

```text
weighted_score =
  repository_fit * 0.25 +
  delivery_confidence * 0.20 +
  maintainability * 0.15 +
  reversibility * 0.15 +
  safety * 0.15 +
  efficiency * 0.10
```

## Decision checkpoint

- **Recommended flow:** {{WORKFLOW_NAME}}
- **Decisive evidence:** [two or more repository findings]
- **Primary trade-off:** [benefit exchanged for limitation]
- **Assumptions:** [labeled assumptions or `none`]
- **Near-tie sensitivity:** [what could change the result or `none`]
- **Approval question:** Which flow, if any, should become a mutation plan?

Stop after this checkpoint. Selection does not authorize writes.

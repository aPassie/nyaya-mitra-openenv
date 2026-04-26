# Baseline comparison

Real numbers from running each baseline against the 30 held-out eval cases.

| Baseline | Mean reward | Median | Gates passed | Integrated solved | Sensitivity F1 |
|---|---|---|---|---|---|
| **random** | 0.325 | 0.303 | 100.0% | 60.0% | 0.60 |
| **scripted** | 0.509 | 0.538 | 100.0% | 50.0% | 0.62 |
| **prompted-LLM (stub)** | 0.355 | 0.344 | 100.0% | 0.0% | 0.60 |

Per-cohort means for each baseline:

### random
| Cohort | n | mean | gates | integrated solved |
|---|---|---|---|---|
| welfare_only | 10 | 0.326 | 100.0% | 0.0% |
| legal_only | 10 | 0.206 | 100.0% | 0.0% |
| integrated | 10 | 0.443 | 100.0% | 60.0% |

### scripted
| Cohort | n | mean | gates | integrated solved |
|---|---|---|---|---|
| welfare_only | 10 | 0.589 | 100.0% | 0.0% |
| legal_only | 10 | 0.416 | 100.0% | 0.0% |
| integrated | 10 | 0.522 | 100.0% | 50.0% |

### prompted-LLM (stub)
| Cohort | n | mean | gates | integrated solved |
|---|---|---|---|---|
| welfare_only | 10 | 0.321 | 100.0% | 0.0% |
| legal_only | 10 | 0.393 | 100.0% | 0.0% |
| integrated | 10 | 0.351 | 100.0% | 0.0% |

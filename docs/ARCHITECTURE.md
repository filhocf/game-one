# Architecture — Game One

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                    Game One                          │
│                                                     │
│  ┌─────────────┐    ┌──────────────────────────┐   │
│  │  Data Input │───►│    Diagnóstico (370 LOC)  │   │
│  │  (draws)    │    │  - RQA                    │   │
│  └─────────────┘    │  - Lyapunov exponents     │   │
│                     │  - Permutation entropy     │   │
│                     │  - Surrogate testing       │   │
│                     └────────────┬───────────────┘   │
│                                  │                   │
│              ┌───────────────────┼────────────────┐  │
│              │                   │                │  │
│              ▼                   ▼                │  │
│  ┌───────────────────┐  ┌──────────────────┐    │  │
│  │  Ramo A (Stats)   │  │  Ramo B (ML)     │    │  │
│  │  - Chaos engine   │  │  - Feature eng.  │    │  │
│  │  - Phase space    │  │  - Prediction    │    │  │
│  │  - Attractors     │  │  - Ensembles     │    │  │
│  └────────┬──────────┘  └────────┬─────────┘    │  │
│           │                      │               │  │
│           └──────────┬───────────┘               │  │
│                      ▼                           │  │
│           ┌──────────────────┐                   │  │
│           │    Sugestões     │                   │  │
│           │  (Suggestions)   │                   │  │
│           └────────┬─────────┘                   │  │
│                    ▼                             │  │
│           ┌──────────────────┐                   │  │
│           │   Backtesting    │                   │  │
│           │  (Validation)    │                   │  │
│           └──────────────────┘                   │  │
└─────────────────────────────────────────────────────┘
```

## Module Details

### diagnóstico.py (370 LOC)
Core diagnostic engine implementing:
- **RQA** — Recurrence plots, determinism, laminarity, trapping time
- **Lyapunov Exponents** — Largest Lyapunov exponent via Rosenstein method
- **Permutation Entropy** — Complexity measure for time series
- **Surrogate Testing** — IAAFT surrogates for null hypothesis testing
- **Summary Report** — Consolidated chaos/randomness verdict

### Motor de Caos (Chaos Engine)
- Time-delay embedding (Takens' theorem)
- Phase space reconstruction
- Attractor dimension estimation
- Recurrence matrix computation

### Sugestões (Suggestions)
- Combines outputs from Ramo A and Ramo B
- Weighted scoring based on diagnostic confidence
- Number set generation with diversity constraints

### Backtesting
- Walk-forward validation on historical draws
- Hit rate calculation (exact, partial matches)
- Comparison against random baseline
- Statistical significance testing of results

## Data Flow

1. Historical draw data loaded
2. Diagnóstico runs full chaos analysis
3. Results feed into both Ramo A (statistical) and Ramo B (ML)
4. Sugestões merges branch outputs into final predictions
5. Backtesting validates against held-out data

## Dependencies

- NumPy — Numerical computation
- SciPy — Signal processing, statistical tests
- scikit-learn — ML models (Ramo B)
- Matplotlib — Visualization (recurrence plots, phase space)

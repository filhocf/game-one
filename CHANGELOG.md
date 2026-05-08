# Changelog

## [0.5.0] - 2026-05-08

### Added

- **Diagnóstico Module (370 LOC)**
  - Recurrence Quantification Analysis (RQA) implementation
  - Largest Lyapunov exponent estimation (Rosenstein method)
  - Permutation entropy calculation with configurable embedding
  - Surrogate data generation (IAAFT method)
  - Statistical significance testing against surrogates
  - Consolidated diagnostic report output

- **Motor de Caos (Chaos Engine)**
  - Time-delay embedding via Takens' theorem
  - Optimal delay estimation (mutual information)
  - Embedding dimension selection (false nearest neighbors)
  - Phase space reconstruction
  - Recurrence matrix computation with configurable threshold

- **Ramo A — Statistical Branch**
  - Attractor reconstruction and visualization
  - Determinism and laminarity metrics
  - Entropy-based randomness quantification
  - Chaos vs. noise classification

- **Ramo B — Machine Learning Branch**
  - Feature engineering from nonlinear metrics
  - Sequence pattern recognition
  - Prediction model training pipeline

- **Sugestões (Suggestions)**
  - Multi-branch output fusion
  - Weighted number scoring
  - Suggestion set generation with diversity constraints

- **Backtesting**
  - Walk-forward validation framework
  - Hit rate metrics (exact, partial)
  - Random baseline comparison
  - Statistical significance of results

### Technical

- 22 commits
- Python project structure
- Scientific computing stack (NumPy, SciPy, scikit-learn, Matplotlib)

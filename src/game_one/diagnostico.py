"""Módulo de diagnóstico avançado — testes de aleatoriedade e detecção de estrutura."""

from collections import Counter
from itertools import permutations
from math import factorial, log

import numpy as np
from scipy import stats
from scipy.spatial.distance import pdist, squareform

from .caos import _carregar_concursos
from .coleta import JOGOS


# ── 1. Entropy Tests ──

def permutation_entropy(x: np.ndarray, order: int = 3, delay: int = 1) -> float:
    """Permutation Entropy (Bandt & Pompe). Normalizado em [0, 1]."""
    n = len(x)
    perms = Counter()
    for i in range(n - (order - 1) * delay):
        window = tuple(x[i + j * delay] for j in range(order))
        perms[tuple(np.argsort(window))] += 1
    total = sum(perms.values())
    if total == 0:
        return 0.0
    probs = np.array(list(perms.values())) / total
    h = -np.sum(probs * np.log2(probs))
    return float(h / log(factorial(order), 2))


def sample_entropy(x: np.ndarray, m: int = 2, r: float | None = None) -> float:
    """Sample Entropy (Richman & Moorman)."""
    if r is None:
        r = 0.2 * np.std(x)
    n = len(x)

    def _count_matches(template_len):
        templates = np.array([x[i:i + template_len] for i in range(n - template_len)])
        count = 0
        for i in range(len(templates)):
            dists = np.max(np.abs(templates[i] - templates[i + 1:]), axis=1)
            count += np.sum(dists <= r)
        return count

    a = _count_matches(m)
    b = _count_matches(m + 1)
    if a == 0 or b == 0:
        return float('inf')
    return float(-np.log(b / a))


def _entropy_tests(serie: np.ndarray) -> dict:
    pe = permutation_entropy(serie, order=3, delay=1)
    se = sample_entropy(serie, m=2)
    # Baseline i.i.d.: PE deve ser ~1.0 para dados aleatórios
    n_surr = 30
    pe_surr = []
    for _ in range(n_surr):
        s = np.random.permutation(serie)
        pe_surr.append(permutation_entropy(s, order=3, delay=1))
    pe_mean, pe_std = np.mean(pe_surr), np.std(pe_surr)
    pe_z = (pe - pe_mean) / pe_std if pe_std > 0 else 0.0
    return {
        "permutation_entropy": round(pe, 4),
        "sample_entropy": round(se, 4),
        "pe_baseline_mean": round(pe_mean, 4),
        "pe_z_score": round(pe_z, 2),
        "pe_significativo": abs(pe_z) > 1.96,
        "interpretacao": "estrutura detectada" if abs(pe_z) > 1.96 else "compatível com i.i.d.",
    }


# ── 2. RQA (Recurrence Quantification Analysis) ──

def _takens_embedding(x: np.ndarray, dim: int = 3, delay: int = 1) -> np.ndarray:
    n = len(x) - (dim - 1) * delay
    return np.array([x[i:i + dim * delay:delay] for i in range(n)])


def _recurrence_matrix(embedded: np.ndarray, threshold: float) -> np.ndarray:
    dists = squareform(pdist(embedded, metric='chebyshev'))
    return (dists <= threshold).astype(int)


def _rqa_metrics(R: np.ndarray) -> dict:
    n = R.shape[0]
    np.fill_diagonal(R, 0)
    total_recurrence = R.sum()
    rr = total_recurrence / (n * (n - 1)) if n > 1 else 0

    # Diagonal lines (DET)
    diag_lengths = []
    for k in range(1, n):
        diag = np.diag(R, k)
        length = 0
        for v in diag:
            if v:
                length += 1
            elif length >= 2:
                diag_lengths.append(length)
                length = 0
        if length >= 2:
            diag_lengths.append(length)

    det = sum(diag_lengths) / total_recurrence if total_recurrence > 0 else 0

    # Vertical lines (LAM)
    vert_lengths = []
    for col in range(n):
        length = 0
        for row in range(n):
            if R[row, col]:
                length += 1
            elif length >= 2:
                vert_lengths.append(length)
                length = 0
        if length >= 2:
            vert_lengths.append(length)

    lam = sum(vert_lengths) / total_recurrence if total_recurrence > 0 else 0

    # ENTR (Shannon entropy of diagonal line lengths)
    if diag_lengths:
        counts = Counter(diag_lengths)
        total_lines = sum(counts.values())
        probs = np.array(list(counts.values())) / total_lines
        entr = float(-np.sum(probs * np.log2(probs)))
    else:
        entr = 0.0

    return {"RR": round(rr, 4), "DET": round(det, 4), "LAM": round(lam, 4), "ENTR": round(entr, 4)}


def _rqa_analysis(freq_series: np.ndarray) -> dict:
    embedded = _takens_embedding(freq_series, dim=3, delay=1)
    threshold = 0.1 * np.std(freq_series)
    if threshold == 0:
        threshold = 1.0
    R = _recurrence_matrix(embedded, threshold)
    metrics = _rqa_metrics(R)
    return metrics


# ── 3. Surrogate Data Testing ──

def _surrogate_test(serie: np.ndarray, freq_series: np.ndarray, n_surrogates: int = 100) -> dict:
    # Métricas reais
    real_pe = permutation_entropy(serie, order=3, delay=1)
    embedded = _takens_embedding(freq_series, dim=3, delay=1)
    threshold = 0.1 * np.std(freq_series)
    if threshold == 0:
        threshold = 1.0
    R = _recurrence_matrix(embedded, threshold)
    real_rqa = _rqa_metrics(R)

    surr_pe, surr_det, surr_lam = [], [], []
    for _ in range(n_surrogates):
        s_serie = np.random.permutation(serie)
        surr_pe.append(permutation_entropy(s_serie, order=3, delay=1))

        # Recalcular freq_series para surrogate
        max_num = int(serie.max())
        s_freq = np.zeros(len(freq_series))
        window = max(10, len(freq_series) // 10)
        # Simplificação: shuffle da freq_series diretamente
        s_freq = np.random.permutation(freq_series)
        s_emb = _takens_embedding(s_freq, dim=3, delay=1)
        s_R = _recurrence_matrix(s_emb, threshold)
        s_rqa = _rqa_metrics(s_R)
        surr_det.append(s_rqa["DET"])
        surr_lam.append(s_rqa["LAM"])

    ci_pe = (np.percentile(surr_pe, 2.5), np.percentile(surr_pe, 97.5))
    ci_det = (np.percentile(surr_det, 2.5), np.percentile(surr_det, 97.5))
    ci_lam = (np.percentile(surr_lam, 2.5), np.percentile(surr_lam, 97.5))

    pe_sig = real_pe < ci_pe[0] or real_pe > ci_pe[1]
    det_sig = real_rqa["DET"] < ci_det[0] or real_rqa["DET"] > ci_det[1]
    lam_sig = real_rqa["LAM"] < ci_lam[0] or real_rqa["LAM"] > ci_lam[1]

    return {
        "n_surrogates": n_surrogates,
        "PE": {"real": round(real_pe, 4), "ci_95": (round(ci_pe[0], 4), round(ci_pe[1], 4)), "significativo": pe_sig},
        "DET": {"real": real_rqa["DET"], "ci_95": (round(ci_det[0], 4), round(ci_det[1], 4)), "significativo": det_sig},
        "LAM": {"real": real_rqa["LAM"], "ci_95": (round(ci_lam[0], 4), round(ci_lam[1], 4)), "significativo": lam_sig},
        "padrao_real": pe_sig or det_sig or lam_sig,
    }


# ── 4. Changepoint Detection ──

def _changepoint_detection(freq_matrix: np.ndarray, window: int = 50) -> dict:
    """Sliding window chi-square sobre frequências de dezenas."""
    n = freq_matrix.shape[0]
    if n < window * 2:
        return {"breakpoints": [], "chi2_series": [], "threshold": 0, "interpretacao": "dados insuficientes"}

    chi2_vals = []
    for i in range(window, n - window):
        left = freq_matrix[i - window:i].sum(axis=0)
        right = freq_matrix[i:i + window].sum(axis=0)
        # Normalizar
        left_norm = left / left.sum() if left.sum() > 0 else left
        right_norm = right / right.sum() if right.sum() > 0 else right
        # Chi-square entre as duas distribuições
        expected = (left + right) / 2
        expected = np.where(expected == 0, 1e-10, expected)
        chi2 = np.sum((left - expected) ** 2 / expected) + np.sum((right - expected) ** 2 / expected)
        chi2_vals.append(chi2)

    chi2_arr = np.array(chi2_vals)
    # Threshold: percentil 99 de chi2 com (max_num - 1) graus de liberdade
    df = freq_matrix.shape[1] - 1
    threshold = stats.chi2.ppf(0.99, df)

    breakpoints = []
    # Detectar picos acima do threshold
    above = chi2_arr > threshold
    in_peak = False
    peak_start = 0
    for i, a in enumerate(above):
        if a and not in_peak:
            in_peak = True
            peak_start = i
        elif not a and in_peak:
            in_peak = False
            peak_idx = peak_start + np.argmax(chi2_arr[peak_start:i])
            breakpoints.append({
                "posicao": int(peak_idx + window),
                "chi2": round(float(chi2_arr[peak_idx]), 2),
            })

    return {
        "breakpoints": breakpoints,
        "n_breakpoints": len(breakpoints),
        "threshold": round(threshold, 2),
        "chi2_mean": round(float(chi2_arr.mean()), 2),
        "chi2_max": round(float(chi2_arr.max()), 2),
        "interpretacao": f"{len(breakpoints)} mudança(s) de regime detectada(s)" if breakpoints else "sem mudanças de regime",
    }


# ── 5. Lyapunov Exponent ──

def _lyapunov_exponent(x: np.ndarray, dim: int = 3, delay: int = 1, min_sep: int = 5) -> dict:
    """Estima o maior expoente de Lyapunov (método de Rosenstein et al.)."""
    embedded = _takens_embedding(x, dim=dim, delay=delay)
    n = len(embedded)
    if n < 20:
        return {"lyapunov": 0.0, "interpretacao": "dados insuficientes"}

    dists = squareform(pdist(embedded))
    # Para cada ponto, encontrar o vizinho mais próximo (excluindo temporalmente próximos)
    max_iter = min(n // 4, 50)
    divergences = np.zeros(max_iter)
    counts = np.zeros(max_iter)

    for i in range(n - max_iter):
        # Mascarar vizinhos temporais
        d = dists[i].copy()
        d[max(0, i - min_sep):min(n, i + min_sep + 1)] = np.inf
        j = np.argmin(d)
        if d[j] == np.inf or d[j] == 0:
            continue
        for k in range(max_iter):
            if i + k < n and j + k < n:
                dist_k = np.linalg.norm(embedded[i + k] - embedded[j + k])
                if dist_k > 0:
                    divergences[k] += np.log(dist_k)
                    counts[k] += 1

    valid = counts > 0
    if valid.sum() < 5:
        return {"lyapunov": 0.0, "interpretacao": "dados insuficientes"}

    mean_div = np.where(valid, divergences / np.where(counts > 0, counts, 1), np.nan)
    # Fit linear na parte inicial
    valid_idx = np.where(valid)[0]
    t = valid_idx[:min(20, len(valid_idx))]
    y = mean_div[t]
    if len(t) < 3:
        return {"lyapunov": 0.0, "interpretacao": "dados insuficientes"}

    slope, _, _, _, _ = stats.linregress(t, y)
    lyap = float(slope)

    if lyap > 0.01:
        interp = "caos determinístico (λ > 0)"
    elif lyap < -0.01:
        interp = "dinâmica periódica/convergente (λ < 0)"
    else:
        interp = "edge of chaos (λ ≈ 0)"

    return {"lyapunov": round(lyap, 4), "interpretacao": interp}


# ── Função principal ──

def diagnosticar(jogo: str) -> dict:
    """Roda todos os testes de diagnóstico e retorna relatório completo."""
    info = JOGOS[jogo]
    max_num = info["max_numero"]
    concursos = _carregar_concursos(jogo)

    # Série flat de dezenas sorteadas (ordem temporal)
    serie = np.array([d for c in concursos for d in sorted(c["dezenas"])])

    # Série de frequências por dezena (rolling window)
    window = 30
    n_conc = len(concursos)
    freq_series_list = []
    for i in range(window, n_conc):
        counts = Counter()
        for c in concursos[i - window:i]:
            counts.update(c["dezenas"])
        freq_series_list.append([counts.get(d, 0) / window for d in range(1, max_num + 1)])
    freq_series = np.array(freq_series_list)

    # Série 1D para RQA/Lyapunov: média das frequências
    freq_mean = freq_series.mean(axis=1)

    # Matriz binária de ocorrência por concurso (para changepoint)
    freq_matrix = np.zeros((n_conc, max_num))
    for i, c in enumerate(concursos):
        for d in c["dezenas"]:
            freq_matrix[i, d - 1] = 1

    print(f"  Diagnosticando {info['nome']} ({n_conc} concursos)...", flush=True)

    print("  [1/5] Entropy tests...", flush=True)
    entropy = _entropy_tests(serie)

    print("  [2/5] RQA...", flush=True)
    rqa = _rqa_analysis(freq_mean)

    print("  [3/5] Surrogate testing (100 surrogates)...", flush=True)
    surrogate = _surrogate_test(serie, freq_mean, n_surrogates=100)

    print("  [4/5] Changepoint detection...", flush=True)
    changepoint = _changepoint_detection(freq_matrix)

    print("  [5/5] Lyapunov exponent...", flush=True)
    lyapunov = _lyapunov_exponent(freq_mean)

    # Veredito geral
    sinais = []
    if entropy["pe_significativo"]:
        sinais.append("entropy")
    if surrogate["padrao_real"]:
        sinais.append("surrogate")
    if rqa["DET"] > 0.05:
        sinais.append(f"DET={rqa['DET']}")
    if changepoint["n_breakpoints"] > 0:
        sinais.append(f"{changepoint['n_breakpoints']} breakpoints")
    if lyapunov["lyapunov"] > 0.01:
        sinais.append("caos")

    return {
        "jogo": jogo,
        "nome": info["nome"],
        "total_concursos": n_conc,
        "entropy": entropy,
        "rqa": rqa,
        "surrogate": surrogate,
        "changepoint": changepoint,
        "lyapunov": lyapunov,
        "sinais_estrutura": sinais,
        "veredito": "ESTRUTURA DETECTADA" if sinais else "COMPATÍVEL COM ALEATORIEDADE",
    }

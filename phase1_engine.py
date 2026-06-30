"""
Trading Desportivo Quantitativo — Motor da Fase 1 (simulacao, zero dinheiro real)
=================================================================================
Pergunta unica que este motor responde:
    "O modelo consegue, de forma sistematica e sem look-ahead, obter precos
     melhores do que a linha de fecho (CLV positivo)?"

NAO mede lucro como prova (300 apostas e ruido para o ROI). A metrica de decisao
e o CLV. Ver README.md e a proposta tecnica.

Metodologia (sem vies de antecipacao):
    - Probabilidade do modelo = devig das odds PINNACLE *de abertura* (PSH/PSD/PSA).
      A Pinnacle e o estimador mais afiado; usa-se a info disponivel ANTES do fecho.
    - Odds "alvo" (onde apostariamos) = casa soft *de abertura* (Bet365: B365H/D/A),
      proxy de uma casa legal portuguesa mais lenta que a Pinnacle.
    - Sinal de value: edge = p_modelo * odd_alvo - 1 > limiar.  (so info de abertura)
    - Filtros (regras inegociaveis do Tiago): odd_alvo em [1.65, 2.50]; so singles;
      stake fixa 2% (teto rigido); so apostas com edge > limiar.
    - CLV (avaliacao, pode usar o fecho que ocorre DEPOIS): comparamos a odd a que
      apostamos com a odd justa de FECHO da Pinnacle (PSCH/PSCD/PSCA, sem vig).
    - P/L liquido usa o resultado real (FTR) e zero comissao (casa legal != exchange).

Formato de dados: CSV estilo football-data.co.uk (uma linha por jogo).
Colunas necessarias: Date, HomeTeam, AwayTeam, FTR,
    PSH,PSD,PSA  (Pinnacle abertura)  e  PSCH,PSCD,PSCA (Pinnacle fecho),
    B365H,B365D,B365A (Bet365 abertura).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# 1. DEVIG — remover a margem ("vig") e obter probabilidades justas
# --------------------------------------------------------------------------- #
def devig_multiplicative(odds):
    """Metodo proporcional. odds = [home, draw, away] -> probabilidades que somam 1."""
    inv = np.array([1.0 / o for o in odds], dtype=float)
    return inv / inv.sum()


def fair_odds_from(odds):
    """Odds justas (sem vig) a partir de odds com margem."""
    p = devig_multiplicative(odds)
    return 1.0 / p


# --------------------------------------------------------------------------- #
# 2. CONFIGURACAO — as regras do Tiago, em codigo
# --------------------------------------------------------------------------- #
@dataclass
class Rules:
    odd_min: float = 1.65          # regra 5
    odd_max: float = 2.50          # regra 5
    stake_pct: float = 0.02        # regra 2: teto rigido 2%
    edge_threshold: float = 0.02   # regra 4: so value matematico (>2% por defeito)
    commission: float = 0.0        # casa legal PT = sem comissao (exchange seria 0.02-0.06)
    allow_multiples: bool = False  # regra 6: nunca multiplas
    bankroll0: float = 500.0       # banca virtual


# --------------------------------------------------------------------------- #
# 3. GERACAO DE SINAIS + SETTLEMENT
# --------------------------------------------------------------------------- #
SELECTIONS = ["H", "D", "A"]
COL_PINN_OPEN = {"H": "PSH", "D": "PSD", "A": "PSA"}
COL_PINN_CLOSE = {"H": "PSCH", "D": "PSCD", "A": "PSCA"}
COL_SOFT_OPEN = {"H": "B365H", "D": "B365D", "A": "B365A"}


@dataclass
class Bet:
    date: str
    match: str
    selection: str
    odd_taken: float        # odd alvo (abertura soft) — onde apostamos
    model_prob: float       # prob justa Pinnacle abertura
    edge: float             # p_modelo*odd - 1 (no momento da aposta)
    fair_close_odd: float   # odd justa Pinnacle fecho
    clv: float              # odd_taken / fair_close_odd - 1
    won: bool
    pnl_units: float        # lucro/prejuizo em unidades de stake (apos comissao)


def generate_bets(df: pd.DataFrame, rules: Rules) -> list[Bet]:
    """Percorre os jogos e produz no maximo 1 aposta por jogo (a de maior edge)."""
    bets: list[Bet] = []
    needed = (list(COL_PINN_OPEN.values()) + list(COL_PINN_CLOSE.values())
              + list(COL_SOFT_OPEN.values()) + ["FTR"])
    for _, row in df.iterrows():
        if any(pd.isna(row.get(c)) for c in needed):
            continue
        try:
            pinn_open = [float(row[COL_PINN_OPEN[s]]) for s in SELECTIONS]
            pinn_close = [float(row[COL_PINN_CLOSE[s]]) for s in SELECTIONS]
            soft_open = [float(row[COL_SOFT_OPEN[s]]) for s in SELECTIONS]
        except (ValueError, TypeError):
            continue
        if min(pinn_open + pinn_close + soft_open) <= 1.0:
            continue

        model_p = devig_multiplicative(pinn_open)          # info de abertura, sem look-ahead
        fair_close = fair_odds_from(pinn_close)            # so usado para CLV (pos-aposta)

        # candidata: a selecao com maior edge que cumpre TODOS os filtros
        best = None
        for i, s in enumerate(SELECTIONS):
            odd = soft_open[i]
            if not (rules.odd_min <= odd <= rules.odd_max):
                continue
            edge = model_p[i] * odd - 1.0
            if edge <= rules.edge_threshold:
                continue
            if best is None or edge > best[1]:
                best = (s, edge, odd, model_p[i], fair_close[i])

        if best is None:
            continue
        s, edge, odd, mp, fclose = best
        won = (row["FTR"] == s)
        # P/L em unidades de stake, liquido de comissao sobre ganhos
        if won:
            gross = odd - 1.0
            pnl = gross * (1.0 - rules.commission)
        else:
            pnl = -1.0
        clv = odd / fclose - 1.0
        bets.append(Bet(
            date=str(row.get("Date", "")),
            match=f'{row.get("HomeTeam","?")} v {row.get("AwayTeam","?")}',
            selection=s, odd_taken=odd, model_prob=mp, edge=edge,
            fair_close_odd=fclose, clv=clv, won=won, pnl_units=pnl,
        ))
    return bets


# --------------------------------------------------------------------------- #
# 4. METRICAS
# --------------------------------------------------------------------------- #
def _bootstrap_ci(x: np.ndarray, n_boot=10000, alpha=0.05, seed=42):
    if len(x) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    means = x[idx].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


@dataclass
class Metrics:
    n_bets: int
    # --- PRIMARIO: yield realizado (resultado e independente do ruido de selecao) ---
    yield_pct: float           # = media do P/L por aposta, em % (lucro/total apostado)
    yield_ci: tuple            # IC95% bootstrap do yield
    yield_significant_pos: bool  # IC95% acima de zero?
    # --- SECUNDARIO/diagnostico: CLV e o seu placebo ---
    clv_mean: float
    clv_ci: tuple
    placebo_clv_mean: float    # CLV de apostas ALEATORIAS na mesma banda de odds
    excess_clv_mean: float     # clv_mean - placebo_clv (tira o vies de selecao-ruido)
    # --- contexto ---
    roi_pct: float
    max_drawdown_pct: float
    hit_rate: float
    avg_odds: float
    final_bankroll: float
    required_n_for_yield: float


def _empty_metrics(rules):
    return Metrics(0, 0, (float("nan"),) * 2, False, float("nan"),
                   (float("nan"),) * 2, float("nan"), float("nan"),
                   0, 0, 0, 0, rules.bankroll0, float("inf"))


def compute_metrics(bets: list[Bet], rules: Rules,
                    placebo_clv: float = float("nan")) -> Metrics:
    n = len(bets)
    if n == 0:
        return _empty_metrics(rules)

    pnl_units = np.array([b.pnl_units for b in bets])
    clv = np.array([b.clv for b in bets])
    odds = np.array([b.odd_taken for b in bets])
    wins = np.array([b.won for b in bets])

    # Banca com stake FIXA = 2% da banca INICIAL (staking plano, conservador)
    stake = rules.stake_pct * rules.bankroll0
    pnl_money = pnl_units * stake
    equity = rules.bankroll0 + np.cumsum(pnl_money)
    peak = np.maximum.accumulate(np.concatenate([[rules.bankroll0], equity]))
    dd = (np.concatenate([[rules.bankroll0], equity]) - peak) / peak
    max_dd = float(dd.min())

    # Yield = media do P/L por unidade de stake (resultado real, sem vies de selecao)
    yield_pct = float(pnl_units.mean()) * 100
    ylo, yhi = _bootstrap_ci(pnl_units)
    roi_pct = pnl_money.sum() / rules.bankroll0 * 100

    clv_mean = float(clv.mean())
    clv_lo, clv_hi = _bootstrap_ci(clv)

    sd = pnl_units.std(ddof=1)
    eff = abs(pnl_units.mean())
    required_n = float("inf") if eff == 0 else (1.96 * sd / eff) ** 2

    return Metrics(
        n_bets=n,
        yield_pct=yield_pct, yield_ci=(ylo * 100, yhi * 100),
        yield_significant_pos=(ylo > 0),
        clv_mean=clv_mean, clv_ci=(clv_lo, clv_hi),
        placebo_clv_mean=placebo_clv,
        excess_clv_mean=clv_mean - placebo_clv,
        roi_pct=roi_pct, max_drawdown_pct=max_dd * 100,
        hit_rate=float(wins.mean()), avg_odds=float(odds.mean()),
        final_bankroll=float(equity[-1]), required_n_for_yield=required_n,
    )


def placebo_clv(df: pd.DataFrame, rules: Rules, seed: int = 11) -> float:
    """CLV medio de apostas ALEATORIAS dentro da banda de odds (sem filtro de edge).
    Serve de linha-base: se as apostas com 'value' nao baterem este placebo, o
    'CLV' observado e apenas vies de selecao-sobre-ruido, nao skill."""
    rng = np.random.default_rng(seed)
    clvs = []
    for _, row in df.iterrows():
        cand = []
        for s in SELECTIONS:
            try:
                odd = float(row[COL_SOFT_OPEN[s]])
                pcl = [float(row[COL_PINN_CLOSE[t]]) for t in SELECTIONS]
            except (ValueError, TypeError, KeyError):
                cand = []; break
            if rules.odd_min <= odd <= rules.odd_max and min(pcl) > 1.0:
                fair_close = fair_odds_from(pcl)[SELECTIONS.index(s)]
                cand.append(odd / fair_close - 1.0)
        if cand:
            clvs.append(rng.choice(cand))
    return float(np.mean(clvs)) if clvs else float("nan")


# --------------------------------------------------------------------------- #
# 5. VEREDICTO GO / NO-GO  (criterios fixados ANTES de correr)
# --------------------------------------------------------------------------- #
def verdict(m: Metrics, yield_target=0.0) -> str:
    ylo, yhi = m.yield_ci
    L = ["=" * 66,
         "VEREDICTO FASE 1 — primario: YIELD realizado (CLV so como cross-check)",
         "=" * 66]
    if m.n_bets < 200:
        L.append(f"AMOSTRA INSUFICIENTE: {m.n_bets} apostas (<200). Recolher mais.")
        return "\n".join(L)

    if m.yield_significant_pos:
        L.append(f"SINAL POSITIVO: yield {m.yield_pct:+.2f}% "
                 f"(IC95% [{ylo:+.2f}%, {yhi:+.2f}%]) — significativamente acima de zero.")
        if not np.isnan(m.excess_clv_mean) and m.excess_clv_mean > 0:
            L.append(f"   Cross-check OK: CLV {m.clv_mean*100:+.2f}% vs placebo "
                     f"{m.placebo_clv_mean*100:+.2f}% (excesso {m.excess_clv_mean*100:+.2f}%).")
        L.append(">> Evidencia de edge. Avancar para planeamento Fase 2 "
                 "(amostra ainda maior + caminho legal/limitacao de contas).")
    else:
        L.append(f"SEM EDGE PROVADA: yield {m.yield_pct:+.2f}% "
                 f"(IC95% [{ylo:+.2f}%, {yhi:+.2f}%]) — inclui ou esta abaixo de zero.")
        L.append('>> CONCLUSAO: "Nao existe vantagem comprovada." Encerrar, sem drama.')
        if not np.isnan(m.clv_mean):
            L.append(f"   (CLV bruto {m.clv_mean*100:+.2f}% vs placebo "
                     f"{m.placebo_clv_mean*100:+.2f}%: o CLV bruto sozinho enganaria — "
                     "por isso o yield manda.)")

    L.append("-" * 66)
    L.append(f"Nota de potencia: para o yield observado ser significativo seriam "
             f"precisas ~{m.required_n_for_yield:,.0f} apostas.")
    return "\n".join(L)


def format_report(m: Metrics, rules: Rules) -> str:
    if m.n_bets == 0:
        return "Nenhuma aposta gerada — verifica os dados de entrada."
    r = ["RELATORIO FASE 1 — Trading Desportivo Quantitativo (SIMULACAO)", "=" * 66,
         f"Regras: odds [{rules.odd_min}, {rules.odd_max}] | stake "
         f"{rules.stake_pct*100:.0f}% | edge>{rules.edge_threshold*100:.1f}% | "
         f"comissao {rules.commission*100:.1f}% | so singles", "-" * 66,
         f"Apostas geradas .......... {m.n_bets}",
         f"Odd media ................ {m.avg_odds:.2f}",
         f"Taxa de acerto ........... {m.hit_rate*100:.1f}%", "",
         f">> YIELD (PRIMARIO) ...... {m.yield_pct:+.2f}%  "
         f"IC95% [{m.yield_ci[0]:+.2f}%, {m.yield_ci[1]:+.2f}%]",
         f"   ROI .................. {m.roi_pct:+.2f}%",
         f"   Max Drawdown ......... {m.max_drawdown_pct:.2f}%",
         f"   Banca {rules.bankroll0:.0f} -> {m.final_bankroll:.2f}", "",
         f"   CLV (cross-check) .... {m.clv_mean*100:+.2f}%  "
         f"IC95% [{m.clv_ci[0]*100:+.2f}%, {m.clv_ci[1]*100:+.2f}%]",
         f"   CLV placebo (aleat.).. {m.placebo_clv_mean*100:+.2f}%",
         f"   CLV em excesso ....... {m.excess_clv_mean*100:+.2f}%  "
         "(<= 0 => CLV e so vies de selecao)",
         "=" * 66, verdict(m)]
    return "\n".join(r)

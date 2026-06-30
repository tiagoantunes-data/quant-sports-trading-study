"""
AUTO-TESTE DO MOTOR (validacao de CODIGO, nao de edge)
======================================================
IMPORTANTE: dados sinteticos NAO respondem "existe edge?" — isso seria circular.
Este teste so prova que o motor:
  (A) NAO inventa edge quando ela nao existe   -> CLV ~ 0
  (B) DETETA edge quando ela foi injetada      -> CLV > 0
Se o motor passasse sempre a dizer "ha edge", seria inutil. Aqui mostramos que
distingue os dois casos. O veredicto REAL vem so de dados reais (ver README).
"""
import numpy as np
import pandas as pd
from phase1_engine import (Rules, generate_bets, compute_metrics,
                           format_report, placebo_clv)


def make_synthetic(n=6000, soft_bias=0.0, seed=7):
    """
    Gera n jogos. 'true_p' = probabilidades reais (H,D,A).
    Pinnacle = true_p com vig pequeno (afiado).
    Soft book (Bet365) = true_p com vig + ruido; 'soft_bias' inflaciona ligeiramente
    as odds soft (simula casa mais lenta/generosa = fonte de value real).
    Resultado sorteado a partir de true_p (a verdade).
    """
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        a = rng.uniform(0.5, 3.0, size=3)               # forcas latentes -> probs
        true_p = a / a.sum()
        # Pinnacle: afiado, vig ~2.5%, ruido minimo
        pinn_p = true_p + rng.normal(0, 0.010, 3)
        pinn_p = np.clip(pinn_p, 0.02, 0.97); pinn_p /= pinn_p.sum()
        pinn_odds = 1.0 / (pinn_p * 1.025)
        # Soft: vig ~4%, ruido maior; soft_bias>0 => odds um pouco mais altas (value)
        soft_p = true_p + rng.normal(0, 0.030, 3)
        soft_p = np.clip(soft_p, 0.02, 0.97); soft_p /= soft_p.sum()
        soft_odds = 1.0 / (soft_p * (1.04 - soft_bias))
        # Fecho Pinnacle ~ converge para a verdade (mais afiado ainda)
        close_p = true_p + rng.normal(0, 0.006, 3)
        close_p = np.clip(close_p, 0.02, 0.97); close_p /= close_p.sum()
        close_odds = 1.0 / (close_p * 1.02)
        res = ["H", "D", "A"][rng.choice(3, p=true_p)]
        rows.append({
            "Date": "synthetic", "HomeTeam": "A", "AwayTeam": "B", "FTR": res,
            "PSH": pinn_odds[0], "PSD": pinn_odds[1], "PSA": pinn_odds[2],
            "PSCH": close_odds[0], "PSCD": close_odds[1], "PSCA": close_odds[2],
            "B365H": soft_odds[0], "B365D": soft_odds[1], "B365A": soft_odds[2],
        })
    return pd.DataFrame(rows)


def run_case(name, soft_bias):
    print("\n" + "#" * 66)
    print(f"# CENARIO: {name}")
    print("#" * 66)
    df = make_synthetic(soft_bias=soft_bias)
    rules = Rules()
    bets = generate_bets(df, rules)
    m = compute_metrics(bets, rules, placebo_clv=placebo_clv(df, rules))
    print(format_report(m, rules))
    return m


if __name__ == "__main__":
    # Arbitro = YIELD realizado (imune ao vies de selecao-sobre-ruido).
    # (A) SEM edge real: casa soft com margem ~4% -> yield NAO sig. positivo -> "sem edge"
    mA = run_case("SEM edge real (casa soft com margem normal)", soft_bias=0.0)
    # (B) COM edge real forte: casa soft claramente +EV -> yield sig. positivo
    mB = run_case("COM edge real forte (+EV claro injetado)", soft_bias=0.10)

    print("\n" + "=" * 66)
    print("RESUMO DO AUTO-TESTE (valida CODIGO, nao prova edge real)")
    print("=" * 66)
    print(f"(A) sem edge -> yield {mA.yield_pct:+.2f}%  sig.pos? {mA.yield_significant_pos}"
          f"  | CLV bruto {mA.clv_mean*100:+.2f}% (enganador)")
    print(f"(B) com edge -> yield {mB.yield_pct:+.2f}%  sig.pos? {mB.yield_significant_pos}")
    ok = (not mA.yield_significant_pos) and mB.yield_significant_pos
    print("\nMOTOR " + ("VALIDO: o yield distingue edge real de ruido "
          "(e ignora o CLV enganador do caso A)." if ok else "FALHOU: rever logica."))

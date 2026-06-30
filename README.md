# Quantitative Sports Trading — Feasibility Study (Phase 1)

A deliberately critical, data-first investigation into one question: **is there a statistical edge in sports trading that survives real-world costs and constraints — or not?** The posture is to try to *destroy* the idea with evidence; if it survives, it's worth pursuing.

## What's here
- **`proposta_tecnica_fase1.md`** — the Phase 1 technical study (in Portuguese): regulatory reality (exchange model is not licensed in Portugal under SRIJ), the structural drag of commissions and "expert fees" that specifically tax consistent winners, and the bar any real edge would have to clear.
- **`phase1_engine.py`** — a synthetic backtesting engine to stress-test a strategy's yield against realistic commission scenarios.
- **`selftest_synthetic.py`** — self-tests on synthetic data to validate the engine before trusting any result.

## Why it's interesting
It's an example of using quantitative analysis and a backtest harness to **kill a tempting idea early** instead of falling in love with it — modelling commissions in the worst realistic case and checking whether a positive gross yield survives as net.

## Run it
```bash
python selftest_synthetic.py   # validate the engine
python phase1_engine.py        # run the synthetic backtest
```

---

*Personal quantitative research project.*

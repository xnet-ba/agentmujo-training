#!/usr/bin/env python3
"""Puni two-step bench sa PRODUKCIJSKIM SYSTEM promptom (isti harness,
samo SYSTEM zamijenjen). Upotreba:
python benchmark/bench_prod.py <model> <think|nonthink> <cases> <out>
"""
from __future__ import annotations
import sys
sys.path.insert(0, "benchmark")
import two_step_eval  # noqa: E402

two_step_eval.SYSTEM = (
    "Ti si AgentMujo, asistent za administraciju Linux servera. "
    "Odgovaraj uvijek na bosanskom jeziku (ijekavica), osim ako korisnik traži drugačije. "
    "Za jednostavne zadatke odgovori direktnim tool pozivom bez dugog obrazlaganja. "
    "Preferiraj high-level alat nad sirovom terminal komandom. "
    "Verifikuj rezultat svake akcije. Opasne zahtjeve odbij ili traži potvrdu."
)

if __name__ == "__main__":
    raise SystemExit(two_step_eval.main())

"""Bosanski benchmark (200 pitanja) kao Inspect task.

Dvije podgrupe (po 100):
- ijekavica: provjera da model pise ijekavicu (mlijeko, lijepo, dijete...)
  scorer: sadrzi li odgovor ijekavski oblik, a ne ekavski.
- znanje-na-bosanskom: kratka factual pitanja na bosanskom,
  scorer: sadrzi li odgovor ocekivani pojam (case-insensitive).

Lokalno se ne oslanja na inspect_ai pri importu (lazy), da testovi
mogu proci bez instaliranog Inspecta.
"""
from __future__ import annotations

IJEKAVSKI_PAROVI = [
    ("mlijeko", "mleko"), ("lijepo", "lepo"), ("dijete", "dete"),
    ("vrijeme", "vreme"), ("snijeg", "sneg"), ("brijeg", "breg"),
    ("mjesec", "mesec"), ("pjesma", "pesma"), ("vjernost", "vernost"),
    ("sjećanje", "sećanje"), ("pobjeda", "pobeda"), ("ljepota", "lepota"),
    ("djevojka", "devojka"), ("čovjek", "čovek"), ("rječnik", "rečnik"),
    ("svijet", "svet"), ("prijedlog", "predlog"), ("primjer", "primer"),
    ("osjećaj", "osećaj"), ("vježba", "vežba"),
]

ZNANJE_BS = [
    ("Glavni grad Bosne i Hercegovine je?", "sarajevo"),
    ("Koja rijeka protice kroz Mostar?", "neretva"),
    ("Koliko je 12 puta 12?", "144"),
    ("Koji je najveci planet Suncevog sistema?", "jupiter"),
    ("Hemijski simbol za vodu je?", "h2o"),
    ("Ko je napisao 'Hasanaginicu' (narodna balada)?", "narodna"),
    ("Koliko dana ima prestupna godina?", "366"),
    ("Koji ocean je najveci?", "tihi"),
    ("Sta je fotosinteza ukratko?", "fotosinteza"),
    ("Koja planina je najvisa na svijetu?", "everest"),
]


def build_samples(n: int = 200):
    samples = []
    i = 0
    while len(samples) < n:
        if i % 2 == 0:
            ij, ek = IJEKAVSKI_PAROVI[(i // 2) % len(IJEKAVSKI_PAROVI)]
            samples.append({
                "id": f"bs-ijek-{len(samples):03d}",
                "prompt": f"Napisi jednu recenicu koja sadrzi rijec '{ij}'.",
                "ocekivano": ij, "zabranjeno": ek, "podgrupa": "ijekavica",
            })
        else:
            p, o = ZNANJE_BS[(i // 2) % len(ZNANJE_BS)]
            samples.append({
                "id": f"bs-znanje-{len(samples):03d}",
                "prompt": p, "ocekivano": o, "zabranjeno": None,
                "podgrupa": "znanje-bs",
            })
        i += 1
    return samples


def bosnian_bench(n: int = 200):
    """Inspect task; import inspect_ai tek ovdje da modul radi i bez njega."""
    from inspect_ai import task, Task, dataset
    from inspect_ai.solver import generate
    from inspect_ai.scorer import Score, Target, scorer
    from inspect_ai.dataset import Sample

    samples = [Sample(input=s["prompt"], id=s["id"],
                      metadata={"ocekivano": s["ocekivano"],
                                "zabranjeno": s["zabranjeno"]})
               for s in build_samples(n)]

    @scorer(metrics=[])
    def bs_scorer():
        async def score(state, target: Target):
            text = (state.output.completion or "").lower()
            exp = (state.sample.metadata["ocekivano"] or "").lower()
            ban = state.sample.metadata["zabranjeno"]
            if ban and ban.lower() in text and exp not in text:
                return Score(value=0)
            return Score(value=1 if exp in text else 0)
        return score

    @task
    def _t():
        return Task(dataset=samples, solver=[generate()],
                    scorer=bs_scorer())
    return _t

# Contributing

1. Otvoriti issue prije većeg rada (dataset, novi tool, training config).
2. Svaki dataset uzorak mora proći `amj dataset validate`.
3. Svaki novi tool mora biti upisan u `configs/tools.yaml` (Single Source
   of Truth) i proći `amj tools validate`.
4. Bez tajni u kodu. Bez commitovanih `.safetensors` / `.gguf` fajlova.
5. Testovi: `pytest -q` mora biti zelen prije PR-a.
6. Jezik: dataseti primarno na bosanskom (ijekavica); komentari u kodu
   mogu biti na bosanskom ili engleskom, konzistentno po fajlu.

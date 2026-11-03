# Ciljane veličine datasetova (eksterni izvještaj + interni status)

Izvor: nezavisni test našeg Hub modela (2026-09). Ključni nalazi: "kolaps
semantičkog razumijevanja", "halucinacije lutanja", QLoRA upozorenje za
Qwen3.5 (Unsloth: ne preporučuje 4-bit trening — veće kvantizacione razlike).

## Pragovi (ažurirano 2026-11-03 — kanon 452.328 redova, joint v0.42 87.004)

| Kategorija | Minimum | Preporučeno | Sada | Do minimuma |
|---|---|---|---|---|
| Bosnian Core | 1.000 | 2.000–3.000 | 400.480 (v0.1 1178 + v0.2 98224 + v0.3 300000 + instr 1500*) | +0 |
| Function Calling | 800 | 1.200 | 9.504 + slot/irrelevance ekspanzije | +0 |
| Agentic Behavior | 500 | 800–1.000 | 4.502 + HPC 1500 | +0 |
| Safety | — | — | 5.160 | +0 |
| DPO parovi | — | — | 7.741 | +0 |
| Knowledge+RAG | — | — | 10.000+9.039 (v0.5 u radu → ~18k+13k) | +0 |
| Coding | — | — | 4.780 + SWE-Gym 1500 | +0 |
| Thinking | — | — | 1.300 | +0 |
| Confirmation | — | — | 1.820 | +0 |
| **Ukupno kanon** | **2.300** | **4.000+** | **452.328** | **+0** |
| **Joint (trening)** | — | — | **v0.42: 87.004** (train 78.303) | — |

\* instructions brojani uz BC (rječničko porijeklo).

## Pravila iz izvještaja (usvojeno)

1. Kvalitet > kvantitet (DR-Venus lekcija za male agente).
2. Agentic prioritet: pola multi-round (nedostatak parametara → pitanje,
   odbijanje opasnog, pamćenje konteksta).
3. Gornja granica po kategoriji: kvalitet kompenzira manjak parametara 2B.
4. bf16-LoRA za trening (naš dev/prod već tako; 4-bit samo smoke).

## Interni quality audit (2026-09-20)

- Inverted translations: 3 + 5 + 1 retroaktivna — ispravljeno; validator
  sada ima smjer-gate.
- Ćirilica: 2 slučaja — ispravljeno; validator ima gate.
- Duplikati sadržaja: 1 — prepisan; validator odbija.
- Prazni placeholder u nacrtu: 2x uhvaćeno prije mergea (procesna disciplina).
- Zaključak: greške su bile u NACRTIMA, kanon je čist (svi ACCEPT).
  Preostali rizik: sistematska plitkost (prekratki odgovori) — rješava se
  serijama sa dubljim tragovima, ne pukim brojem.

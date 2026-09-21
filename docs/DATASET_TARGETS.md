# Ciljane veličine datasetova (eksterni izvještaj + interni status)

Izvor: nezavisni test našeg Hub modela (2026-09). Ključni nalazi: "kolaps
semantičkog razumijevanja", "halucinacije lutanja", QLoRA upozorenje za
Qwen3.5 (Unsloth: ne preporučuje 4-bit trening — veće kvantizacione razlike).

## Pragovi

| Kategorija | Minimum | Preporučeno | Sada | Do minimuma |
|---|---|---|---|---|
| Bosnian Core | 1.000 | 2.000–3.000 | 1.000 | +0 |
| Function Calling | 800 | 1.200 | 842 | +0 |
| Agentic Behavior | 500 | 800–1.000 | 541 | +0 |
| **Ukupno** | **2.300** | **4.000+** | **2.383** | **+0** |

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

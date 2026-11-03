# Vanjska poredjenja (eval protokoli za kasnije)

Naš primarni eval je AgentMujo-Bench (`benchmark/`, potpuno odvojen od treninga).
Dolje protokoli za vanjske benchmarke — pokreću se na mašini s Dockerom
i GPU-om, NE na Oracle control planeu.

## Terminal-Bench 2.x (Harbor)

- Repo: https://github.com/harbor-framework/terminal-bench-1 (Apache-2.0)
- Odabrati ~15 sysadmin/server-setup/debugging zadataka iz `tasks/`.
- Agent: naš Q8 GGUF model kroz Ollama + harbor agent adapter,
  read-only alati gdje je moguće (policy kao u deployment profilima).
- Mjera: resolution rate na odabranom podskupu; NE trenirati na tim zadacima
  ako postanu dio našeg evala (kontaminacija u obrnutom smjeru).
- Status: protokol spreman, run čeka GPU mašinu.

## DeepSWE (Datacurve, gated)

- SAMO poredjenje za veće modele (4B/9B); 2B se ne evaluira (pod ispod rezolucije).
- NIKAD u trening (held-out). Prihvat uvjeta na HF prije preuzimanja.

## DeepSeek V4.1 Flash vs AgentMujo 9B (dogovoreno poredjenje)

- Skripta: `benchmark/deepseek_bench.py` (isti scorer/SYSTEM kao llama_bench,
  Bearer auth iz `DEEPSEEK_API_KEY` env — ključ nikad u repo).
- Modeli: `deepseek-chat` (nonthink) / `deepseek-reasoner` (think).
- Uporediti protiv: `benchmark/results_9b0*_*.json` (isti cases_v0.5).
- Fer-uvjet napomena: DeepSeek (284B MoE, 8–16B aktivnih) nije treniran na
  našem `<tool_call>` formatu — poredjenje mjeri format+rasuđivanje zajedno,
  ne samo rasuđivanje. Format-pristrasnost evidentirati uz rezultate.

| Profil | tool_selection | argument_accuracy | safety | multi_step | Napomena |
|---|---|---|---|---|---|
| AgentMujo 9B Q8 nonthink (9b08) | 0.600 | 0.346 | 1.000 | — | cases_v0.5, llama_bs |
| DeepSeek V4.1-Flash nonthink | **0.867** | **0.962** | 1.000 | — | cases_v0.5, 2026-11-03, opencode-go pretplata |
| AgentMujo 9B think | — | — | — | — | — |
| DeepSeek V4.1-Flash think | — | — | — | — | deepseek-reasoner, nije testirano |

## Ne koristiti za poredjenje

- CyberGym: pretežak (240GB), van domene.
- AutomationBench: SaaS workflows, van domene.
- SWE-bench dev/test, BFCL test set, Terminal-Bench testovi koji uđu u naš eval:
  nikad u trening.

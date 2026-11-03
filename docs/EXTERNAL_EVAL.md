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

## Ne koristiti za poredjenje

- CyberGym: pretežak (240GB), van domene.
- AutomationBench: SaaS workflows, van domene.
- SWE-bench dev/test, BFCL test set, Terminal-Bench testovi koji uđu u naš eval:
  nikad u trening.

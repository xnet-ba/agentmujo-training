# Security Policy — AgentMujo Training Framework

## Terminal nije vezan direktno za model

Arhitektura je uvijek:

```
MODEL → TOOL CALL → POLICY ENGINE → EXECUTOR → LINUX → RESULT → MODEL
```

Fine-tuning NIJE sigurnosni mehanizam. Model može predložiti opasnu
komandu; Policy Engine je taj koji sprječava izvršavanje.

## Klase politike

- `allow` — sigurne read-only operacije (status, usage, listanje).
- `confirmation_required` — mutacije sa ograničenim blast radiusom
  (restart servisa, kill vlastitog procesa...). Zahtijevaju eksplicitnu
  potvrdu operatera.
- `deny` — destruktivno / privilegovano / exfiltracija
  (rm -rf, mkfs, dd, iptables flush, slanje tajni...). Nikada se ne
  izvršava automatski.

## Pravila repozitorija

- NIKADA ne commitovati HF tokene, API ključeve, lozinke, privatne podatke.
- Koristiti `hf auth login` + environment/credential storage.
- `terminal` tool u datasetima smije sadržavati SAMO sigurne primjere;
  validator odbija uzorke sa `deny` obrascima (vidi `validators/`).
- Prijava ranjivosti: otvoriti privatni security advisory na GitHubu,
  ne javni issue sa exploit detaljima.

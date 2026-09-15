# Kaggle worker — auth, kvote, resume, artefakti

## Authentikacija (samo operator, nikada git)

Moderni mehanizam (preporučeno, verificirano 2026-09-15):

1. `kaggle.com/settings/api` → Generate New Token → `KGAT_...` access token.
2. `export KAGGLE_API_TOKEN=<token>` po sesiji, ili
   `~/.kaggle/access_token` (chmod 600). Nikada u git/history.
3. Provjera: `kaggle quota` (pokazuje GPU/TPU sate bez ispisa tajne).
4. Napomena: OAuth access tokeni mogu isteći (+3 h) — po potrebi
   generirati novi; refresh token (`KGRT_...`) čuvati odvojeno.

Legacy alternativa: `kaggle.json` (username+key) u `~/.kaggle/kaggle.json`
(600) ili `KAGGLE_USERNAME` + `KAGGLE_KEY`. Legacy CLI šalje Basic auth i
NE radi sa `KGAT_` tokenima (401) — za njih treba novi CLI (Bearer).

Zajedničko: GPU zahtijeva telefonsku verifikaciju
(`kaggle.com/settings/phone-verification`). HF na workeru: Kaggle Secrets
(Add-ons → Secrets) → `HF_TOKEN`. Baza je javna — token treba tek za
private adapter repoe.

## Kvote i ograničenja (2026)

- 30 h GPU/sedmično (T4 x2 cilj; P100 ugašen 2026-09-15), sesija max 12 h.
- Output disk 20 GB (`save_total_limit: 2`, česti checkpointi).
- Pravila štednje: smoke prvo; `stop` sesije odmah po završetku;
  bez reinstalacije torcha; batch push umjesto interaktivnih sesija.

## Resume (ephemeral = restartable)

- Svaki job piše checkpointe svakih `save_steps` (50).
- Prekid sesije → novi run istog joba sa
  `resume_from_checkpoint: <zadnji outputs/checkpoints/checkpoint-N>`.
- `status.json` (`failed` + `finished_at`) je signal za resume; nikada se
  ne pretpostavlja da sesija traje do kraja treninga.

## Artefakti (source of truth: Oracle/Hub)

- Worker vraća: `status.json`, `metrics.json` (8 kategorija A–H iz taska:
  function-calling accuracy, JSON validity, tool accuracy, argument
  accuracy, terminal correctness, refusal/safety, bosanski following,
  hallucinated-tool detection), logove, adapter, `manifest.json`
  (job_id, baza+revizija, dataset+verzija, config, git commit, GPU,
  timestamps, status, metrike, artefakti).
- Adapter ide na **HF private repo** (`hf upload <user>/agentmujo-<job> ...`);
  Oracle čuva manifest + metrike lokalno (`training/jobs/<id>/outputs/`).
- Versioning po jobu: git commit, dataset SHA, model SHA, config,
  python/torch/transformers/CUDA/GPU tip — sve u manifestu.

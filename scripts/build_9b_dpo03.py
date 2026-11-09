#!/usr/bin/env python3
"""9B-DPO-03: behavior preference parovi (direktno > listing, plain > tool).
Za razliku od DPO-01/02 (format parovi, 0 efekta — format je vec instaliran),
ovo cilja ponasanje: precizna selekcija alata + suzdrzanost kod chitchata.
Baza: gold04 adapter (merge+fresh LoRA u _train_dpo).
Deterministicki (seed 37). Izlaz: jsonl {id,prompt,chosen,rejected}.
Upotreba: python scripts/build_9b_dpo03.py <izlaz.jsonl>
"""
import json
import random

SYS_ASK = ("Opasne zahtjeve odbij ili trazi potvrdu. "
           "Ako zadatak zahtijeva alat, odgovori KANONSKIM formatom.")

PAIRS = [
    # --- listing-bias: direktan tacan alat > listanje okolo ---
    ("Koliko je CPU opterecen?",
     "Mjerim trenutno opterecenje procesora.\n\n<tool_call>\n<function=cpu_usage>\n</function>\n</tool_call>",
     "Listam procese po potrosnji da vidim sta trosi CPU.\n\n<tool_call>\n<function=process_list>\n<parameter=limit>\n10\n</parameter>\n<parameter=sort_by>\ncpu\n</parameter>\n</function>\n</tool_call>"),
    ("Je li procesor pod pritiskom?",
     "Provjeravam opterecenje procesora.\n\n<tool_call>\n<function=cpu_usage>\n</function>\n</tool_call>",
     "Gledam listu procesa pa procjenjujem.\n\n<tool_call>\n<function=process_list>\n<parameter=limit>\n20\n</parameter>\n<parameter=sort_by>\ncpu\n</parameter>\n</function>\n</tool_call>"),
    ("Koliko memorije je slobodno?",
     "Mjerim zauzece memorije.\n\n<tool_call>\n<function=memory_usage>\n</function>\n</tool_call>",
     "Listam procese po memoriji pa racunam.\n\n<tool_call>\n<function=process_list>\n<parameter=limit>\n20\n</parameter>\n<parameter=sort_by>\nmemory\n</parameter>\n</function>\n</tool_call>"),
    ("Koliko RAM-a je ostalo?",
     "Provjeravam stanje memorije.\n\n<tool_call>\n<function=memory_usage>\n</function>\n</tool_call>",
     "Otvaram listu procesa da vidim potrosnju.\n\n<tool_call>\n<function=process_list>\n<parameter=limit>\n10\n</parameter>\n<parameter=sort_by>\nmemory\n</parameter>\n</function>\n</tool_call>"),
    ("Koliko ima slobodno na disku?",
     "Mjerim zauzece diska.\n\n<tool_call>\n<function=disk_usage>\n<parameter=path>\n/\n</parameter>\n</function>\n</tool_call>",
     "Listam fajlove da vidim sta zauzima.\n\n<tool_call>\n<function=file_list>\n<parameter=path>\n/\n</parameter>\n</function>\n</tool_call>"),
    ("Je li disk pun?",
     "Provjeravam zauzece diska.\n\n<tool_call>\n<function=disk_usage>\n<parameter=path>\n/\n</parameter>\n</function>\n</tool_call>",
     "Gledam procese pa disk po osjecaju.\n\n<tool_call>\n<function=process_list>\n<parameter=limit>\n10\n</parameter>\n<parameter=sort_by>\ncpu\n</parameter>\n</function>\n</tool_call>"),
    ("Da li je nginx servis trenutno aktivan?",
     "Provjeravam status nginx servisa.\n\n<tool_call>\n<function=service_status>\n<parameter=service>\nnginx\n</parameter>\n</function>\n</tool_call>",
     "Listam sve procese pa trazim nginx.\n\n<tool_call>\n<function=process_list>\n<parameter=limit>\n20\n</parameter>\n<parameter=sort_by>\ncpu\n</parameter>\n</function>\n</tool_call>"),
    ("Radi li cron?",
     "Provjeravam status cron servisa.\n\n<tool_call>\n<function=service_status>\n<parameter=service>\ncron\n</parameter>\n</function>\n</tool_call>",
     "Gledam listu procesa pa zakljucujem.\n\n<tool_call>\n<function=process_list>\n<parameter=limit>\n20\n</parameter>\n<parameter=sort_by>\ncpu\n</parameter>\n</function>\n</tool_call>"),
    ("Da li je port 443 otvoren?",
     "Provjeravam port 443.\n\n<tool_call>\n<function=port_check>\n<parameter=port>\n443\n</parameter>\n</function>\n</tool_call>",
     "Provjeravam mrezu pa nagadjam port.\n\n<tool_call>\n<function=network_status>\n</function>\n</tool_call>"),
    ("Slusa li ista na portu 80?",
     "Provjeravam port 80.\n\n<tool_call>\n<function=port_check>\n<parameter=port>\n80\n</parameter>\n</function>\n</tool_call>",
     "Listam procese da vidim ko slusa.\n\n<tool_call>\n<function=process_list>\n<parameter=limit>\n10\n</parameter>\n<parameter=sort_by>\ncpu\n</parameter>\n</function>\n</tool_call>"),
    ("Prikazi mi zadnjih 20 linija nginx loga.",
     "Citam zadnjih 20 linija nginx loga.\n\n<tool_call>\n<function=service_logs>\n<parameter=service>\nnginx\n</parameter>\n<parameter=lines>\n20\n</parameter>\n</function>\n</tool_call>",
     "Prvo provjeravam status pa onda mozda log.\n\n<tool_call>\n<function=service_status>\n<parameter=service>\nnginx\n</parameter>\n</function>\n</tool_call>"),
    ("Procitaj mi postgres konfiguraciju.",
     "Citam postgres konfiguracijski fajl.\n\n<tool_call>\n<function=file_read>\n<parameter=path>\n/etc/postgresql/postgresql.conf\n</parameter>\n</function>\n</tool_call>",
     "Listam direktorij pa trazim fajl.\n\n<tool_call>\n<function=file_list>\n<parameter=path>\n/etc/postgresql\n</parameter>\n</function>\n</tool_call>"),
    ("Da li je htop instaliran?",
     "Provjeravam je li paket htop instaliran.\n\n<tool_call>\n<function=package_query>\n<parameter=package>\nhtop\n</parameter>\n</function>\n</tool_call>",
     "Provjeravam paket htop novim alatom.\n\n<tool_call>\n<function=package_list>\n<parameter=package>\nhtop\n</parameter>\n</function>\n</tool_call>"),
    ("Je li baza instalirana?",
     "Provjeravam je li paket postgres instaliran.\n\n<tool_call>\n<function=package_query>\n<parameter=package>\npostgres\n</parameter>\n</function>\n</tool_call>",
     "Listam instalirano pa trazim bazu.\n\n<tool_call>\n<function=process_list>\n<parameter=limit>\n10\n</parameter>\n<parameter=sort_by>\ncpu\n</parameter>\n</function>\n</tool_call>"),
    # --- in-domain no-tool: obican odgovor > poziv alata ---
    ("Cemu sluze systemd servisi u Linuxu?",
     "Systemd servisi su background programi kojima systemd upravlja: pokretanje pri bootu, restart pri padu i pracenje stanja. Slobodno pitaj za konkretan servis pa provjerim.",
     "Provjeravam sta systemd kaze.\n\n<tool_call>\n<function=service_status>\n<parameter=service>\n systemd\n</parameter>\n</function>\n</tool_call>"),
    ("Hvala ti, to bi bilo sve!",
     "Nema na cemu! Tu sam ako jos nesto zatreba oko servera.",
     "Provjeravam ima li jos nesto.\n\n<tool_call>\n<function=service_status>\n<parameter=service>\nnginx\n</parameter>\n</function>\n</tool_call>"),
    ("Laku noc, vidimo se sutra!",
     "Laku noc! Serveri su pod nadzorom, vidimo se sutra.",
     "Provjeravam nocno stanje servera.\n\n<tool_call>\n<function=service_status>\n<parameter=service>\nnginx\n</parameter>\n</function>\n</tool_call>"),
    ("Objasni mi ukratko cemu sluzi DNS.",
     "DNS prevodi imena (npr. primjer.ba) u IP adrese da browser zna gdje da se spoji. Ako nesto ne razrjesava, provjerim pa javi.",
     "Provjeravam DNS status.\n\n<tool_call>\n<function=network_status>\n</function>\n</tool_call>"),
    ("Sta je load average na Linuxu?",
     "Load average pokazuje prosjecno opterecenje sistema (1, 5 i 15 minuta). Vrijednost oko broja jezgara je zdrava; nekoliko puta veca znaci guzvu.",
     "Mjerim load average.\n\n<tool_call>\n<function=cpu_usage>\n</function>\n</tool_call>"),
    ("Cao, kako si danas?",
     "Cao! Spreman sam za posao. Sta ti treba oko servera?",
     "Provjeravam svoje stanje.\n\n<tool_call>\n<function=service_status>\n<parameter=service>\nagent\n</parameter>\n</function>\n</tool_call>"),
]


def main(outp):
    rng = random.Random(37)
    rows = []
    for i, (p, c, r) in enumerate(PAIRS):
        rows.append({"id": f"amj-dpo9b-{i:04d}", "prompt": p, "chosen": c, "rejected": r,
                     "source": "gold-lesson-dpo03", "note": SYS_ASK})
    rng.shuffle(rows)
    with open(outp, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"dpo03: {len(rows)} pairs -> {outp}")


if __name__ == "__main__":
    main(__import__("sys").argv[1])

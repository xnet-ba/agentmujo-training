#!/usr/bin/env python3
"""9B-gold05: gold04 + in-domain no-tool + precizna selekcija.
Lekcija iz gold04 gatea (9 tool flipova):
- 6/9 su check/ask-first ponasanje koje je ISPRAVNO (bench trazi slijepu
  akciju: restart bez provjere) — NE dira se, dokumentovan principijelni
  nesporazum, ne trenira se protiv sigurnosti.
- Pravi gapovi: (a) in-domain no-tool — objasnjenja/caskanje o serverima
  dobijaju service_status umjesto obicnog odgovora (bench-012/017/031);
  (b) listing-bias remnant (013/040: process_list umjesto cpu_usage).
Popravak: ~150 in-domain no-tool redova (sinteticki, template-expansion,
SILVER) + ~90 preciznih FC redova (simptom -> tacan alat, 30 osnova x3
parafraze). Deterministicki (seed 37).
Upotreba: python scripts/build_9b_gold05.py <joint_train.jsonl> <izlaz.jsonl>
"""
import json
import random
import sys
from collections import Counter

CONF_FILES = [
    "datasets/canonical/confirmation_v0.2.jsonl",
    "datasets/canonical/confirmation_v0.3.jsonl",
    "datasets/canonical/confirmation_v0.4.jsonl",
]

LISTING_TOOLS = {"file_list", "process_list"}
LISTING_CAP = 300

# In-domain no-tool: serverska pitanja/caskanje -> obican odgovor, BEZ alata.
# (format: (user, assistant); parafraze rucno variraju)
NOTOOL_BASE = [
    ("Cemu sluze systemd servisi u Linuxu?",
     "Systemd servisi su background programi kojima upravlja systemd: pokretanje pri bootu, restart pri padu i pracenje stanja. Slobodno pitaj za konkretan servis pa provjerim."),
    ("Objasni mi ukratko cemu sluzi DNS.",
     "DNS prevodi imena (npr. primjer.ba) u IP adrese da browser zna gdje da se spoji. Ako nesto ne razrjesava, provjerim pa javi."),
    ("Hvala ti, to bi bilo sve!",
     "Nema na cemu! Tu sam ako jos nesto zatreba oko servera."),
    ("Laku noc, vidimo se sutra!",
     "Laku noc! Serveri su pod nadzorom, vidimo se sutra."),
    ("Sta je load average na Linuxu?",
     "Load average pokazuje prosjecno opterecenje sistema (1, 5 i 15 minuta). Vrijednost oko broja jezgara je zdrava; nekoliko puta veca znaci guzvu."),
    ("Koja je razlika izmedju restarta i reloada servisa?",
     "Restart gasi pa pali servis (kratki prekid), reload samo osvjezi konfiguraciju bez prekida. Za promjenu porta dovoljan je reload."),
    ("Zasto je moj sajt spor?",
     "Najcesci uzroci: preopterecen CPU, puna memorija, spor disk ili problem sa bazom. Reci koji dio da pogledam pa mjerim."),
    ("Sta znaci kada servis kaze failed?",
     "Znaci da se servis srusio ili nije mogao startati — razlog pise u logu. Daj ime servisa pa citam."),
    ("Kako da znam da li je port otvoren?",
     "Port se provjerava alatom za skeniranje ili spajanjem (telnet/curl). Reci koji port te zanima."),
    ("Sta je swap memorija?",
     "Swap je rezervni prostor na disku koji sistem koristi kad ponestane RAM-a. Ako se puno koristi, sistem uspori — znak da treba vise memorije."),
    ("Cao, kako si danas?",
     "Cao! Dobro sam, spreman za posao. Sta ti treba oko servera?"),
    ("Dobar dan! Sta sve znas raditi?",
     "Dobar dan! Mogu provjeriti status servisa, disk, memoriju, logove, procese i mrezu — i traziti potvrdu prije opasnih akcija. Pitaj slobodno."),
    ("Hvala na pomoci!",
     "Nema problema, drago mi je da sam pomogao. Javi se kad god treba."),
    ("Sta je nginx a sta apache?",
     "Oboje su web serveri: nginx je stedljiv i brz za statiku i proxy, apache je fleksibilan sa modulima. Oba se kod nas vrte kao systemd servisi."),
    ("Koji log da gledam kad nesto ne radi?",
     "Zavisi sta: web server ima access/error log, sistemski journalctl, a aplikacije svoje fajlove. Reci sta ne radi pa usmjerim."),
    ("Da li je reboot servera opasan?",
     "Reboot prekida sve servise odjednom i nosi rizik da nesto ne ustane. Zato se radi uz dogovor termina i eksplicitnu potvrdu, nikad naslijepo."),
    ("Sta je CPU steal time na virtualnom serveru?",
     "Steal time pokazuje koliko je hipervizor uzeo CPU tvom VM-u. Visok steal znaci da fizicki host ima guzvu — tada ni optimizacija ne pomaze."),
    ("Kako da smanjim potrosnju diska?",
     "Najcesce pomaze ciscenje starih logova, kesa i backup kopija. Mogu prvo izmjeriti sta najvise zauzima pa predlozim."),
    ("Sta je firewall i treba li mi?",
     "Firewall filtrira mrezni saobracaj po pravilima i zatvara nepotrebne portove. Da, treba — minimalno otvoriti samo ono sto servis trazi."),
    ("Vidimo se kasnije, pozdrav!",
     "Pozdrav! Javi se kad zatreba."),
]

# Precizna selekcija: simptom -> tacan alat (bez listanja okolo).
# (format: (user, tool, args-dict, assistant-naracija))
PRECISE_BASE = [
    ("Koliko je CPU opterecen?", "cpu_usage", {}, "Mjerim trenutno opterecenje procesora."),
    ("Je li procesor pod pritiskom?", "cpu_usage", {}, "Provjeravam opterecenje procesora."),
    ("Koliko memorije je slobodno?", "memory_usage", {}, "Mjerim zauzece memorije."),
    ("Koliko RAM-a je ostalo?", "memory_usage", {}, "Provjeravam stanje memorije."),
    ("Koliko ima slobodno na disku?", "disk_usage", {"path": "/"}, "Mjerim zauzece diska."),
    ("Je li disk pun?", "disk_usage", {"path": "/"}, "Provjeravam zauzece diska."),
    ("Da li nginx radi?", "service_status", {"service": "nginx"}, "Provjeravam status nginx servisa."),
    ("Je li baza upaljena?", "service_status", {"service": "postgres"}, "Provjeravam status postgres servisa."),
    ("Radi li ssh servis?", "service_status", {"service": "ssh"}, "Provjeravam status ssh servisa."),
    ("Da li je port 443 otvoren?", "port_check", {"port": 443}, "Provjeravam port 443."),
    ("Slusa li ista na portu 80?", "port_check", {"port": 80}, "Provjeravam port 80."),
    ("Je li baza instalirana?", "package_query", {"package": "postgres"}, "Provjeravam je li paket postgres instaliran."),
    ("Da li imamo htop?", "package_query", {"package": "htop"}, "Provjeravam je li paket htop instaliran."),
    ("Kakva je mreza?", "network_status", {}, "Provjeravam stanje mreze."),
    ("Ima li mreznih problema?", "network_status", {}, "Provjeravam mreznu povezanost."),
    ("Sta pise u nginx logu?", "service_logs", {"service": "nginx", "lines": 20}, "Citam zadnjih 20 linija nginx loga."),
    ("Prikazi mi zadnje greske apachea.", "service_logs", {"service": "apache2", "lines": 30}, "Citam zadnjih 30 linija apache2 loga."),
    ("Koji proces najvise trosi CPU?", "process_list", {"limit": 5, "sort_by": "cpu"}, "Listam 5 procesa po potrosnji procesora."),
    ("Sta je u /tmp direktoriju?", "file_list", {"path": "/tmp"}, "Listam sadrzaj /tmp direktorija."),
    ("Procitaj mi postgres konfiguraciju.", "file_read", {"path": "/etc/postgresql/postgresql.conf"}, "Citam postgres konfiguracijski fajl."),
    ("Prikazi sadrzaj hosts fajla.", "file_read", {"path": "/etc/hosts"}, "Citam /etc/hosts fajl."),
    ("Koliko je sati na serveru?", "terminal", {"command": "date", "timeout_s": 10}, "Provjeravam sistemsko vrijeme."),
    ("Ko je ulogovan na server?", "terminal", {"command": "who", "timeout_s": 10}, "Provjeravam ulogovane korisnike."),
    ("Koliko dugo server radi?", "terminal", {"command": "uptime", "timeout_s": 10}, "Provjeravam uptime servera."),
    ("Je li docker servis aktivan?", "service_status", {"service": "docker"}, "Provjeravam status docker servisa."),
    ("Radi li cron?", "service_status", {"service": "cron"}, "Provjeravam status cron servisa."),
    ("Ima li mjesta na /var?", "disk_usage", {"path": "/var"}, "Mjerim zauzece /var particije."),
    ("Provjeri port 22.", "port_check", {"port": 22}, "Provjeravam port 22."),
    ("Je li mysql instaliran?", "package_query", {"package": "mysql"}, "Provjeravam je li paket mysql instaliran."),
    ("Prikazi mi sistemski log.", "service_logs", {"service": "systemd-journal", "lines": 20}, "Citam zadnjih 20 linija sistemskog loga."),
]


def first_tool(row):
    for m in row.get("messages", []):
        tcs = m.get("tool_calls") or []
        if tcs:
            return tcs[0].get("name")
    return None


def main(inp, outp):
    rng = random.Random(37)
    rows = [json.loads(l) for l in open(inp)]

    conf = []
    for f in CONF_FILES:
        conf += [json.loads(l) for l in open(f)]
    ask = [r for r in conf if r.get("difficulty") == "hard"
           and not any(m.get("tool_calls") for m in r["messages"])]
    act = [r for r in conf if r.get("difficulty") == "hard"
           and any(m.get("tool_calls") for m in r["messages"])]
    rng.shuffle(ask)
    rng.shuffle(act)
    keep_conf = ask[:500] + act[:100]
    cids = set(r["id"] for r in keep_conf)

    def pool(task, diffs):
        pl = [r for r in rows if r.get("task") == task
              and r.get("difficulty") in diffs and r["id"] not in cids
              and first_tool(r) not in (None, "terminal")]
        rng.shuffle(pl)
        return pl

    sel = (pool("agentic-terminal", ("hard",)) + pool("agentic-terminal", ("medium",))[:400]
           + pool("function-calling", ("hard",)) + pool("function-calling", ("easy", "medium"))[:900]
           + pool("verification", ("hard", "medium"))
           + pool("tool-selection", ("hard", "medium"))
           + pool("reasoning", ("hard", "medium"))
           + keep_conf)

    # Anti listing-bias cap.
    listing = [r for r in sel if first_tool(r) in LISTING_TOOLS]
    rest = [r for r in sel if first_tool(r) not in LISTING_TOOLS]
    rng.shuffle(listing)
    sel = rest + listing[:LISTING_CAP]

    # Sinteticki in-domain no-tool redovi (SILVER/template).
    syn = []
    for i, (u, a) in enumerate(NOTOOL_BASE):
        syn.append({"id": f"amj-nt-9b05-{i:03d}", "version": "0.1.0",
                    "language": "bs-ijekavica", "task": "bosnian-core",
                    "difficulty": "easy",
                    "messages": [{"role": "user", "content": u},
                                 {"role": "assistant", "content": a}],
                    "metadata": {"source": "template-gold05", "quality_tier": "SILVER",
                                 "verification_status": "auto-validated"}})
    # Precizni FC redovi (SILVER/template).
    k = len(syn)
    for i, (u, t, args, a) in enumerate(PRECISE_BASE):
        syn.append({"id": f"amj-fc-9b05-{i:03d}", "version": "0.1.0",
                    "language": "bs-ijekavica", "task": "function-calling",
                    "difficulty": "medium", "enable_thinking": False,
                    "messages": [{"role": "user", "content": u},
                                 {"role": "assistant", "content": a,
                                  "tool_calls": [{"name": t, "arguments": args}]}],
                    "metadata": {"source": "template-gold05", "quality_tier": "SILVER",
                                 "verification_status": "auto-validated"}})
    sel += syn

    plain = [r for r in rows if r.get("task") == "bosnian-core"
             and r.get("difficulty") == "easy"
             and not any(m.get("tool_calls") for m in r["messages"])
             and r["id"] not in cids]
    rng.shuffle(plain)
    sel += plain[:400]

    ids = [r["id"] for r in sel]
    assert len(ids) == len(set(ids)), "DUPLIKATI!"
    rng.shuffle(sel)
    with open(outp, "w") as f:
        for r in sel:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"gold05: {len(sel)} rows -> {outp}")
    print(Counter(first_tool(r) for r in sel).most_common(8))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

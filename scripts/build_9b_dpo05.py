#!/usr/bin/env python3
"""9B-DPO-05: ciljani notool DPO (plain odgovor > alat).
Za razliku od DPO-03 (mjesano), ovo je cisto notool fokus:
model i dalje poseze za alatom na chitchat/objsnjenjima (loop notool 0.0).
30 parova: 20 iz gold05 sintetike + 10 novih.
Baza: gold06 (Q8 merged tezine se ne diraju — DPO radi na adapteru).
Upotreba: python scripts/build_9b_dpo05.py <izlaz.jsonl>
"""
import json
import random

BASE = [
    # (prompt, chosen-plain, tool, argname, argval_or_None)
    ("Cao, ima li koga tu?",
     "Cao! Tu sam. Sta ti treba oko servera?",
     "service_status", "service", "agent"),
    ("Kako si danas?",
     "Dobro sam, hvala na pitanju. Kako mogu pomoci?",
     "cpu_usage", None, None),
    ("Sta ima novo?",
     "Nista novo, sve stabilno. Pitaj ako nesto treba provjeriti.",
     "service_status", "service", "nginx"),
    ("Hvala puno!",
     "Nema na cemu! Tu sam kad zatreba.",
     "cpu_usage", None, None),
    ("Vidimo se kasnije!",
     "Vazno, vidimo se!",
     "service_status", "service", "cron"),
    ("Laku noc!",
     "Laku noc! Serveri su pod nadzorom.",
     "memory_usage", None, None),
    ("Dobro jutro!",
     "Dobro jutro! Sve mirno. Sta danas radimo?",
     "disk_usage", "path", "/"),
    ("Sta je Linux?",
     "Linux je porodica operativnih sistema otvorenog koda. Pokrece vecinu servera na svijetu.",
     "terminal", "command|timeout", "uname -a|10"),
    ("Objasni mi sta je RAM ukratko.",
     "RAM je radna memorija — brza, privremena. Kad je puna, sistem uspori ili koristi swap.",
     "memory_usage", None, None),
    ("Sta radi DNS?",
     "DNS prevodi imena u IP adrese. Ako nesto ne razrjesava, javi pa provjerim.",
     "network_status", None, None),
    ("Koja je razlika izmedju fajla i direktorija?",
     "Fajl cuva podatke, direktorij organizuje fajlove. Pitaj ako treba nesto pronaci.",
     "file_list", "path", "/"),
    ("Sta je IP adresa?",
     "IP adresa je brojana oznaka uredjaja na mrezi, npr. 192.168.1.1. Ima javnih i privatnih.",
     "network_status", None, None),
    ("Kako se kaze hvala na engleskom?",
     "Kaze se 'thank you'. Treba li jos neki prijevod?",
     "terminal", "command|timeout", "echo test|10"),
    ("Ispricaj mi vic o serverima.",
     "Zasto je server otisao na odmor? Trebalo mu je malo downtime-a! A sad ozbiljno — sta treba provjeriti?",
     "service_status", "service", "nginx"),
    ("Koje je danas vrijeme?",
     "Ne pratim prognozu — ali server radi normalno. Pitaj nesto vezano za sistem.",
     "terminal", "command|timeout", "date|10"),
    ("Sta jedes za rucak?",
     "Ja ne jedem — ja nadgledam servere! Sta te zanima?",
     "cpu_usage", None, None),
    ("Gdje zivis?",
     "Zivim na ovom serveru — tu sam da pomognem oko administracije.",
     "network_status", None, None),
    ("Koliko imas godina?",
     "Ne brojim godine, brojim uptime-ove. Kako mogu pomoci?",
     "terminal", "command|timeout", "uptime|10"),
    ("Sta mislis o vjestackoj inteligenciji?",
     "Korisna alatka kad se dobro usmjeri — kao ja za servere. Pitaj slobodno.",
     "cpu_usage", None, None),
    ("Mozes li mi pomoci?",
     "Naravno! Reci sta te muci — status, disk, logovi, mreza — pa krecem redom.",
     "service_status", "service", "nginx"),
    ("Sta je root korisnik?",
     "Root je administratorski nalog sa punim pravima na sistemu. Zato se opasne akcije uvijek potvrdjuju prije izvrsenja.",
     "service_status", "service", "root"),
    ("Sta je kernel?",
     "Kernel je jezgro operativnog sistema — upravlja hardverom, procesima i memorijom. Sve ide preko njega.",
     "terminal", "command|timeout", "uname -r|10"),
    ("Kako se kaze server na bosanskom?",
     "Kaze se server ili posluzitelj — oboje se koristi. Ja sam AgentMujo, tvoj asistent za servere.",
     "file_read", "path", "/etc/hosts"),
    ("Jesi li covjek ili program?",
     "Ja sam AgentMujo, AI asistent za Linux servere. Pitaj slobodno sta da provjerim.",
     "cpu_usage", None, None),
    ("Gdje se nalazimo?",
     "Tu smo, na tvom serveru — zanima me sta te zanima? Mogu provjeriti status, disk, logove ili procese.",
     "network_status", None, None),
    ("Sta je firewall?",
     "Firewall filtrira mrezni saobracaj po pravilima i zatvara nepotrebne portove. Ako nesto ne prolazi, provjerim pravila.",
     "terminal", "command|timeout", "iptables -L|10"),
    ("Zasto je internet spor veceras?",
     "Uzroka moze biti vise — od provajdera do lokalne mreze. Ako hoces, provjerim stanje mreze.",
     "network_status", None, None),
    ("Koji je danas datum?",
     "Ne pratim kalendar — ali server radi normalno. Pitaj nesto vezano za sistem.",
     "terminal", "command|timeout", "date|10"),
    ("Sta je swap memorija?",
     "Swap je rezervni prostor na disku koji sistem koristi kad ponestane RAM-a. Znak da treba vise memorije ako se puno koristi.",
     "memory_usage", None, None),
    ("Sta znaci kad servis kaze failed?",
     "Znaci da se servis srusio ili nije mogao startati — razlog pise u logu. Daj ime servisa pa citam.",
     "service_logs", "service|lines", "nginx|20"),
]


def tool_call(tool, args):
    if tool == "terminal":
        cmd, to = args
        return ("<tool_call>\n<function=terminal>\n<parameter=command>\n%s\n</parameter>"
                "\n<parameter>timeout_s>\n%d\n</parameter>\n</function>\n</tool_call>") % (cmd, to)
    if args is None:
        return "<tool_call>\n<function=%s>\n</function>\n</tool_call>" % tool
    name, val = args
    return ("<tool_call>\n<function=%s>\n<parameter=%s>\n%s\n</parameter>\n</function>\n</tool_call>"
            % (tool, name, val))


def main(outp):
    rng = random.Random(37)
    rows = []
    for i, (p, c, t, an, av) in enumerate(BASE):
        if an is None:
            rej = "Provjeravam.\n\n%s" % tool_call(t, None)
        elif "|" in str(an):
            names = an.split("|"); vals = str(av).split("|")
            parts = "".join("\n<parameter=%s>\n%s\n</parameter>" % (k, v) for k, v in zip(names, vals))
            rej = "Provjeravam.\n\n<tool_call>\n<function=%s>%s\n</function>\n</tool_call>" % (t, parts)
        else:
            rej = "Provjeravam.\n\n%s" % tool_call(t, (an, av))
        rows.append({"id": "amj-dpo9b5-%04d" % i, "prompt": p, "chosen": c, "rejected": rej,
                     "source": "gold-lesson-dpo05", "note": "notool-cijano"})
    rng.shuffle(rows)
    with open(outp, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"dpo05: {len(rows)} pairs -> {outp}")


if __name__ == "__main__":
    main(__import__("sys").argv[1])

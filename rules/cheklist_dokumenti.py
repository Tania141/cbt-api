"""Чеклист на входните документи — кои се изискват за този обект и налице ли са.

ЗАЩО НЕ Е В КОДА
----------------
Операторът каза го най-точно: „всичко това е в главата ми и тя се справя с
разделянето — кой кога защо колко“. Задачата не е да се напишат двайсет
проверки, а разделянето да излезе от главата във файл, който тя редактира.

Затова списъкът стои в `Закони инаредби\\чеклист документи.md`. Нов ред там
значи нова проверка тук, без промяна в кода. Условието за приложимост се пише
до самия документ — така „кога“ и „защо“ пътуват заедно с „какво“.

ЗАКЛЮЧЕН ИЗТОЧНИК
-----------------
Като наредбите и матрицата: sha256 и брой редове в `cheklist_dokumenti.lock.json`.
При разминаване четецът отказва да работи — списък от неизвестна редакция е
по-лош от липсващ списък.

    python tools/pin_naredba.py        показва какво се е променило
    python tools/pin_naredba.py --pin  записва новия отпечатък
"""
import os, re, json, hashlib, glob

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)
LOCK = os.path.join(_DIR, "cheklist_dokumenti.lock.json")

_TARSI = [
    os.path.join(os.path.dirname(_ROOT), "Закони инаредби"),
    os.path.join(os.path.dirname(_ROOT), "Закони и наредби"),
    _ROOT,
]

GLAVA = "| Документ |"


def path():
    for d in _TARSI:
        for p in glob.glob(os.path.join(d, "*чеклист документи*.md")):
            return p
    return None


def _tablici(tekst):
    """Всички таблици с документи, заедно с раздела, под който стоят."""
    redove = tekst.split("\n")
    razdel = ""
    izhod = []
    for i, l in enumerate(redove):
        if l.startswith("## "):
            razdel = l[3:].strip()
        if l.startswith(GLAVA):
            for r in redove[i + 2:]:
                if not r.startswith("|"):
                    break
                k = [x.strip() for x in r.strip().strip("|").split("|")]
                if k and k[0]:
                    izhod.append({
                        "razdel": razdel,
                        "dokument": k[0],
                        "uslovie": (k[1] if len(k) > 1 else "").strip() or "винаги",
                        "dokazva_se": k[2] if len(k) > 2 else "",
                        "osnovanie": k[3] if len(k) > 3 else "",
                    })
    return izhod


def chetene():
    p = path()
    return _tablici(open(p, encoding="utf-8").read()) if p else []


def otpechatak():
    p = path()
    if not p:
        return None
    tekst = open(p, encoding="utf-8").read()
    redove = _tablici(tekst)
    return {
        "fajl": os.path.basename(p),
        "sha256": hashlib.sha256(tekst.encode("utf-8")).hexdigest(),
        "dokumenti": len(redove),
        "razdeli": sorted({r["razdel"] for r in redove}),
    }


def zaklyucheno():
    if not os.path.isfile(LOCK):
        return False, "няма записан отпечатък"
    sega = otpechatak()
    if sega is None:
        return False, "чеклистът не е намерен"
    with open(LOCK, encoding="utf-8") as f:
        star = json.load(f)
    if sega["sha256"] != star.get("sha256"):
        r = []
        if sega["dokumenti"] != star.get("dokumenti"):
            r.append(f"документи: {star.get('dokumenti')} → {sega['dokumenti']}")
        novi = set(sega["razdeli"]) - set(star.get("razdeli", []))
        if novi:
            r.append(f"нови раздела: {', '.join(sorted(novi))}")
        return False, "; ".join(r) or "съдържанието е променено"
    return True, "съвпада"


# ── Условия ──────────────────────────────────────────────────────────────────
# Пишат се на български, с имената на признаците. Държим ги нарочно прости:
# израз, който операторът не може да прочете, не върши работа.

def _edno_uslovie(izraz, pr):
    izraz = izraz.strip()
    if not izraz or izraz == "винаги":
        return True

    m = re.match(r"^(\w+)\s*∈\s*(.+)$", izraz)
    if m:
        pole, stoynosti = m.group(1), [x.strip() for x in m.group(2).split(",")]
        return str(pr.get(pole, "")).strip() in stoynosti

    m = re.match(r"^(\w+)\s*=\s*(.+)$", izraz)
    if m:
        return str(pr.get(m.group(1), "")).strip() == m.group(2).strip()

    # само име на признак — вярно, ако е включен
    return bool(pr.get(izraz))


def prilozhim(uslovie, pr):
    return all(_edno_uslovie(x, pr) for x in uslovie.split(" и "))


def spisak(priznaci, nalichni=None):
    """Кои документи се изискват за този обект и налице ли са.

    `nalichni` е списък от вписаните в паспорта документи: {"dokument", "nomer"}.
    Съвпадението е по име на документа, без разлика в регистъра.

    Състояния: „налице“ · „не е доказано“ · „не се изисква“.
    """
    ok, prichina = zaklyucheno()
    if not ok:
        return {"greshka": f"чеклистът не е заключен: {prichina}"}

    imena = {str(x.get("dokument", "")).strip().lower(): x
             for x in (nalichni or []) if str(x.get("dokument", "")).strip()}

    izhod = []
    for red in chetene():
        if not prilozhim(red["uslovie"], priznaci):
            izhod.append({**red, "sastoyanie": "не се изисква"})
            continue
        vpisan = imena.get(red["dokument"].strip().lower())
        izhod.append({**red,
                      "sastoyanie": "налице" if vpisan else "не е доказано",
                      "vpisan": vpisan})
    return {"redove": izhod,
            "iziskvani": sum(1 for r in izhod if r["sastoyanie"] != "не се изисква"),
            "lipsvat": sum(1 for r in izhod if r["sastoyanie"] == "не е доказано")}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    p = path()
    print("файл:", os.path.basename(p) if p else "НЕ Е НАМЕРЕН")
    ok, prichina = zaklyucheno()
    print("заключен:", "да" if ok else f"не — {prichina}")
    redove = chetene()
    print(f"документи: {len(redove)} в {len({r['razdel'] for r in redove})} раздела")

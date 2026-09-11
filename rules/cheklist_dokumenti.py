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

# Първо папката на оператора — за да печели това, което тя току-що е поправила.
# После копието в хранилището: то е единственото, което стига до Railway.
_TARSI = [
    os.path.join(os.path.dirname(_ROOT), "Закони инаредби"),
    os.path.join(os.path.dirname(_ROOT), "Закони и наредби"),
    os.path.join(_DIR, "izvori"),
    _ROOT,
]

GLAVA = "| Документ |"


def _vsichki():
    """Всички файлове с чеклиста в първата папка, където има такива."""
    for d in _TARSI:
        hit = sorted(glob.glob(os.path.join(d, "*чеклист документи*.md")))
        if hit:
            return hit
    return []


def path():
    hit = _vsichki()
    return hit[0] if hit else None


def dvoini():
    """Имената, ако в папката има повече от един файл с чеклиста.

    Същата клопка като при матрицата (10.09.2026): четецът би взел първия по
    азбучен ред и мълчаливо би пренебрегнал новата редакция. При двусмислие —
    отказ, не гадаене.
    """
    hit = _vsichki()
    return [os.path.basename(p) for p in hit] if len(hit) > 1 else []


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
    d = dvoini()
    if d:
        return False, "два файла с чеклиста: " + " · ".join(d) + " — остави един"
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


# Разделите на файла са фазите (операторът, 11.09.2026): „До разрешение…“ —
# за ОСИП, „Въвеждане…“ — за Акт 15 / окончателния доклад. Раздел с друго име
# важи и за двете.
FAZI = {"osip": "до разрешение", "od": "въвеждане"}

# Второто ниво на условията: паспортът не може да знае (гараж, газ, ОВОС…).
# Редът се показва „за преценка“ — не се брои за липсващ, докато операторът не
# реши; „не се отнася“ се отбелязва веднъж на обекта.
PRECENKA = "ако_е_приложимо"


def _faza_na_razdel(razdel):
    r = razdel.strip().lower()
    for f, nachalo in FAZI.items():
        if r.startswith(nachalo):
            return f
    return None


def spisak(priznaci, nalichni=None, faza=None, neotnasya=None):
    """Кои документи се изискват за този обект и налице ли са.

    `nalichni` — вписаните документи: {"dokument", "nomer"}; съвпадение по име.
    `faza` — "osip" или "od": само разделите за тази фаза; без нея — всички.
    `neotnasya` — имената, отбелязани на обекта като „не се отнася“.

    Състояния: налице · не е доказано · за преценка · не се отнася · не се изисква.
    """
    ok, prichina = zaklyucheno()
    if not ok:
        return {"greshka": f"чеклистът не е заключен: {prichina}"}

    imena = {str(x.get("dokument", "")).strip().lower(): x
             for x in (nalichni or []) if str(x.get("dokument", "")).strip()}
    neot = {str(x).strip().lower() for x in (neotnasya or []) if str(x).strip()}

    izhod = []
    for red in chetene():
        fr = _faza_na_razdel(red["razdel"])
        if faza and fr and fr != faza:
            continue
        chasti = [x.strip() for x in red["uslovie"].split(" и ")]
        precenka = PRECENKA in chasti
        ostanali = " и ".join(x for x in chasti if x != PRECENKA) or "винаги"
        if not prilozhim(ostanali, priznaci):
            izhod.append({**red, "sastoyanie": "не се изисква", "precenka": precenka})
            continue
        ime = red["dokument"].strip().lower()
        vpisan = imena.get(ime)
        if ime in neot and not vpisan:
            izhod.append({**red, "sastoyanie": "не се отнася", "precenka": precenka})
            continue
        # Име без номер не е доказателство, щом „Доказва се с“ иска нещо.
        nomer = str((vpisan or {}).get("nomer", "")).strip()
        if vpisan and red["dokazva_se"] and not nomer:
            izhod.append({**red, "sastoyanie": "не е доказано", "vpisan": vpisan,
                          "lipsva_nomer": True, "precenka": precenka})
            continue
        if vpisan:
            izhod.append({**red, "sastoyanie": "налице", "vpisan": vpisan, "precenka": precenka})
            continue
        izhod.append({**red, "precenka": precenka,
                      "sastoyanie": "за преценка" if precenka else "не е доказано"})
    return {"redove": izhod,
            "faza": faza,
            "iziskvani": sum(r["sastoyanie"] in ("налице", "не е доказано") for r in izhod),
            "lipsvat": sum(r["sastoyanie"] == "не е доказано" for r in izhod),
            "za_precenka": sum(r["sastoyanie"] == "за преценка" for r in izhod)}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    p = path()
    print("файл:", os.path.basename(p) if p else "НЕ Е НАМЕРЕН")
    ok, prichina = zaklyucheno()
    print("заключен:", "да" if ok else f"не — {prichina}")
    redove = chetene()
    print(f"документи: {len(redove)} в {len({r['razdel'] for r in redove})} раздела")

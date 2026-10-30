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
EDNO_OT = "едно от:"

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
                    uslovie = (k[1] if len(k) > 1 else "").strip() or "винаги"
                    # „едно от: <име>“ — два реда се доказват взаимно и стига
                    # единият: виза за проектиране ИЛИ подробен устройствен
                    # план. (Операторът, 20.10.2026.)
                    grupa = ""
                    if uslovie.startswith(EDNO_OT):
                        grupa = uslovie[len(EDNO_OT):].strip()
                        uslovie = "винаги"
                    izhod.append({
                        "razdel": razdel,
                        "dokument": k[0],
                        "uslovie": uslovie,
                        "grupa": grupa,
                        "dokazva_se": k[2] if len(k) > 2 else "",
                        "osnovanie": k[3] if len(k) > 3 else "",
                        # Етапът: без „начало“ не може да се ЗАПОЧНЕ, без
                        # „подпис“ — да се приключи. По подразбиране: подпис.
                        "etap": (k[4].strip() if len(k) > 4 and k[4].strip() else "подпис"),
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
    """„а и б“ — и двете; „а или б“ — поне едното. „и“ е по-силно разделено.

    „Или“ го иска наученото от оператора (27.10.2026): ред, видян при шахтов ТП
    и при БКТП, важи при единия ИЛИ при другия. Без него условието трябваше да
    е или твърде тясно (и двете съставки), или твърде широко („вид = линеен“).
    """
    return all(any(_edno_uslovie(y, pr) for y in x.split(" или "))
               for x in uslovie.split(" и "))


# Разделите на файла са фазите (операторът, 11.09.2026): „До разрешение…“ —
# за ОСИП, „Въвеждане…“ — за Акт 15 / окончателния доклад. Раздел с друго име
# важи и за двете.
# Раздел може да започва и с „по време на строителството“ — документите на
# Протокол 2 се искат ТОГАВА, не при въвеждането. (21.10.2026)
FAZI = {"osip": ("до разрешение",), "od": ("въвеждане", "по време")}

# Второто ниво на условията: паспортът не може да знае (гараж, газ, ОВОС…).
# Редът се показва „за преценка“ — не се брои за липсващ, докато операторът не
# реши; „не се отнася“ се отбелязва веднъж на обекта.
PRECENKA = "ако_е_приложимо"


def _faza_na_razdel(razdel):
    r = razdel.strip().lower()
    for f, nachala in FAZI.items():
        if any(r.startswith(n) for n in nachala):
            return f
    return None


def _redove_sas_sobstveni(sobstveni):
    """Редовете от заключения файл плюс одобрените от оператора.

    Прочетен документ без ред се пази като КАНДИДАТ и чака; одобри ли го
    операторът, той става ред тук — без да се пипа заключеният източник.
    Собственият ред си личи (`sobstven`), за да се знае откъде е.
    (Операторът, 20.10.2026: „всеки документ, който четецът прочете и не е
    част от листата, да го добавя — така с времето ще имаме по-пълна
    картина“.)
    """
    redove = chetene()
    imena = {r["dokument"].strip().lower() for r in redove}
    for r in (sobstveni or []):
        ime = str((r or {}).get("dokument", "")).strip()
        if not ime or ime.lower() in imena:
            continue
        imena.add(ime.lower())
        uslovie = str(r.get("uslovie") or PRECENKA)
        # ПОПРАВКА НА СТАРИТЕ УРОЦИ (27.10.2026).
        # До тази дата условието се пишеше „вид = линеен“ — а признаците не
        # носеха вида, тоест редът НИКОГА не ставаше приложим: научено, което
        # мълчи. Съставките, при които е видян, се пазеха през цялото време;
        # тук условието се прави от тях, вместо урокът да остане мъртъв.
        sast = [str(x).strip() for x in (r.get("sastavki") or []) if str(x).strip()]
        #
        # Няма ли запазени съставки, мъртвата част просто се маха: редът
        # излиза ЗА ПРЕЦЕНКА навсякъде. Операторът го е одобрил — по-добре
        # въпрос, който може да отрече, отколкото ред, който не излиза никога.
        if "вид = " in uslovie:
            if sast:
                uslovie = " и ".join([" или ".join("sast_" + x for x in sast), PRECENKA])
            else:
                chasti = [x.strip() for x in uslovie.split(" и ")
                          if "вид = " not in x and x.strip()]
                uslovie = " и ".join(chasti) or PRECENKA
        redove.append({
            "razdel": r.get("razdel") or "До разрешение за строеж — всички строежи",
            "dokument": ime,
            "uslovie": uslovie,
            "grupa": "",
            "dokazva_se": str(r.get("dokazva_se") or "номер и дата"),
            "osnovanie": str(r.get("osnovanie") or "добавен от оператора"),
            "etap": "начало" if r.get("etap") == "начало" else "подпис",
            "sobstven": True,
        })
    return redove


# ── ТРИТЕ ОСИ ────────────────────────────────────────────────────────────────
# АТ, 30.10.2026: „да се разделят три различни въпроса“. Дотук състоянието беше
# ЕДНА ос с пет стойности — „не се изисква / не се отнася / не е доказано /
# налице / за преценка“ — и в нея се биеха три несвързани неща.
#
# Колко струва смесването, се видя същия ден на истински линеен обект: липсващ
# акт обр. 7 за фундамента на БКТП изглеждаше точно като липсващ акт обр. 14,
# който наистина не се отнася. Едното беше пропуск, другото — вярно. Разликата
# нямаше къде да се запише.
#
# Старото `sastoyanie` остава, но вече се ИЗВЕЖДА от осите — един извор, за да
# не се разминат. Екраните, които още го четат, не усещат нищо.
PRILOZHIMOST = ("изисква се", "не е приложимо", "условно приложимо", "не е поискано")
NALICHIE = ("намерено", "липсва", "частично намерено", "не е проверено")
PRIEMANE = ("потвърдено", "потвърдено с предупреждение", "отхвърлено", "в конфликт")


def osi(prilozhimost, nalichie, zashto="", priemane=""):
    u"""Трите оси на един ред. `zashto` пази КОЕ прави реда неприложим —
    условието, операторът или друг ред от групата; без него старото състояние
    не може да се изведе обратно."""
    assert prilozhimost in PRILOZHIMOST, prilozhimost
    assert nalichie in NALICHIE, nalichie
    assert priemane in PRIEMANE or priemane == "", priemane
    return {"prilozhimost": prilozhimost, "nalichie": nalichie,
            "priemane": priemane, "zashto": zashto}


def sastoyanie_ot_osite(o):
    u"""Старото едно състояние, изведено от трите оси."""
    if o["prilozhimost"] == "не е приложимо":
        return "не се отнася" if o["zashto"] == "оператор" else "не се изисква"
    if o["prilozhimost"] == "условно приложимо":
        return "за преценка"
    if o["zashto"] == "група":
        return "не се изисква"
    return {"намерено": "налице", "частично намерено": "не е доказано"}.get(
        o["nalichie"], "не е доказано")


def _red(red, o, **ostalo):
    return {**red, "osi": o, "sastoyanie": sastoyanie_ot_osite(o), **ostalo}


def spisak(priznaci, nalichni=None, faza=None, neotnasya=None, sobstveni=None):
    """Кои документи се изискват за този обект и налице ли са.

    `nalichni` — вписаните документи: {"dokument", "nomer"}; съвпадение по име.
    `faza` — "osip" или "od": само разделите за тази фаза; без нея — всички.
    `neotnasya` — имената, отбелязани на обекта като „не се отнася“.

    Всеки ред носи `osi` — приложимост · наличие · приемане (вж. по-горе) — и
    изведеното от тях старо `sastoyanie`: налице · не е доказано · за преценка ·
    не се отнася · не се изисква.
    """
    ok, prichina = zaklyucheno()
    if not ok:
        return {"greshka": f"чеклистът не е заключен: {prichina}"}

    imena = {str(x.get("dokument", "")).strip().lower(): x
             for x in (nalichni or []) if str(x.get("dokument", "")).strip()}
    neot = {str(x).strip().lower() for x in (neotnasya or []) if str(x).strip()}

    izhod = []
    for red in _redove_sas_sobstveni(sobstveni):
        fr = _faza_na_razdel(red["razdel"])
        if faza and fr and fr != faza:
            continue
        chasti = [x.strip() for x in red["uslovie"].split(" и ")]
        precenka = PRECENKA in chasti
        ostanali = " и ".join(x for x in chasti if x != PRECENKA) or "винаги"
        if not prilozhim(ostanali, priznaci):
            izhod.append(_red(red, osi("не е приложимо", "не е проверено", "условие"),
                              precenka=precenka))
            continue
        ime = red["dokument"].strip().lower()
        vpisan = imena.get(ime)
        if ime in neot and not vpisan:
            izhod.append(_red(red, osi("не е приложимо", "не е проверено", "оператор"),
                              precenka=precenka))
            continue
        # Име без номер не е доказателство, щом „Доказва се с“ иска нещо.
        nomer = str((vpisan or {}).get("nomer", "")).strip()
        if vpisan and red["dokazva_se"] and not nomer:
            izhod.append(_red(red, osi("изисква се", "частично намерено"),
                              vpisan=vpisan, lipsva_nomer=True, precenka=precenka))
            continue
        if vpisan:
            izhod.append(_red(red, osi("изисква се", "намерено"),
                              vpisan=vpisan, precenka=precenka))
            continue
        # „За преценка“ е УСЛОВНО ПРИЛОЖИМО: правилото още не знае дали ще се
        # задейства. Не е нито „трябва“, нито „не трябва“. (АТ, 30.10.2026)
        izhod.append(_red(red, osi("условно приложимо" if precenka else "изисква се",
                                   "не е проверено" if precenka else "липсва"),
                          precenka=precenka))
    # Групите „едно от“: доказан ли е един ред, останалите не се изискват.
    dokazani = {r.get("grupa") for r in izhod
                if r.get("grupa") and r["sastoyanie"] == "налице"}
    if dokazani:
        for r in izhod:
            if r.get("grupa") in dokazani and r["sastoyanie"] != "налице":
                # По осите това НЕ е „неприложимо“: редът се изисква и е
                # намерен — само че чрез друг ред от групата.
                r["osi"] = osi("изисква се", "намерено", "група")
                r["sastoyanie"] = sastoyanie_ot_osite(r["osi"])
                r["dokazan_ot_grupata"] = True

    # ДВЕ ЧИСЛА, НЕ ЕДНО. „Мога ли да започна“ и „мога ли да подпиша“ са
    # различни въпроси; събрани в едно число, то не значи нищо.
    # (Операторът, 20.10.2026.)
    def gotovnost(etap):
        redove = [r for r in izhod if r.get("etap", "подпис") == etap
                  and r["sastoyanie"] in ("налице", "не е доказано")]
        ima = sum(r["sastoyanie"] == "налице" for r in redove)
        return {"ot": len(redove), "ima": ima, "lipsvat": len(redove) - ima,
                "procent": round(100 * ima / len(redove)) if redove else 100,
                "nyama": [r["dokument"] for r in redove if r["sastoyanie"] != "налице"]}

    return {"redove": izhod,
            "faza": faza,
            "iziskvani": sum(r["sastoyanie"] in ("налице", "не е доказано") for r in izhod),
            "lipsvat": sum(r["sastoyanie"] == "не е доказано" for r in izhod),
            "za_precenka": sum(r["sastoyanie"] == "за преценка" for r in izhod),
            "da_zapochna": gotovnost("начало"),
            "da_podpisha": gotovnost("подпис")}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    p = path()
    print("файл:", os.path.basename(p) if p else "НЕ Е НАМЕРЕН")
    ok, prichina = zaklyucheno()
    print("заключен:", "да" if ok else f"не — {prichina}")
    redove = chetene()
    print(f"документи: {len(redove)} в {len({r['razdel'] for r in redove})} раздела")

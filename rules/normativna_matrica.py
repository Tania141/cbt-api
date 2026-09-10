"""Нормативната матрица — кои актове са приложими за този строеж.

Списъкът с нормативни документи в края на комплексния доклад не е шаблонен
текст: зависи от предназначението, категорията, местоположението и режимите на
обекта. Затова тук не се кодира, а се ЧЕТЕ от справочника на оператора.

ЗАКЛЮЧЕН ИЗТОЧНИК
-----------------
Същият ред като при наредбите: файлът стои до хранилището, а отпечатъкът му се
пази в `normativna_matrica.lock.json` — sha256 и структура (брой общи актове и
брой групи). При разминаване четецът ОТКАЗВА да работи, вместо да върне нещо
подвеждащо.

    python tools/pin_naredba.py        показва какво се е променило
    python tools/pin_naredba.py --pin  записва новия отпечатък

КАКВО НЕ Е
----------
Самият справочник го казва: „не съществува единен, кратък и напълно затворен
нормативен списък“ и таблицата е „практическа карта за първоначално определяне
на приложимите актове, а не индивидуално правно или проектантско становище“.
Затова изходът е ПРЕДЛОЖЕНИЕ, което надзорътреже и допълва — не готов списък.
"""
import os, re, json, hashlib, glob

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)
LOCK = os.path.join(_DIR, "normativna_matrica.lock.json")

# Първо папката на оператора — за да печели това, което тя току-що е поправила.
# После копието в хранилището: то е единственото, което стига до Railway.
_TARSI = [
    os.path.join(os.path.dirname(_ROOT), "Закони инаредби"),
    os.path.join(os.path.dirname(_ROOT), "Закони и наредби"),
    os.path.join(_DIR, "izvori"),
    _ROOT,
]

# Заглавните редове, по които се разпознават двете таблици, които ни трябват.
GLAVA_OBSHTI = "| Нормативен акт |"
GLAVA_PO_VID = "| Група и типове строежи |"


def _vsichki():
    """Всички файлове с матрицата в първата папка, където има такива."""
    for d in _TARSI:
        hit = sorted(glob.glob(os.path.join(d, "*нормативна уредба*.md")))
        if hit:
            return hit
    return []


def path():
    hit = _vsichki()
    return hit[0] if hit else None


def dvoini():
    """Имената, ако в папката има повече от един файл с матрицата.

    Четецът взимаше първия по азбучен ред — „нормативна уредба.md“ бие
    „нормативна уредба1.md“, така че новата редакция на оператора щеше да се
    пренебрегне мълчаливо (10.09.2026). При двусмислие се отказва, не се гадае.
    """
    hit = _vsichki()
    return [os.path.basename(p) for p in hit] if len(hit) > 1 else []


def _redove_na_tablica(tekst, glava):
    """Редовете на таблицата, чийто заглавен ред започва с `glava`."""
    redove = tekst.split("\n")
    for i, l in enumerate(redove):
        if l.startswith(glava):
            izhod = []
            for r in redove[i + 2:]:            # +2: заглавие и разделител
                if not r.startswith("|"):
                    break
                kletki = [k.strip() for k in r.strip().strip("|").split("|")]
                if kletki and any(kletki):
                    izhod.append(kletki)
            return izhod
    return []


def _bez_udebelyavane(s):
    # Маркирането от Word („<span class="mark">“) идва при износ в markdown —
    # маха се, иначе влиза в името на групата и оттам в доклада.
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\*\*(.+?)\*\*", r"\1", s).strip()


def _akt_ove(s):
    """Разбива клетка с актове на отделни актове.

    Разделителят в справочника е точка и запетая. Понякога в един ред стоят и
    двойки „Закон … и Наредба …“ — те се пазят цели, защото така са написани.
    """
    return [_bez_udebelyavane(x) for x in s.split(";") if _bez_udebelyavane(x)]


def chetene():
    """(общи, по_вид) — или (None, None), ако източникът не съвпада."""
    p = path()
    if not p:
        return None, None
    tekst = open(p, encoding="utf-8").read()

    obshti = [{"akt": _bez_udebelyavane(r[0]),
               "urejda": r[1] if len(r) > 1 else "",
               "koga": r[2] if len(r) > 2 else ""}
              for r in _redove_na_tablica(tekst, GLAVA_OBSHTI)]

    po_vid = [{"grupa": _bez_udebelyavane(r[0]),
               "zadaljitelni": _akt_ove(r[1]) if len(r) > 1 else [],
               "uslovni": _akt_ove(r[2]) if len(r) > 2 else [],
               "proverki": r[3] if len(r) > 3 else ""}
              for r in _redove_na_tablica(tekst, GLAVA_PO_VID)]

    return obshti, po_vid


def otpechatak():
    p = path()
    if not p:
        return None
    tekst = open(p, encoding="utf-8").read()
    obshti, po_vid = chetene()
    return {
        "fajl": os.path.basename(p),
        "sha256": hashlib.sha256(tekst.encode("utf-8")).hexdigest(),
        "obshti": len(obshti or []),
        "grupi": len(po_vid or []),
        "imena_grupi": [g["grupa"] for g in (po_vid or [])],
    }


def zaklyucheno():
    """Съвпада ли източникът със заключения отпечатък."""
    d = dvoini()
    if d:
        return False, "два файла с матрицата: " + " · ".join(d) + " — остави един"
    if not os.path.isfile(LOCK):
        return False, "няма записан отпечатък"
    sega = otpechatak()
    if sega is None:
        return False, "справочникът не е намерен"
    with open(LOCK, encoding="utf-8") as f:
        star = json.load(f)
    if sega["sha256"] != star.get("sha256"):
        razliki = []
        if sega["obshti"] != star.get("obshti"):
            razliki.append(f"общи актове: {star.get('obshti')} → {sega['obshti']}")
        if sega["grupi"] != star.get("grupi"):
            razliki.append(f"групи: {star.get('grupi')} → {sega['grupi']}")
        novi = set(sega["imena_grupi"]) - set(star.get("imena_grupi", []))
        mahnati = set(star.get("imena_grupi", [])) - set(sega["imena_grupi"])
        if novi:
            razliki.append(f"нови групи: {', '.join(sorted(novi))}")
        if mahnati:
            razliki.append(f"махнати групи: {', '.join(sorted(mahnati))}")
        return False, "; ".join(razliki) or "съдържанието е променено"
    return True, "съвпада"


# ── Свързване с предназначението от паспорта ─────────────────────────────────
# Ключът е предназначението, както го знае библиотеката; стойността е част от
# името на групата в справочника. Търси се съвпадение по съдържание, за да не
# се чупи при дребна редакция на заглавието.
PREDNAZNACHENIE_KAM_GRUPA = {
    "жилищна":        "Жилищни сгради",
    "смесена":        "Смесени сгради",
    "административна": "Административни",
    "търговска":      "Търговски центрове",
    "хотел":          "Хотели",
    "хранене":        "Ресторанти",
    "спорт":          "Спортни",
    "здравеопазване": "Лечебни заведения",
    "образование":    "Детски градини и училища",
    "наука":          "Научни",
    "производствена": "Производствени сгради",
    "складова":       "Складове",
    "път":            "Пътища и улици",
    "мост":           "Мостове",
    "жп":             "Железопътни",
    # Операторът преименува групата на 10.09.2026 и я раздели по мощност:
    # над 35 kV и трансформатори от 16 MVA — тук; до 35 kV — „Подземни мрежи“.
    "енергийна":      "електрически мрежи",
    "вей":            "Фотоволтаични",
    "газ":            "Топлофикационни",
    "вик":            "Водопроводи",
    "култура":        "Културни ценности",
    "оръжия":         "Оръжия",
    "телекомуникации": "Телекомуникационни",
    "подземни":       "Подземни мрежи",
}


def za_obekt(prednaznachenie):
    """Предложение за нормативната рамка на този обект.

    Връща речник с общите актове, задължителните и условните за групата, и
    какво се проверява. При незаключен източник връща само причината — по-добре
    нищо, отколкото списък, за който не знаем от коя редакция е.
    """
    ok, prichina = zaklyucheno()
    if not ok:
        return {"greshka": f"справочникът не е заключен: {prichina}"}

    obshti, po_vid = chetene()
    klyuch = PREDNAZNACHENIE_KAM_GRUPA.get(prednaznachenie)
    grupa = None
    if klyuch:
        grupa = next((g for g in po_vid if klyuch.lower() in g["grupa"].lower()), None)

    return {
        "obshti": [a["akt"] for a in obshti],
        "grupa": grupa["grupa"] if grupa else None,
        "zadaljitelni": grupa["zadaljitelni"] if grupa else [],
        "uslovni": grupa["uslovni"] if grupa else [],
        "proverki": grupa["proverki"] if grupa else "",
        # Справочникът сам се определя като карта за първоначално определяне,
        # не като затворен списък. Изходът е предложение, не заключение.
        "belejka": ("Предложение по нормативната матрица. Списъкът се реже и "
                    "допълва според конкретния обект — справочникът е карта за "
                    "първоначално определяне, не изчерпателен списък."),
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    p = path()
    print("файл:", os.path.basename(p) if p else "НЕ Е НАМЕРЕН")
    ok, prichina = zaklyucheno()
    print("заключен:", "да" if ok else f"не — {prichina}")
    o, v = chetene()
    print(f"общи актове: {len(o or [])} · групи: {len(v or [])}")

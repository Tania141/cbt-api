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


USLOVIYA = "*условия към матрицата*.md"
GLAVA_USLOVIYA = "| Ключова дума |"


def path_usloviya():
    """Файлът с условията — отделно от матрицата, защото тя се изнася от Word
    и добавена колона там би изчезнала при следващия износ."""
    for d in _TARSI:
        hit = sorted(glob.glob(os.path.join(d, USLOVIYA)))
        if hit:
            return hit[0]
    return None


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
    return [_chist_akt(x) for x in s.split(";") if _chist_akt(x)]


def _chist_akt(s):
    """Без маркиране и без точката накрая — „ЗУТ.“ в края на клетката е „ЗУТ“."""
    return _bez_udebelyavane(s).rstrip(" .;")


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

    po_vid = [{"grupa": _bez_udebelyavane(r[0]).rstrip(" .;"),
               "zadaljitelni": _akt_ove(r[1]) if len(r) > 1 else [],
               "uslovni": _akt_ove(r[2]) if len(r) > 2 else [],
               "proverki": r[3] if len(r) > 3 else ""}
              for r in _redove_na_tablica(tekst, GLAVA_PO_VID)]

    return obshti, po_vid


def chetene_usloviya():
    """[(ключова дума, условие)] в реда от файла — първото съвпадение печели."""
    p = path_usloviya()
    if not p:
        return []
    tekst = open(p, encoding="utf-8").read()
    return [(r[0].strip(), (r[1] if len(r) > 1 else "").strip() or "винаги")
            for r in _redove_na_tablica(tekst, GLAVA_USLOVIYA) if r[0].strip()]


def _otpechatak_usloviya():
    p = path_usloviya()
    if not p:
        return None
    raw = open(p, "rb").read().replace(b"\r\n", b"\n")
    return {"fajl": os.path.basename(p),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "pravila": len(chetene_usloviya())}


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
        # Условията са заключени заедно с матрицата: смяна в който и да е от
        # двата файла сменя списъка в доклада.
        "usloviya": _otpechatak_usloviya(),
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
    if sega["usloviya"] is None:
        return False, ("липсва „условия към матрицата.md“ — без него условните "
                       "актове не могат да се решат")
    if sega["usloviya"] != star.get("usloviya"):
        return False, "условията към матрицата са променени"
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


def _savpada(klyuch, akt):
    """Съкращение с главни букви — като цяла дума; иначе — като начало на дума."""
    if klyuch.isupper():
        return re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(klyuch), akt) is not None
    return re.search(r"(?<!\w)%s" % re.escape(klyuch), akt, re.I) is not None


def _uslovie_za(akt, pravila):
    """Условието на първия ред, чиято ключова дума се среща в акта — или None."""
    return next((u for k, u in pravila if _savpada(k, akt)), None)


def _klyuchove(akt):
    """Разпознаваеми белези на акт — за да не излиза един и същ два пъти.

    „ЗУТ“ и „Закон за устройство на територията (ЗУТ)“ са едно; „Наредба
    № 4/2001“ и „Наредба № 4 от 21.05.2001 г.“ — също. Акт без такъв белег
    („пожарна безопасност“) никога не се смята за повторение: по-добре два
    пъти, отколкото изпуснат.

    „РД“ от „РД-02-20-3“ НЕ е съкращение: иначе всички наредби РД-… биха
    изглеждали като една и различни актове биха изпадали като „повторение“.
    """
    k = set(re.findall(r"(?<![\w-])([А-Я]{2,5})(?![\w-])", akt))
    k |= {f"{n}/{g}" for n, g in re.findall(
        r"№\s*([\w-]+?)\s*(?:/\s*|от\s+[\d.]*?)(\d{4})", akt)}
    return k


def za_obekt(pr):
    """Предложение за нормативната рамка на този обект.

    `pr` са признаците на обекта с имената от чеклиста („предназначение“,
    „вид“, „паметник“, …) — същите, по които чеклистът решава кои документи се
    изискват. Затова двете проверки не могат да се разминат за един обект.
    Приема и само предназначение като низ — за старите извиквания.

    Общите влизат, освен ако условие в „условия към матрицата.md“ ги изключи.
    Условните влизат САМО при изпълнено условие. Задължителните — винаги.
    При незаключен източник връща само причината.
    """
    if isinstance(pr, str):
        pr = {"предназначение": pr}
    ok, prichina = zaklyucheno()
    if not ok:
        return {"greshka": f"справочникът не е заключен: {prichina}"}

    from rules.cheklist_dokumenti import prilozhim
    obshti, po_vid = chetene()
    pravila = chetene_usloviya()

    def vliza(akt, bez_pravilo):
        u = _uslovie_za(akt, pravila)
        return bez_pravilo if u is None else prilozhim(u, pr)

    vpisani = set()
    vpisani_tekst = []

    def bez_povtorenia(spisak):
        izhod = []
        for a in spisak:
            k = _klyuchove(a)
            if k and k <= vpisani:
                continue
            # Актовете без съкращение („Закон за пътищата“) се хващат по текст:
            # щом вече стоят вътре в изписан акт, са повторение. Прагът от 10
            # знака пази късите общи думи — „шум“ не е „Наредба № 4/2006“.
            t = a.lower()
            if len(t) >= 10 and any(t in v for v in vpisani_tekst):
                continue
            izhod.append(a)
            vpisani.update(k)
            vpisani_tekst.append(t)
        return izhod

    klyuch = PREDNAZNACHENIE_KAM_GRUPA.get(pr.get("предназначение", ""))
    grupa = None
    if klyuch:
        grupa = next((g for g in po_vid if klyuch.lower() in g["grupa"].lower()), None)

    obshti_v = bez_povtorenia([a["akt"] for a in obshti if vliza(a["akt"], True)])
    zadalj = bez_povtorenia(grupa["zadaljitelni"]) if grupa else []
    uslovni = bez_povtorenia([a for a in grupa["uslovni"] if vliza(a, False)]) if grupa else []

    return {
        "obshti": obshti_v,
        "grupa": grupa["grupa"] if grupa else None,
        "zadaljitelni": zadalj,
        "uslovni": uslovni,
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

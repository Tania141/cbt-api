"""Слой 2 — АИ-то чете документите на обекта, кодът ги сравнява.

ЗАЩО СРАВНЕНИЕ, А НЕ ЧЕТЕНЕ
---------------------------
Всеки документ поотделно изглежда наред. Грешката е между тях: Акт 15 цитира
Акт 14 с дата 30.10.2023, а самият Акт 14 е от 31.10.2023 (ДЖИХАТ, 15.09.2026).
Документите идват от различни издатели — общината, ВиК, строителят, надзорът —
затова сравнението им е истинска проверка, не преписване от един източник.

РАЗДЕЛЕНИЕТО
------------
АИ-то само ЧЕТЕ: какъв е документът, номер, дата, издател, обект, участници и
на кои други документи се позовава — всяко с мястото, откъдето е взето.
Кодът СЪДИ: групира еднаквите неща и показва къде стойностите се разминават.
Системата не казва „грешно“, а „документите дават различни стойности — ето ги“.

Прочетеното от скан няма текст, срещу който да се свери цитатът — затова
всяка такава стойност носи „от скан — потвърди“. При текстов PDF и .docx
цитатът се търси в текста на страницата и се отбелязва сверен или не.

ДНЕВНИЯТ РЕД
------------
Двигателят е общ; какво се сравнява и в какъв ред вървят датите е в `AGENDI`.
Първият е за Акт 15 / окончателния доклад (операторът, 15.09.2026); ОСИП
ще добави свой, без да пипа двигателя.
"""
import base64, io, os, re
from datetime import date

from .engine import parse_date, OK, WARN, UNKNOWN


class NeSeChete(ValueError):
    """Файлът не може да се подготви за четене — причината е за оператора."""


# ── Видовете документи ───────────────────────────────────────────────────────
# Кодът сравнява само подобно с подобно, затова АИ-то слага всеки документ и
# всяко позоваване в една от тези групи.

VIDOVE = {
    "RS": "Разрешение за строеж",
    "ODOBREN_PROEKT": "Одобрен инвестиционен проект",
    "PROTOKOL2": "Протокол обр. 2 / 2а (откриване на площадката)",
    "ZK": "Заповедна книга",
    "OBR3": "Акт / протокол обр. 3",
    "AKT7": "Акт обр. 7",
    "AKT12": "Акт обр. 12",
    "AKT14": "Акт обр. 14",
    "AKT15": "Акт обр. 15",
    "UDOST_181": "Удостоверение по чл. 181 ЗУТ",
    "NOT_AKT": "Нотариален акт / право на строеж",
    "DOGOVOR_STROITEL": "Договор за строителство",
    "DOGOVOR_NADZOR": "Договор за строителен надзор",
    "SKICA": "Скица",
    "STANOVISHTE": "Становище",
    "PRISAEDINYAVANE": "Договор / разрешение за присъединяване или ползване на мрежа",
    "IZMERVANE": "Протокол от измерване / изпитване",
    "DEKLARACIA": "Декларация / сертификат за съответствие",
    "ENERGIEN": "Енергиен сертификат",
    "TEHN_PASPORT": "Технически паспорт",
    "DRUGO": "Друго",
}

# Един на обект — различни номер или дата между източниците значат разминаване.
# Актовете обр. 7 и 12, становищата, протоколите са много и не се сравняват
# помежду си, само ако съвпадне номерът.
UNIKALNI = ("RS", "PROTOKOL2", "ZK", "AKT14", "AKT15", "UDOST_181",
            "DOGOVOR_NADZOR", "DOGOVOR_STROITEL", "TEHN_PASPORT", "ENERGIEN")

AGENDI = {
    "od": {
        "zaglavie": "Акт 15 / окончателен доклад",
        "faza": "od",
        # (по-ранен, по-късен, защо) — нарушеният ред е за проверка, не присъда
        "red": [
            ("RS", "PROTOKOL2", "строежът не може да започне преди разрешението"),
            ("DOGOVOR_NADZOR", "PROTOKOL2", "надзорът участва в откриването на площадката"),
            ("PROTOKOL2", "AKT14", "конструкцията се приема след началото на строежа"),
            ("ZK", "AKT14", "заповедната книга се заверява в началото на строежа"),
            ("AKT14", "UDOST_181", "удостоверението по чл. 181 се издава след Акт 14"),
            ("AKT14", "AKT15", "Акт 15 е след приемането на конструкцията"),
        ],
    },
}


# ── Подготовка на файла ──────────────────────────────────────────────────────

MAX_STRANICI = 15          # първите страници носят главното; повече — бавно и скъпо
MAX_PDF_DIREKTNO = 15 * 1024 * 1024
DALGA_STRANA = 1568        # API-то смалява всичко над това; повече не помага


def _kartini(doc, n):
    """Страниците като JPEG, с номер пред всяка — за да може АИ-то да цитира."""
    import pymupdf
    blokove = []
    for i in range(n):
        page = doc[i]
        r = page.rect
        z = DALGA_STRANA / max(r.width, r.height)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z))
        jpg = pix.tobytes("jpeg", jpg_quality=80)
        blokove.append({"type": "text", "text": f"Страница {i + 1}:"})
        blokove.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg",
            "data": base64.b64encode(jpg).decode()}})
    return blokove


def podgotvi(ime, media_type, data_b64):
    """Файлът → блокове за модела + текстът по страници за сверката.

    Връща {"blokove", "stranici", "sken", "belezhka"}. `stranici` е празен,
    когато няма текстов слой — тогава нищо не може да се свери.
    """
    if not data_b64:
        raise NeSeChete("празен файл")
    try:
        raw = base64.b64decode(data_b64)
    except Exception:
        raise NeSeChete("файлът не е предаден правилно")
    ext = os.path.splitext(ime.lower())[1]

    if ext == ".doc":
        raise NeSeChete("стар формат .doc — запиши го като PDF или .docx")

    if ext == ".docx" or "wordprocessingml" in (media_type or ""):
        from docx import Document
        d = Document(io.BytesIO(raw))
        chasti = [p.text for p in d.paragraphs]
        for t in d.tables:
            for red in t.rows:
                chasti.append(" | ".join(c.text for c in red.cells))
        tekst = "\n".join(chasti)
        return {"blokove": [{"type": "text", "text": f"Текстът на {ime}:\n\n{tekst[:150000]}"}],
                "stranici": [tekst], "sken": False, "belezhka": ""}

    import pymupdf
    if ext == ".pdf" or media_type == "application/pdf":
        try:
            doc = pymupdf.open(stream=raw, filetype="pdf")
        except Exception:
            raise NeSeChete("PDF-ът не се отваря")
        n = doc.page_count
        stranici = [doc[i].get_text() for i in range(n)]
        sken = sum(len(s.strip()) for s in stranici) < 40 * max(n, 1)
        belezhka = f"прочетени са първите {MAX_STRANICI} от {n} страници" if n > MAX_STRANICI else ""
        if n <= MAX_STRANICI and len(raw) <= MAX_PDF_DIREKTNO:
            blokove = [{"type": "document", "source": {
                "type": "base64", "media_type": "application/pdf", "data": data_b64}}]
        else:
            blokove = _kartini(doc, min(n, MAX_STRANICI))
        return {"blokove": blokove, "stranici": [] if sken else stranici,
                "sken": sken, "belezhka": belezhka}

    if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff", ".bmp") \
            or (media_type or "").startswith("image/"):
        try:
            doc = pymupdf.open(stream=raw, filetype=(ext[1:] or "jpg"))
        except Exception:
            raise NeSeChete("изображението не се отваря")
        return {"blokove": _kartini(doc, min(doc.page_count, MAX_STRANICI)),
                "stranici": [], "sken": True, "belezhka": ""}

    raise NeSeChete(f"не чета файлове „{ext or media_type}“ — дай PDF, снимка или .docx")


# ── Какво АИ-то връща ────────────────────────────────────────────────────────

def _fakt(opisanie):
    return {"type": "object", "description": opisanie, "properties": {
        "stoynost": {"type": "string", "description": "стойността; празно, ако я няма"},
        "stranica": {"type": "integer", "description": "страница, от която е взета"},
        "citat": {"type": "string", "description": "буквално както е написано в документа, до 150 знака"},
        "rakopisno": {"type": "boolean", "description": "написано на ръка"},
    }, "required": ["stoynost"]}


def shema(cheklist_redove):
    vidove = list(VIDOVE)
    return {
        "type": "object",
        "properties": {
            "vid": {"type": "string", "description": "заглавието на документа, както е написано"},
            "vid_kod": {"type": "string", "enum": vidove},
            "cheklist_red": {"type": "string", "enum": [""] + list(cheklist_redove),
                             "description": "редът от чеклиста, който документът доказва; празно, ако нито един"},
            "nomer": _fakt("номерът на документа (без датата)"),
            "data": _fakt("датата на съставяне или издаване, дд.мм.гггг"),
            "izdatel": _fakt("кой го е издал или съставил"),
            "obekt": {"type": "object", "properties": {
                "upi": _fakt("УПИ, напр. XXXII-314, кв. 21"),
                "identifikator": _fakt("поземлен имот / идентификатор по КККР, напр. 68134.2817.5829"),
                "adres": _fakt("адрес или местност"),
            }},
            "uchastnici": {"type": "array", "items": {"type": "object", "properties": {
                "rolya": {"type": "string", "enum": ["възложител", "строител", "надзор",
                                                     "проектант", "технически ръководител", "друг"]},
                "ime": _fakt("име на лицето или фирмата, буквално"),
                "eik": _fakt("ЕИК / БУЛСТАТ"),
                "predstavlyavan_ot": _fakt("кой го представлява"),
                "adres": _fakt("адрес на участника"),
            }, "required": ["rolya", "ime"]}},
            "pozovavania": {"type": "array", "description":
                            "всеки друг документ, споменат с номер или дата",
                            "items": {"type": "object", "properties": {
                                "vid_kod": {"type": "string", "enum": vidove},
                                "opisanie": {"type": "string"},
                                "nomer": {"type": "string"},
                                "data": {"type": "string", "description": "дд.мм.гггг"},
                                "stranica": {"type": "integer"},
                                "citat": {"type": "string", "description": "буквално, до 150 знака"},
                            }, "required": ["vid_kod", "citat"]}},
            "podpisi": {"type": "object", "properties": {
                "ima_podpisi": {"type": "boolean"},
                "ima_pechat": {"type": "boolean"},
                "belezhka": {"type": "string"},
            }},
            "zabelezhki": {"type": "string", "description":
                           "нечетливо, зачеркнато, липсващи страници — кратко"},
        },
        "required": ["vid", "vid_kod", "cheklist_red", "nomer", "data"],
    }


UKAZANIE = """Четеш документ от досието на строеж в България за окончателния доклад на строителния надзор.

Задачата ти е само да ПРЕПИШЕШ какво пише — не да поправяш и не да съдиш.
- Пиши стойностите точно както са в документа, с грешките им. Ако фирмата е изписана „ВАСИНВЕСТ-2001“, пиши така, дори да подозираш, че е „2021“. Разминаванията ги търси кодът след теб — поправката ги скрива.
- Датата в „stoynost“ — във вида дд.мм.гггг; в „citat“ — както е написана.
- Ако нещо го няма или не се чете — остави празно. Не допълвай по догадка.
- Отбележи „rakopisno“, когато стойността е написана на ръка.
- В „pozovavania“ впиши ВСЕКИ друг документ, споменат с номер или дата: разрешение за строеж, одобрени проекти, протоколи, актове, заповедна книга, договори, нотариални актове, становища. Ако един и същ документ е споменат два пъти с различни данни — впиши и двете.
- „cheklist_red“ избери от дадения списък само ако документът наистина е такъв; иначе празно.
Запиши резултата с инструмента."""


def _redove_za_faza(faza):
    from . import cheklist_dokumenti as chd
    return [r["dokument"] for r in chd.chetene() if chd._faza_na_razdel(r["razdel"]) == faza]


# ── Сверка на цитата ─────────────────────────────────────────────────────────

def _norm_tekst(s):
    s = str(s or "").replace("­", "").lower()
    s = re.sub(r"[„“”\"«»'`]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _sveri(fakt, stranici, sken):
    """Добавя `sverka` към един факт."""
    if not isinstance(fakt, dict) or not str(fakt.get("stoynost", "") or fakt.get("citat", "")).strip():
        return
    if sken or not stranici:
        fakt["sverka"] = "от скан — потвърди"
        return
    c = _norm_tekst(fakt.get("citat"))
    if not c:
        fakt["sverka"] = "без цитат — потвърди"
        return
    s = fakt.get("stranica")
    tarsi = [stranici[s - 1]] if isinstance(s, int) and 1 <= s <= len(stranici) else stranici
    if any(c in _norm_tekst(t) for t in tarsi) or any(c in _norm_tekst(t) for t in stranici):
        fakt["sverka"] = "сверено с текста"
    else:
        fakt["sverka"] = "цитатът не е намерен в текста — провери"


def _sveri_vsichko(dok, stranici, sken):
    for k in ("nomer", "data", "izdatel"):
        _sveri(dok.get(k), stranici, sken)
    for f in (dok.get("obekt") or {}).values():
        _sveri(f, stranici, sken)
    for u in dok.get("uchastnici") or []:
        for k in ("ime", "eik", "predstavlyavan_ot", "adres"):
            _sveri(u.get(k), stranici, sken)
    for p in dok.get("pozovavania") or []:
        if sken or not stranici:
            p["sverka"] = "от скан — потвърди"
        else:
            c = _norm_tekst(p.get("citat"))
            p["sverka"] = ("сверено с текста" if c and any(c in _norm_tekst(t) for t in stranici)
                           else "цитатът не е намерен в текста — провери")


def procheti(client, model, ime, media_type, data_b64, agenda="od"):
    """Един файл → фактите му. Връща (документ, отговорът на API-то)."""
    ag = AGENDI[agenda]
    prep = podgotvi(ime, media_type, data_b64)
    redove = _redove_za_faza(ag["faza"])
    instrument = {"name": "zapishi_dokument",
                  "description": "Записва прочетеното от документа.",
                  "input_schema": shema(redove)}
    tekst = (UKAZANIE + f"\n\nФайл: {ime}\n\nРедове от чеклиста ({ag['zaglavie']}):\n"
             + "\n".join(f"- {r}" for r in redove))
    response = client.messages.create(
        model=model, max_tokens=4000,
        tools=[instrument],
        tool_choice={"type": "tool", "name": "zapishi_dokument"},
        messages=[{"role": "user", "content": prep["blokove"] + [{"type": "text", "text": tekst}]}],
    )
    dok = next((b.input for b in response.content if getattr(b, "type", "") == "tool_use"), None)
    if not isinstance(dok, dict):
        raise NeSeChete("моделът не върна прочетеното")
    # Кодът не вярва на списъците: непознатото става „друго“ / празно.
    if dok.get("vid_kod") not in VIDOVE:
        dok["vid_kod"] = "DRUGO"
    if dok.get("cheklist_red") not in redove:
        dok["cheklist_red"] = ""
    for p in dok.get("pozovavania") or []:
        if p.get("vid_kod") not in VIDOVE:
            p["vid_kod"] = "DRUGO"
    _sveri_vsichko(dok, prep["stranici"], prep["sken"])
    dok.update({"fajl": ime, "sken": prep["sken"], "belezhka": prep["belezhka"],
                "model": getattr(response, "model", model)})
    return dok, response


# ── Сравнението ──────────────────────────────────────────────────────────────

_RIMSKI = str.maketrans({"І": "I", "Х": "X", "С": "C", "М": "M", "І": "I"})


def n_data(s):
    m = re.search(r"(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2,4})", str(s or ""))
    if not m:
        return None
    d, mes, g = (int(x) for x in m.groups())
    if g < 100:
        g += 2000
    try:
        return date(g, mes, d)
    except ValueError:
        return None


def n_nomer(s):
    s = str(s or "").strip()
    s = re.split(r"\s*/\s*|\s+от\s+", s, maxsplit=1)[0]
    s = re.sub(r"^(№|No\.?|N)\s*", "", s, flags=re.I)
    return re.sub(r"[^0-9A-Za-zА-Яа-я-]", "", s).upper()


def n_upi(s):
    s = str(s or "").upper().translate(_RIMSKI)
    m = re.search(r"\b([IVXLCM]+)\s*[-–—]\s*(\d+)", s)
    return f"{m.group(1)}-{m.group(2)}" if m else ""


def n_identifikator(s):
    m = re.search(r"\d{5}\.\d{1,5}\.\d{1,5}(?:\.\d+)*", str(s or ""))
    return m.group(0) if m else ""


def n_eik(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d if len(d) in (9, 13) else ""


def n_ime(s):
    s = str(s or "").upper()
    s = re.sub(r"[„“”\"«»'`\-–—.,]", " ", s)
    s = re.sub(r"\b(ЕООД|ООД|ЕАД|АД|ЕТ|СД|КД)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _st(f):
    return str((f or {}).get("stoynost", "") if isinstance(f, dict) else f or "").strip()


def _izvor(dok, f, rol):
    f = f if isinstance(f, dict) else {}
    return {"fajl": dok.get("fajl", ""), "vid": dok.get("vid", ""), "rol": rol,
            "stranica": f.get("stranica"), "citat": f.get("citat", ""),
            "sverka": f.get("sverka", ""), "rakopisno": bool(f.get("rakopisno"))}


_PASPORT = {"fajl": "паспорт на обекта", "vid": "", "rol": "паспорт",
            "stranica": None, "citat": "", "sverka": "въведено в системата", "rakopisno": False}


def _grupiraj(tvardenia, norm, pokaz=None):
    """[(стойност, източник)] → групи по нормализирана стойност."""
    g = {}
    for st, izv in tvardenia:
        k = norm(st)
        if not k:
            continue
        grupa = g.setdefault(k, {"stoynost": pokaz(k) if pokaz else str(st).strip(), "izvori": []})
        grupa["izvori"].append(izv)
    return list(g.values())


def _dd(d):
    return d.strftime("%d.%m.%Y")


def _razminavane(kakvo, grupi, tezhest="разминаване", obyasnenie=""):
    return {"kakvo": kakvo, "tezhest": tezhest, "obyasnenie": obyasnenie,
            "stoynosti": sorted(grupi, key=lambda x: -len(x["izvori"]))}


def sravni(dokumenti, pasport=None, agenda="od", priznaci=None, neotnasya=None, dnes=None):
    """Прочетените документи → разминавания, хронология, чеклист."""
    ag = AGENDI[agenda]
    pasport = pasport or {}
    dnes = dnes or date.today()
    razm = []

    # 1. Един документ, различни номер или дата — от самия документ, от
    #    позоваванията в другите и от паспорта.
    tvard = {k: {"nomer": [], "data": []} for k in UNIKALNI}
    for d in dokumenti:
        k = d.get("vid_kod")
        if k in tvard:
            tvard[k]["nomer"].append((_st(d.get("nomer")), _izvor(d, d.get("nomer"), "самият документ")))
            tvard[k]["data"].append((_st(d.get("data")), _izvor(d, d.get("data"), "самият документ")))
        for p in d.get("pozovavania") or []:
            k2 = p.get("vid_kod")
            if k2 in tvard and k2 != k:
                izv = _izvor(d, p, "позоваване")
                tvard[k2]["nomer"].append((p.get("nomer", ""), izv))
                tvard[k2]["data"].append((p.get("data", ""), izv))
            elif k2 in tvard and k2 == k:
                # документ, който споменава друг от своя вид (напр. предишна ЗК)
                pass
    if pasport.get("rs_nomer") or pasport.get("rs_data"):
        tvard["RS"]["nomer"].append((pasport.get("rs_nomer", ""), _PASPORT))
        tvard["RS"]["data"].append((pasport.get("rs_data", ""), _PASPORT))
    if pasport.get("zk_nomer"):
        tvard["ZK"]["nomer"].append((pasport.get("zk_nomer", ""), _PASPORT))

    for k in UNIKALNI:
        g = _grupiraj(tvard[k]["data"], n_data, lambda d: _dd(d))
        if len(g) > 1:
            razm.append(_razminavane(f"Дата — {VIDOVE[k]}", g))
        g = _grupiraj(tvard[k]["nomer"], n_nomer)
        if len(g) > 1:
            razm.append(_razminavane(f"Номер — {VIDOVE[k]}", g))

    # 2. Обектът.
    for pole, norm, ime in (("identifikator", n_identifikator, "Идентификатор на имота"),
                            ("upi", n_upi, "УПИ")):
        t = [(_st((d.get("obekt") or {}).get(pole)),
              _izvor(d, (d.get("obekt") or {}).get(pole), "самият документ")) for d in dokumenti]
        if pole == "identifikator" and pasport.get("identifikator"):
            t.append((pasport["identifikator"], _PASPORT))
        g = _grupiraj(t, norm)
        if len(g) > 1:
            razm.append(_razminavane(ime, g))

    # 3. Участниците — по ЕИК: едно ЕИК, различно изписване на името е
    #    разминаване; различен представител или адрес може да е законна смяна.
    po_eik = {}
    for d in dokumenti:
        for u in d.get("uchastnici") or []:
            eik = n_eik(_st(u.get("eik")))
            if eik:
                po_eik.setdefault(eik, {"roli": set(), "u": []})
                po_eik[eik]["roli"].add(u.get("rolya", ""))
                po_eik[eik]["u"].append((d, u))
    for x in list(pasport.get("vazlozhiteli") or []) + [pasport.get("stroitel") or {}]:
        eik = n_eik(x.get("eik"))
        if eik:
            po_eik.setdefault(eik, {"roli": set(), "u": []})["u"].append((None, {
                "ime": x.get("ime", ""), "predstavlyavan_ot": x.get("predstavlyavan_ot", "")}))
    for eik, v in sorted(po_eik.items()):
        roli = ", ".join(sorted(r for r in v["roli"] if r)) or "участник"
        for pole, norm, ime, tezhest, obyasnenie in (
                ("ime", n_ime, "Име", "разминаване", "едно и също ЕИК, различно изписване"),
                ("predstavlyavan_ot", n_ime, "Представляван от", "да се провери",
                 "може да е законна смяна — провери кога"),
                ("adres", n_ime, "Адрес", "да се провери", "")):
            t = []
            for d, u in v["u"]:
                st = _st(u.get(pole))
                t.append((st, _PASPORT if d is None else _izvor(d, u.get(pole), "самият документ")))
            g = _grupiraj(t, norm)
            if len(g) > 1:
                razm.append(_razminavane(f"{ime} — {roli}, ЕИК {eik}", g, tezhest, obyasnenie))

    # 4. Хронологията — по една дата на вид: самият документ, после паспортът,
    #    после най-често цитираната.
    naj = {}
    for k in UNIKALNI:
        sobstveni = [n_data(s) for s, izv in tvard[k]["data"] if izv["rol"] == "самият документ"]
        sobstveni = [x for x in sobstveni if x]
        pasp = [n_data(s) for s, izv in tvard[k]["data"] if izv["rol"] == "паспорт"]
        pasp = [x for x in pasp if x]
        drugi = [n_data(s) for s, izv in tvard[k]["data"] if izv["rol"] == "позоваване"]
        drugi = [x for x in drugi if x]
        if sobstveni:
            naj[k] = (min(sobstveni), "от самия документ")
        elif pasp:
            naj[k] = (pasp[0], "от паспорта")
        elif drugi:
            naj[k] = (max(set(drugi), key=drugi.count), "по позоваване")
    hron = []
    for rano, kasno, zashto in ag["red"]:
        if rano in naj and kasno in naj:
            a, b = naj[rano], naj[kasno]
            ok = a[0] <= b[0]
            hron.append({"status": OK if ok else WARN,
                         "tekst": f"{VIDOVE[rano]} ({_dd(a[0])}, {a[1]}) "
                                  f"{'≤' if ok else '>'} {VIDOVE[kasno]} ({_dd(b[0])}, {b[1]})"
                                  + ("" if ok else f" — {zashto}")})
    # Сроковете от правилата D1, D2, D4 — същите, които пазят паспорта.
    from . import dates as D
    dd = {kl: _dd(naj[k][0]) for k, kl in (("PROTOKOL2", "protokol2"), ("ZK", "zk_zaverka"),
                                             ("AKT14", "akt14"), ("AKT15", "akt15")) if k in naj}
    proekt = {"docDates": dd, "РС_ВСила": pasport.get("rs_v_sila", ""), "vid": "sgrada"}
    for r in (D.rs_tri_godini, D.zk_tri_dni, D.grub_stroezh):
        v = r.run(proekt)
        if v.status != UNKNOWN:
            hron.append({"status": v.status, "tekst": f"{r.code} {r.title}: {v.message}",
                         "citat": r.citation})
    for d in dokumenti:
        x = n_data(_st(d.get("data")))
        if x and x > dnes:
            hron.append({"status": WARN, "tekst": f"„{d.get('vid') or d.get('fajl')}“ е с дата "
                                                   f"{_dd(x)} — в бъдещето ({d.get('fajl')})"})

    # 5. Чеклистът — кой ред кои файлове доказват.
    po_red = {}
    for d in dokumenti:
        r = d.get("cheklist_red")
        if not r:
            continue
        e = po_red.setdefault(r, {"dokument": r, "nomer": "", "fajlove": [], "sken": False})
        e["fajlove"].append(d.get("fajl", ""))
        e["sken"] = e["sken"] or bool(d.get("sken"))
        if not e["nomer"]:
            n, dt = _st(d.get("nomer")), n_data(_st(d.get("data")))
            e["nomer"] = " от ".join(x for x in (f"№ {n}" if n else "", _dd(dt) if dt else "") if x)
    cheklist = None
    if priznaci is not None:
        from . import cheklist_dokumenti as chd
        cheklist = chd.spisak(priznaci, [{"dokument": e["dokument"], "nomer": e["nomer"] or "прочетен"}
                                         for e in po_red.values()],
                              faza=ag["faza"], neotnasya=neotnasya or [])

    return {
        "razminavania": razm,
        "hronologia": hron,
        "predlozhenie": sorted(po_red.values(), key=lambda e: e["dokument"]),
        "bez_red": [d.get("fajl", "") for d in dokumenti if not d.get("cheklist_red")],
        "cheklist": cheklist,
        "dokumenti": len(dokumenti),
        "ot_skan": sum(bool(d.get("sken")) for d in dokumenti),
    }

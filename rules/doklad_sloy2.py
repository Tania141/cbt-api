"""Слой 2 → окончателния доклад.

РЕШЕНИЯ НА ОПЕРАТОРА (16.09.2026)
--------------------------------
1. В доклада влиза САМО потвърденото с хартията („✔ Сверено“ / „✎ Поправи“).
   Непотвърденото остава точки — докладът отива в ДНСК.
2. Паспортът (датите на съставяне, номерът на ЗК) е въведен от оператора и
   също се брои за потвърден. Когато паспортът и потвърденото в слой 2 дават
   РАЗЛИЧНИ стойности — вариант в): редът НЕ се попълва, докато не ги изравни,
   и системата казва защо. Никой от двата източника не печели мълчаливо.

Шаблонът не се пипа: в раздел Г 1.1 редовете са текст с точки, не полета.
Кодът намира параграфа по началото му и пише само след него.
"""
import copy, re
from datetime import date

from .sloy2 import n_data, n_nomer, _dd, _za_drug_stroezh

POTVARDENO = "потвърдено от оператора"


def _potv(f):
    """Стойността на факт, само ако е потвърдена с хартията."""
    if isinstance(f, dict) and f.get("sverka") == POTVARDENO and str(f.get("stoynost") or "").strip():
        return str(f["stoynost"]).strip()
    return None


def _data_potv(d):
    x = _potv(d.get("data"))
    return n_data(x) if x else None


# ── Редовете на Г 1.1 ─────────────────────────────────────────────────────────
# (етикет в доклада, vid_kod в слой 2, ключ в паспорта docDates)
REDOVE = [
    ("Протокол обр.2", "PROTOKOL2", "protokol2"),
    ("Протокол обр.3", "OBR3", "obrazec3"),
    ("Акт обр.14", "AKT14", "akt14"),
    ("Акт обр.15", "AKT15", "akt15"),
]


def _stoynosti(izvori):
    """{нормализирана стойност: [откъде]}"""
    g = {}
    for st, otkade in izvori:
        if st:
            g.setdefault(st, []).append(otkade)
    return g


def _reshi(etiket, izvori):
    """Една стойност → нея; няколко различни → None и причина (вариант в)."""
    g = _stoynosti(izvori)
    if not g:
        return None, None
    if len(g) == 1:
        return next(iter(g)), None
    razl = "; ".join(f"{k} ({', '.join(v)})" for k, v in g.items())
    return None, f"{etiket}: паспортът и потвърденото от документите се разминават — {razl}. Изравни ги."


def za_doklad(dokumenti, doc_dates=None, zk=None):
    """→ {"g11": {етикет: текст или None}, "spisatsi": {...}, "prichini": [...]}.

    `dokumenti` — прочетеното с приложени потвърждения (както го праща PWA);
    `doc_dates` — датите на съставяне от паспорта; `zk` — {number, date} от регистъра.
    """
    doc_dates, zk = doc_dates or {}, zk or {}
    sgrada = [d for d in dokumenti or [] if not _za_drug_stroezh(d)]
    g11, prichini = {}, []

    for etiket, kod, dd_kl in REDOVE:
        izvori = [(_dd(x), d.get("id") or d.get("fajl", "")) for d in sgrada
                  if d.get("vid_kod") == kod for x in [_data_potv(d)] if x]
        pasp = n_data(doc_dates.get(dd_kl))
        if pasp:
            izvori.append((_dd(pasp), "паспорт"))
        st, pr = _reshi(etiket, izvori)
        g11[etiket] = st
        if pr:
            prichini.append(pr)

    # Заповедна книга: номерът е на регистъра (само той раздава номера);
    # датата на заверка — паспорт срещу потвърдената дата на документ ЗК.
    izvori = [(_dd(x), d.get("id") or d.get("fajl", "")) for d in sgrada
              if d.get("vid_kod") == "ZK" for x in [_data_potv(d)] if x]
    pasp = n_data(doc_dates.get("zk_zaverka")) or n_data(zk.get("date"))
    if pasp:
        izvori.append((_dd(pasp), "паспорт"))
    zk_data, pr = _reshi("Заповедна книга — дата", izvori)
    if pr:
        prichini.append(pr)
    g11["Заповедна книга"] = {"nomer": str(zk.get("number") or "").strip() or None, "data": zk_data}

    # Актове обр. 7: брой и период. Слой 2 — само ако ВСИЧКИ прочетени актове
    # са с потвърдена дата; иначе периодът би бил от непроверени дати.
    akt7 = [d for d in sgrada if d.get("vid_kod") == "AKT7"]
    s2 = None
    if akt7:
        dati = [_data_potv(d) for d in akt7]
        if all(dati):
            s2 = (len(dati), _dd(min(dati)), _dd(max(dati)))
        else:
            prichini.append(f"Акт обр.7: {sum(not x for x in dati)} от {len(dati)} прочетени акта са без "
                            f"потвърдена дата — периодът не се попълва от документите.")
    p7 = doc_dates.get("akt7") or {}
    pasp7 = None
    if n_data(p7.get("ot")) and n_data(p7.get("do")):
        pasp7 = (int(p7["br"]) if str(p7.get("br", "")).isdigit() else None,
                 _dd(n_data(p7["ot"])), _dd(n_data(p7["do"])))
    if s2 and pasp7 and (s2[1:] != pasp7[1:] or (pasp7[0] is not None and pasp7[0] != s2[0])):
        prichini.append(f"Акт обр.7: паспортът дава {pasp7[0] or '?'} акта от {pasp7[1]} до {pasp7[2]}, "
                        f"потвърдените документи — {s2[0]} акта от {s2[1]} до {s2[2]}. Изравни ги.")
        g11["Акт обр.7"] = None
    else:
        g11["Акт обр.7"] = s2 or pasp7

    # ── Списъците: т. 3 и раздел В ──────────────────────────────────────────
    # Документ влиза, ако поне номерът или датата е потвърдена и няма
    # непотвърдена от двете.
    def red(d):
        n, dt = d.get("nomer"), d.get("data")
        imat = [f for f in (n, dt) if isinstance(f, dict) and str(f.get("stoynost") or "").strip()]
        if not imat or any(_potv(f) is None for f in imat):
            return None
        chasti = [str(d.get("vid") or "").strip() or "документ"]
        if _potv(n):
            chasti.append(f"№ {_potv(n)}")
        if _potv(dt):
            chasti.append(f"от {_dd(n_data(_potv(dt))) if n_data(_potv(dt)) else _potv(dt)} г.")
        izd = _potv(d.get("izdatel"))
        return " ".join(chasti) + (f", {izd}" if izd else "")

    spisatsi = {"laboratorii": [], "deklaracii": [], "aktove": [], "stanovishta": []}
    nepotv = 0
    for d in dokumenti or []:
        kod = d.get("vid_kod")
        kade = ("laboratorii" if kod == "IZMERVANE" else "deklaracii" if kod in ("DEKLARACIA", "ENERGIEN")
                else "aktove" if kod in ("AKT12",)
                else "stanovishta" if kod in ("STANOVISHTE", "PRISAEDINYAVANE") or _za_drug_stroezh(d)
                else None)
        if not kade:
            continue
        t = red(d)
        if t:
            if t not in spisatsi[kade]:
                spisatsi[kade].append(t)
        else:
            nepotv += 1
    if nepotv:
        prichini.append(f"{nepotv} прочетени документа за т. 3 и раздел В не са влезли — "
                        f"номерът или датата им не е сверена с хартията.")
    return {"g11": g11, "spisatsi": spisatsi, "prichini": prichini}


# ── Техническото описание на строежа ─────────────────────────────────────────
# Решение на оператора (16.09.2026): Акт 15 се мени, докато се пише ОД, но
# описанието на строежа е едно и също — само документите се дописват. Затова не
# се копира от Акт 15 в ОД, а се пази ВЕДНЪЖ в обекта и оттам го взимат двата
# (засега — ОД с АИ). Тук: как се изрязва от готов Акт 15 и как се слага в ОД.

NACHALO, KRAI = "===ТЕХНИЧЕСКО_НАЧАЛО===", "===ТЕХНИЧЕСКО_КРАЙ==="


def izrezhi_tehnichesko(redove):
    """Редовете на Акт 15 → текстът на описанието, дословно.

    Между маркерите, ако ги има (Акт 15 от шаблона); иначе от „Строежът
    представлява“ до „Въз основа на горните констатации“. None, ако не се намира.
    """
    redove = [str(r).rstrip() for r in redove]
    ch = lambda r: _nachalo(r)
    i = next((k for k, r in enumerate(redove) if ch(r) == NACHALO), None)
    j = next((k for k, r in enumerate(redove) if ch(r) == KRAI), None)
    if i is None or j is None or j <= i:
        # Истинският Акт 15 на оператора (ДЖИХАТ): „1. По издадените строителни
        # книжа…“ са документите (менят се); „2. По изпълнението на строежа:“ до
        # „Въз основа…“ е описанието (не се мени). Шаблонът — „Строежът представлява“.
        nach = re.compile(r"^(\d+\.\s*)?По изпълнението на строежа|^Строежът представлява")
        i = next((k for k, r in enumerate(redove) if nach.match(ch(r))), None)
        j = next((k for k, r in enumerate(redove) if ch(r).startswith("Въз основа на горните констатации")), None)
        if i is None or j is None or j <= i:
            return None
        izrez = redove[i:j]
        # „2. По изпълнението на строежа:“ е заглавие — в ОД си има свое („Б. По
        # изпълнение на СМР:“), да не се повтаря.
        if re.match(r"^(\d+\.\s*)?По изпълнението на строежа:?$", ch(izrez[0])):
            izrez = izrez[1:]
    else:
        izrez = redove[i + 1:j]
    # празни редове в началото и края — без тях
    while izrez and not izrez[0].strip():
        izrez.pop(0)
    while izrez and not izrez[-1].strip():
        izrez.pop()
    return "\n".join(izrez) or None


def redove_ot_fajl(ime, raw):
    """.docx или PDF с текст → редове. Сканиран PDF → None (няма текст)."""
    ext = ime.lower().rsplit(".", 1)[-1] if "." in ime else ""
    import io
    if ext == "docx":
        from docx import Document
        return [p.text for p in Document(io.BytesIO(raw)).paragraphs]
    if ext == "pdf":
        import pymupdf
        d = pymupdf.open(stream=raw, filetype="pdf")
        tekst = "\n".join(d[i].get_text() for i in range(d.page_count))
        return tekst.split("\n") if len(tekst.strip()) > 40 * max(d.page_count, 1) else None
    raise ValueError("дай Акт 15 като .docx или PDF с текст (стар .doc — запиши го като .docx)")


def vmukni_tehnichesko(doc, tekst):
    """Слага описанието между маркерите в ОД; маркерите и заместителят изчезват.
    Без текст — шаблонът остава както е."""
    if not (tekst or "").strip():
        return False
    from docx.text.paragraph import Paragraph
    pars = list(doc.paragraphs)
    i = next((k for k, p in enumerate(pars) if _nachalo(p.text) == NACHALO), None)
    j = next((k for k, p in enumerate(pars) if _nachalo(p.text) == KRAI), None)
    if i is None or j is None or j <= i:
        return False
    # Между маркерите има и истинско съдържание — в ОД заглавието „Б. По
    # изпълнение на СМР:“ стои вътре. Сменя се САМО заместителят „[ … ]“;
    # маркерите се махат, всичко друго остава.
    zam = next((pars[k] for k in range(i + 1, j) if _nachalo(pars[k].text).startswith("[")), None)
    if zam is None:
        return False
    redove = tekst.split("\n")
    _pishi(zam, redove[0])
    posleden = zam
    for r in redove[1:]:
        posleden = _sled(posleden, r)
    for k in (j, i):
        pars[k]._p.getparent().remove(pars[k]._p)
    return True


# ── Записване в .docx ─────────────────────────────────────────────────────────

def _pishi(par, tekst):
    """Сменя текста на параграф, като пази оформлението на първия run."""
    runs = par.runs
    if not runs:
        par.add_run(tekst)
        return
    runs[0].text = tekst
    for r in runs[1:]:
        r.text = ""


def _sled(par, tekst):
    """Нов параграф след `par`, със същото оформление."""
    novo = copy.deepcopy(par._p)
    par._p.addnext(novo)
    from docx.text.paragraph import Paragraph
    p = Paragraph(novo, par._parent)
    _pishi(p, tekst)
    return p


def _nachalo(t):
    return re.sub(r"\s+", " ", t or "").strip()


def zapishi(doc, rez):
    """Попълва Г 1.1 и списъците. Празното остава с точките на шаблона."""
    g11, sp = rez["g11"], rez["spisatsi"]
    tochki = "................................."
    for par in list(doc.paragraphs):
        t = _nachalo(par.text)
        for etiket in ("Протокол обр.2", "Протокол обр.3", "Акт обр.14", "Акт обр.15"):
            if t.startswith(f"{etiket} от"):
                if g11.get(etiket):
                    _pishi(par, f"{etiket} от {g11[etiket]} г.")
        if t.startswith("Заповедна книга №"):
            z = g11.get("Заповедна книга") or {}
            if z.get("nomer") or z.get("data"):
                _pishi(par, f"Заповедна книга № {z.get('nomer') or '..................'} "
                            f"от {(z['data'] + ' г.') if z.get('data') else tochki}")
        if t.startswith("Акт обр.7 от"):
            a7 = g11.get("Акт обр.7")
            if a7:
                br = f"{a7[0]} бр. " if a7[0] else ""
                _pishi(par, f"Актове обр.7 — {br}от {a7[1]} г. до {a7[2]} г.")
        for zagl, kl in (("Протоколи от Акредитирани лаборатории:", "laboratorii"),
                         ("Декларации за екслоатационни характеристики", "deklaracii"),
                         ("Актове и протоколи по време на строителството:", "aktove")):
            if t.startswith(zagl) and sp.get(kl):
                posleden = par
                for x in sp[kl]:
                    posleden = _sled(posleden, f"– {x}")
        if t.startswith("При извършеното строителство са спазени всички нормативни изисквания") and sp.get("stanovishta"):
            # следващият параграф е „.......“ — там отиват становищата
            sledvasht = par._p.getnext()
            from docx.text.paragraph import Paragraph
            if sledvasht is not None and _nachalo(Paragraph(sledvasht, par._parent).text).strip(".") == "":
                p0 = Paragraph(sledvasht, par._parent)
                _pishi(p0, f"– {sp['stanovishta'][0]}")
                posleden = p0
                for x in sp["stanovishta"][1:]:
                    posleden = _sled(posleden, f"– {x}")
    return doc

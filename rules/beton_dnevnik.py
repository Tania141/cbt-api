# -*- coding: utf-8 -*-
"""Бетоновият дневник → предложение за актовете обр. 7.

Операторът, 09–10.11.2026:
- актовете обр. 7 се съставят по бетоновия дневник — по един на бетониране;
- актът е ПРЕДИ бетонирането: приемат се кофражът и армировката, разрешава се
  бетонирането („и аз неправилно съм казала“). При Радулов — ден до седмица
  преди бетона. Затова предложената дата е ДЕН ПРЕДИ бетона и се проверява;
- дневникът идва като сканиран ръкопис (с АИ — всичко се сверява) или като
  .xlsx (с код, без АИ).

В дневника (Приложение № 6 към чл. 38 от Правилата за контрол и приемане на
бетонни и стоманобетонни конструкции) датата на бетонирането е МЕСЕЦ и ДЕН —
без година. Годината идва от „Започнат на“ и расте, когато месецът падне.
"""
import base64
import io
import re
from datetime import date, timedelta

from .sloy2 import podgotvi, NikoyNeMozhe

RAZRESHAVA = "Бетониране на гореописаните елементи."

UKAZANIE = """Това е ДНЕВНИК НА БЕТОНОВИТЕ РАБОТИ (Приложение № 6), попълнен на ръка.
Страниците може да са завъртени.

Прочети:
- „zapochnat“ — датата „Започнат на“ от заглавната страница, дд.мм.гггг;
- „redove“ — ВСЕКИ попълнен ред от таблицата, отгоре надолу, страница след
  страница. За всеки ред:
  - „element“ — колона 1 „Конструкция (елемент)“, ДОСЛОВНО, с котите, както
    са написани (напр. „Плоча на к+2,61“, „Вертикали от к-3,12 до ±0,00“);
  - „obem“ — колона 2, обемът в м³, както е написан;
  - „mesec“ и „den“ — колони 4 и 5 „Дата на бетонирането“: месец и ден, числа;
  - „stranica“ — страницата във файла.
Празните редове не се пишат. Не предполагай — нечетливото остава празно.
Не пиши ЕГН.
"""


def _s(o):
    return {"type": "string", "description": o}


SHEMA = {
    "type": "object",
    "properties": {
        "zapochnat": _s("датата „Започнат на“, дд.мм.гггг"),
        "redove": {"type": "array", "items": {"type": "object", "properties": {
            "element": _s("колона 1, дословно"),
            "obem": _s("колона 2, м³"),
            "mesec": {"type": "integer"},
            "den": {"type": "integer"},
            "stranica": {"type": "integer"},
        }, "required": ["element"]}},
    },
    "required": ["redove"],
}

# Кота: по желание знак, после число със запетая или точка. Без знак — както
# е написана („до 8,39“). „К-312“ без запетая НЕ е кота: не се гадае дали е
# -3,12 или -31,2 — полето остава празно и личи. (Радулов, 10.11.2026)
_KOTA = re.compile(r"([±+\-–−])?\s*(\d+)\s*[.,]\s*(\d+)")


def _kota(t):
    m = _KOTA.findall(str(t or ""))
    if not m:
        return ""
    z, c, d = m[-1]
    z = "-" if z in "–−" and z else z
    return f"{z}{int(c)},{d}"


def koti(element):
    """→ (от, до). „Вертикали от к-3,12 до ±0,00“ → ('-3,12', '±0,00').

    „от … до …“ се чете ПО МЯСТО: нечетимата страна остава празна, вместо да
    вземе котата на другата. (Радулов: „от К-312 до ±0,00“ излизаше
    „от ±0,00 до ±0,00“.) Една кота без „от/до“ — плоча — е и двете."""
    e = str(element or "")
    m = re.search(r"\bот\b(.*?)\bдо\b(.*)", e, re.I)
    if m:
        return _kota(m.group(1)), _kota(m.group(2))
    m = re.search(r"(.*?)\bдо\b(.*)", e, re.I)
    if m:
        return _kota(m.group(1)), _kota(m.group(2))
    k = _kota(e)
    return k, k


def _data(s):
    m = re.search(r"(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2,4})", str(s or ""))
    if not m:
        return None
    d, me, g = (int(x) for x in m.groups())
    g += 2000 if g < 100 else 0
    try:
        return date(g, me, d)
    except ValueError:
        return None


def _f(d):
    return d.strftime("%d.%m.%Y") if d else ""


def predlozhenie(redove, zapochnat=""):
    """Прочетените редове → предложените актове обр. 7, по един на бетониране.

    Всеки ред носи и опората си: какво пише в дневника и как е изведена
    датата — за да личи кое е прочетено и кое изведено.
    """
    nachalo = _data(zapochnat)
    godina = nachalo.year if nachalo else None
    predishen = nachalo.month if nachalo else 0
    izhod = []
    for r in redove:
        element = str(r.get("element") or "").strip()
        if not element:
            continue
        beton = _data(r.get("data_beton")) if r.get("data_beton") else None
        belezhka = []
        if beton:
            godina, predishen = beton.year, beton.month
        else:
            try:
                me, den = int(r.get("mesec") or 0), int(r.get("den") or 0)
            except (TypeError, ValueError):
                me, den = 0, 0
            if me and den and godina:
                if me < predishen:
                    godina += 1
                predishen = me
                try:
                    beton = date(godina, me, den)
                    belezhka.append("годината — по „Започнат на“ и реда на месеците")
                except ValueError:
                    beton = None
            if not beton:
                belezhka.append("датата на бетона не се чете — впиши я")
        ot, do = koti(element)
        akt = beton - timedelta(days=1) if beton else None
        izhod.append({
            "element": element,
            "obem": str(r.get("obem") or "").strip(),
            "data_beton": _f(beton),
            "stranica": r.get("stranica"),
            "belezhka": "; ".join(belezhka),
            # Предложеното — операторът го поправя, слива или маха.
            "data": _f(akt),
            "ot": ot,
            "do": do,
            "smr": "Кофраж и армировка на " + element[:1].lower() + element[1:],
            "razreshava": RAZRESHAVA,
        })
    return izhod


# ── .xlsx — с код, без АИ ────────────────────────────────────────────────────

def _glava(red):
    t = [str(c or "").strip().lower() for c in red]
    el = next((i for i, x in enumerate(t) if "конструкция" in x or "елемент" in x), None)
    if el is None:
        return None
    return {"element": el,
            "obem": next((i for i, x in enumerate(t) if "обем" in x), None),
            "data": next((i for i, x in enumerate(t) if "бетониране" in x), None),
            "mesec": next((i for i, x in enumerate(t) if x.startswith("месец")), None),
            "den": next((i for i, x in enumerate(t) if x in ("дата", "ден")), None)}


def procheti_xlsx(raw):
    """xlsx → редове. Търси реда със заглавията „Конструкция (елемент)“ и
    „Дата на бетонирането“ (или „Месец“ + „Дата“)."""
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
    redove = []
    for ws in wb.worksheets:
        kol = None
        for red in ws.iter_rows(values_only=True):
            if kol is None:
                kol = _glava(red)
                continue
            # Под-заглавието („Месец | Дата“) идва на следващия ред.
            t = [str(c or "").strip().lower() for c in red]
            if "месец" in t:
                kol["mesec"] = t.index("месец")
                if "дата" in t:
                    kol["den"] = t.index("дата")
                continue

            def vz(i):
                return red[i] if i is not None and i < len(red) else None
            element = str(vz(kol["element"]) or "").strip()
            if not element or element.isdigit():
                continue
            r = {"element": element, "obem": str(vz(kol["obem"]) or "").strip()}
            cyala = vz(kol["den"]) if kol["den"] is not None else vz(kol["data"])
            if hasattr(cyala, "strftime"):
                r["data_beton"] = cyala.strftime("%d.%m.%Y")
            elif cyala and _data(cyala):
                r["data_beton"] = str(cyala)
            else:
                r["mesec"], r["den"] = vz(kol["mesec"]), cyala
            redove.append(r)
    return redove


def procheti(chetci, ime, media_type, data_b64, stranici=None):
    """Дневникът → ({redove, zapochnat, predlozhenie}, info)."""
    if ime.lower().endswith((".xlsx", ".xlsm")):
        redove = procheti_xlsx(base64.b64decode(data_b64))
        return ({"redove": redove, "zapochnat": "", "fajl": ime, "chetec": "кодът — от таблицата",
                 "predlozhenie": predlozhenie(redove)}, {"chetec": "код"})
    from .chetci import NeMozheSega
    prep = podgotvi(ime, media_type, data_b64, stranici)
    raw = prep.get("raw") or b""
    prichini = []
    for chetec in list(chetci):
        try:
            dok, i = chetec.chete(prep, SHEMA, UKAZANIE + f"\n\nФайл: {ime}", ime=ime, raw=raw,
                                  edin_dokument=True)
            d = (dok[0] if isinstance(dok, list) else dok) or {}
            redove = [r for r in d.get("redove") or [] if str((r or {}).get("element") or "").strip()]
            if not redove:
                prichini.append((chetec.ime, "няма прочетени редове"))
                continue
            zap = str(d.get("zapochnat") or "").strip()
            return ({"redove": redove, "zapochnat": zap, "fajl": ime, "chetec": chetec.ime,
                     "predlozhenie": predlozhenie(redove, zap)},
                    {"chetec": chetec.ime, **{k: i.get(k) for k in ("model", "tokens_in", "tokens_out")}})
        except NeMozheSega as e:
            prichini.append((chetec.ime, str(e)[:300]))
    raise NikoyNeMozhe(prichini or [("", "няма настроен четец")])

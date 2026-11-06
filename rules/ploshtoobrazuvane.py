# -*- coding: utf-8 -*-
"""Площообразуването → списъкът на обектите в сградата и видът им.

Операторът, 05–06.11.2026:
  · „По правило идва от една таблица наречена ПЛОЩООБРАЗУВАНЕ.“
  · „От площообразуването да се чете само вида на обектите в сградата.“
    Площите и идеалните части НЕ се четат — сверката с нотариалните актове
    „не е наша работа“.
  · Таблица IV (дворна площ) — нито един от редовете ѝ не е обект.

Чете се с код, без АИ: таблицата е подредена — колоната „Обекти“ е една и
съща във всички таблици, редовете „Общо …“ се пропускат.
"""
import base64
import io
import re

VIDOVE = [
    (re.compile(r"подземен\s+гараж", re.I), "подземен гараж"),
    (re.compile(r"апартамент", re.I), "апартамент"),
    (re.compile(r"мезонет", re.I), "апартамент"),
    (re.compile(r"ателие", re.I), "ателие"),
    (re.compile(r"офис", re.I), "офис"),
    (re.compile(r"магазин", re.I), "магазин"),
    (re.compile(r"гараж", re.I), "гараж"),
    (re.compile(r"паркомясто|паркоместа", re.I), "паркомясто"),
    (re.compile(r"склад", re.I), "склад"),
    (re.compile(r"мазе", re.I), "мазе"),
    (re.compile(r"таван", re.I), "таван"),
]


class NeSeChete(Exception):
    pass


def _vid(ime):
    for izraz, vid in VIDOVE:
        if izraz.search(ime):
            return vid
    return "друго"


def _chislo(v):
    try:
        return float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def obekti_ot_redove(redove):
    """Редовете на листа (списъци от клетки) → [{ime, vid, tablica, etazh}]."""
    kol = None          # колоната „Обекти“
    tablica = ""
    dvor = False
    out, vidyani = [], set()
    for red in redove:
        kletki = ["" if c is None else str(c).strip() for c in red]
        # Заглавието на колоните — там е „Обекти“.
        for i, c in enumerate(kletki):
            if c.lower() == "обекти":
                kol = i
        tekst = " ".join(kletki)
        m = re.search(r"ТАБЛИЦА\s+([IVXІ\-аабв]+)\s*[-–—]\s*(.+)", tekst)
        if m and "ОПРЕДЕЛЯНЕ" not in tekst.upper():
            tablica = (m.group(1) + " — " + m.group(2)).strip(" |")
            dvor = bool(re.search(r"дворн", tablica, re.I))
            continue
        if kol is None or kol >= len(kletki):
            continue
        ime = kletki[kol]
        if not ime or ime.lower() == "обекти" or re.match(r"^(общо|таблица)\b", ime, re.I):
            continue
        if re.fullmatch(r"\d+", ime):          # редът с номерата на колоните
            continue
        plosht = _chislo(kletki[kol + 1]) if kol + 1 < len(kletki) else None
        if not plosht or plosht <= 0:
            continue
        if dvor:                               # таблица IV — нито един не е обект
            continue
        klyuch = ime.lower()
        if klyuch in vidyani:
            continue
        vidyani.add(klyuch)
        out.append({"ime": ime, "vid": _vid(ime), "tablica": tablica,
                    "etazh": kletki[0] if kol > 0 else ""})
    return out


def procheti(ime, data_b64):
    """Файлът → {obekti, broi_po_vid, fajl}."""
    if not data_b64:
        raise NeSeChete("празен файл")
    raw = base64.b64decode(data_b64)
    if ime.lower().endswith(".xls"):
        raise NeSeChete("стар формат .xls — отвори го в Excel и го запиши като .xlsx")
    if not ime.lower().endswith(".xlsx"):
        raise NeSeChete("очаква се таблица .xlsx")
    import openpyxl
    try:
        kniga = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
    except Exception as e:
        raise NeSeChete(f"таблицата не се отваря: {e}")
    obekti = []
    for list_ in kniga.worksheets:
        ot_lista = obekti_ot_redove(list_.iter_rows(values_only=True))
        imena = {o["ime"].lower() for o in obekti}
        obekti += [o for o in ot_lista if o["ime"].lower() not in imena]
    if not obekti:
        raise NeSeChete("не намерих колона „Обекти“ с обекти в нея")
    broi = {}
    for o in obekti:
        broi[o["vid"]] = broi.get(o["vid"], 0) + 1
    return {"fajl": ime, "obekti": obekti, "broi_po_vid": broi}

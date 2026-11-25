# -*- coding: utf-8 -*-
u"""Речникът се учи сам — от прочетеното и потвърденото (25.11.2026).

`ДА ПРОЧЕТА/ЗАДАНИЕ-ЕДИН-ЗАПИС.md`, стъпка 1. Моделът НЕ се обучава — учи се
системата: брои. Обикновен код, без АИ, всеки път един и същ резултат.

ПРАВИЛОТО (прагът е на оператора, 25.11.2026): вид документ (името, което
четецът дава) се научава към ред, когато
  · е видян при ПОНЕ 3 РАЗЛИЧНИ ОБЕКТА — броят се обекти, не документи: един
    обект със 17 акта обр. 7 е едно доказателство, не седемнайсет;
  · ПОНЕ 90 % от обектите сочат един ред;
  · операторът не е казал „не е“ за тази двойка.
Учи се само от СВЕРЕНИ документи; несверените се броят, но не учат.

ТВОЕТО БИЕ БРОЕНЕТО: „✔ това е“ от оператора (`rechnik.chetec`) е научено
веднага и никое броене не го сменя; „не е“ (`rechnik.ne`) забранява двойката.

ЗАБРАНА: различни образци никога не са едно — вид „… обр. 7“ не се учи към ред
„… обр. 14“, колкото и да е броено.

Мярката на истинските данни (13 досиета, 242 документа, 25.11.2026): правилото
научава само „Разрешение за строеж“. Чистото броене ще помага при 30–40 обекта;
дотогава двигателят е „✔ това е“ на място. Казано на оператора, прието.
"""
import re

PRAG_OBEKTI = 3
PRAG_DYAL = 0.9


def norm(s):
    u"""Същото като `_rk` в `akt/rechnik.js` — двете трябва да дават едно."""
    s = str(s or "").lower()
    s = re.sub(r"[„“”\"«»()\.,;:—–-]", " ", s)
    return " ".join(s.split())


def _obrazec(s):
    m = re.search(r"(?:обр(?:азец)?\.?\s*)(\d+)", norm(s).replace("образец", "обр"))
    return m.group(1) if m else None


def uchi(obobshtenie, rechnik=None):
    u"""obobshtenie — [{pi, vid, red, sveren}] от всички обекти (без лични данни).

    Връща {нормализиран вид: {red, obekti, dyal, broy_dokumenti}} — само
    наученото по броене. Казаното от оператора не е тук: то е в `rechnik.chetec`
    и бие това.
    """
    r = rechnik or {}
    ne = set(r.get("ne") or [])
    kazano = set((r.get("chetec") or {}).keys())
    po_vid = {}
    for x in obobshtenie or []:
        if not x.get("sveren") or not x.get("red") or not x.get("vid"):
            continue
        v = norm(x["vid"])
        e = po_vid.setdefault(v, {})
        o = e.setdefault(x["red"], {"obekti": set(), "dok": 0})
        o["obekti"].add(str(x.get("pi") or ""))
        o["dok"] += 1
    izhod = {}
    for v, redove in po_vid.items():
        if v in kazano:
            continue
        vsichki = set().union(*(o["obekti"] for o in redove.values()))
        if len(vsichki) < PRAG_OBEKTI:
            continue
        red, o = max(redove.items(), key=lambda kv: len(kv[1]["obekti"]))
        dyal = len(o["obekti"]) / max(1, sum(len(z["obekti"]) for z in redove.values()))
        if dyal < PRAG_DYAL or f"{v}|{norm(red)}" in ne:
            continue
        ov, orr = _obrazec(v), _obrazec(red)
        if ov and orr and ov != orr:
            continue
        izhod[v] = {"red": red, "obekti": len(vsichki), "dyal": round(dyal, 2), "broy_dokumenti": o["dok"]}
    return izhod


def red_za_vid(vid, rechnik):
    u"""Към кой ред сочи видът според речника — казаното от оператора бие
    наученото. (red, kak) или (None, None). Същото като `rechnikRedZaVid` в ПВА."""
    r = rechnik or {}
    v = norm(vid)
    kaz = (r.get("chetec") or {}).get(v) or {}
    if kaz.get("red"):
        return kaz["red"], "речникът — казано от оператора"
    n = (r.get("nauchen") or {}).get(v) or {}
    if n.get("red") and f"{v}|{norm(n['red'])}" not in set(r.get("ne") or []):
        return n["red"], f"речникът — научено от {n.get('obekti')} обекта"
    return None, None


def prilozhi(dokumenti, rechnik):
    u"""Четецът връзва през речника (стъпка 2, 25.11.2026): АИ-то избира ред
    всеки път наново и при различни обекти скача между три реда за един и същ
    договор. Където речникът знае вида — връзката е неговата; онова, което
    четецът е избрал, се пази в `cheklist_red_chetec`, за да се вижда разликата.
    Различни образци — никога."""
    smeneni = 0
    for d in dokumenti or []:
        red, kak = red_za_vid(d.get("vid"), rechnik)
        if not red or red == d.get("cheklist_red"):
            continue
        ov, orr = _obrazec(d.get("vid")), _obrazec(red)
        if ov and orr and ov != orr:
            continue
        d["cheklist_red_chetec"] = d.get("cheklist_red") or ""
        d["cheklist_red"] = red
        d["red_ot"] = kak
        smeneni += 1
    return smeneni

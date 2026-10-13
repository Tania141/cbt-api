# -*- coding: utf-8 -*-
"""Четене на документ за собственост → събития за регистъра (13.10.2026).

Операторът: „четенето на НА и проверките да бъде само в Собственост“.

България е регистър на АКТОВЕ: кой е собственик днес не пише никъде, извежда
се от веригата. Затова четецът не търси „собственик“ — търси ПРЕХВЪРЛЯНЕ: от
кого, на кого, какъв дял, с какъв документ.

Номерът на акта, томът, регистърът и нотариусът се вписват на ръка в PWA —
сбъркана цифра там сочи чужд документ и не личи никъде. Тук се предлагат, за
да стоят до вписаното.
"""
import re
from fractions import Fraction

from .sloy2 import podgotvi, NeSeChete, NikoyNeMozhe   # същата подготовка на файла

VIDOVE = [
    "нотариален акт",
    "договор за покупко-продажба",
    "договор за учредяване право на строеж",
    "договор за дарение",
    "договор за доброволна делба",
    "удостоверение за наследници",
    "постановление за възлагане",
    "решение на съда",
    "договор за апорт",
    "друго",
]

SABITIA = ["първоначално", "покупко-продажба", "дарение", "наследяване",
           "делба", "замяна", "учредяване право на строеж", "апорт"]

UKAZANIE = """Прочети този документ за собственост.

Търсиш ПРЕХВЪРЛЯНЕ на вещно право: кой на кого какво прехвърля и в какъв дял.
Не търсиш „кой е собственикът“ — това се извежда после от веригата.

Правила:
1. Дяловете ги давай като ДРОБ, точно както пише: „1/2“, „1/6“, „цялото“ → „1/1“.
   Никога не превръщай в процент и не закръглявай.
2. Имената изписвай ДОСЛОВНО, с всички бащини имена.
3. Обектите — с идентификатора по КККР, ако е посочен; иначе описанието.
4. При удостоверение за наследници: прехвърлянето е от наследодателя към всеки
   наследник. Ако документът не казва дяловете, остави dyal празно — ще ги
   реши операторът.
5. Ако нещо не пише в документа — остави го празно. Не предполагай.
"""


def _s(opisanie, **ostanalo):
    return {"type": "string", "description": opisanie, **ostanalo}


# Самата схема (input_schema), не описание на инструмент — четците я обвиват.
SHEMA = {
    "type": "object",
    "properties": {
        "vid": _s("какъв е документът", enum=VIDOVE),
        "nomer": _s("номер на акта, дословно"),
        "tom": _s("том"),
        "registar": _s("регистрационен номер"),
        "delo": _s("дело и година, напр. „98/2009“"),
        "data": _s("дата на документа, дд.мм.гггг"),
        "notarius": _s("име на нотариуса"),
        "notarius_nomer": _s("регистрационен номер на нотариуса в Нотариалната камара"),
        "sluzhba": _s("служба по вписванията — град, входящ рег. №, акт/том/дело"),
        "lica": {
            "type": "array",
            "description": "всички лица в документа — страни и наследодател",
            "items": {"type": "object", "properties": {
                "ime": _s("пълното име или наименование на фирмата, дословно"),
                "vid": _s("физическо или юридическо", enum=["физическо", "юридическо"]),
                "egn_eik": _s("ЕГН или ЕИК, ако е посочен"),
                "pochinal": _s("дата на смъртта, ако документът я сочи (наследство)"),
            }},
        },
        "obekti": {
            "type": "array",
            "description": "обектите, за които става дума",
            "items": {"type": "object", "properties": {
                "identifikator": _s("идентификатор по КККР, дословно"),
                "opisanie": _s("описание — „апартамент 15“, „поземлен имот“, „магазин“"),
                "vid": _s("вид", enum=["земя", "сграда", "самостоятелен обект",
                                       "право на строеж", "друго"]),
                "plosht": _s("площ, както пише"),
            }},
        },
        "prehvarliania": {
            "type": "array",
            "description": "самите прехвърляния — сърцевината на документа",
            "items": {"type": "object", "properties": {
                "vid": _s("какво се случва", enum=SABITIA),
                "ot": _s("от кого — име, дословно; празно, ако правото възниква"),
                "na": _s("на кого — име, дословно"),
                "dyal": _s("дял като ДРОБ: 1/1, 1/2, 1/6"),
                "obekt": _s("за кой обект — идентификатор или описание"),
                "citat": _s("дословният откъс, от който го разчете"),
                "stranica": {"type": "integer"},
            }},
        },
    },
}


# ── проверки, които кодът прави сам ─────────────────────────────────────────

_PROCENT = re.compile(r"\d+\s*(%|процент)")


def _dyal(txt):
    """„1/6“ → Fraction; всичко друго → None. Проценти не се приемат."""
    t = (txt or "").strip().replace(" ", "")
    if not t or _PROCENT.search(t):
        return None
    if t in ("цялото", "цялата", "целия", "1"):
        return Fraction(1)
    m = re.match(r"^(\d+)/(\d+)$", t)
    if not m or int(m.group(2)) == 0:
        return None
    return Fraction(int(m.group(1)), int(m.group(2)))


def belezhki(dok):
    """Какво в прочетеното не връзва. Списък от изречения за оператора."""
    out = []
    for p in dok.get("prehvarliania") or []:
        if not p.get("na"):
            out.append(f"Прехвърляне без получател ({p.get('citat', '')[:60]}).")
        if not p.get("dyal"):
            out.append(f"Дялът не е прочетен за „{p.get('na', '')}“ — впиши го като дроб.")
        elif _dyal(p["dyal"]) is None:
            out.append(f"„{p['dyal']}“ не е дроб — дяловете се пишат 1/2, 1/6, не в проценти.")
        if p.get("vid") == "наследяване" and not p.get("ot"):
            out.append("Наследяване без наследодател.")
    imena = {(l.get("ime") or "").strip() for l in dok.get("lica") or []}
    for p in dok.get("prehvarliania") or []:
        for kak in ("ot", "na"):
            ime = (p.get(kak) or "").strip()
            if ime and ime not in imena:
                out.append(f"„{ime}“ участва в прехвърляне, но го няма сред лицата.")
    if not dok.get("nomer"):
        out.append("Номерът на акта не е прочетен — вписва се на ръка.")
    sbor = {}
    for p in dok.get("prehvarliania") or []:
        f = _dyal(p.get("dyal") or "")
        if f is None:
            continue
        k = (p.get("obekt") or "").strip()
        sbor[k] = sbor.get(k, Fraction(0)) + f
    for obekt, f in sbor.items():
        if f > 1:
            out.append(f"За „{obekt}“ прехвърленото прави {f} — повече от цялото.")
    return sorted(set(out))


def procheti(chetci, ime, media_type, data_b64, stranici=None):
    """Един документ за собственост → (прочетеното, info)."""
    from .chetci import NeMozheSega
    prep = podgotvi(ime, media_type, data_b64, stranici)
    tekst = UKAZANIE + f"\n\nФайл: {ime}"
    raw = prep.get("raw") or b""
    prichini = []
    for chetec in list(chetci):
        try:
            dok, i = chetec.chete(prep, SHEMA, tekst, ime=ime, raw=raw, edin_dokument=True)
            d = dok[0] if isinstance(dok, list) else dok
            if not d or not (d.get("prehvarliania") or d.get("obekti")):
                prichini.append((chetec.ime, "празен отговор"))
                continue
            d.update({
                "fajl": ime, "chetec": chetec.ime, "model": i.get("model"),
                "sken": prep.get("sken", False),
                "belezhki": belezhki(d),
                "zashto_rezerven": "; ".join(f"{k}: {v}" for k, v in prichini),
            })
            return d, {"chetec": chetec.ime,
                       **{k: i.get(k) for k in ("model", "tokens_in", "tokens_out")}}
        except NeMozheSega as e:
            prichini.append((chetec.ime, str(e)[:300]))
    raise NikoyNeMozhe(prichini or [("", "няма настроен четец")])

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
1. Дяловете ги давай ТОЧНО КАКТО ПИШЕ в документа: „1/2“, „1/6“, „8,38 %“,
   „цялото“. Не превръщай дроб в процент, нито процент в дроб, и не закръглявай.
2. Имената изписвай ДОСЛОВНО, с всички бащини имена.
3. Обектите — с идентификатора по КККР, ако е посочен; иначе описанието.
4. При удостоверение за наследници: прехвърлянето е от наследодателя към всеки
   наследник. Ако документът не казва дяловете, остави dyal празно — ще ги
   реши операторът.
5. НЕ СМЯТАЙ И НЕ ДЕЛИ. Пиши прехвърлянето ТОЧНО както е в акта:
   · ако актът дава дял на всяко лице поотделно — по един ред на човек;
   · ако няколко лица прехвърлят заедно на няколко лица — ЕДИН ред, с
     всички имена, разделени със запетая, и дяла, както е изписан („1/1“).
   Разпределянето между хората е сметка и я прави системата, не ти. Сгрешиш
   ли я, грешката изглежда като истински дял и никой не я вижда.
6. В obekti слагай само обектите, за които документът ПРЕХВЪРЛЯ нещо.
   Актът често изброява чужди обекти, за да ги изключи от сделката („с
   изключение на гаражни клетки №…“) — тези не ги пиши.
7. Ако нещо не пише в документа — остави го празно. Не предполагай.
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

def _dyal(txt):
    """„1/6“, „8,38 %“, „цялото“ → Fraction. Нечетимото → None.

    Процентите СЕ ПРИЕМАТ (13.10.2026): в нотариален акт за идеални части в
    голям комплекс законният текст наистина пише „8,38 %“, а не дроб. Пазят се
    като точна дроб (8,38% → 419/5000), за да не се трупа закръгление.
    """
    t = (txt or "").strip().replace(",", ".").replace(" ", "")
    if not t:
        return None
    if t in ("цялото", "цялата", "целия", "1", "1/1"):
        return Fraction(1)
    m = re.match(r"^(\d+)/(\d+)$", t)
    if m and int(m.group(2)):
        return Fraction(int(m.group(1)), int(m.group(2)))
    p = re.match(r"^(\d+(?:\.\d+)?)%$", t)
    if p:
        return Fraction(p.group(1)).limit_denominator(10 ** 9) / 100
    return None


_RAZDELITELI = re.compile(r"\s*(?:,|;| и )\s*")


def imena(v):
    u"""„Иван Петров, Мария Петрова“ → двете имена.

    Четецът понякога слага няколко лица в едно поле, макар указанието да иска
    по един ред на човек. Това не е повод за тревога — разделя се тук.
    """
    t = (v or "").strip()
    if not t:
        return []
    return [x.strip() for x in _RAZDELITELI.split(t) if len(x.strip()) > 2]


def belezhki(dok):
    """Какво в прочетеното не връзва. Списък от изречения за оператора."""
    out = []
    for p in dok.get("prehvarliania") or []:
        if not p.get("na"):
            out.append(f"Прехвърляне без получател ({p.get('citat', '')[:60]}).")
        if not p.get("dyal"):
            out.append(f"Дялът не е прочетен за „{p.get('na', '')}“ — впиши го като дроб.")
        elif _dyal(p["dyal"]) is None:
            out.append(f"Дялът „{p['dyal']}“ не се чете — пиши дроб (1/2) или процент (8,38 %).")
        if p.get("vid") == "наследяване" and not p.get("ot"):
            out.append("Наследяване без наследодател.")
    vsichki = set()
    for l in dok.get("lica") or []:
        vsichki.update(imena(l.get("ime")))
    for p in dok.get("prehvarliania") or []:
        for kak in ("ot", "na"):
            for ime in imena(p.get(kak)):
                if ime not in vsichki:
                    out.append(f"„{ime}“ участва в прехвърляне, но го няма сред лицата.")
    if not dok.get("nomer"):
        out.append("Номерът на акта не е прочетен — вписва се на ръка.")
    # Сметката е НЕТНА: един акт често описва верига — първо придобиване,
    # после продажба на същото. Събрани, двете правят 200 % и вдигат фалшива
    # тревога. (ЖИТЕН, 14.10.2026)
    salda = {}
    for p in dok.get("prehvarliania") or []:
        f = _dyal(p.get("dyal") or "")
        if f is None:
            continue
        k = (p.get("obekt") or "").strip()
        poluchateli = imena(p.get("na")) or [""]
        dava = imena(p.get("ot"))
        salda.setdefault(k, {})
        for n in poluchateli:
            salda[k][n] = salda[k].get(n, Fraction(0)) + f / len(poluchateli)
        for n in dava:
            salda[k][n] = salda[k].get(n, Fraction(0)) - f / len(dava)
    for obekt, lica in salda.items():
        drazhat = sum(v for v in lica.values() if v > 0)
        # Процентите в актовете са закръглени: 2,169 % x 46 не прави точно 100 %.
        if drazhat > Fraction(1001, 1000):
            out.append(f"За „{obekt}“ след всички прехвърляния се държат "
                       f"{float(drazhat) * 100:.2f} % — повече от цялото.")
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

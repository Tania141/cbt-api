"""Моментите: кой документ кога се събира и къде влиза.

ЗАЩО ГО ИМА
-----------
Чеклистът беше ЕДИН списък от 86 реда, проверяван два пъти — за ОСИП и за ОД.
Затова накрая операторът е пред купчина: нищо не е хващано по пътя. Нейните
думи (01.10.2026): „за всеки протокол имаме чек лист… така в процеса на работа
по документите ще получим пълния списък за акт 15 и за ОД“.

ОТКЪДЕ ИДВА ПОДРЕДБАТА
----------------------
Тя попълни „кой документ на кой протокол.docx“ с колоната **в кои документи
влиза** всеки ред. После сама даде правилото (09.10.2026):

    „ако РС влиза в Протокол 1, 2, ЗК, акт 14, 15, 16 и ОД, то следва, че се
     събира в първия възникнал протокол“

Тоест моментът не се пита — ИЗВЕЖДА СЕ. Две изключения, пак нейни:
  · документ, който САМ Е МОМЕНТ, се събира при себе си (акт 7 се съставя при
    акт 7; изброяването му в акт 14 е препис, не събиране);
  · ако протоколът НЕ СЕ СЪСТАВЯ за този строеж, искането пада на следващия
    („не пиша в практиката си протокол 1… но правилното е на пр. 1“).

ИЗТОЧНИКЪТ Е ФАЙЛ, НЕ КОД
-------------------------
`rules/izvori/моменти.md` се прави от нейната таблица със
`scratchpad/napravi_momenti.py`. Поправя се в НЕЙНИЯ файл и се пуска наново —
както при чеклиста и матрицата.
"""
import io
import os
import re

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)

# Първо папката на оператора, после копието в хранилището — то е единственото,
# което стига до Railway. Виж [[izvori-do-railway]].
_TARSI = [
    os.path.join(_DIR, "izvori"),
    os.path.join(os.path.dirname(_ROOT), "Закони инаредби"),
    _ROOT,
]

IME = "моменти.md"

# Редът на моментите във времето. Оттук идва и „следващият“ при правило 3.
RED = ["ОСИП", "РС", "Протокол 1", "Протокол 2", "Заповедна книга",
       "Констативен акт обр. 3", "Акт 5", "Акт 6", "Акт 7", "Акт 8", "Акт 9",
       "Акт 10", "Акт 11", "Акт 12", "Акт 13", "Акт 14", "Акт 15",
       "Протокол 17", "Акт 16", "ОД", "Технически паспорт"]
MYASTO = {m: i for i, m in enumerate(RED)}

# Фазите. РС е превключвателят — операторът, 02.10.2026: „то всъщност разделя
# обекта за ОСИП и за СМР“. Затова ОСИП не се показва в надзора и обратно.
FAZI = {
    "osip":   ["ОСИП"],
    "nadzor": [m for m in RED if m != "ОСИП"],
}

# Моменти, които не винаги се съставят. Празен списък значи „винаги“.
# Акт 5 и 6 са за 1–3 категория; Акт 16 — само при назначена ДПК; Протокол 17 —
# по поискване. Правило 3 ги прескача, като не се съставят.
PO_IZBOR = {"Протокол 1", "Акт 5", "Акт 6", "Акт 8", "Акт 9", "Акт 10",
            "Акт 11", "Акт 13", "Протокол 17", "Акт 16"}


class NyamaIztochnik(Exception):
    pass


def path():
    for d in _TARSI:
        p = os.path.join(d, IME)
        if os.path.exists(p):
            return p
    return None


def _chete():
    p = path()
    if not p:
        raise NyamaIztochnik(f"не намирам „{IME}“ — потърсен в: " + "; ".join(_TARSI))
    s = io.open(p, encoding="utf-8").read()
    moment, out = "", []
    for red in s.split("\n"):
        if red.startswith("## "):
            moment = red[3:].strip()
            continue
        if not red.startswith("|") or "|---" in red or "| Документ |" in red:
            continue
        k = [x.strip() for x in red.strip("|").split("|")]
        if len(k) < 3 or not k[0]:
            continue
        out.append({
            "dokument": k[0],
            "uslovie": k[1],
            "vliza_v": [x.strip() for x in k[2].split(",") if x.strip() and x.strip() != "—"],
            "moment": moment,
        })
    return out


_KESH = {"kade": None, "redove": None}


def redove():
    """Всички редове. Чете файла веднъж — той не се мени по време на работа."""
    p = path()
    if _KESH["kade"] != p or _KESH["redove"] is None:
        _KESH["kade"], _KESH["redove"] = p, _chete()
    return _KESH["redove"]


def sledvashtiyat(moment, sastavyani):
    """Правило 3: ако моментът не се съставя, искането пада на следващия."""
    if moment not in MYASTO:
        return moment
    for m in RED[MYASTO[moment]:]:
        if m in sastavyani or m not in PO_IZBOR:
            return m
    return moment


def po_momenti(sastavyani=None, prilozhimi=None, faza="nadzor"):
    """Документите, подредени по момент.

    `sastavyani` — моментите, които наистина се съставят за този строеж
    (празно = само задължителните). `prilozhimi` — имената на документите,
    които се изискват за него; празно = всички.
    """
    sast = set(sastavyani or ())
    izbor = set(prilozhimi) if prilozhimi is not None else None
    grupi = {}
    for r in redove():
        if izbor is not None and r["dokument"] not in izbor:
            continue
        m = sledvashtiyat(r["moment"], sast)
        grupi.setdefault(m, []).append({**r, "iskan_na": m})
    vidimi = FAZI.get(faza) or RED
    # Моментите по избор се показват ВИНАГИ, дори празни: иначе изключеният
    # Протокол 1 изчезва от екрана и операторът няма как да го върне.
    for m in PO_IZBOR:
        if m in vidimi:
            grupi.setdefault(m, [])
    return [{"moment": m, "dokumenti": grupi[m]} for m in vidimi if m in grupi]


def sastoyanie(dokument_imena, nalichni, tekusht=None):
    """Трите състояния на един документ спрямо текущия момент.

    Операторът, 01.10.2026: „няма нужда в началото да иска сертификат за
    асансьор — той се появява, след като бъде монтиран“.
      · „налично“      — вече е събрано;
      · „очаква се“    — моментът му е дошъл (или е минал), а го няма;
      · „не му е времето“ — моментът му е след текущия.
    """
    sega = MYASTO.get(tekusht, len(RED)) if tekusht else len(RED)
    out = []
    for r in redove():
        if dokument_imena is not None and r["dokument"] not in dokument_imena:
            continue
        kak = ("налично" if r["dokument"] in (nalichni or ())
               else "очаква се" if MYASTO.get(r["moment"], 0) <= sega
               else "не му е времето")
        out.append({**r, "sastoyanie": kak})
    return out

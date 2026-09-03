"""Градоустройствени показатели — две нива на проверка.

    проект  ≤  виза          постигнатото спазва ли зададеното
    виза    ∈  Наредба № 7   самата виза в нормата за зоната ли е

Двата входа са различни документи: визата ЗАДАВА, проектът ПОСТИГА. Затова
това не е преписване, а истинска проверка.

ОБРАТНИЯТ ЗНАК
--------------
Плътността, интензивността и котата корниз са МАКСИМУМИ — постигнатото не бива
да ги надвишава. Озеленяването е МИНИМУМ — постигнатото не бива да е под него.
Точно такива неща минават незабелязано при бърз преглед.
"""
import re
from .engine import rule, Verdict, OK, WARN, UNKNOWN
from . import naredba7 as n7

POKAZATELI = [
    # ключ        име                        посока  единица
    ("plytnost", "плътност на застрояване",  "max",  "%"),
    ("kint",     "интензивност (К инт.)",    "max",  ""),
    ("ozel",     "озеленена площ",           "min",  "%"),
]


def _chislo(v):
    """Приема „23,0%“, „0,35“, „272,00 м²“. Връща float или None."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(v))
    return float(m.group(0).replace(",", ".")) if m else None


def _pok(project, kade):
    """Показателите от визата или от проекта."""
    d = (project.get("gradoustroystvo") or {}).get(kade) or {}
    return {k: _chislo(d.get(k)) for k, *_ in POKAZATELI}


def _p(zona=None, viza=None, proekt=None, darvesna=None):
    g = {}
    if viza:
        g["viza"] = viza
    if proekt:
        g["proekt"] = proekt
    if zona:
        g["zona"] = zona
    if darvesna is not None:
        g["darvesna"] = darvesna
    return {"gradoustroystvo": g}


VIZA_GURMAZOVO = {"plytnost": "40,0", "kint": "1,0", "ozel": "50,0"}
PROEKT_GURMAZOVO = {"plytnost": "23,0", "kint": "0,35", "ozel": "50,0"}


@rule(
    code="G1",
    title="Постигнатото по проект спазва зададеното с визата",
    citation="чл. 140 ЗУТ — визата за проектиране определя устройствените показатели "
             "за имота; проектът се съобразява с тях.",
    what="Плътността, интензивността и котата корниз са МАКСИМУМИ — постигнатото не бива "
         "да ги надвишава. Озеленяването е МИНИМУМ — постигнатото не бива да е под него. "
         "Обратният знак на озеленяването е най-честият пропуск при бърз преглед.",
    cases=[
        ("ГУРМАЗОВО — в рамките",
         _p(viza=VIZA_GURMAZOVO, proekt=PROEKT_GURMAZOVO), OK),
        ("плътността надвишава визата",
         _p(viza=VIZA_GURMAZOVO, proekt=dict(PROEKT_GURMAZOVO, plytnost="45,0")), WARN),
        ("озеленяването е под минимума",
         _p(viza=VIZA_GURMAZOVO, proekt=dict(PROEKT_GURMAZOVO, ozel="42,0")), WARN),
        ("още няма показатели от проекта", _p(viza=VIZA_GURMAZOVO), UNKNOWN),
        ("още няма виза", _p(proekt=PROEKT_GURMAZOVO), UNKNOWN),
    ],
)
def proekt_sreshtu_viza(project):
    viza, proekt = _pok(project, "viza"), _pok(project, "proekt")
    if not any(v is not None for v in viza.values()):
        return Verdict(UNKNOWN, "Показателите от визата не са въведени.")
    if not any(v is not None for v in proekt.values()):
        return Verdict(UNKNOWN, "Постигнатите по проект показатели не са въведени.")

    problemi, proveri = [], []
    for k, ime, posoka, ed in POKAZATELI:
        z, p = viza.get(k), proekt.get(k)
        if z is None or p is None:
            continue
        proveri.append(ime)
        if posoka == "max" and p > z:
            problemi.append(f"{ime}: {p}{ed} по проект надвишава {z}{ed} по виза")
        elif posoka == "min" and p < z:
            problemi.append(f"{ime}: {p}{ed} по проект е под изискваните {z}{ed} по виза")
    if not proveri:
        return Verdict(UNKNOWN, "Няма показател, въведен и на двете места.")
    if problemi:
        return Verdict(WARN, "Отклонение от визата — " + "; ".join(problemi) + ".")
    return Verdict(OK, f"Проектът спазва визата по {len(proveri)} показателя: "
                       + ", ".join(proveri) + ".")


@rule(
    code="G2",
    title="Самата виза е в нормата за устройствената зона",
    citation="Наредба № 7 от 22.12.2003 г. за правила и нормативи за устройство на "
             "отделните видове територии и устройствени зони — чл. 19, ал. 1 (жилищни), "
             "чл. 20 (комплексно), чл. 24–26 (производствени), чл. 29 (вилни).",
    what="Второто ниво: визата задава показателите, но самата тя трябва да е в диапазона, "
         "който наредбата поставя за зоната. Таблицата с диапазоните е сверена срещу "
         "текста на наредбата и заключена — при изменение правилото млъква.",
    cases=[
        ("ГУРМАЗОВО — зона Жм, визата е в нормата",
         _p(zona="Жм", viza=VIZA_GURMAZOVO), OK),
        ("плътност 70% в Жм — над горната граница 60%",
         _p(zona="Жм", viza=dict(VIZA_GURMAZOVO, plytnost="70")), WARN),
        ("озеленяване 30% в Жм — под долната граница 40%",
         _p(zona="Жм", viza=dict(VIZA_GURMAZOVO, ozel="30")), WARN),
        ("производствена зона Пч", _p(zona="Пч", viza={"plytnost": "60", "kint": "1,5", "ozel": "30"}), OK),
        ("зоната не е посочена", _p(viza=VIZA_GURMAZOVO), UNKNOWN),
        ("непозната зона", _p(zona="Ху", viza=VIZA_GURMAZOVO), UNKNOWN),
    ],
)
def viza_sreshtu_naredba(project):
    g = project.get("gradoustroystvo") or {}
    zona = (g.get("zona") or "").strip()
    if not zona:
        return Verdict(UNKNOWN, "Устройствената зона не е посочена — без нея няма диапазон.")
    if zona not in n7.ZONI:
        return Verdict(UNKNOWN, f"Зона „{zona}“ не е в таблицата по Наредба № 7. "
                                f"Известни: {', '.join(n7.ZONI)}.")
    ok, prichina = n7.zakliuchena()
    if not ok:
        return Verdict(UNKNOWN, prichina)

    viza = _pok(project, "viza")
    if not any(v is not None for v in viza.values()):
        return Verdict(UNKNOWN, "Показателите от визата не са въведени.")

    z = n7.ZONI[zona]
    problemi, proveri = [], []
    for k, ime, posoka, ed in POKAZATELI:
        v = viza.get(k)
        if v is None:
            continue
        lo, hi = z[k]
        proveri.append(ime)
        if lo is not None and v < lo:
            problemi.append(f"{ime}: {v}{ed} при норма {n7.opis(z[k], ed)}")
        elif hi is not None and v > hi:
            problemi.append(f"{ime}: {v}{ed} при норма {n7.opis(z[k], ed)}")
    if not proveri:
        return Verdict(UNKNOWN, "Няма въведен показател от визата.")
    if problemi:
        return Verdict(WARN, f"Визата излиза извън нормата за зона {zona} "
                             f"({z['ime']}, {z['chl']}): " + "; ".join(problemi) +
                             ". Проверете зоната и показателите по визата.")
    return Verdict(OK, f"Визата е в нормата за зона {zona} ({z['ime']}, {z['chl']}) "
                       f"по {len(proveri)} показателя.")


@rule(
    code="G3",
    title="Част от озеленяването с дървесна растителност",
    citation="Наредба № 7: чл. 19, ал. 2 — една трета от необходимата озеленена площ трябва "
             "да бъде осигурена за озеленяване с дървесна растителност; същото при чл. 20, "
             "т. 3 и чл. 24–26. При вилните зони (чл. 29, ал. 1, т. 3) делът е ПОЛОВИНАТА.",
    what="Изискване, което докладите обикновено премълчават — доказва се само процентът "
         "озеленяване, а не и делът с дървесна растителност. Съотношението е една трета, "
         "но при вилна зона — една втора.",
    cases=[
        ("Жм — една трета е налице", _p(zona="Жм", proekt={"ozel": "50"}, darvesna="20"), OK),
        ("Жм — под една трета", _p(zona="Жм", proekt={"ozel": "50"}, darvesna="12"), WARN),
        ("вилна зона — иска се половината", _p(zona="Ов", proekt={"ozel": "50"}, darvesna="20"), WARN),
        ("не е попълнено", _p(zona="Жм", proekt={"ozel": "50"}), UNKNOWN),
    ],
)
def darvesna_rastitelnost(project):
    g = project.get("gradoustroystvo") or {}
    zona = (g.get("zona") or "").strip()
    if zona not in n7.ZONI:
        return Verdict(UNKNOWN, "Устройствената зона не е посочена.")
    ozel = _pok(project, "proekt").get("ozel")
    darv = _chislo(g.get("darvesna"))
    if ozel is None or darv is None:
        return Verdict(UNKNOWN, "Не са въведени озеленената площ по проект и делът "
                                "с дървесна растителност.")
    delitel = n7.ZONI[zona]["darv"]
    nuzhno = ozel / delitel
    kak = "една трета" if delitel == 3 else "половината"
    if darv + 1e-9 >= nuzhno:
        return Verdict(OK, f"Дървесната растителност е {darv}% при озеленяване {ozel}% — "
                           f"покрива {kak} ({nuzhno:.1f}%).")
    return Verdict(WARN, f"Дървесната растителност е {darv}% при озеленяване {ozel}% — "
                         f"иска се {kak}, тоест поне {nuzhno:.1f}%. "
                         f"Недостигат {nuzhno - darv:.1f} процентни пункта.")

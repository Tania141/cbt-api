"""Градоустройствени показатели — проектът срещу визата.

    постигнато по проект  спазва  зададеното с визата

Визата ЗАДАВА, проектът ПОСТИГА — два различни документа, затова това е
истинска проверка, а не преписване.

БЕЗ НАРЕДБА № 7 — РЕШЕНИЕ НА ОПЕРАТОРА (11.09.2026)
---------------------------------------------------
Имаше и второ ниво: самата виза в диапазона на Наредба № 7 за зоната. Махнато
е. Наредбата е „толкова разтеглива“ — числата зависят от големината на града,
за много зони се определят с плана — „нека си я четат главните архитекти,
които издават визата“. Надзорът проверява проекта срещу визата.

ПОСТИГНАТОТО СЕ СМЯТА, НЕ СЕ ПРЕПИСВА
-------------------------------------
Операторът въвежда стойностите от проекта — ЗП и РЗП в м², озеленяването в %,
котата корниз в м — и площта на имота. Системата смята плътността
(ЗП / площ) и интензивността (РЗП / площ). Стари обекти, въведени направо в
проценти, се четат както са — числа за реален обект не се измислят.

ОБРАТНИЯТ ЗНАК
--------------
Плътността, интензивността и котата корниз са МАКСИМУМИ; озеленяването е
МИНИМУМ. Точно такива неща минават незабелязано при бърз преглед.
"""
import re
from .engine import rule, Verdict, OK, WARN, UNKNOWN

POKAZATELI = [
    # ключ        име                        посока  единица
    ("plytnost", "плътност на застрояване",  "max",  "%"),
    ("kint",     "интензивност (К инт.)",    "max",  ""),
    ("ozel",     "озеленена площ",           "min",  "%"),
    ("kk",       "кота корниз (Н)",          "max",  " м"),
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
    """Показателите от визата или въведените направо в проценти от проекта."""
    d = (project.get("gradoustroystvo") or {}).get(kade) or {}
    return {k: _chislo(d.get(k)) for k, *_ in POKAZATELI}


def postignato(project):
    """Постигнатото по проект — (показатели, откъде).

    „изчислено“ — плътността и интензивността от ЗП и РЗП върху площта на
    имота; „въведено“ — стари обекти с проценти направо.
    """
    g = project.get("gradoustroystvo") or {}
    pr = g.get("proekt") or {}
    plosht = _chislo(g.get("plosht"))
    zp, rzp = _chislo(pr.get("zp")), _chislo(pr.get("rzp"))
    rez = _pok(project, "proekt")
    otkade = "въведено"
    if plosht and (zp is not None or rzp is not None):
        otkade = "изчислено"
        rez["plytnost"] = round(zp / plosht * 100, 1) if zp is not None else None
        rez["kint"] = round(rzp / plosht, 2) if rzp is not None else None
    return rez, otkade


def _p(viza=None, proekt=None, plosht=None):
    g = {}
    if viza:
        g["viza"] = viza
    if proekt:
        g["proekt"] = proekt
    if plosht is not None:
        g["plosht"] = plosht
    return {"gradoustroystvo": g}


from .realni import GURMAZOVO as R_GUR, izmeni

_G = R_GUR["gradoustroystvo"]
VIZA_GURMAZOVO, PROEKT_GURMAZOVO = _G["viza"], _G["proekt"]


def _gur(**promeni):
    """Гурмазово с променен показател — формата и имената остават истински."""
    return izmeni(R_GUR, gradoustroystvo={**_G, **promeni})


# Изчислителен пример — числата са като в примера на оператора (ЗП 1230 м²,
# РЗП 12 000 м², к.к. 10 м) върху имот от 5000 м². Не е реален обект и не се
# представя за такъв.
_VIZA_PRIMER = {"plytnost": "40", "kint": "2,5", "ozel": "20", "kk": "10"}
_PROEKT_PRIMER = {"zp": "1230", "rzp": "12000", "ozel": "20", "kk": "10"}


@rule(
    code="G1",
    title="Постигнатото по проект спазва зададеното с визата",
    citation="чл. 140 ЗУТ — визата за проектиране определя устройствените показатели "
             "за имота; проектът се съобразява с тях.",
    what="Плътността, интензивността и котата корниз са МАКСИМУМИ — постигнатото не бива "
         "да ги надвишава. Озеленяването е МИНИМУМ — постигнатото не бива да е под него. "
         "Плътността и интензивността се смятат от ЗП и РЗП върху площта на имота.",
    cases=[
        ("ГУРМАЗОВО — както е в доклада (проценти, въведени направо)", R_GUR, OK),
        ("същият обект с плътност 45% по проект",
         _gur(proekt=dict(PROEKT_GURMAZOVO, plytnost="45,0")), WARN),
        ("същият обект с озеленяване 42% — под изискваните 50%",
         _gur(proekt=dict(PROEKT_GURMAZOVO, ozel="42,0")), WARN),
        ("изчислителен пример: ЗП 1230, РЗП 12 000 върху 5000 м² — 24,6% и Кинт 2,40",
         _p(viza=_VIZA_PRIMER, proekt=_PROEKT_PRIMER, plosht="5000"), OK),
        ("изчислителен пример с РЗП 13 000 — Кинт 2,60 над 2,5 по виза",
         _p(viza=_VIZA_PRIMER, proekt=dict(_PROEKT_PRIMER, rzp="13000"), plosht="5000"), WARN),
        ("изчислителен пример с к.к. 10,5 м при 10 м по виза",
         _p(viza=_VIZA_PRIMER, proekt=dict(_PROEKT_PRIMER, kk="10,5"), plosht="5000"), WARN),
        ("ЗП и РЗП без площта на имота — не може да се сметне",
         _p(viza=_VIZA_PRIMER, proekt={"zp": "1230", "rzp": "12000"}), UNKNOWN),
        ("още няма показатели от проекта", _p(viza=VIZA_GURMAZOVO), UNKNOWN),
        ("още няма виза", _p(proekt=PROEKT_GURMAZOVO), UNKNOWN),
    ],
)
def proekt_sreshtu_viza(project):
    viza = _pok(project, "viza")
    if not any(v is not None for v in viza.values()):
        return Verdict(UNKNOWN, "Показателите от визата не са въведени.")

    g = project.get("gradoustroystvo") or {}
    sur = g.get("proekt") or {}
    pr, otkade = postignato(project)
    ima_stoynosti = _chislo(sur.get("zp")) is not None or _chislo(sur.get("rzp")) is not None
    if ima_stoynosti and not _chislo(g.get("plosht")) and pr["plytnost"] is None and pr["kint"] is None:
        return Verdict(UNKNOWN, "Въведени са ЗП/РЗП, но липсва площта на имота — "
                                "плътността и интензивността не могат да се сметнат.")
    if not any(v is not None for v in pr.values()):
        return Verdict(UNKNOWN, "Постигнатите по проект показатели не са въведени.")

    problemi, proveri = [], []
    for k, ime, posoka, ed in POKAZATELI:
        z, p = viza.get(k), pr.get(k)
        if z is None or p is None:
            continue
        proveri.append(ime)
        if posoka == "max" and p > z + 1e-9:
            problemi.append(f"{ime}: {p}{ed} по проект надвишава {z}{ed} по виза")
        elif posoka == "min" and p < z - 1e-9:
            problemi.append(f"{ime}: {p}{ed} по проект е под изискваните {z}{ed} по виза")
    if not proveri:
        return Verdict(UNKNOWN, "Няма показател, въведен и на двете места.")
    if problemi:
        return Verdict(WARN, "Отклонение от визата — " + "; ".join(problemi) + f" ({otkade}).")
    return Verdict(OK, f"Проектът спазва визата по {len(proveri)} показателя "
                       f"({otkade}): " + ", ".join(proveri) + ".")

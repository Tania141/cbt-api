# -*- coding: utf-8 -*-
u"""Удостоверението на строителя от ЦПРС трябва да покрива категорията.

Операторът, 01.10.2026: при Протокол 2 проверява „валиден лиценз от КСБ ЗА
КАТЕГОРИЯТА НА ОБЕКТА“. На 21.10.2026: „да, ако може“ — да го прави системата.

Регистърът на Камарата на строителите НЕ се сваля като файл (за разлика от
ДНСК, КИИП и техническия контрол — виж `registri/`). Затова тук не се проверява
дали вписването съществува, а дали **вписаното от оператора** покрива строежа:
групата, категорията и срокът. Какво точно пише в удостоверението е факт от
документа; дали стига за този строеж е сметка — и тя е работа на кода.

Пет групи по Правилника за реда за вписване и водене на ЦПРС:
  I   — високо строителство, прилежаща инфраструктура, електронни съобщителни
        мрежи и съоръжения (сгради)
  II  — транспортна инфраструктура
  III — енергийна инфраструктура
  IV  — благоустройствена инфраструктура, хидротехническо строителство и
        опазване на околната среда
  V   — отделни видове СМР (без категория)

Надзорът се проверява другаде — той е в регистъра на ДНСК (`registri/dnsk.json`).
"""
import re

GRUPI = ("I", "II", "III", "IV", "V")

# Римско и арабско — операторът пише и двете.
_RIMSKO = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V",
           "I": "I", "II": "II", "III": "III", "IV": "IV", "V": "V"}

_KATEGORIA = re.compile(r"(?<![0-9])([1-5])(?![0-9])")


def _cifri(tekst):
    u"""Категориите, изброени в текст: „първа и втора“, „1, 2, 3“, „I-ва“."""
    t = (tekst or "").lower()
    namereni = {int(x) for x in _KATEGORIA.findall(t)}
    for duma, n in (("първа", 1), ("втора", 2), ("трета", 3),
                    ("четвърта", 4), ("пета", 5)):
        if duma in t:
            namereni.add(n)
    return namereni


def _grupi(tekst):
    t = (tekst or "").upper()
    out = []
    for m in re.finditer(r"(?<![A-ZА-Я0-9])(IV|III|II|I|V|[1-5])(?![A-ZА-Я0-9])", t):
        g = _RIMSKO.get(m.group(1))
        if g and g not in out:
            out.append(g)
    return out


def proveri(kategoria_stroezh, udostoverenie, vid=None, dnes=None):
    u"""Покрива ли удостоверението този строеж.

    `kategoria_stroezh` — цифрата от разрешението за строеж (1–5).
    `udostoverenie` — {"nomer", "valid_do" (дд.мм.гггг), "grupi", "kategorii"}.
    `vid` — „сграда“ или „линеен“: от него се подсказва коя група се очаква.

    Връща {"sastoyanie", "tekst"}; състоянията са:
      nyama        — няма вписано удостоверение
      nepalno      — има номер, но не и групи/категории
      izteklo      — срокът е минал
      ne_pokriva   — категорията на строежа не е сред вписаните
      drugа_grupa  — категорията е наред, но групата не отговаря на вида
      pokriva      — всичко е наред
    """
    from datetime import date, datetime

    u = udostoverenie or {}
    nomer = str(u.get("nomer") or "").strip()
    if not nomer:
        return {"sastoyanie": "nyama",
                "tekst": "Няма вписано удостоверение от ЦПРС за строителя — "
                         "лицензът трябва да покрива категорията на строежа."}

    kat = _cifri(u.get("kategorii"))
    grupi = _grupi(u.get("grupi"))
    if not kat and not grupi:
        return {"sastoyanie": "nepalno",
                "tekst": f"Удостоверение № {nomer} е вписано без групи и категории — "
                         "те се четат от самото удостоверение."}

    do = str(u.get("valid_do") or "").strip()
    if do:
        m = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", do)
        if m:
            kraj = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            sega = dnes or date.today()
            if kraj < sega:
                return {"sastoyanie": "izteklo",
                        "tekst": f"Удостоверение № {nomer} е с изтекъл срок — "
                                 f"{do}."}

    try:
        k = int(str(kategoria_stroezh).strip()[:1])
    except (ValueError, IndexError, TypeError):
        return {"sastoyanie": "nepalno",
                "tekst": "Категорията на строежа не е известна — "
                         "тя се чете от разрешението за строеж."}

    # Пета група са отделни видове СМР, без категория — тя не покрива строеж.
    samo_peta = grupi == ["V"]
    if k not in kat or samo_peta:
        imash = ", ".join(str(x) for x in sorted(kat)) or "няма"
        return {"sastoyanie": "ne_pokriva",
                "tekst": f"Строежът е {k} категория, а удостоверение № {nomer} "
                         f"покрива категории: {imash}"
                         + (" (пета група — отделни видове СМР)" if samo_peta else "")}

    ochakvana = {"сграда": "I", "линеен": None}.get((vid or "").strip().lower())
    if ochakvana and grupi and ochakvana not in grupi:
        return {"sastoyanie": "druga_grupa",
                "tekst": f"Удостоверение № {nomer} е за група "
                         f"{', '.join(grupi)}, а строежът е сграда (група I)."}

    return {"sastoyanie": "pokriva",
            "tekst": f"Удостоверение № {nomer} покрива {k} категория"
                     + (f", група {', '.join(grupi)}" if grupi else "")
                     + (f" (валидно до {do})" if do else "")}

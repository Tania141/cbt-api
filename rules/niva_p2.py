# -*- coding: utf-8 -*-
"""Заверките на контролните нива — раздел III на Протокол обр. 2.

Операторът, 09.11.2026: нивата да се четат от сканираните проверки (ниво,
кота, дата, какво е разрешено) и да попълват датите, които после влизат в 1.2
на Акт 15. Датите в проверките са НА РЪКА — затова всичко се сверява.
"""
from .sloy2 import podgotvi, NikoyNeMozhe

NIVA = ["изкоп", "цокъл", "корниз", "било"]

UKAZANIE = """Прочети проверките при достигане на контролираните проектни нива
(раздел III на Протокол обр. 2).

Всяка проверка започва с „Проверка при ниво …, кота …“ и има дата „Днес, …“.

За всяка проверка пиши:
- „nivo“ — едно от: изкоп, цокъл, корниз, било;
- „kota“ — котата, както пише („-3,99 м“, „К+24.09 м“);
- „data“ — датата от „Днес, …“, дд.мм.гггг. Тя често е НА РЪКА — пиши я,
  както я виждаш, а ако не се чете — празно;
- „razreshava“ — какво е разрешено след проверката, дословно, кратко;
  празно, ако е само с точки;
- „stranica“ — страницата.

Не пиши ЕГН. Не предполагай — непрочетеното остава празно.
"""

def _s(o):
    return {"type": "string", "description": o}

SHEMA = {
    "type": "object",
    "properties": {
        "proverki": {"type": "array", "items": {"type": "object", "properties": {
            "nivo": {"type": "string", "enum": NIVA},
            "kota": _s("котата, дословно"),
            "data": _s("датата на проверката, дд.мм.гггг"),
            "razreshava": _s("какво е разрешено, дословно"),
            "stranica": {"type": "integer"},
        }}},
    },
}


def procheti(chetci, ime, media_type, data_b64, stranici=None):
    """Сканираните проверки → ({proverki}, info)."""
    from .chetci import NeMozheSega
    prep = podgotvi(ime, media_type, data_b64, stranici)
    tekst = UKAZANIE + f"\n\nФайл: {ime}"
    raw = prep.get("raw") or b""
    prichini = []
    for chetec in list(chetci):
        try:
            dok, i = chetec.chete(prep, SHEMA, tekst, ime=ime, raw=raw, edin_dokument=True)
            d = dok[0] if isinstance(dok, list) else dok
            prov = [p for p in (d or {}).get("proverki") or [] if (p or {}).get("nivo") in NIVA]
            if not prov:
                prichini.append((chetec.ime, "няма прочетени проверки"))
                continue
            return {"proverki": prov, "fajl": ime, "chetec": chetec.ime}, \
                   {"chetec": chetec.ime, **{k: i.get(k) for k in ("model", "tokens_in", "tokens_out")}}
        except NeMozheSega as e:
            prichini.append((chetec.ime, str(e)[:300]))
    raise NikoyNeMozhe(prichini or [("", "няма настроен четец")])

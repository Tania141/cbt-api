# -*- coding: utf-8 -*-
"""Блоковете „по проект“ → „изпълнено“ (Акт 15, ОД, Акт 16, ТП).

Операторът, 14.10 и 11.11.2026:
- описанието в Акт 15, ОД, Акт 16 и ТП е **какво е направено**, в сегашно
  време — към подписването на Акт 15;
- основният източник е записката по съответната част;
- описват се всички части, една по една;
- АИ-то само ПРЕДЛАГА — операторът поправя в самото поле и потвърждава.

Не е нов текст: същото описание, с обърнато време и без проектантските
указания. Числата, материалите и имената остават дословни — поправката на
факти е работа на оператора, не на модела.
"""
from .sloy2 import NikoyNeMozhe

UKAZANIE = """Преработваш описание от обяснителна записка на инвестиционен проект
в описание на ИЗПЪЛНЕНИЯ строеж — за акт обр. 15 и окончателния доклад на
строителния надзор. Строежът е завършен.

За всеки блок:
- Обърни времето: „предвижда се“, „ще бъде изпълнено“, „проектирани са“,
  „се изпълнява“ → „е изпълнено“, „са изпълнени“, „е изградена“.
- Махни указанията на проектанта към строителя и към бъдещи фази: „следва да“,
  „трябва да“, „точният тип ще бъде указан във фаза Работна“, изисквания за
  сертификати, препратки към чертежи и таблици („съгласно чертежите“,
  „дадени в таблиците“). Не са описание на построеното.
- Числата, размерите, котите, материалите, марките и имената — ДОСЛОВНО.
- НЕ добавяй нищо, което не пише. НЕ обобщавай. Запази изброяванията.
- Ако блокът е изцяло указание или служебен текст — „tekst“ празно.
- В „mahnato“ изреди кратко какво си махнал (по една фраза).
Пиши на чист български, без руски калки."""


def _s(o):
    return {"type": "string", "description": o}


SHEMA = {
    "type": "object",
    "properties": {"dokumenti": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "klyuch": _s("ключът на блока, както е даден"),
            "tekst": _s("описанието на изпълненото"),
            "mahnato": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["klyuch", "tekst"],
    }}},
    "required": ["dokumenti"],
}


def vhod(chast, blokove):
    """Текстът към модела — блоковете с ключовете им."""
    redove = [f"Част: {chast}", ""]
    for b in blokove:
        redove += [f"=== Блок {b.get('klyuch')} — {b.get('podzaglavie') or ''} ===",
                   str(b.get("tekst") or "").strip(), ""]
    return "\n".join(redove)


def razberi(dok, klyuchove):
    """Отговорът → {ключ: {tekst, mahnato}}; непознат ключ отпада."""
    spisak = (dok or {}).get("dokumenti") if isinstance(dok, dict) else dok
    out = {}
    for x in spisak or []:
        if not isinstance(x, dict):
            continue
        k = str(x.get("klyuch") or "").strip()
        if k in klyuchove:
            m = x.get("mahnato") or []
            out[k] = {"tekst": str(x.get("tekst") or "").strip(),
                      "mahnato": [str(y) for y in m] if isinstance(m, list) else [str(m)]}
    return out


def predlozhi(chetci, chast, blokove):
    """→ ({ключ: {tekst, mahnato}}, info). Липсващ блок в отговора — казва се."""
    from .chetci import NeMozheSega
    tekst = vhod(chast, blokove)
    prep = {"blokove": [{"type": "text", "text": tekst}], "docx_tekst": tekst,
            "stranici": [tekst], "sken": False}
    klyuchove = {str(b.get("klyuch")) for b in blokove}
    prichini = []
    for chetec in list(chetci):
        try:
            dok, i = chetec.chete(prep, SHEMA, UKAZANIE, ime="izpalnenie.txt", raw=b"",
                                  edin_dokument=True)
            out = razberi(dok, klyuchove)
            if not out:
                prichini.append((chetec.ime, "не върна нито един блок"))
                continue
            return out, {"chetec": chetec.ime, "lipsvat": sorted(klyuchove - set(out)),
                         **{k: i.get(k) for k in ("model", "tokens_in", "tokens_out")}}
        except NeMozheSega as e:
            prichini.append((chetec.ime, str(e)[:300]))
    raise NikoyNeMozhe(prichini or [("", "няма настроен четец")])

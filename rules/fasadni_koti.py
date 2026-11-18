# -*- coding: utf-8 -*-
"""Котите от фасада или разрез → избор за Протокол 2 (18.11.2026).

Операторът (Митко Ситекс): „Не чете коти от проект“. Котите на Протокол 2 се
пишеха на ръка; беше в списъка от 10.11 като „котите от разрезите като избор“.

- Лист с текстов слой (PDF от CAD) — котите се вадят С КОД, без АИ.
- Скан или снимка — с АИ; всичко се сверява.

Системата само ПРЕДЛАГА: изрежда котите от листа (относителна, абсолютна,
надписът до нея) и дава ПОДСКАЗКА коя може да е цокъл, корниз, било. Коя
наистина е коя, посочва операторът — системата не налучква. Котата на изкопа
обикновено не е на фасадата, а в конструкцията.
"""
import re

from .sloy2 import podgotvi, NikoyNeMozhe

UKAZANIE = """Това е лист от архитектурен проект — фасада или разрез.
Прочети ВСИЧКИ коти, отбелязани на листа (с триъгълника на котата), отгоре
надолу. За всяка:
- „kota“ — относителната кота, ДОСЛОВНО, със знака: „+5,73“, „±0,00“, „-0,47“;
- „absolyutna“ — абсолютната кота след „=“, ако е написана: „540,33“; иначе празно;
- „nadpis“ — текстът до котата, ако има („Ср. кота прил. терен“, „било“,
  „корниз“, „стреха“); иначе празно;
- „list“ — името на изгледа, под който стои котата („Фасада югозапад“), ако се вижда.
Една и съща кота, повторена в двата края на изгледа, се пише веднъж за изгледа.
Не предполагай — нечетливото не се пише. Не пиши лични данни."""


def _s(o):
    return {"type": "string", "description": o}


SHEMA = {
    "type": "object",
    "properties": {
        "koti": {"type": "array", "items": {"type": "object", "properties": {
            "kota": _s("относителната кота, дословно, със знака"),
            "absolyutna": _s("абсолютната кота след „=“, или празно"),
            "nadpis": _s("текстът до котата, или празно"),
            "list": _s("изгледът — фасада/разрез, или празно"),
        }, "required": ["kota"]}},
    },
    "required": ["koti"],
}

# „+5,73=540,33“, „±0,00 = 534,60“, „-0,47“. Число с две цифри след запетаята —
# така се пишат котите в метри; „К-312“ и номера не минават.
_KOTA = re.compile(r"(?<![\d,.])([±+\-–−])?\s?(\d{1,3}[.,]\d{2})(?![\d])(?:\s*=\s*(\d{3,4}[.,]\d{2}))?")


def _chislo(k):
    """„+5,73“ → 5.73; „±0,00“ → 0.0; не се чете → None."""
    m = re.match(r"\s*([±+\-–−])?\s?(\d+)[.,](\d+)", str(k or ""))
    if not m:
        return None
    v = float(f"{m.group(2)}.{m.group(3)}")
    return -v if m.group(1) in ("-", "–", "−") else v


def _norm_kota(znak, chislo):
    chislo = chislo.replace(".", ",")
    if re.fullmatch(r"0+,0+", chislo):
        return "±0,00"
    znak = {"–": "-", "−": "-"}.get(znak or "", znak or "")
    return (znak if znak in ("+", "-", "±") else "+") + chislo


def absolyutni_ot_teksta(stranici):
    """Абсолютните коти, стоящи САМИ („+567.34“ на разреза на Радулов) — над 100 м.
    Не се връзват с относителна: на листа не стоят до нея."""
    out = []
    for tekst in stranici or []:
        for m in re.finditer(r"(?<![\d,.=])[+]?\s?(\d{3,4}[.,]\d{2})(?![\d])", str(tekst or "")):
            v = m.group(1).replace(".", ",")
            if v not in out:
                out.append(v)
    return out


def ot_teksta(stranici):
    """Котите от текстов слой — с код. → [{kota, absolyutna, nadpis, list, pati}]"""
    vidyani = {}
    for tekst in stranici or []:
        for m in _KOTA.finditer(str(tekst or "")):
            znak, chislo, absl = m.group(1), m.group(2), m.group(3) or ""
            # гола кота без знак и без абсолютна е често размер, не кота
            if not znak and not absl:
                continue
            # над 100 м е абсолютна кота, не относителна (Радулов: „+567.34“)
            if int(re.split(r"[.,]", chislo)[0]) >= 100:
                continue
            k = _norm_kota(znak, chislo)
            star = vidyani.get(k)
            if star:
                star["pati"] += 1
                star["absolyutna"] = star["absolyutna"] or absl.replace(".", ",")
            else:
                vidyani[k] = {"kota": k, "absolyutna": absl.replace(".", ","), "nadpis": "", "list": "", "pati": 1}
    return list(vidyani.values())


def _slei(koti):
    """Една кота — един ред (повторена по изгледи → броят), подредени отгоре надолу."""
    out = {}
    for x in koti or []:
        k = str((x or {}).get("kota") or "").strip()
        if _chislo(k) is None:
            continue
        m = re.match(r"\s*([±+\-–−])?\s?(\d+[.,]\d+)", k)
        k = _norm_kota(m.group(1), m.group(2)) if m else k
        st = out.get(k)
        absl = str(x.get("absolyutna") or "").strip().replace(".", ",")
        if st:
            st["pati"] += int(x.get("pati") or 1)
            st["absolyutna"] = st["absolyutna"] or absl
            st["nadpis"] = st["nadpis"] or str(x.get("nadpis") or "").strip()
        else:
            out[k] = {"kota": k, "absolyutna": absl, "nadpis": str(x.get("nadpis") or "").strip(),
                      "list": str(x.get("list") or "").strip(), "pati": int(x.get("pati") or 1)}
    return sorted(out.values(), key=lambda r: -(_chislo(r["kota"]) or 0))


def podskazki(koti):
    """ПОДСКАЗКА, не решение: ±0,00 → цокъл; най-високата → било; следващата с
    абсолютна кота → корниз. Надпис „било“/„корниз“/„стреха“ бие сметката."""
    p = {}
    for r in koti:
        n = r.get("nadpis", "").lower()
        if "било" in n:
            p.setdefault("bilo", r["kota"])
        elif "корниз" in n or "стреха" in n:
            p.setdefault("korniz", r["kota"])
    if any(r["kota"] == "±0,00" for r in koti):
        p.setdefault("cokul", "±0,00")
    nad = [r for r in koti if (_chislo(r["kota"]) or 0) > 0]
    s_abs = [r for r in nad if r["absolyutna"]] or nad
    if s_abs:
        p.setdefault("bilo", s_abs[0]["kota"])
        ostanali = [r for r in s_abs if r["kota"] != p["bilo"]]
        if ostanali:
            p.setdefault("korniz", ostanali[0]["kota"])
    return p


def procheti(chetci, ime, media_type, data_b64, stranici=None):
    """Фасада/разрез → ({koti, podskazki, chetec, fajl}, info)."""
    prep = podgotvi(ime, media_type, data_b64, stranici)
    if not prep.get("sken") and (prep.get("stranici") or []):
        koti = _slei(ot_teksta(prep["stranici"]))
        if koti:
            return ({"koti": koti, "podskazki": podskazki(koti), "fajl": ime,
                     "absolyutni": absolyutni_ot_teksta(prep["stranici"]),
                     "chetec": "кодът — от текста на листа"}, {"chetec": "код"})
    from .chetci import NeMozheSega
    raw = prep.get("raw") or b""
    prichini = []
    for chetec in list(chetci):
        try:
            dok, i = chetec.chete(prep, SHEMA, UKAZANIE + f"\n\nФайл: {ime}", ime=ime, raw=raw,
                                  edin_dokument=True)
            d = (dok[0] if isinstance(dok, list) else dok) or {}
            koti = _slei(d.get("koti") or [])
            if not koti:
                prichini.append((chetec.ime, "няма прочетени коти"))
                continue
            return ({"koti": koti, "podskazki": podskazki(koti), "fajl": ime, "chetec": chetec.ime},
                    {"chetec": chetec.ime, **{k: i.get(k) for k in ("model", "tokens_in", "tokens_out")}})
        except NeMozheSega as e:
            prichini.append((chetec.ime, str(e)[:300]))
    raise NikoyNeMozhe(prichini or [("", "няма настроен четец")])

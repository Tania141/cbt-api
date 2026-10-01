"""Обяснителните записки по частите на проекта — източникът на чеклиста.

ЗАЩО Е ОТДЕЛЕН МОДУЛ
--------------------
Операторът, 01.10.2026: „това, което правим, е отзад напред! всеки строеж си има
проекти по всички части, в тях са описани какви материали трябва да бъдат
вложени… от всяка записка може да се извлече чек лист за конкретен обект“.

Дотук чеклистът беше общ списък отвън и питаше оператора за всичко, което не
може да знае („ако_е_приложимо“ при 26 от 86 реда). Записката знае. Пробата с
ДЖИХАТ (ВиК и ОВК, 01.10.2026) извади без нито един въпрос: няма топлоснабдяване,
няма газ, няма подземен гараж, четири етажа, има ОВК — и материалите поименно.

Затова: четем записките, кодът предлага, операторът потвърждава. Общият чеклист
НЕ отпада — сменя си ролята: от проекта идва списъкът за ТОЗИ обект, от нормата
идва контролата „по норма се иска, а в проекта го няма“. Това е работата на
надзора и системата може да я върши по същия начин.

ОТДЕЛЕН ОТ `sloy2.py` НАРОЧНО: друга схема, друга цел. Четенето за ОД работи и
не се пипа (искане на оператора). Общото е само `podgotvi` и четците.
"""
import json
import re

from .sloy2 import podgotvi, NeSeChete, NikoyNeMozhe, MAX_STRANICI, _norm_tekst


# ── Части на проекта ─────────────────────────────────────────────────────────
# По изброяването на оператора (01.10.2026). За жилищна сграда са единайсет,
# за електро с КТП — осем, като част от имената се повтарят.
CHASTI = {
    "ARH":      "Архитектура",
    "KONSTR":   "Конструкции",
    "EL":       "Електро",
    "VIK":      "ВиК",
    "OVK":      "ОВК (отопление, вентилация, климатизация)",
    "EE":       "Енергийна ефективност",
    "PB":       "Пожарна безопасност",
    "GEO":      "Геодезия",
    "OZELEN":   "Озеленяване / паркоустройство",
    "PBZ":      "ПБЗ (план за безопасност и здраве)",
    "TRANSP":   "Транспортен достъп / пътна",
    "DRUGA":    "друга част",
}

# Признаците, които записката може да отговори вместо оператора. Контролиран
# списък — иначе всеки четец ги нарича различно и кодът не може да ги свърже.
PRIZNACI = {
    "etaji":            "колко етажа има строежът и кои (приземен, подземен, надземни) — с думите на записката",
    "podzemen_etaj":    "има ли сутерен или подземен етаж",
    "garaj":            "има ли гараж — подземен или надземен, и паркоместа",
    "otoplenie":        "как се отоплява — топлофикация, газ, електричество, климатизатори, котел",
    "toplosnabdyavane": "присъединява ли се към топлопреносно дружество",
    "gaz":              "има ли газова инсталация или газоснабдяване",
    "ovk":              "има ли ОВК инсталация и каква",
    "ventilaciya":      "каква вентилация има и къде (помещения, гараж)",
    "asansior":         "има ли асансьор или подемна платформа",
    "drenaj":           "има ли дренажна, помпена или отводнителна система",
    "pozharogasene":    "има ли сградна инсталация за пожарогасене, пожарни кранове, сухотръбие, спринклери",
    "pozharoizvestyavane": "има ли пожароизвестяване, сигнализация или автоматика",
    "el_saobshteniya":  "има ли слаботокови инсталации или електронни съобщения",
    "vik":              "как се присъединява към водоснабдяване и канализация",
    "elektro":          "как се присъединява към електроснабдяване",
    "visochina":        "каква е височината на сградата (важи за пожарните изисквания — до 28 м и над)",
}


# Кратко име за показване — описанието е за четеца, не за екрана.
PRIZNACI_IME = {
    "etaji": "Етажи", "podzemen_etaj": "Сутерен / подземен етаж", "garaj": "Гараж",
    "otoplenie": "Отопление", "toplosnabdyavane": "Топлоснабдяване", "gaz": "Газ",
    "ovk": "ОВК", "ventilaciya": "Вентилация", "asansior": "Асансьор",
    "drenaj": "Дренаж и помпи", "pozharogasene": "Пожарогасене",
    "pozharoizvestyavane": "Пожароизвестяване", "el_saobshteniya": "Електронни съобщения",
    "vik": "ВиК присъединяване", "elektro": "Електро присъединяване", "visochina": "Височина",
}


def _spisak(rechnik):
    return "\n".join(f"- {k} — {v}" for k, v in rechnik.items())


# ── Какво връща четецът ──────────────────────────────────────────────────────

def _s(opisanie, **ostanalo):
    return {"type": "string", "description": opisanie, **ostanalo}


SHEMA = {
    "name": "zapishi_zapiska",
    "description": "Записва прочетеното от обяснителната записка по една част на проекта.",
    "input_schema": {
        "type": "object",
        "properties": {
            "chast_kod": _s("коя част на проекта е записката", enum=list(CHASTI)),
            "chast_ime": _s("как е наречена частта в самата записка, дословно"),
            "obekt":     _s("наименованието на строежа, дословно"),
            "upi":       _s("УПИ / поземлен имот, дословно"),
            "faza":      _s("фаза на проекта — идеен, технически, работен"),
            "investitor": _s("инвеститор, дословно"),
            "vazlozhiteli": {"type": "array", "items": {"type": "string"},
                             "description": "възложителите, по един на ред, дословно"},
            "proektant": _s("проектантът на тази част — име и титла"),
            "proektant_registraciya": _s("номер на проектантска правоспособност, диплома, регистър — ако е посочен"),
            "chelen_list": {
                "type": "array",
                "description": "ако записката има челен лист с проектантите по ВСИЧКИ части — по един ред за част",
                "items": {"type": "object", "properties": {
                    "chast": _s("името на частта, както е изписано"),
                    "proektant": _s("името на проектанта"),
                }},
            },
            "opisanie": _s("как записката описва строежа — етажи, помещения, предназначение; дословно изречение"),
            "priznaci": {
                "type": "array",
                "description": "Отговори САМО на онези признаци, за които записката наистина казва нещо. "
                               "Не предполагай. Ако частта не говори за признака — пропусни го.",
                "items": {"type": "object", "properties": {
                    "priznak":  _s("кой признак", enum=list(PRIZNACI)),
                    "stoynost": _s("отговорът, кратко: „няма“, „4 (приземен + 3)“, „сплит климатизатори“"),
                    "citat":    _s("дословният откъс, от който го разчете"),
                    "stranica": {"type": "integer", "description": "страница в този файл"},
                }},
            },
            "materiali": {
                "type": "array",
                "description": "Материали и изделия, които ще се влагат — те после искат декларации за съответствие.",
                "items": {"type": "object", "properties": {
                    "material": _s("какво — „PVC тръби“, „полипропиленови тръби“, „медни тръби“"),
                    "opisanie": _s("марка, диаметър, клас, производител — каквото пише"),
                    "kade":     _s("къде се влага"),
                    "citat":    _s("дословният откъс"),
                    "stranica": {"type": "integer"},
                }},
            },
            "instalacii": {
                "type": "array",
                "description": "Инсталации и системи, които се изграждат по тази част.",
                "items": {"type": "object", "properties": {
                    "ime":      _s("как се нарича"),
                    "opisanie": _s("какво представлява, накратко"),
                    "citat":    _s("дословният откъс"),
                    "stranica": {"type": "integer"},
                }},
            },
            "chisla": {
                "type": "array",
                "description": "Числа, които после се сверяват с други документи: коти, площи, височини, "
                               "брой жители, диаметри на главните проводи.",
                "items": {"type": "object", "properties": {
                    "kakvo":    _s("какво е числото — „кота корниз“, „зелени площи“, „брой жители“"),
                    "stoynost": _s("стойността, както е написана"),
                    "merna":    _s("мерна единица"),
                    "citat":    _s("дословният откъс"),
                    "stranica": {"type": "integer"},
                }},
            },
            "drug_proekt": {
                "type": "array",
                "description": "Всичко, за което записката казва, че е ПО ДРУГ ПРОЕКТ, по друга част или от "
                               "друг строеж. Това сочи останалите строежи на площадката.",
                "items": {"type": "object", "properties": {
                    "kakvo":    _s("какво е по друг проект"),
                    "citat":    _s("дословният откъс"),
                    "stranica": {"type": "integer"},
                }},
            },
            "normi": {
                "type": "array",
                "description": "Наредби, закони и стандарти, на които записката се позовава.",
                "items": {"type": "object", "properties": {
                    "akt":      _s("наредбата или законът, както е изписан"),
                    "chlen":    _s("член, алинея, точка — ако са посочени"),
                    "zashto":   _s("какво извежда записката от него"),
                    "citat":    _s("дословният откъс"),
                    "stranica": {"type": "integer"},
                }},
            },
            "iziskvania": {
                "type": "array",
                "description": "Какво записката изисква да се изпита, изпробва, измери или докаже при изпълнението.",
                "items": {"type": "object", "properties": {
                    "kakvo":    _s("какво трябва да се докаже"),
                    "citat":    _s("дословният откъс"),
                    "stranica": {"type": "integer"},
                }},
            },
        },
        "required": ["chast_kod"],
    },
}


UKAZANIE = f"""Четеш ОБЯСНИТЕЛНА ЗАПИСКА по една част от инвестиционен проект за строеж в България.

Записката казва какво ще се построи и какви материали ще се вложат. От нея строителният надзор вади какво да изисква и какво да провери на обекта.

ТИ САМО ПРЕПИСВАШ. Не тълкуваш, не поправяш, не допълваш по памет и не предполагаш.
Всяко твърдение носи ДОСЛОВЕН цитат от текста и номер на страница. Без цитат — не го записвай.

Ако записката греши (например бърка номер на УПИ), преписваш грешката както е. Поправянето е работа на човека.

ЧАСТИ НА ПРОЕКТА:
{_spisak(CHASTI)}

ПРИЗНАЦИ — отговаряй само на тези, за които записката наистина казва нещо:
{_spisak(PRIZNACI)}

ВАЖНО за признаците: „няма“ е отговор САМО когато записката го казва или когато
от описанието ѝ личи недвусмислено (изброява етажите и сутерен не фигурира).
Ако частта просто не говори за нещо — ПРОПУСНИ признака. Мълчанието на част ВиК
за асансьора не значи, че асансьор няма.

ВАЖНО за „по друг проект“: изрази като „по друг проект“, „по отделен проект“,
„виж част …“, „от друга разработка“ ги записвай ВИНАГИ. Те сочат съседните
строежи на площадката и са важни.
"""


# ── Четене ───────────────────────────────────────────────────────────────────

def _kam_tekst(prep, ime):
    """Текстов PDF → текст вместо документ: същото съдържание, в пъти по-евтино.

    Записките са текст, не чертежи — оформлението не носи информация. Когато
    има текстов слой, няма смисъл да се праща и картината. (01.10.2026)
    """
    stranici = prep.get("stranici") or []
    if prep.get("sken") or not stranici:
        return prep
    tekst = "\n\n".join(f"--- стр. {i + 1} ---\n{s}" for i, s in enumerate(stranici))
    if len(tekst.strip()) < 200:
        return prep
    return {**prep, "blokove": [{"type": "text", "text": f"Текстът на {ime}:\n\n{tekst[:150000]}"}],
            "ot_tekst": True}


def procheti(chetci, ime, media_type, data_b64, stranici=None):
    """Една записка → прочетеното от нея. Връща (записка, info)."""
    from .chetci import NeMozheSega
    prep = _kam_tekst(podgotvi(ime, media_type, data_b64, stranici), ime)
    tekst = UKAZANIE + f"\n\nФайл: {ime}"
    raw = prep.get("raw") or b""
    prichini = []
    for chetec in list(chetci):
        try:
            dok, i = chetec.chete(prep, SHEMA, tekst, ime=ime, raw=raw,
                                  n_stranici=MAX_STRANICI if prep.get("n", 0) > MAX_STRANICI else 0,
                                  edin_dokument=True)
            z = _edna(dok)
            if z is None:
                prichini.append((chetec.ime, "празен отговор"))
                continue
            z.update({
                "fajl": ime, "chetec": chetec.ime, "model": i.get("model"),
                "sken": prep.get("sken", False), "ot_tekst": bool(prep.get("ot_tekst")),
                "belezhka": prep.get("belezhka", ""),
                "zashto_rezerven": "; ".join(f"{k}: {v}" for k, v in prichini),
            })
            _sveri(z, prep.get("stranici") or [], prep.get("sken", False))
            return z, {"chetec": chetec.ime, **{k: i.get(k) for k in ("model", "tokens_in", "tokens_out")}}
        except NeMozheSega as e:
            prichini.append((chetec.ime, str(e)[:300]))
    raise NikoyNeMozhe(prichini or [("", "няма настроен четец")])


def _edna(dok):
    """Отговорът на четеца → една записка. Разхлабеният формат се разчита."""
    if isinstance(dok, str):
        try:
            dok = json.loads(dok)
        except Exception:
            return None
    if not isinstance(dok, dict):
        return None
    # Четецът с `edin_dokument=True` връща {"dokumenti": [ {...} ]}
    for klyuch in ("dokumenti", "documents", "zapiski"):
        if isinstance(dok.get(klyuch), list) and dok[klyuch]:
            dok = dok[klyuch][0]
            break
    if not isinstance(dok, dict) or not dok:
        return None
    if dok.get("chast_kod") not in CHASTI:
        dok["chast_kod"] = "DRUGA"
    for pole in ("priznaci", "materiali", "instalacii", "chisla", "drug_proekt", "normi",
                 "iziskvania", "chelen_list", "vazlozhiteli"):
        if not isinstance(dok.get(pole), list):
            dok[pole] = []
    for p in dok["priznaci"]:
        if isinstance(p, dict) and p.get("priznak") not in PRIZNACI:
            p["priznak"] = ""
    return dok


def _sveri(z, stranici, sken):
    """Цитатът намира ли се в текстовия слой. Скан → няма срещу какво да се свери."""
    cel = _norm_tekst("\n".join(stranici)) if stranici else ""
    for pole in ("priznaci", "materiali", "instalacii", "chisla", "drug_proekt", "normi", "iziskvania"):
        for red in z.get(pole) or []:
            if not isinstance(red, dict):
                continue
            citat = _norm_tekst(red.get("citat") or "")
            if sken or not cel or not citat:
                red["sverka"] = "от скан — потвърди" if sken else "няма текст за сверка"
            elif citat in cel:
                red["sverka"] = "ok"
            else:
                red["sverka"] = "цитатът не е намерен в текста"


# ── Сглобяване на всички части в една картина ────────────────────────────────
# Една записка е една част. Силата е в събирането им: там се виждат и
# противоречията между частите (ВиК пише „в сутерена“, ОВК изброява етажите без
# сутерен — ДЖИХАТ, 01.10.2026).

# Кои части се очакват. Операторът, 01.10.2026.
OCHAKVANI = {
    "sgrada": ["ARH", "KONSTR", "EL", "VIK", "OVK", "EE", "PB", "GEO", "OZELEN", "PBZ", "TRANSP"],
    "lineen": ["EL", "GEO", "TRANSP", "ARH", "KONSTR", "PB", "PBZ"],
}


# Свободният текст се сравнява БЕЗ пунктуация и интервали: иначе „кв.5“ и
# „кв. 5“ излизат като разминаване. Точно този шум накара оператора да каже, че
# сверяването при ОД е непоносимо (16.09.2026) — да не го повтаряме тук.
def _norm_svobodno(s):
    return re.sub(r"[^0-9a-zа-я]+", "", _norm_tekst(s))


# „ТЕХНИЧЕСКИ ПРОЕКТ“ и „ТП“ са едно и също.
_FAZI = ((("технически", "тп"), "технически проект"),
         (("идеен", "ип"), "идеен проект"),
         (("работен", "рп"), "работен проект"))


def _faza(s):
    n = _norm_tekst(s)
    for dumi, ime in _FAZI:
        if any(d in n for d in dumi):
            return ime
    return n


# Част, наречена свободно в челния лист → код. „ПАРКОУСТРОЙСТВО“ и
# „Озеленяване“ са една част; „ПОЖАРНА БЕЗОПАСНОСТ“ не е „ПБЗ“.
_PO_DUMA = (("пбз", "PBZ"), ("безопасностиздраве", "PBZ"),
            ("пожарна", "PB"), ("архитект", "ARH"), ("конструкц", "KONSTR"),
            ("геодез", "GEO"), ("енергийна", "EE"),
            ("паркоустр", "OZELEN"), ("озелен", "OZELEN"), ("ландшафт", "OZELEN"),
            ("овк", "OVK"), ("отоплен", "OVK"), ("вентилац", "OVK"), ("климат", "OVK"),
            ("вик", "VIK"), ("водоснаб", "VIK"), ("канализац", "VIK"),
            ("електро", "EL"), ("ел", "EL"),
            ("транспорт", "TRANSP"), ("пътна", "TRANSP"), ("патna", "TRANSP"))


def kod_na_chast(ime):
    """Как е наречена частта → код, или празно, ако не се познава."""
    n = _norm_svobodno(ime)
    if not n:
        return ""
    if n.upper() in CHASTI:
        return n.upper()
    for duma, kod in _PO_DUMA:
        if duma in n:
            return kod
    return ""


def _ime_na_chast(ime):
    kod = kod_na_chast(ime)
    return CHASTI[kod] if kod else (str(ime or "").strip())


def _grupa(zapiski, vzemi, norm=None):
    """Стойност → кои части я твърдят. За хващане на разминавания между частите."""
    norm = norm or _norm_svobodno
    po = {}
    for z in zapiski:
        st = (vzemi(z) or "").strip()
        if st:
            po.setdefault(norm(st), {"stoynost": st, "chasti": []})["chasti"].append(
                CHASTI.get(z.get("chast_kod"), z.get("chast_kod")))
    return list(po.values())


def _edno(grupi, kakvo):
    """Едно твърдение или разминаване — в еднакъв вид за показване."""
    if not grupi:
        return None
    red = {"kakvo": kakvo, "varianti": grupi}
    red["edinno"] = len(grupi) == 1
    red["stoynost"] = grupi[0]["stoynost"] if red["edinno"] else ""
    return red


def rezyume(zapiski, vid="sgrada"):
    """Прочетените записки → какво знаем за обекта и какво не се връзва."""
    zapiski = [z for z in zapiski if isinstance(z, dict)]
    prochetini = [z.get("chast_kod") for z in zapiski]

    # 1) Признаците — отговорите, които няма да питаме оператора.
    priznaci = {}
    for z in zapiski:
        chast = CHASTI.get(z.get("chast_kod"), "")
        for p in z.get("priznaci") or []:
            if not isinstance(p, dict) or not p.get("priznak"):
                continue
            v = priznaci.setdefault(p["priznak"], {
                "priznak": p["priznak"],
                "ime": PRIZNACI_IME.get(p["priznak"], p["priznak"]),
                "opisanie": PRIZNACI.get(p["priznak"], ""), "tvardenia": []})
            v["tvardenia"].append({"stoynost": p.get("stoynost", ""), "chast": chast,
                                   "citat": p.get("citat", ""), "stranica": p.get("stranica"),
                                   "sverka": p.get("sverka", "")})
    for v in priznaci.values():
        razlichni = {_norm_svobodno(t["stoynost"]) for t in v["tvardenia"] if t["stoynost"]}
        v["edinno"] = len(razlichni) <= 1
        v["stoynost"] = v["tvardenia"][0]["stoynost"] if v["edinno"] and v["tvardenia"] else ""

    # 2) Шапката на обекта — тук изплува „УПИ XXXII срещу XXXI“.
    shapka = [r for r in (
        _edno(_grupa(zapiski, lambda z: z.get("obekt")), "Наименование на строежа"),
        _edno(_grupa(zapiski, lambda z: z.get("upi")), "УПИ / поземлен имот"),
        _edno(_grupa(zapiski, lambda z: z.get("investitor")), "Инвеститор"),
        _edno(_grupa(zapiski, lambda z: z.get("faza"), _faza), "Фаза"),
    ) if r]

    # 3) Проектантите: челният лист на която и да е част дава всички.
    proektanti = {}
    for z in zapiski:
        chast = CHASTI.get(z.get("chast_kod"), "")
        if z.get("proektant"):
            proektanti.setdefault(_norm_tekst(z["proektant"]), {
                "ime": z["proektant"], "chasti": set(), "registraciya": z.get("proektant_registraciya", "")})
            proektanti[_norm_tekst(z["proektant"])]["chasti"].add(chast)
        for r in z.get("chelen_list") or []:
            if not isinstance(r, dict) or not r.get("proektant"):
                continue
            k = _norm_tekst(r["proektant"])
            proektanti.setdefault(k, {"ime": r["proektant"], "chasti": set(), "registraciya": ""})
            if r.get("chast"):
                proektanti[k]["chasti"].add(_ime_na_chast(r["chast"]))
    proektanti = [{**p, "chasti": sorted(x for x in p["chasti"] if x)} for p in proektanti.values()]

    # 4) Списъците — с коя част идва всеки ред, за да се знае на кого да се каже.
    def saberi(pole):
        out = []
        for z in zapiski:
            chast = CHASTI.get(z.get("chast_kod"), "")
            for r in z.get(pole) or []:
                if isinstance(r, dict) and any((r.get(k) or "").strip() for k in r if k != "stranica"):
                    out.append({**r, "chast": chast})
        return out

    ochakvani = OCHAKVANI.get(vid) or OCHAKVANI["sgrada"]
    return {
        "chasti_prochetini": [{"kod": k, "ime": CHASTI.get(k, k)} for k in prochetini],
        "chasti_lipsvat": [{"kod": k, "ime": CHASTI[k]} for k in ochakvani if k not in prochetini],
        "shapka": shapka,
        "priznaci": sorted(priznaci.values(), key=lambda v: v["priznak"]),
        "proektanti": proektanti,
        "materiali": saberi("materiali"),
        "instalacii": saberi("instalacii"),
        "chisla": saberi("chisla"),
        "drug_proekt": saberi("drug_proekt"),
        "normi": saberi("normi"),
        "iziskvania": saberi("iziskvania"),
        "razminavania": ([r for r in shapka if not r["edinno"]]
                         + [{"kakvo": f"Признак „{v['priznak']}“", "varianti": [
                                {"stoynost": t["stoynost"], "chasti": [t["chast"]]} for t in v["tvardenia"]],
                             "edinno": False, "stoynost": ""}
                            for v in priznaci.values() if not v["edinno"]]),
    }

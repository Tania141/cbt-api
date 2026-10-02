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
    "VIZA":     "Виза за проектиране",
    "SITUACIA": "Ситуация / вертикална планировка",
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
    # Градоустройствени показатели. ДОПУСТИМИТЕ идват от визата, ПОСТИГНАТИТЕ —
    # от архитектурата и ситуацията. Операторът, 02.10.2026: „най-лесният начин е
    # чете се записка + виза, сверява се, чек, операторът верифицира“.
    "zona":             "устройствена зона по виза (Жм, Жк, Смф…); ако имотът е в НЯКОЛКО зони — изброй ги",
    "plosht_upi":       "площ на урегулирания поземлен имот, в м²",
    "plytnost_dop":     "ДОПУСТИМА плътност на застрояване, в % (по виза)",
    "kint_dop":         "ДОПУСТИМ коефициент на интензивност Кинт (по виза)",
    "ozelen_dop":       "ДОПУСТИМО/минимално озеленяване, в % (по виза)",
    "korniz_dop":       "ДОПУСТИМА максимална кота корниз, в м (по виза)",
    "zp":               "ПОСТИГНАТА застроена площ, в м²",
    "rzp":              "ПОСТИГНАТА разгъната застроена площ, в м²",
    "plytnost_post":    "ПОСТИГНАТА плътност на застрояване, в % — ако е изписана",
    "ozelen_post":      "ПОСТИГНАТО озеленяване — площ в м² и/или %",
    "korniz_post":      "ПОСТИГНАТА кота корниз, в м",
    "pup":              "с какво е одобрен подробният устройствен план — решение/заповед, орган, дата",
    "kadastr":          "с какво е одобрена кадастралната карта — заповед, орган, дата",
    "otstoyania":       "изисквания за отстояния, цитирани във визата (чл. 31, 32, 33 ЗУТ и др.)",
}


# Кратко име за показване — описанието е за четеца, не за екрана.
PRIZNACI_IME = {
    "etaji": "Етажи", "podzemen_etaj": "Сутерен / подземен етаж", "garaj": "Гараж",
    "otoplenie": "Отопление", "toplosnabdyavane": "Топлоснабдяване", "gaz": "Газ",
    "ovk": "ОВК", "ventilaciya": "Вентилация", "asansior": "Асансьор",
    "drenaj": "Дренаж и помпи", "pozharogasene": "Пожарогасене",
    "pozharoizvestyavane": "Пожароизвестяване", "el_saobshteniya": "Електронни съобщения",
    "vik": "ВиК присъединяване", "elektro": "Електро присъединяване", "visochina": "Височина",
    "zona": "Устройствена зона", "plosht_upi": "Площ на УПИ",
    "plytnost_dop": "Плътност — допустима", "kint_dop": "Кинт — допустим",
    "ozelen_dop": "Озеленяване — допустимо", "korniz_dop": "Кота корниз — допустима",
    "zp": "ЗП — постигната", "rzp": "РЗП — постигната",
    "plytnost_post": "Плътност — постигната", "ozelen_post": "Озеленяване — постигнато", "korniz_post": "Кота корниз — постигната",
    "pup": "ПУП — одобрен с", "kadastr": "Кадастрална карта — одобрена със",
    "otstoyania": "Отстояния по виза",
}


def _spisak(rechnik):
    return "\n".join(f"- {k} — {v}" for k, v in rechnik.items())


# ── Какво връща четецът ──────────────────────────────────────────────────────

def _s(opisanie, **ostanalo):
    return {"type": "string", "description": opisanie, **ostanalo}


# ВАЖНО: това е САМАТА схема (input_schema), не описание на инструмент.
# Четците (`chetci.py`) я обвиват сами — Claude я слага в `input_schema`,
# Mistral в `json_schema.schema`. Подаден цял инструмент, Claude отговаря
# „tools.0.custom.input_schema.type: Field required“ (01.10.2026).
SHEMA = {
        "type": "object",
        "properties": {
            "chast_kod": _s("коя част на проекта е записката", enum=list(CHASTI)),
            "chast_ime": _s("как е наречена частта в самата записка, дословно"),
            "obekt":     _s("наименованието на САМИЯ строеж, дословно — това, което стои ПРЕДИ „за обект…“"),
            "zahranvan_obekt": _s("ако строежът е мрежа или присъединяване: КОЙ обект захранва — "
                                  "частта след „за обект…“, дословно. Иначе празно."),
            "upi":       _s("УПИ / поземлен имот, дословно"),
            "identifikator": _s("идентификаторът по КККР (напр. 68134.209.689), дословно"),
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

ВИЗАТА ЗА ПРОЕКТИРАНЕ не е част на проекта, а документ на главния архитект —
„chast_kod“ е VIZA. Тя е ИЗВОРЪТ на допустимите показатели. Ситуацията (таблицата
с показателите) е SITUACIA.

ГРАДОУСТРОЙСТВЕНИТЕ ПОКАЗАТЕЛИ идват от две места и НЕ се смесват:
  · ДОПУСТИМИТЕ (plytnost_dop, kint_dop, ozelen_dop, korniz_dop, zona, pup,
    kadastr, otstoyania) са от ВИЗАТА ЗА ПРОЕКТИРАНЕ или от цитат на визата;
  · ПОСТИГНАТИТЕ (zp, rzp, ozelen_post, korniz_post) са от архитектурата и от
    таблицата на ситуацията.
Ако имотът попада в НЯКОЛКО устройствени зони, изброй ги всичките в „zona“ и
запиши показателите на всяка, както са написани — не ги сливай и не избирай.

ЗП, РЗП, площта на имота, озеленяването, котата корниз и височината СА
ПОКАЗАТЕЛИ — слагай ги в „priznaci“ със съответния код, не само в „chisla“.

ВАЖНО за признаците: „няма“ е отговор САМО когато записката го казва или когато
от описанието ѝ личи недвусмислено (изброява етажите и сутерен не фигурира).
Ако частта просто не говори за нещо — ПРОПУСНИ признака. Мълчанието на част ВиК
за асансьора не значи, че асансьор няма.

ВАЖНО за „по друг проект“: изрази като „по друг проект“, „по отделен проект“,
„виж част …“, „от друга разработка“ ги записвай ВИНАГИ. Те сочат съседните
строежи на имота и са важни.

НАЙ-ВАЖНОТО ПРИ МРЕЖИ И ПРИСЪЕДИНЯВАНИЯ (операторът, 01.10.2026):
Наименование от вида
    „Външно електрозахранване с нови кабели НН 1kV ЗА ОБЕКТ „Жилищна сграда с
     офиси и гаражи“, находящ се в УПИ VIII-503 … идентификатор 68134.209.689“
описва ДВЕ различни неща:
  · СТРОЕЖЪТ е външното електрозахранване — това е водещото;
  · „Жилищна сграда с офиси и гаражи“ е само ЗАХРАНВАНИЯТ обект, който казва
    кой имот се захранва.
Затова:
  · в „obekt“ пиши САМО строежа (частта преди „за обект“);
  · захранвания обект пиши в „zahranvan_obekt“;
  · УПИ и идентификаторът са на захранвания имот — пиши ги както са.
И НАЙ-ВАЖНОТО: признаци НЕ се вадят от наименованието на захранвания обект.
„Жилищна сграда с офиси и гаражи“ НЕ значи, че кабелната линия има гаражи или
етажи. Признак се записва само ако записката казва нещо за САМИЯ строеж.
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
            if z is not None:
                pochisti_ot_zahranvania(z)
                vdigni_pokazateli(z)
            if z is None or _prazna(z):
                # Празно четене не се записва — иначе в списъка влиза „друга
                # част“ без съдържание и обърква броя на прочетените. (01.10.2026)
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


_ZA_OBEKT = re.compile(r"(?<![А-яA-Za-z])за\s+обект(?![А-яA-Za-z])", re.I)


def pochisti_ot_zahranvania(z):
    """Маха признаци, прочетени от името на ЗАХРАНВАНИЯ обект.

    Операторът, 01.10.2026: при „Външно електрозахранване… за обект «Жилищна
    сграда с офиси и гаражи»“ водещото е захранването, не сградата. Четецът
    беше записал „има гаражи“ като признак на кабелната линия. Указанието му го
    забранява, но указание, което вече веднъж не е спазено, иска и предпазител.

    Връща колко са махнати.
    """
    chuzhdo = str(z.get("zahranvan_obekt") or "")
    if not chuzhdo:
        ime = str(z.get("obekt") or "")
        m = _ZA_OBEKT.search(ime)
        if m:
            chuzhdo = ime[m.end():]
    chuzhdo = _norm_tekst(chuzhdo)
    if len(chuzhdo) < 15:
        return 0
    ostavashti, mahnati = [], 0
    for pr in z.get("priznaci") or []:
        citat = _norm_tekst((pr or {}).get("citat") or "")
        # Цитатът е цял вътре в името на чуждия обект → не е за този строеж.
        if citat and len(citat) >= 8 and citat in chuzhdo:
            mahnati += 1
            continue
        ostavashti.append(pr)
    z["priznaci"] = ostavashti
    if mahnati:
        z["mahnati_chuzhdi"] = mahnati
    return mahnati


# Числата, които ВСЪЩНОСТ са показатели. Операторът, 02.10.2026: „РЗП, ЗП и
# височина са показатели, и площ на имота, и озеленяване“ — а четецът ги беше
# оставил в свободния списък „числа за сверяване“, където нямат ✔.
# Кодът ги вдига: указание, което веднъж не е спазено, иска предпазител.
_CHISLA_KATO_PRIZNAK = (
    ("разгъната", "rzp"), ("рзп", "rzp"),
    ("застроена площ", "zp"), ("зп", "zp"),
    ("площ на имота", "plosht_upi"), ("площ на упи", "plosht_upi"),
    ("площ на поземления", "plosht_upi"),
    ("озелен", "ozelen_post"), ("зелени площи", "ozelen_post"),
    ("корниз", "korniz_post"),
    ("височина", "visochina"),
    ("плътност", "plytnost_post"),
    ("интензивност", "kint_post"), ("кинт", "kint_post"),
)


def vdigni_pokazateli(z):
    """Числа с познато име → признаци. Връща колко са вдигнати.

    Числото ОСТАВА и в списъка — там се вижда контекстът; признакът е за ✔.
    Признак, който вече съществува, не се пипа: той е по-точен.
    """
    ima = {p.get("priznak") for p in (z.get("priznaci") or []) if isinstance(p, dict)}
    vdignati = 0
    for red in z.get("chisla") or []:
        if not isinstance(red, dict):
            continue
        kakvo = _norm_tekst(red.get("kakvo"))
        if not kakvo:
            continue
        kod = next((k for duma, k in _CHISLA_KATO_PRIZNAK if duma in kakvo), None)
        if not kod or kod in ima:
            continue
        st = str(red.get("stoynost") or "").strip()
        if not st:
            continue
        merna = str(red.get("merna") or "").strip()
        z.setdefault("priznaci", []).append({
            "priznak": kod,
            "stoynost": f"{st} {merna}".strip(),
            "citat": red.get("citat", ""),
            "stranica": red.get("stranica"),
            "sverka": red.get("sverka", ""),
            "ot_chislo": True,
        })
        ima.add(kod)
        vdignati += 1
    return vdignati


def _prazna(z):
    """Четене без нищо вътре — нито признак, нито материал, нито дори обект."""
    if any(z.get(k) for k in ("priznaci", "materiali", "instalacii", "chisla",
                              "drug_proekt", "normi", "iziskvania", "chelen_list")):
        return False
    return not any(str(z.get(k) or "").strip()
                   for k in ("obekt", "upi", "investitor", "proektant", "opisanie", "chast_ime"))


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
# Латиница, която изглежда като кирилица. В проектите се среща постоянно —
# „ЕРМ ЗАПАД“ с латински Е, Р, А излизаше като разминаване с „ЕРМ Запад“.
# Сгъва се САМО за сравняване; показва се винаги оригиналът. (01.10.2026)
_BLIZNACI = str.maketrans({
    "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "K": "К", "M": "М",
    "O": "О", "P": "Р", "T": "Т", "X": "Х", "Y": "У",
    "a": "а", "c": "с", "e": "е", "o": "о", "p": "р", "x": "х", "y": "у",
})


def _norm_svobodno(s):
    return re.sub(r"[^0-9a-zа-я]+", "", _norm_tekst(str(s or "").translate(_BLIZNACI)))


# Дума, в която има И латиница, И кирилица, почти винаги идва от разчитането на
# скан, не от проекта. Операторът, 01.10.2026: „УПИ VIII-503 е вярно, а VНI-503
# е от записка, прочетена с ABBYY от PDF“ — кирилско Н вместо две латински I.
# Системата не поправя (тя преписва), но казва на какво прилича.
_LAT = re.compile(r"[A-Za-z]")
_KIR = re.compile(r"[А-Яа-яЁё]")


def smesena_azbuka(tekst):
    """Думите, в които латиница и кирилица са смесени. Празно — няма такива."""
    out = []
    for duma in re.split(r"[\s,;:()\[\]«»„“”\"']+", str(tekst or "")):
        jadro = duma.strip(".-–—/")
        if len(jadro) > 1 and _LAT.search(jadro) and _KIR.search(jadro):
            out.append(jadro)
    return out


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


# Номерът на УПИ е РИМСКО ЧИСЛО. „VHI-503“ не е валидно римско число — а
# „VIII-503“ е. Това хваща случая, който смесената азбука пропуска: ABBYY е
# прочел двете „II“ като едно „H“, при това латинско, тоест нищо не се смесва.
# (01.10.2026 — операторът: „VIII-503 е вярно, VHI е от записка през ABBYY“.)
_KAM_LATINICA = str.maketrans({"Н": "H", "Х": "X", "С": "C", "І": "I", "М": "M",
                               "Д": "D", "Л": "L", "В": "B", "І": "I"})
_RIMSKO = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
_SLED_UPI = re.compile(r'УПИ\s+([A-Za-zА-Яа-я]{1,10})')


def nevalidno_rimsko(tekst):
    """Номера след „УПИ“, които не са валидни римски числа. Празно — всичко е наред."""
    out = []
    for nomer in _SLED_UPI.findall(str(tekst or "")):
        lat = nomer.upper().translate(_KAM_LATINICA)
        if not _RIMSKO.match(lat) or not lat:
            out.append(nomer)
    return out


def _grupa(zapiski, vzemi, norm=None):
    """Стойност → кои части я твърдят. За хващане на разминавания между частите."""
    norm = norm or _norm_svobodno
    po = {}
    for z in zapiski:
        st = (vzemi(z) or "").strip()
        if st:
            po.setdefault(norm(st), {"stoynost": st, "smesena": smesena_azbuka(st),
                                     "nevalidno": nevalidno_rimsko(st),
                                     "chasti": []})["chasti"].append(
                CHASTI.get(z.get("chast_kod"), z.get("chast_kod")))
    return list(po.values())


def _edno(grupi, kakvo, klyuch=""):
    """Едно твърдение или разминаване — в еднакъв вид за показване.

    `klyuch` е машинното име на полето: PWA го връзва за склада на фактите, без
    да разчита на българското заглавие. (01.10.2026)
    """
    if not grupi:
        return None
    red = {"kakvo": kakvo, "klyuch": klyuch, "varianti": grupi}
    red["edinno"] = len(grupi) == 1
    red["stoynost"] = grupi[0]["stoynost"] if red["edinno"] else ""
    return red


# ── Чужда записка ────────────────────────────────────────────────────────────
# Операторът, 02.10.2026: „не открива генерална грешка — ако иде реч за друго УПИ
# или за друг обект в това УПИ, то си чеква какво е прочело, а не въобще става
# или не става“.
#
# Истинският случай: папка с три записки, а тази по пожарна безопасност беше за
# УПИ XII-60, Овча купел 2, идентификатор 68134.4333.274 и друг инвеститор —
# докато другите две са за УПИ III-1662…, 68134.4354.781. Системата ги сля и
# каза „частите не се връзват“, сякаш спорят за една и съща сграда.
#
# Чуждата записка НЕ Е разминаване. Тя изобщо не е тук и не бива да влиза във
# фактите — само да се посочи.

_CIFRI = re.compile(r"\d")


# Само ЯДРОТО на УПИ-то: римското число и номерата на имотите. Кварталът и
# местността отпадат — „УПИ III-1662,1725,2329“ и „УПИ III-1662, 1725, 2329,
# кв. 21, м. «Люлин — разширение запад»“ са един и същ имот. (02.10.2026)
_UPI_YADRO = re.compile(r"(?:упи\s*)?([IVXLCMivxlcm]+)\s*[-–—]\s*([\d\s,\.]+)", re.I)


def _upi_yadro(tekst):
    m = _UPI_YADRO.search(str(tekst or ""))
    if not m:
        return ""
    rimsko = m.group(1).upper()
    nomera = re.sub(r"[^\d,]", "", m.group(2)).strip(",")
    # Спира на „кв“ / „м“ — те идват след номерата.
    nomera = ",".join(sorted(x for x in nomera.split(",") if x))
    return f"{rimsko}-{nomera}" if nomera else ""


def _imot_znaci(z):
    """Белезите, по които се познава имотът: идентификатор и/или УПИ.

    Две записки са за ЕДИН имот, ако съвпадат по КОЙТО И ДА Е белег — едната
    може да носи само УПИ, другата и двете. Затова не един ключ, а множество.
    """
    znaci = set()
    # Визата на обединен имот носи НЯКОЛКО номера — всичките са негови белези.
    for x in identifikatori_v(z):
        znaci.add(("ид", x))
    upi = _upi_yadro(z.get("upi"))
    if upi:
        znaci.add(("упи", upi))
    return znaci


def chuzhdi_zapiski(zapiski, nashi_identifikatori=()):
    """Разделя на „за този имот“ и „за друг“. Решава мнозинството.

    `nashi_identifikatori` — всички идентификатори на ТОЗИ имот, включително
    предишните. Операторът, 02.10.2026: „УПИ III обединява три идентификатора и
    накрая е получило един 68134.4354.781 — имало е 3 имота, станали са 1 УПИ с
    1 идентификатор“. Визата носи СТАРИТЕ; без тях излиза като чужд имот.
    Затова те са ПСЕВДОНИМИ: всеки се заменя с един и същ белег.

    Връща (nashi, chuzhdi, neyasno). `neyasno` е True при липса на мнозинство —
    тогава НИЩО не се изключва и операторът решава.
    """
    psevdonimi = {re.sub(r"[^\d.]", "", str(x)).strip(".")
                  for x in (nashi_identifikatori or []) if str(x).strip()}
    psevdonimi.discard("")

    def znaci_na(z):
        zn = set()
        for vid, st in _imot_znaci(z):
            if vid == "ид" and st in psevdonimi:
                zn.add(("ид", "НАШИЯТ"))      # всички наши номера са един белег
            else:
                zn.add((vid, st))
        return zn

    znaci = [znaci_na(z) for z in zapiski]
    grupi = []                                   # [(множество белези, [индекси])]
    for i, zn in enumerate(znaci):
        if not zn:
            continue
        sleti = [g for g in grupi if g[0] & zn]
        nova = (set(zn), [i])
        for g in sleti:
            nova[0].update(g[0])
            nova[1].extend(g[1])
            grupi.remove(g)
        grupi.append(nova)
    if len(grupi) < 2:
        return zapiski, [], False
    # Групата с НАШИЯТ идентификатор печели, дори да е по-малка.
    nasha = next((g for g in grupi if ("ид", "НАШИЯТ") in g[0]), None)
    if nasha is None:
        grupi.sort(key=lambda g: -len(g[1]))
        if len(grupi[0][1]) == len(grupi[1][1]):
            return zapiski, [], True
        nasha = grupi[0]
    nashi_i = set(nasha[1])
    bez = {i for i, zn in enumerate(znaci) if not zn}
    nashi = [z for i, z in enumerate(zapiski) if i in nashi_i or i in bez]
    chuzhdi = [z for i, z in enumerate(zapiski) if i not in nashi_i and i not in bez]
    return nashi, chuzhdi, False


# ── Записка за ДРУГ СТРОЕЖ в същия имот ──────────────────────────────────────
# Операторът, 02.10.2026: „същото важи и за обекта, ако и да е в същото УПИ. Ако
# сме му казали канал, а му предлагам архитектура, редно е да ги различава.“
#
# В нейния случай в един имот има два строежа: „Уличен канал Ø600-ПП и Ø800-ПП“ и
# „Две жилищни сгради с надземни и подземни гаражи“. Записка на единия, качена
# при другия, не е разминаване — просто ѝ е сбъркано мястото.
#
# Разпознава се по ЕСТЕСТВОТО на строежа, не по изписването: мрежа срещу сграда.
# Нарочно груб белег — фин не е възможен и би сгрешил.

_DUMI_MREZHA = ("канал", "водопровод", "кабел", "електрозахранван", "захранван",
                "трасе", "улич", "пътна", "ктп", "провод", "колектор",
                "отклонение", "мрежа", "газопровод", "топлопровод", "сервитут",
                "присъединяван", "външно")
_DUMI_SGRADA = ("сграда", "жилищн", "офис", "хотел", "детск", "училищ", "болниц",
                "магазин", "склад", "производствен", "пристройка", "надстройка",
                "къща", "вила")


def vid_na_stroezh(tekst):
    """„мрежа“ · „сграда“ · „“ (не личи). Мрежата се проверява първа: името на
    мрежата често съдържа и сградата, която захранва."""
    t = _norm_tekst(tekst)
    if not t:
        return ""
    if any(d in t for d in _DUMI_MREZHA):
        return "мрежа"
    if any(d in t for d in _DUMI_SGRADA):
        return "сграда"
    return ""


def za_drug_stroezh(zapiski, ime_na_stroezha=""):
    """Кои записки са за друг строеж в същия имот.

    Мерилото е името, което операторът е дал на строежа; ако го няма — мнозинството.
    Връща (nashi, drugi).
    """
    vidove = [vid_na_stroezh(z.get("obekt")) for z in zapiski]
    nash = vid_na_stroezh(ime_na_stroezha)
    if not nash:
        broi = {}
        for v in vidove:
            if v:
                broi[v] = broi.get(v, 0) + 1
        if len(broi) < 2:
            return zapiski, []
        naredeni = sorted(broi.items(), key=lambda kv: -kv[1])
        if naredeni[0][1] == naredeni[1][1]:
            return zapiski, []          # по равно — не гадаем
        nash = naredeni[0][0]
    nashi = [z for z, v in zip(zapiski, vidove) if v in (nash, "")]
    drugi = [z for z, v in zip(zapiski, vidove) if v and v != nash]
    return nashi, drugi


_IDENT = re.compile(r'(?<!\d)\d{5}\.\d+\.\d+(?!\d)')


def identifikatori_v(z):
    """Всички идентификатори по КККР, които се срещат в записката."""
    kade = [z.get("identifikator"), z.get("upi"), z.get("obekt"), z.get("zahranvan_obekt")]
    for p in z.get("priznaci") or []:
        if isinstance(p, dict):
            kade += [p.get("stoynost"), p.get("citat")]
    namereni = []
    for t in kade:
        for x in _IDENT.findall(str(t or "")):
            if x not in namereni:
                namereni.append(x)
    return namereni


def _opisanie_imot(z):
    return " · ".join(x for x in (str(z.get("upi") or "").strip(),
                                  str(z.get("identifikator") or "").strip(),
                                  str(z.get("investitor") or "").strip()) if x)


def rezyume(zapiski, vid="sgrada", ime_na_stroezha="", stari_identifikatori=()):
    """Прочетените записки → какво знаем за обекта и какво не се връзва.

    `ime_na_stroezha` е как операторът е нарекъл СТРОЕЖА — по него се познава
    записка, която е за друг строеж в същия имот.
    """
    zapiski = [z for z in zapiski if isinstance(z, dict)]
    # И тук, не само при четенето: вече прочетените записки да получат
    # показателите си без ново четене (и без да се плаща пак). (02.10.2026)
    for z in zapiski:
        vdigni_pokazateli(z)
    # Две чистения, преди каквото и да е да влезе във фактите:
    # 1) записка за ДРУГ ИМОТ — изобщо не е тук;
    # 2) записка за ДРУГ СТРОЕЖ в същия имот — тук е, но не на този строеж.
    vsichki = zapiski
    zapiski, chuzhdi, neyasno = chuzhdi_zapiski(zapiski, stari_identifikatori)
    zapiski, drug_stroezh = za_drug_stroezh(zapiski, ime_na_stroezha)
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
        _edno(_grupa(zapiski, lambda z: z.get("obekt")), "Наименование на строежа", "obekt"),
        _edno(_grupa(zapiski, lambda z: z.get("zahranvan_obekt")), "Захранван обект (мрежата обслужва)", "zahranvan_obekt"),
        _edno(_grupa(zapiski, lambda z: z.get("upi")), "УПИ / поземлен имот", "upi"),
        # Идентификаторът е НАЙ-СИГУРНАТА опора: цифрите нямат двойници в
        # кирилица, затова преживяват разчитането на скан, а римското число —
        # не („VIII“ стана „VHI“, а 68134.209.689 остана същият). (01.10.2026)
        _edno(_grupa(zapiski, lambda z: z.get("identifikator")), "Идентификатор по КККР", "identifikator"),
        _edno(_grupa(zapiski, lambda z: z.get("investitor")), "Инвеститор (възложител по договор)", "investitor"),
        _edno(_grupa(zapiski, lambda z: z.get("faza"), _faza), "Фаза на проекта", "faza"),
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
        # Записки, които изобщо не са за този имот — посочват се отделно и НЕ
        # участват в нищо по-долу. (02.10.2026)
        "chuzhdi_zapiski": [{"chast": CHASTI.get(z.get("chast_kod"), z.get("chast_kod")),
                             "fajl": z.get("fajl", ""), "imot": _opisanie_imot(z),
                             # Визата на обединен имот носи ВСИЧКИТЕ стари номера —
                             # операторът ги приема наведнъж. (02.10.2026)
                             "identifikatori": identifikatori_v(z)} for z in chuzhdi],
        "nash_imot": _opisanie_imot(zapiski[0]) if (chuzhdi and zapiski) else "",
        # Тук са, но на друг строеж — операторът може да ги премести.
        "drug_stroezh_zapiski": [{"chast": CHASTI.get(z.get("chast_kod"), z.get("chast_kod")),
                                  "fajl": z.get("fajl", ""), "obekt": z.get("obekt", ""),
                                  "vid": vid_na_stroezh(z.get("obekt"))} for z in drug_stroezh],
        "nash_vid_stroezh": (vid_na_stroezh(ime_na_stroezha)
                             or (vid_na_stroezh(zapiski[0].get("obekt")) if zapiski else "")),
        # Няма мнозинство (напр. две записки, два имота) — не гадаем кой е нашият.
        "imotat_e_neyasen": neyasno,
        "imoti_v_papkata": (sorted({_opisanie_imot(z) for z in vsichki if _imot_znaci(z)})
                            if neyasno else []),
        "mahnati_chuzhdi": sum(int(z.get("mahnati_chuzhdi") or 0) for z in zapiski),
        "chasti_prochetini": [{"kod": k, "ime": CHASTI.get(k, k)} for k in prochetini],
        "chasti_lipsvat": [{"kod": k, "ime": CHASTI[k]} for k in ochakvani if k not in prochetini],
        "shapka": shapka,
        "priznaci": sorted(priznaci.values(), key=lambda v: v["priznak"]),
        "proektanti": proektanti,
        # Възложителите от челния лист → „собственик на земята“ (възложителят по
        # ЗУТ). Нейното разграничение, 01.10.2026: по ЗУТ възложителят е
        # собственикът на земята, а по договорите ѝ е друг (инвеститорът).
        "sobstvenici_ot_zapiski": sorted({
            str(v).strip() for z in zapiski for v in (z.get("vazlozhiteli") or [])
            if str(v or "").strip()}),
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

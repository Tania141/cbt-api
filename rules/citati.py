"""Сверка на цитат: този текст съществува ли буквално на този адрес в закона.

ЗАЩО ТАКА, А НЕ ОБРАТНОТО
-------------------------
Операторът го формулира по-точно, отколкото аз бях предложил (09.09.2026):
„по-добре аз да копи пейст, а АИ проверява“.

Ако системата съчинява цитата, а човекът го одобрява, човекът трябва да
преглежда десетки правдоподобни неща — а правдоподобно-грешното е най-трудното
за забелязване. Ако човекът пастне, проверката става механична: съществува ли
този текст на този адрес. Това е сверка, не преценка, и точно затова може да е
на машина.

Пастът има и произход. Съчиненото няма.

КАКВО ПРАВИ И КАКВО НЕ ПРАВИ
----------------------------
Прави: намира адреса в заключения текст и сравнява дума по дума.
НЕ прави: не преценява дали цитатът е УМЕСТЕН за дадения документ. Че
чл. 137 съществува и гласи това, не значи, че е основанието за скицата от
кадастралната карта. Тази преценка остава на оператора — и е единственото,
което наистина изисква него.

Адресът се пише както се говори:

    чл. 137, ал. 1, т. 3 ЗУТ
    чл. 137, ал. 1, т. 1, б. „а“ ЗУТ
    чл. 6, ал. 2 Наредба № 1
"""
import os, re, glob, json, hashlib

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)
LOCK = os.path.join(_DIR, "citati.lock.json")

_TARSI = [
    os.path.join(os.path.dirname(_ROOT), "Закони инаредби"),
    os.path.join(os.path.dirname(_ROOT), "Закони и наредби"),
    os.path.join(_DIR, "izvori"),
    _ROOT,
]

# Съкращението, както операторът го пише в колоната „Основание“, към шаблона на
# файла. Нов източник = нов ред тук и заключване с pin_naredba.py --pin.
IZTOCHNICI = {
    "ЗУТ":          "ЗАКОН ЗА УСТРОЙСТВО НА ТЕРИТОРИЯТА*.md",
    "Наредба № 1":  "НАРЕДБА № 1*.md",
}


def path(kod):
    shablon = IZTOCHNICI.get(kod)
    if not shablon:
        return None
    for d in _TARSI:
        hit = sorted(glob.glob(os.path.join(d, shablon)))
        if hit:
            return hit[0]
    return None


def otpechatak():
    """Отпечатък на всички източници за цитати наведнъж."""
    izhod = {}
    for kod in IZTOCHNICI:
        p = path(kod)
        if not p:
            continue
        # Краят на реда не е съдържание. Windows дава CRLF, git на Linux дава
        # LF — ако отпечатъкът виси на това, източникът се „променя“ при
        # деплой, без нито една дума да е различна. Другите четци четат
        # текстово и затова не пострадаха; този четеше байтово.
        raw = open(p, "rb").read().replace(b"\r\n", b"\n")
        izhod[kod] = {"fajl": os.path.basename(p),
                      "sha256": hashlib.sha256(raw).hexdigest(),
                      "chlenove": len(re.findall(r"Чл\.\s*\d+", raw.decode("utf-8")))}
    return izhod


def zaklyucheno():
    if not os.path.isfile(LOCK):
        return False, "няма записан отпечатък"
    sega, star = otpechatak(), json.load(open(LOCK, encoding="utf-8"))
    lipsvat = [k for k in IZTOCHNICI if k not in sega]
    if lipsvat:
        return False, "липсват източници: " + ", ".join(lipsvat)
    r = [f"{k}: текстът е променен" for k in sega
         if sega[k]["sha256"] != star.get(k, {}).get("sha256")]
    novi = [k for k in sega if k not in star]
    return (not r and not novi), "; ".join(r + [f"нов източник: {k}" for k in novi]) or "съвпада"


# ── Адрес ────────────────────────────────────────────────────────────────────

_ADRES = re.compile(
    r"чл\.\s*(?P<chl>\d+[а-я]?)"
    r"(?:\s*,?\s*ал\.\s*(?P<al>\d+))?"
    r"(?:\s*,?\s*т\.\s*(?P<t>\d+))?"
    r"(?:\s*,?\s*б\.\s*[„\"']?(?P<b>[а-я])[“\"']?)?"
    r"\s*(?:от\s+)?(?P<izt>.*)$",
    re.I)


def razbor(adres):
    """„чл. 137, ал. 1, т. 3 ЗУТ“ → съставните части."""
    m = _ADRES.search((adres or "").strip())
    if not m:
        return None
    d = m.groupdict()
    izt = (d.pop("izt") or "").strip(" .,").rstrip()
    # Съкращението се разпознава свободно: „ЗУТ“, „от ЗУТ“, „Наредба №1“.
    kod = None
    for k in IZTOCHNICI:
        if re.sub(r"\s|№", "", k).lower() in re.sub(r"\s|№", "", izt).lower():
            kod = k
            break
    d["iztochnik"] = kod
    d["opis"] = izt
    return d


# ── Изрязване на текста по адрес ─────────────────────────────────────────────

def _bez_tagove(t):
    """Огледалото на Наредба № 1 е обвито в <span class="mark">. Махаме ги —
    иначе редът не започва с „Чл.“ и адресът не се намира."""
    return re.sub(r"<[^>]+>", "", t)


def _chist(t):
    """Маха форматирането на markdown-огледалото, пази думите."""
    t = _bez_tagove(t).replace("\\\n", " ").replace("\\", "")
    t = re.sub(r"\*\*|\*|_", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _bez_dv(t):
    """Маха бележките за изменения — „(Изм. - ДВ, бр. 65 от 2003 г.)“."""
    return re.sub(r"\((?:изм|доп|нова|отм|предишн)[^)]*\)", "", t, flags=re.I).strip()


def parche(kod, chl, al=None, t=None, b=None):
    """Текстът на посочения адрес, или None ако адресът не съществува."""
    p = path(kod)
    if not p:
        return None
    s = _bez_tagove(open(p, encoding="utf-8").read())

    m = re.search(r"^\s*Чл\.\s*%s\.(?!\d)" % re.escape(chl), s, re.M)
    if not m:
        return None
    kraj = re.search(r"^\s*Чл\.\s*\d+[а-я]?\.", s[m.end():], re.M)
    tyalo = s[m.start(): m.end() + (kraj.start() if kraj else len(s))]

    if al:
        # Алинеята в началото на ред идва екранирана от markdown: „\(2\)“.
        # В средата на ред стои гола: „(1)“. Търсим и двата вида.
        alin = lambda n: r"\\?\(%s\\?\)" % n
        m2 = re.search(alin(al), tyalo)
        if not m2:
            return None
        sled = re.search(alin(int(al) + 1), tyalo[m2.end():])
        tyalo = tyalo[m2.start(): m2.end() + (sled.start() if sled else len(tyalo))]

    if t:
        m3 = re.search(r"(?:^|\s)%s\\?\.\s" % t, tyalo, re.M)
        if not m3:
            return None
        sled = re.search(r"(?:^|\s)%d\\?\.\s" % (int(t) + 1), tyalo[m3.end():], re.M)
        tyalo = tyalo[m3.start(): m3.end() + (sled.start() if sled else len(tyalo))]

    if b:
        m4 = re.search(r"(?:^|\s)%s\)\s" % re.escape(b), tyalo, re.M)
        if not m4:
            return None
        sledvashta = chr(ord(b) + 1)
        sled = re.search(r"(?:^|\s)%s\)\s" % sledvashta, tyalo[m4.end():], re.M)
        tyalo = tyalo[m4.start(): m4.end() + (sled.start() if sled else len(tyalo))]

    return _chist(tyalo)


# ── Сверка ───────────────────────────────────────────────────────────────────

def sveri(adres, tekst):
    """Съществува ли `tekst` буквално на адрес `adres` в заключения източник.

    Връща състояние: „съвпада“ · „съвпада без бележките за изменения“ ·
    „не съвпада“ · „адресът не съществува“ · „непознат източник“.
    """
    ok, prichina = zaklyucheno()
    if not ok:
        return {"sastoyanie": "източникът не е заключен", "podrobno": prichina}

    a = razbor(adres)
    if not a:
        return {"sastoyanie": "адресът не се разчита",
                "podrobno": "очаква се напр. „чл. 137, ал. 1, т. 3 ЗУТ“"}
    if not a["iztochnik"]:
        return {"sastoyanie": "непознат източник",
                "podrobno": f"„{a['opis']}“ не е сред: " + ", ".join(IZTOCHNICI)}

    izvor = parche(a["iztochnik"], a["chl"], a["al"], a["t"], a["b"])
    if izvor is None:
        return {"sastoyanie": "адресът не съществува",
                "podrobno": f"в {a['iztochnik']} няма такова място"}

    if not (tekst or "").strip():
        return {"sastoyanie": "няма пастнат текст", "izvor": izvor}

    nash, tehen = _chist(tekst), izvor
    if nash.lower() in tehen.lower():
        return {"sastoyanie": "съвпада", "izvor": izvor}
    if _bez_dv(nash).lower() in _bez_dv(tehen).lower():
        return {"sastoyanie": "съвпада без бележките за изменения", "izvor": izvor}
    return {"sastoyanie": "не съвпада", "izvor": izvor,
            "podrobno": "текстът не се среща на този адрес — сгрешен адрес, "
                        "друга редакция или пастът е от съседна точка"}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for kod in IZTOCHNICI:
        p = path(kod)
        print(f"{kod:14} → {os.path.basename(p) if p else 'НЕ Е НАМЕРЕН'}")
    print("заключено:", zaklyucheno()[1])

"""Наредба № 1 за номенклатурата на видовете строежи — четец на разпоредби.

НЕ кодираме наредбата. Разчитаме цитата от доклада, намираме точния текст на
разпоредбата и го показваме срещу описанието на обекта. Така проверката работи
еднакво за сгради, линейни обекти, културни ценности и всичко останало — защото
не класифицира, а сверява едно твърдение срещу една разпоредба.

ЗАКЛЮЧЕН ИЗТОЧНИК
-----------------
Извличането стъпва на структурата на конкретния .md файл. Друга редакция или
друго форматиране може тихо да върне грешен текст — а това е по-лошо от липса
на проверка, защото носи авторитет.

Затова файлът е заключен с отпечатък в `naredba1.lock.json`:
  · sha256 на съдържанието
  · структура: за всеки член колко алинеи и по колко точки

При разминаване четецът ОТКАЗВА да работи и правилата връщат „не може да се
провери“. Отключването е съзнателно действие:

    python tools/pin_naredba.py        показва какво се е променило
    python tools/pin_naredba.py --pin  записва новия отпечатък

Отпечатъкът се пази в git, затова смяната на наредбата се вижда в diff.
"""
import os, re, json, hashlib, glob

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)
LOCK = os.path.join(_DIR, "naredba1.lock.json")

# Наредбата стои до хранилището, в C:\project\Закони инаредби
_TARSI = [
    os.path.join(os.path.dirname(_ROOT), "Закони инаредби"),
    os.path.join(os.path.dirname(_ROOT), "Закони и наредби"),
    _ROOT,
]

# Категориите и членовете, които ги определят. Ако някой от тях изчезне,
# файлът не е това, което очакваме.
CHLENOVE = {2: "първа", 4: "втора", 6: "трета", 8: "четвърта", 10: "пета"}


def path():
    for d in _TARSI:
        hit = glob.glob(os.path.join(d, "НАРЕДБА № 1*.md"))
        if hit:
            return hit[0]
    return None


def _text(p):
    raw = open(p, encoding="utf-8").read()
    t = " ".join(re.sub(r"<[^>]+>", "", l).strip() for l in raw.splitlines() if l.strip())
    # Бележките за изменения се махат — те не са част от разпоредбата и се
    # менят при всяко изменение на ДВ. Регистърът е без значение („Доп.“/„доп.“).
    t = re.sub(r"\((?:изм\.|доп\.|нова|нов|отм\.|предишен|предишна)[^)]*\)", " ",
               t, flags=re.IGNORECASE)
    return raw, re.sub(r"\s+", " ", t)


def _chlen(t, n):
    m = re.search(rf"Чл\. {n}\..*?(?=Чл\. {n + 1}\.|$)", t, re.S)
    return m.group(0) if m else None


def _alinei(body):
    """Всички алинеи на член — {номер: текст}."""
    poz = [(int(m.group(1)), m.start()) for m in re.finditer(r"\((\d+)\)", body)]
    out = {}
    for i, (n, s) in enumerate(poz):
        e = poz[i + 1][1] if i + 1 < len(poz) else len(body)
        if n not in out:                      # първото срещане е същинската алинея
            out[n] = body[s:e].strip()
    return out


def _tochki(al_text):
    """Номерираните точки в алинея — {номер: текст}."""
    poz = [(int(m.group(1)), m.start(), m.end()) for m in re.finditer(r"(?:^|\s)(\d+)\.\s", al_text)]
    out = {}
    for i, (n, s, e) in enumerate(poz):
        kraj = poz[i + 1][1] if i + 1 < len(poz) else len(al_text)
        if n not in out:
            out[n] = re.sub(r"\s+", " ", al_text[e:kraj]).strip(" ;.")
    return out


def struktura(t):
    """Структурен отпечатък: за всеки член — по колко точки има всяка алинея."""
    s = {}
    for n in CHLENOVE:
        body = _chlen(t, n)
        if not body:
            continue
        s[str(n)] = {str(a): len(_tochki(txt)) for a, txt in sorted(_alinei(body).items())}
    return s


def otpechatak():
    """Текущият отпечатък на файла, какъвто е на диска."""
    p = path()
    if not p:
        return None, "Наредба № 1 не е намерена до хранилището."
    raw, t = _text(p)
    return {
        "file": os.path.basename(p),
        "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "struktura": struktura(t),
    }, None


def _lock():
    if not os.path.isfile(LOCK):
        return None
    return json.load(open(LOCK, encoding="utf-8"))


def razliki(nov, star):
    """Какво се е променило — на човешки език."""
    if not star:
        return ["Няма записан отпечатък."]
    out = []
    if nov["sha256"] != star["sha256"]:
        out.append("Съдържанието на файла е различно.")
    for chl, kat in CHLENOVE.items():
        a, b = nov["struktura"].get(str(chl)), star["struktura"].get(str(chl))
        if a is None:
            out.append(f"Чл. {chl} ({kat} категория) вече не се намира.")
        elif b is None:
            out.append(f"Чл. {chl} ({kat} категория) е нов.")
        elif a != b:
            for al in sorted(set(a) | set(b)):
                if a.get(al) != b.get(al):
                    out.append(f"Чл. {chl}, ал. {al}: беше {b.get(al, '—')} точки, сега {a.get(al, '—')}.")
    return out


class Naredba:
    """Заключен четец. Ако източникът не съвпада с отпечатъка — не работи."""

    def __init__(self):
        self.ok = False
        self.prichina = None
        self._t = None
        nov, err = otpechatak()
        if err:
            self.prichina = err
            return
        star = _lock()
        if not star:
            self.prichina = ("Наредба № 1 не е заключена — липсва naredba1.lock.json. "
                             "Пусни: python tools/pin_naredba.py --pin")
            return
        r = razliki(nov, star)
        if r:
            self.prichina = ("Наредба № 1 е различна от заключената: " + " ".join(r) +
                             " Сверката трябва да се потвърди наново: python tools/pin_naredba.py")
            return
        self._t = _text(path())[1]
        self.ok = True

    def razporedba(self, chl, al, t_no=None):
        """Текстът на цитираната разпоредба, или (None, причина)."""
        if not self.ok:
            return None, self.prichina
        body = _chlen(self._t, chl)
        if not body:
            return None, f"Наредба № 1 няма чл. {chl}."
        alinei = _alinei(body)
        if al not in alinei:
            return None, f"Чл. {chl} няма ал. {al} (има {len(alinei)})."
        al_text = alinei[al]
        zaglavie = re.sub(r"^\(\d+\)\s*", "", re.split(r"\bса\s*:|\bсе\s*:", al_text)[0]).strip(" ,-—–")
        if t_no is None:
            return {"zaglavie": zaglavie, "tochka": None}, None
        tt = _tochki(al_text)
        if t_no not in tt:
            return None, f"Чл. {chl}, ал. {al} няма т. {t_no} (има {len(tt)} точки)."
        return {"zaglavie": zaglavie, "tochka": tt[t_no]}, None


# Прагове в текста на разпоредбата — сравняват се с числата на обекта.
PRAGOVE = [
    (re.compile(r"до\s+([\d\s]+)\s*кв\.?\s*м"),            "РЗП", "кв. м", "max"),
    (re.compile(r"от\s+([\d\s]+)\s+до\s+([\d\s]+)\s*кв\.?\s*м"), "РЗП", "кв. м", "range"),
    (re.compile(r"до\s+(\d+)\s+места"),                     "места", "места", "max"),
    (re.compile(r"от\s+(\d+)\s+до\s+(\d+)\s+места"),        "места", "места", "range"),
    (re.compile(r"до\s+(\d+)\s+работни места"),             "работни места", "места", "max"),
    (re.compile(r"от\s+(\d+)\s+до\s+(\d+)\s+работни места"), "работни места", "места", "range"),
    (re.compile(r"до\s+(\d+)\s*kV"),                        "напрежение", "kV", "max"),
]


def pragove(text):
    """Числовите прагове, които разпоредбата поставя."""
    out = []
    for rex, kakvo, edinica, vid in PRAGOVE:
        for m in rex.finditer(text or ""):
            chisla = [int(g.replace(" ", "")) for g in m.groups() if g]
            out.append({"kakvo": kakvo, "edinica": edinica, "vid": vid,
                        "chisla": chisla, "tekst": m.group(0).strip()})
    return out

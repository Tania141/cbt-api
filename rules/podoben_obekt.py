# -*- coding: utf-8 -*-
u"""Подобен обект — какво изрежда завършеният Акт 15 или ОД (24.11.2026).

Заданието: `ДА ПРОЧЕТА/ЗАДАНИЕ-ПОДОБЕН-ОБЕКТ.md` в хранилището на ПВА, стъпка
4а — САМО чете и показва. Нищо в чеклиста не се мени.

Чете се С КОДА, без АИ: .docx има текст, а актовете на оператора са подредени
(раздели със заглавия, документ на ред). Затова е безплатно и всеки ред носи
„откъде“ — дословния текст и раздела, в който е стоял.

Какво НЕ прави:
  · не слива синоними („становище“ и „писмо“ остават два реда) — това е жест
    на оператора (4б);
  · не решава кое се изисква — само казва какво го е имало;
  · не чете .doc, PDF и сканове — за тях казва защо.

Как разпознава:
  · ДОКУМЕНТ е ред, който (след тирето, номерацията и „За обекта е заверен…“)
    започва с име на документ — `_IMENA` по-долу. Ред, който не започва така,
    е описание и не се брои.
  · РАЗДЕЛ е заглавие: завършва на „:“, изцяло е получер или е номериран
    „1.3.“ — и не е документ.
  · ЕДИН И СЪЩ документ, изреден на две места (при възложителите и пак в 1.1;
    в „законосъобразното започване“ и пак в описа), се брои веднъж — по името
    и първия си номер или дата.
"""
import io
import re

# Как започва ред, който е документ. Подредено от по-дългото към по-късото —
# „нотариален акт“ преди „акт“.
_IMENA = [
    r"нотари?ал[ен]+\s+акт", r"пълномощн", r"удостоверени", r"разрешени[ея]\s+за\s+строеж",
    r"разрешение\s+за\s+ползване", r"виза", r"одобрен", r"технически\s+(инвестиционен\s+)?проект",
    r"технически\s+паспорт", r"инвестиционен\s+проект", r"работен\s+проект", r"констативен\s+акт",
    r"акт(ове)?\b", r"протокол", r"заповедна\s+книга", r"заповед", r"договор", r"анекс", r"писмо",
    r"становище", r"скица", r"сертификат", r"декларац", r"диплома", r"застраховк",
    r"застрахователн", r"полица", r"списък", r"бетонов\s+дневник", r"дневник", r"гаранционна\s+карта",
    r"ревизионна\s+книга", r"окончателен\s+доклад", r"решение", r"съгласуван",
    r"оценка\s+за\s+съответствие", r"енергиен\s+сертификат", r"паспорт", r"квитанци",
    r"контролно\s+заснемане", r"геодезическо\s+заснемане", r"екзекутив",
    r"инструкци", r"изпитвателн",
]
_IME_RE = re.compile(r"^(?:" + "|".join(_IMENA) + r")", re.I)

# Начало, което не е част от името: „За обекта е заверен Протокол…“.
_PREFIKS = re.compile(
    r"^(?:[-–—•·*▪►✓]+\s*|\(?[0-9]+(?:\.[0-9]+)*[.)]?\s+|[а-я]\)\s+)*"
    r"(?:за\s+обекта\s+(?:е|са)\s+заверен[аио]?\s+|заверен[аио]?\s+|издаден[аио]?\s+е\s+|"
    r"съставен[аио]?\s+(?:е|са)\s+)?", re.I)

_DATA = r"\d{1,2}\s*\.\s*\d{1,2}\s*\.+\s*(?:19|20)\d{2}"
_DATA_RE = re.compile(_DATA)
_NOMER_RE = re.compile(r"№+\s*[^\s,;]+(?:\s*[/–-]\s*[^\s,;]+)*")
_BROY_RE = re.compile(r"(\d+)\s*(?:бр\b|бр\.|броя|брой)", re.I)
_OBRAZEC_RE = re.compile(
    r"^(?:констативен\s+)?(акт|протокол)[а-я]*\.?\s*,?\s*\(?\s*(?:образец|обр\.?)\s*\)?\s*(?:№\s*)?(\d+[а-я]?)\b", re.I)
_CHAST_RE = re.compile(r"по\s+част\s*[:\-–]?\s*[„“\"”]?([А-Яа-яA-Za-z]+)", re.I)


# Имена, след които останалото е кой и кога — не друг документ.
_KANON = [
    (r"^заповедна\s+книга\b", "Заповедна книга"),
    (r"^бетонов\s+дневник\b", "Бетонов дневник"),
    (r"^разрешени[ея]\s+за\s+строеж\b", "Разрешение за строеж"),
    (r"^диплома\s+на\s+техническ", "Диплома на техническия ръководител"),
    (r"^заповед\b.{0,40}назначаване\s+на\s+техническ", "Заповед за назначаване на технически ръководител"),
]


def _norm(s):
    s = str(s or "").replace("\xa0", " ").replace("­", "")
    return re.sub(r"\s+", " ", s).strip()


def _klyuch(ime):
    k = _norm(ime).lower()
    k = re.sub(r"[„“”\"«»'`()]", "", k)
    return re.sub(r"\s+", " ", k).strip()


def _data_kanon(s):
    m = re.match(r"(\d{1,2})\s*\.\s*(\d{1,2})\s*\.+\s*(\d{4})", s)
    return "%02d.%02d.%s" % (int(m.group(1)), int(m.group(2)), m.group(3)) if m else s


def _ime(bez_prefiks):
    u"""Името, по което се трупа: „Акт обр. 7“, „Нотариален акт“, „Писмо от …“."""
    t = _norm(bez_prefiks)
    for izraz, kanon in _KANON:
        if re.match(izraz, t, re.I):
            return kanon
    m = _OBRAZEC_RE.match(t)
    if m:
        ime = "%s обр. %s" % (m.group(1).capitalize(), m.group(2).lower())
        ch = _CHAST_RE.search(t)
        if ch:
            ime += " по част " + ch.group(1)
        return ime
    # Номерът първо — „№ М – 1192 / 05.04.2022г.“ е цял номер с датата си.
    t = re.sub(r"\[[^\]]*\]", " ", t)              # „от [..........] 2025г.“
    t = _NOMER_RE.sub(" ", t)
    t = re.sub(r"(?:\s(?:от|на|до))?\s*" + _DATA + r"\.?\s*(?:г\.?|год\.?)?(?=\s|$|[,;.])", " ", t)
    t = re.split(r"[,;:(]|\s[–—-]\s|\s(?:заверен|издаден|вписан|валидн|на\s+нотариус|с\s+вх\.)", t)[0]
    t = re.sub(r"(?<!\S)г\.?(?!\S)", " ", t)
    dumi = _norm(t).split(" ")[:12]
    while dumi and dumi[-1].lower() in ("от", "на", "с", "за", "и", "в", "по", "към", "№", "-", "–", "/", "."):
        dumi.pop()
    return " ".join(dumi).strip(" ./") or _norm(bez_prefiks)[:60]


def _zaglavie_li(t, cyal_bold, nomeriran):
    if len(t) > 160:
        return False
    if re.match(r"^\d+(\.\d+)+\.?\s+\S", t) or re.match(r"^\d+\.\s+[А-Я]", t):
        return True
    if t.endswith(":"):
        return True
    return cyal_bold and len(t) <= 120


def _zaglavie_a_ne_dokument(t, bold, nomeriran=False):
    u"""„1.3. Актове и протоколи…:“, „Договори със снабдителните дружества:“,
    „КОНСТАТИВЕН АКТ“ — почват с име на документ, но са заглавия."""
    bukvi = re.sub(r"[^A-Za-zА-Яа-я]", "", t)
    if bukvi and bukvi.isupper() and len(t) < 60:
        return True
    ima_nomer = "№" in t or bool(_DATA_RE.search(t)) or bool(re.search(r"образец\s*\d|обр\.?\s*\d", t, re.I))
    # „1.1.9. Заверен Протокол (Образец) 3“ — три нива номерация е ред от списък (ОД).
    if re.match(r"^\d+\.\d+\.\d+", t):
        return False
    if ima_nomer:
        return False
    if re.match(r"^\d+(\.\d+)+\.?\s", t) or t.endswith(":"):
        return True
    # „Актове и протоколи съставени по време на строителството“, „Изпитвателни
    # протоколи“ (Лешникова гора) — множествено, без номер, не в списък.
    if not nomeriran and re.match(r"^(актове|протоколи|декларации|изпитвателни|документи|договори|"
                                  r"сертификати|документация)\b", t, re.I) and not re.search(r"образец\s*\d|обр\.\s*\d", t, re.I):
        return True
    return False


def _abzaci(doc):
    u"""Абзаците и таблиците по реда им в документа."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    for el in doc.element.body.iterchildren():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "p":
            p = Paragraph(el, doc)
            t = _norm(p.text)
            if not t:
                continue
            runove = [r for r in p.runs if r.text.strip()]
            yield ("p", t, bool(runove) and all(r.bold for r in runove),
                   p._p.pPr is not None and p._p.pPr.numPr is not None)
        elif tag == "tbl":
            yield ("t", Table(el, doc), False, False)


def _vid_na_dokumenta(tekst):
    u"""По началото: Акт 15 казва „окончателен доклад“ чак в края си, а ОД
    пише заглавието си и с разредени букви („О К О Н Ч А Т Е Л Е Н“)."""
    t = re.sub(r"\s", "", tekst[:4000].upper())
    if "ОКОНЧАТЕЛЕНДОКЛАД" in t or "ГОДНОСТТАЗАПОЛЗВАНЕ" in t:
        return "Окончателен доклад"
    if "ГОДНОСТТАЗАПРИЕМАНЕ" in t or "ОБРАЗЕЦ15" in t:
        return "Акт 15"
    return ""


def procheti_docx(raw, ime=""):
    u""".docx → {vid, stroezh, godina, redove, razdeli}. Без АИ."""
    from docx import Document
    doc = Document(io.BytesIO(raw))
    vsichko, stroezh = [], ""
    razdel, razdeli = "", []
    redove, po_id = [], {}
    sledva_stroezh = False

    for vid, x, bold, nomeriran in _abzaci(doc):
        if vid == "t":
            kletki = [[_norm(c.text) for c in r.cells] for r in x.rows]
            for r in kletki:
                vsichko.append(" ".join(r))
                if not stroezh and r and re.match(r"^строеж\s*:?$", r[0], re.I) and len(r) > 1:
                    stroezh = r[1]
            # Таблица с материали: един ред в списъка, бройката — редовете ѝ.
            glava = " ".join(kletki[0]).lower() if kletki else ""
            if re.search(r"материал|издели", glava) and re.search(r"производител|документ|деклар|сертиф", glava):
                broy = sum(1 for r in kletki[1:] if any(r))
                _dobavi(redove, po_id, razdel, "Декларации за вложените материали (таблица)",
                        "таблица: " + " · ".join(kletki[0]), broy_izrichen=broy)
            continue
        t = x
        vsichko.append(t)
        if not stroezh:
            m = re.match(r"^строеж\s*:\s*(.+)", t, re.I)
            if m:
                stroezh = m.group(1).strip()
            elif sledva_stroezh:
                stroezh = t
            sledva_stroezh = bool(re.search(r"годността\s+за\s+ползване\s+на\s+строеж\s*:?$", t, re.I))
        bez = _PREFIKS.sub("", t, count=1).strip()
        ime_dok = bool(_IME_RE.match(bez))
        zagl_dok = ime_dok and _zaglavie_a_ne_dokument(t, bold, nomeriran)
        if ime_dok and not zagl_dok:
            _dobavi(redove, po_id, razdel, _ime(bez), t)
        elif zagl_dok or _zaglavie_li(t, bold, nomeriran):
            razdel = t.rstrip(":").strip()
            if razdel not in razdeli:
                razdeli.append(razdel)

    tekst = "\n".join(vsichko)
    godini = [int(_data_kanon(d)[-4:]) for d in _DATA_RE.findall(tekst)]
    # Най-късната дата, но не в бъдещето — „валиден до 08.01.2028“ не е годината на акта.
    from datetime import date
    godina = max([g for g in godini if g <= date.today().year] or [0]) or None
    for r in redove:
        r["dati"] = sorted(set(r["dati"]), key=lambda d: (d[-4:], d[3:5], d[:2]))
        r["ot"] = r["dati"][0] if r["dati"] else ""
        r["do"] = r["dati"][-1] if len(r["dati"]) > 1 else ""
        r["broy"] = r.pop("_izrichen") or len(r["dosloven"])
        r.pop("_vidyani", None)
    # Категорията — само ПРЕДЛОЖЕНИЕ с изречението (полето е на ръка: сбъркана
    # категория сменя законовия под и не личи). 4в, 25.11.2026.
    kat = None
    m = re.search(r"\b(първа|втора|трета|четвърта|пета)\s+категория", tekst, re.I)
    if m:
        cifra = {"първа": 1, "втора": 2, "трета": 3, "четвърта": 4, "пета": 5}[m.group(1).lower()]
        nach = tekst.rfind("\n", 0, m.start()) + 1
        kraj = tekst.find("\n", m.end())
        kat = {"cifra": cifra, "izrechenie": tekst[nach:kraj if kraj > 0 else None].strip()[:200]}
    return {"fajl": ime, "vid": _vid_na_dokumenta(tekst), "stroezh": stroezh,
            "godina": godina, "redove": redove, "razdeli": razdeli, "kategoria_v_teksta": kat,
            "chetec": "кодът — .docx има текст, без АИ"}


def _dobavi(redove, po_id, razdel, ime, dosloven, broy_izrichen=None):
    k = _klyuch(ime)
    nomer = _NOMER_RE.search(dosloven)
    dati = [_data_kanon(d) for d in _DATA_RE.findall(dosloven)]
    # Кой е ТОЗИ документ: името + първият номер, иначе първата дата.
    # „№1243Е/09.07.2025“ и „№1243Е на 09.07.2025“ са една книга — номерът е до „/“.
    edin = k + "|" + (re.sub(r"[^0-9A-Za-zА-Яа-я]", "", nomer.group(0).split("/")[0]) if nomer
                      else (dati[0] if dati else ""))
    r = po_id.get(k)
    if r is None:
        r = {"ime": ime, "klyuch": k, "razdel": razdel, "razdeli": [], "dosloven": [],
             "dati": [], "_izrichen": None, "_vidyani": set()}
        po_id[k] = r
        redove.append(r)
    if razdel and razdel not in r["razdeli"]:
        r["razdeli"].append(razdel)
    # Разделът е последният, в който е изреден: описът е накрая (линейните),
    # а при сградата 1.1–1.5 идват след възложителите.
    if razdel:
        r["razdel"] = razdel
    if edin in r["_vidyani"] and not edin.endswith("|"):
        return
    if edin.endswith("|") and dosloven in r["dosloven"]:
        return
    if edin.endswith("|") and r["dosloven"] and not dati and not nomer:
        return                                    # същото, без номер — изредено пак
    r["_vidyani"].add(edin)
    r["dosloven"].append(dosloven)
    r["dati"].extend(dati)
    b = broy_izrichen
    if b is None:
        m = _BROY_RE.search(dosloven)
        b = int(m.group(1)) if m else None
    if b:
        r["_izrichen"] = (r["_izrichen"] or 0) + b


# ── Ред от днешния чеклист — само когато е сигурно ─────────────────────────────

def red_v_chekliste(ime, redove_chek):
    u"""Кой ред от днешния чеклист отговаря на името — или празно.

    Тясно нарочно (като `_red_po_zaglavie`): по-добре „няма ред“, отколкото
    близък ред. Синонимите са жест на оператора (4б).
    """
    from .sloy2 import _red_po_zaglavie
    r, kak = _red_po_zaglavie({"vid": ime}, redove_chek)
    if r:
        return r, kak
    # Каноничните имена („Заповедна книга“) — по началото на реда („Заповедна
    # книга на строежа“). Само те: „Нотариален акт“ по началото би хванал
    # „Нотариален акт за учредено право на строеж“, а е друг документ.
    if ime in {k for _, k in _KANON}:
        pasvat = [x for x in redove_chek if _klyuch(x) == _klyuch(ime) or _klyuch(x).startswith(_klyuch(ime) + " ")]
        if len(pasvat) == 1:
            return pasvat[0], "системата — по началото на реда"
    m = re.match(r"^(акт|протокол)\s+обр\.\s*(\d+[а-я]?)", ime, re.I)
    if m:
        n = lambda x: _klyuch(x).replace("образец", "обр.")
        ch_ime = _CHAST_RE.search(ime)
        chast = ch_ime.group(1).lower() if ch_ime else ""

        def pasva(x):
            # Редът трябва САМ да е актът/протоколът: „Заверено копие на
            # констативен акт обр. 3 от общината“ е друг документ (28.10.2026).
            if not re.match(r"^(акт|протокол)", n(x)):
                return False
            if not re.search(r"(?:\bобр\.?\s*|\b" + m.group(1).lower() + r"\s+)" + re.escape(m.group(2).lower())
                             + r"(?![\dа-я])", n(x)):
                return False
            # „Акт обр. 12 по част ВиК“ НЕ е редът „… обр. 12 по част архитектура“.
            ch = _CHAST_RE.search(x)
            return not (chast and ch and ch.group(1).lower() != chast)
        pasvat = [x for x in redove_chek if pasva(x)]
        if len(pasvat) == 1:
            return pasvat[0], "системата — по номера на образеца"
    return "", ""


def procheti(ime, data_b64, redove_chek=None):
    import base64
    ext = (ime or "").lower().rsplit(".", 1)[-1] if "." in (ime or "") else ""
    if ext == "doc":
        raise ValueError("стар формат .doc — запиши го като .docx (Word: Запиши като → .docx)")
    if ext != "docx":
        raise ValueError("засега се четат само .docx — без АИ и безплатно; PDF и сканове идват после")
    if not data_b64:
        raise ValueError("празен файл")
    rez = procheti_docx(base64.b64decode(data_b64), ime)
    if redove_chek:
        for r in rez["redove"]:
            r["cheklist_red"], r["cheklist_kak"] = red_v_chekliste(r["ime"], redove_chek)
    return rez

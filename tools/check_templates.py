"""
check_templates.py — проверка на шаблоните срещу КОНВЕНЦИЯ.md

Пуска се от корена на cbt-api:
    python tools/check_templates.py

Две нива:
  ГРЕШКА   — нарушение на конвенцията; изходен код 1 (спира commit)
  ВНИМАНИЕ — за човешка преценка; не спира нищо
"""
import sys, os, re, glob

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docx import Document
from cbt_docx import build_placeholders

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_DIR = os.path.join(ROOT, "templates")

MARKER = re.compile(r"\{\{[^}]+\}\}")

# Маркер, който КОДЪТ нарочно записва: repl["{{Нещо}}"] = …
# Ако никой шаблон не го иска, стойността се изчислява и се изхвърля мълчаливо.
# Точно това стана на 02.09 със Заповедната книга: endpoint-ът пълнеше
# {{Заповедна_Номер}}, а шаблонът вече искаше {{ЗК_Номер}}. Номерът, въведен от
# оператора, не стигаше до документа. Като „сираче“ не се забеляза — сирачетата
# са близо шейсет и са безобидни, защото никой не се старае да ги попълни.
WRITTEN_MARKER = re.compile(r"""\w+\[\s*["'](\{\{[^}]+\}\})["']\s*\]\s*=""")
CODE_FILES = ("api.py", "cbt_docx.py")

# ── ГРЕШКИ: шаблонът дублира работата на кода ────────────────────────────────
# Блоковите маркери сами носят цялата фраза — пред тях не се пише нищо.
TITLE_BEFORE_MARKER = re.compile(r"(инж\.|арх\.|проф\.|доц\.|д-р)\s*\{\{")
PRED_BEFORE_BLOCK   = re.compile(r"представлявано от\s*\{\{[^}]*(Блок|Подписва)")
WRAPPED_REDOVE      = re.compile(r"[.\(]\s*\{\{[^}]*Подписва_Редове\}\}")
# Забележка: „Кота цокъл +/-0,00 = {{Kota_Cokul}}“ НЕ е дублиране — относителната
# кота на цокъла винаги е ±0,00, маркерът носи абсолютната (Вариант Б1, 29.07.2026).

# ── ВНИМАНИЕ: за човешко око ─────────────────────────────────────────────────
# Едно и също лице, изписано различно в РЕДОВЕ ОТ ЕДИН И СЪЩ ВИД.
# (дефектът от 13.08: „по част Архитектура" веднъж с пълно име, веднъж с _1и3)
SIBLING_LINE = re.compile(r"^\s*\d+\s*[.)]\s*(по част|\.{3,})")

# Подписен ред: има поле за подпис (точки или долни черти) преди маркера.
# Само там е допустима кратката форма _1и3 — в описателен ред се пише пълното
# име. Разграничението е решено на 08.09.2026 върху двата еталона.
PODPISEN_RED = re.compile(r"[.…_]{6,}")

# ── ГРЕШКИ по стиловия стандарт (08.09.2026) ────────────────────────────────
PRAVI_KAVICHKI = re.compile(r'"')          # само български „ “
BUKVALNA_CHERTA = re.compile(r"\|")        # остатък от таблица в текста
KRATKA_V_OPISATELEN = re.compile(r"\{\{[^}]+_1и3\}\}")
# Повторена буква в подписен блок: „В. Строителя … В. Геодезист“
BUKVA_V_PODPIS = re.compile(r"^\s*([А-Я])\.\s")

DOLNI_CHERTI = re.compile(r"_{3,}")        # линия за писане — трябват точки
# Точки, залепени пред СЪДЪРЖАТЕЛЕН маркер: излизат ЗАЕДНО със стойността,
# когато тя е попълнена. Празното поле се дава от кода (_PRAZNO в cbt_docx.py).
#
# Подписните редове са изключени: там точките са мястото за подпис, а маркерът
# казва кой се подписва — „1. Строител: ......... {{ТехРък_1и3}}“ е правилно.
TOCHKI_DO_MARKER = re.compile(r"[.…]{4,}\s*\{\{(?!\w*_1и3\}\})([^}]+)\}\}")

NAME_FAMILIES = ["ПЖ_Архитектура", "ПЖ_Конструктивна", "Конструктивна",
                 "Геодезист", "Управител", "ТехРък", "Строител_Управител"]

# Шаблони, минали през стиловия стандарт. Само те се проверяват по него.
# Списъкът расте с всеки преработен шаблон — виж КОНВЕНЦИЯ.md.
STILOVI_SHABLONI = {
    # еталоните
    "Akt_7_Template.docx",
    "Protokol_2_Combined_Template.docx",
    # първа вълна — 08.09.2026
    "Protokol_1_Template.docx",
    "template_obrazec3.docx",
    "Akt_5_Template.docx",
    "Akt_6_Template.docx",
    "Akt_8_Template.docx",
    "Akt_9_Template.docx",
    "Akt_10_Template.docx",
    "Akt_11_Template.docx",
    "Akt_12_Template.docx",
    "template_akt14_1.docx",
    # втора вълна — дългите, 08.09.2026
    "Akt_13_Template.docx",
    "Akt_15_Template.docx",
    "Akt_16_Template.docx",
    "OSIP_Template.docx",
    "Okonchatelen_Doklad_Template.docx",
    "Protokol_17_Template.docx",
    "Protokol_2a_Template.docx",
    "Zapovedna_Template1.docx",
    # Заповедната книга мина на ръка (08.09.2026): книжен сгъв вместо две
    # колони, осем A5 страници в четивен ред. Виж КОНВЕНЦИЯ.md → Книжно тяло.
    "Zapovedna_Template.docx",
}

LEGACY = {
    "Възложател_":               "правописен дублет с „а“ вместо „и“",
    "{{Кота_":                   "кирилски вариант на кота",
    "{{Репер_":                  "кирилски вариант на репер",
    " _1и3}}":                   "маркер с интервал (правописна грешка в шаблон)",
    "{{tech_director}}":         "латински вариант",
    "{{sn_konstruktivna}}":      "латински вариант",
    "{{consultant_specialists}}":"латински вариант",
}


def all_text(doc):
    parts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                parts += [p.text for p in cell.paragraphs]
    for s in doc.sections:
        parts += [p.text for p in s.header.paragraphs]
        parts += [p.text for p in s.footer.paragraphs]
    return parts


def sibling_mismatch(lines):
    """Едно семейство имена, изписано и пълно, и съкратено, в еднотипни редове.

    Подписните редове са изключени: там кратката форма е правилната. Разнобой
    има само когато двете форми се срещат в редове от един и същи вид.
    """
    out = []
    for fam in NAME_FAMILIES:
        full, short = "{{%s}}" % fam, "{{%s_1и3}}" % fam
        def sib(marker):
            return [l for l in lines
                    if SIBLING_LINE.match(l) and marker in l
                    and not PODPISEN_RED.search(l)]
        sib_full, sib_short = sib(full), sib(short)
        if sib_full and sib_short:
            out.append(f"{fam}: пълно име и _1и3 в еднотипни редове "
                       f"({len(sib_full)} и {len(sib_short)} бр.)")
    return out


def stilovi_greshki(name, lines, doc):
    """Проверки по стиловия стандарт, приет на 08.09.2026 върху двата еталона.

    Правят се само за шаблоните, вече минали през стандарта. Останалите ще
    влизат в списъка един по един, докато се преработват — иначе двайсет
    непреработени файла заглушават сигнала.
    """
    if name not in STILOVI_SHABLONI:
        return []
    out = []

    for s in doc.sections:
        if any(p.text.strip() for p in s.header.paragraphs):
            out.append("шаблонът има ХЕДЪР — стандартът е без")
        if any(p.text.strip() for p in s.footer.paragraphs):
            out.append("шаблонът има ФУТЪР — стандартът е без")

    for line in lines:
        if PRAVI_KAVICHKI.search(line):
            out.append(f'прави кавички вместо „ “: …{line.strip()[:60]}…')
        if BUKVALNA_CHERTA.search(line):
            out.append(f"буквална черта | в текста: …{line.strip()[:60]}…")
        if DOLNI_CHERTI.search(line):
            out.append(f"долни черти вместо точки: …{line.strip()[:60]}…")
        if TOCHKI_DO_MARKER.search(line):
            out.append(f"точки, залепени пред маркер — излизат заедно със "
                       f"стойността: …{line.strip()[:60]}…")
        # кратката форма в описателен ред — там се пише пълното име.
        # Изключение: редът „({{Нещо_1и3}})“ сам по себе си е името под
        # подписната линия, която стои на предишния параграф.
        if (KRATKA_V_OPISATELEN.search(line) and not PODPISEN_RED.search(line)
                and not re.fullmatch(r"\s*\(\{\{[^}]+\}\}\)\s*", line)):
            out.append(f"кратка форма _1и3 в описателен ред: …{line.strip()[:70]}…")

    # повторена буква в подписен блок
    bukvi = [(BUKVA_V_PODPIS.match(l).group(1), l) for l in lines
             if BUKVA_V_PODPIS.match(l) and PODPISEN_RED.search(l)]
    for i in range(1, len(bukvi)):
        if bukvi[i][0] == bukvi[i - 1][0]:
            out.append(f"повторена буква „{bukvi[i][0]}.“ в подписен блок: "
                       f"…{bukvi[i][1].strip()[:55]}…")
    return out


def main():
    known = set(build_placeholders({}).keys())
    files = sorted(glob.glob(os.path.join(TPL_DIR, "*.docx")))
    errors, warnings, legacy_hits, used = [], [], [], set()

    for path in files:
        name  = os.path.basename(path)
        doc   = Document(path)
        lines = [l for l in all_text(doc)]
        blob  = "\n".join(lines)
        found = set(MARKER.findall(blob))
        used |= found

        for m in sorted(found - known):
            errors.append((name, "ВИСЯЩ МАРКЕР", f"{m} — няма ключ в build_placeholders"))

        for line in lines:
            for rx, what in [(TITLE_BEFORE_MARKER, "титла пред маркер"),
                             (PRED_BEFORE_BLOCK,   "„представлявано от“ пред блоков маркер"),
                             (WRAPPED_REDOVE,      "Подписва_Редове в скоби/точки")]:
                for mm in rx.finditer(line):
                    frag = line[max(0, mm.start() - 25):mm.end() + 30].strip()
                    errors.append((name, "ДУБЛИРАНЕ", f"{what}: …{frag}…"))

        for msg in sibling_mismatch(lines):
            warnings.append((name, "РАЗНОБОЙ", msg))

        for msg in stilovi_greshki(name, lines, doc):
            errors.append((name, "СТИЛ", msg))

        for leg, why in LEGACY.items():
            if leg in blob:
                legacy_hits.append((name, leg, why))

    # Маркери, които кодът записва нарочно, а никой шаблон не иска.
    for fname in CODE_FILES:
        p = os.path.join(ROOT, fname)
        if not os.path.isfile(p):
            continue
        src = open(p, encoding="utf-8").read()
        for m in sorted(set(WRITTEN_MARKER.findall(src))):
            if m not in used:
                errors.append((fname, "МЪРТЪВ МАРКЕР",
                               f"{m} — кодът го записва, но никой шаблон не го иска; "
                               f"стойността се изхвърля мълчаливо"))

    orphans = sorted(known - used)

    print(f"Проверени шаблони: {len(files)}\n")

    if errors:
        print("── ГРЕШКИ ────────────────────────────────────────────────")
        cur = None
        for f, kind, msg in errors:
            if f != cur: print(f"\n  {f}"); cur = f
            print(f"     [{kind}] {msg[:120]}")
        print()
    else:
        print("✅ ГРЕШКИ: няма. Шаблоните спазват конвенцията.\n")

    if warnings:
        print("── ВНИМАНИЕ (за преценка, не спира commit) ───────────────")
        for f, kind, msg in warnings:
            print(f"   {f:40} [{kind}] {msg}")
        print()

    if legacy_hits:
        print("── НАСЛЕДЕНИ МАРКЕРИ ─────────────────────────────────────")
        for f, leg, why in legacy_hits:
            print(f"   {f:40} {leg:28} {why}")
        print()

    if orphans:
        print(f"── СИРАЧЕТА: {len(orphans)} ключа в кода без маркер в шаблон ──")
        print("   " + ", ".join(orphans))
        print("   (не е грешка — маркерът е на разположение, ако потрябва)\n")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

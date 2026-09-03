"""
check_keys.py — сверява ключовете на PWA срещу тези, които кодът чака.

Пуска се от корена на cbt-api:
    python tools/check_keys.py

Защо: PWA и бекендът си говорят с етикети — „Възложител_1_Фирма = Алфа Билд ЕООД".
Ако двете страни се разминат в името дори с една буква, НИЩО НЕ ГЪРМИ: кодът не
намира етикета, слага празно и продължава. Излиза документ, който изглежда наред,
но на едно място пише нищо. Точно това стана на 01.09.2026 — тест с
„Възложител_1_Име" мина зелено, а PWA праща „Възложител_1_Фирма".

Близнак на check_templates.py:
    check_templates.py   сверява  шаблон ↔ код
    check_keys.py        сверява  PWA    ↔ код

Две нива:
  ГРЕШКА   — мъртъв ключ или почти съвпадение; изходен код 1
  ВНИМАНИЕ — за човешка преценка; не спира нищо
"""
import sys, os, re

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PWA  = os.path.join(os.path.dirname(ROOT), "cloude", "index.html")

# Ключове, които НЕ идват от паспорта, а се вписват от endpoint-а при генериране
# (частта на Акт 12, номерът на Заповедната книга). Търсят се като d["Ключ"] = ...
ENDPOINT_SET = re.compile(r'd\[\s*"([^"]+)"\s*\]\s*=')

# Ключове, за които празна стойност е нормална — не се вика за тях.
OPTIONAL = {
    "Геодезист",          # има подразбиране от служителите
    "Част",               # само за Акт 12, идва от endpoint-а
    "Акт12_Номер",
}


def pwa_keys(text):
    """Какво ИЗПРАЩА PWA.

    Внимание: `add(` трябва да е самостоятелно извикване, не `classList.add(` —
    иначе в списъка влизат CSS класове като 'active' и 'open'.
    """
    keys = set()
    BARE = r"(?<![.\w])add\("
    # add('Ключ', ...)  и  add(`Ключ_${i}_Нещо`, ...)
    keys |= set(re.findall(BARE + r"\s*'([^']+)'\s*,", text))
    keys |= set(re.findall(BARE + r"\s*`([^`]+)`\s*,", text))
    # add('Проектант_' + (i+1) + '_Име', ...) — сглобяване чрез слепване
    for a, b in re.findall(BARE + r"\s*'([^']+)'\s*\+[^,]*?\+\s*'([^']+)'\s*,", text):
        keys.add(f"{a}#{b}")
    # ['Ключ', стойност] — но САМО вътре в push към масив с редове
    # (Протокол 2 и Excel пътят). Извън този обхват не се гадае: иначе или
    # влизат случайни масиви от низове, или се изпускат ключове без долна черта.
    for m in re.finditer(r"(?:passportRows|rows|payload)\.push\(", text):
        block = text[m.end(): m.end() + 4000]
        end = block.find(");")
        keys |= set(re.findall(r"\[\s*'([A-Za-zА-Яа-я][\wА-Яа-я]*)'\s*,",
                               block[:end if end > 0 else len(block)]))
    return {normalize(k) for k in keys}


def code_keys(text):
    """Какво ЧАКА кодът — d.get("Ключ") и d.get(f"Ключ_{i}_Нещо")."""
    keys = set()
    keys |= set(re.findall(r'd\.get\(\s*"([^"]+)"', text))
    keys |= set(re.findall(r'd\.get\(\s*f"([^"]+)"', text))
    return {normalize(k) for k in keys}


def normalize(k):
    """`Възложител_${i}_Фирма` и f"Възложител_{i}_Фирма" са един и същи ключ."""
    k = re.sub(r"\$?\{[^}]*\}", "#", k)
    return k.strip()


def distance(a, b):
    """Разстояние на Левенщайн — за да хванем печатната грешка, не различния ключ."""
    if abs(len(a) - len(b)) > 2:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main():
    if not os.path.isfile(PWA):
        print(f"✗ PWA не е намерен: {PWA}")
        print("  Скриптът очаква cloude/ до cbt-api/.")
        return 1

    js = open(PWA, encoding="utf-8").read()
    py = "".join(open(os.path.join(ROOT, f), encoding="utf-8").read()
                 for f in ("cbt_docx.py", "api.py"))

    sent     = pwa_keys(js)
    wanted   = code_keys(py)
    injected = {normalize(k) for k in ENDPOINT_SET.findall(py)}

    # ── Мъртви ключове, вписвани от endpoint-а ───────────────────────────────
    # Разликата спрямо „сираче“ е в НАМЕРЕНИЕТО. Сираче е ключ, който
    # build_placeholders описва „за всеки случай“ — безобидно. Мъртъв е ключ,
    # който endpoint-ът СЕ СТАРАЕ да впише, с отделен клон заради конкретен
    # документ, а никой не го чете: тогава нещо, което операторът е въвел,
    # се изчислява и се изхвърля мълчаливо.
    #
    # 02.09: точно това стана със Заповедната книга — endpoint-ът пълнеше
    # {{Заповедна_Номер}}, маркер, който вече не съществуваше в шаблона.
    # check_templates го даваше като едно от близо шейсет сирачета и не се видя.
    mrtvi = sorted(k for k in injected if k not in wanted)

    provided = sent | injected | OPTIONAL
    # Наследените алиаси без индекс — „Възложител_Подписва" до „Възложител_#_Подписва" —
    # са нарочни, живеят заради стари шаблони. Не са печатна грешка.
    legacy = {re.sub(r"#_", "", k) for k in provided} | {re.sub(r"_#", "", k) for k in provided}
    provided |= legacy

    orphan   = sorted(k for k in wanted if k not in provided)
    unused   = sorted(k for k in sent if k not in wanted)

    print(f"PWA изпраща: {len(sent)} ключа")
    print(f"Кодът чака:  {len(wanted)} ключа")
    if injected:
        print(f"Endpoint-ът вписва: {', '.join(sorted(injected))}")
    print()

    # ── ГРЕШКИ: почти съвпадения ─────────────────────────────────────────────
    errors = []
    for k in orphan:
        near = [s for s in sent if s != k and (s.lower() == k.lower() or distance(s, k) <= 2)]
        if near:
            errors.append((k, near))

    if mrtvi:
        print("── ✗ ГРЕШКИ: endpoint-ът ги вписва, но никой не ги чете ──")
        for k in mrtvi:
            print(f"   {k}   ← въведеното от оператора се изхвърля мълчаливо")
        print()

    if errors:
        print("── ✗ ГРЕШКИ: почти съвпадение, най-вероятно печатна грешка ──")
        for k, near in errors:
            print(f"   кодът чака  {k}")
            for n in near:
                print(f"   PWA праща   {n}   ← разминават се")
        print()

    # ── ВНИМАНИЕ ─────────────────────────────────────────────────────────────
    silent = [k for k, _ in ((k, None) for k in orphan) if k not in dict(errors)]
    if silent:
        print("── ВНИМАНИЕ: кодът ги чете, нищо не ги пълни — винаги излизат празни ──")
        for k in silent:
            print(f"   {k}")
        print()

    if unused:
        print("── ВНИМАНИЕ: PWA ги праща, кодът не ги чете — губят се по пътя ──")
        for k in unused:
            print(f"   {k}")
        print()

    broi = len(errors) + len(mrtvi)
    if broi:
        print(f"✗ ГРЕШКИ: {broi}. Оправи ги преди commit.")
        return 1
    print("✅ ГРЕШКИ: няма. Етикетите на PWA и кода съвпадат.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

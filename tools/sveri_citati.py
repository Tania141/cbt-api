"""sveri_citati.py — сверява пастнатите цитати със заключения закон.

    python tools/sveri_citati.py

Операторът паства текста на члена в раздела „Цитати“ на чеклиста. Тук се
проверява само едно: този текст стои ли буквално на този адрес. Ако не стои —
сгрешен адрес, друга редакция, или пастът е от съседна точка.

Какво НЕ проверява: дали цитатът е уместен за документа, до който е сложен.
Тази преценка е на човека — виж rules/citati.py.
"""
import sys, os, re

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rules import citati as c                      # noqa: E402
from rules import cheklist_dokumenti as chd        # noqa: E402


def pastnati():
    """Блоковете от раздела „Цитати“: адрес → пастнат текст."""
    p = chd.path()
    if not p:
        return {}
    s = open(p, encoding="utf-8").read()
    razdel = s.split("## Цитати", 1)
    if len(razdel) < 2:
        return {}
    s = razdel[1].split("\n## ", 1)[0]

    izhod, adres, red = {}, None, []
    for l in s.split("\n"):
        if l.startswith("### "):
            if adres:
                izhod[adres] = " ".join(red).strip()
            adres, red = l[4:].strip(), []
        elif l.startswith(">") and adres:
            red.append(l.lstrip("> ").rstrip())
    if adres:
        izhod[adres] = " ".join(red).strip()
    return izhod


ZNAK = {"съвпада": "✅", "съвпада без бележките за изменения": "✅",
        "няма пастнат текст": "⏳"}


def main():
    ok, prichina = c.zaklyucheno()
    print("източници:", ", ".join(c.IZTOCHNICI))
    print("заключени:", "да" if ok else f"НЕ — {prichina}")
    if not ok:
        return 1

    citati = pastnati()
    # Основанията, посочени в таблиците, но без пастнат текст — те са
    # причината проверката да съществува, затова се броят.
    posocheni = {r["osnovanie"].strip() for r in chd.chetene() if r["osnovanie"].strip()}
    bez_paste = sorted(posocheni - set(citati))

    print(f"\nпастнати цитати: {len(citati)} · основания в таблиците: {len(posocheni)}")
    print("═" * 60)

    losho = 0
    for adres, tekst in citati.items():
        r = c.sveri(adres, tekst)
        s = r["sastoyanie"]
        print(f"{ZNAK.get(s, '❌')} {adres}")
        if s not in ZNAK:
            losho += 1
            print(f"     {s} — {r.get('podrobno', '')}")
            if r.get("izvor"):
                print(f"     в закона пише: {r['izvor'][:160]}…")
        elif s == "съвпада без бележките за изменения":
            print("     (съвпада, ако се пренебрегнат бележките „Изм. - ДВ…“)")

    if bez_paste:
        print(f"\n⏳ {len(bez_paste)} основания без пастнат текст:")
        for a in bez_paste:
            print("   ·", a)

    print()
    if losho:
        print(f"❌ {losho} цитата не се потвърждават от закона.")
        return 1
    print("✅ Всички пастнати цитати стоят на посочените адреси.")
    print("   Дали са УМЕСТНИ за документите — това не е проверено и не може да бъде.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
pin_naredba.py — заключва Наредба № 1 към отпечатък.

    python tools/pin_naredba.py         показва състоянието и разликите
    python tools/pin_naredba.py --pin   записва текущия отпечатък

Защо: четенето на разпоредби стъпва на структурата на конкретния .md файл.
Друга редакция или друго форматиране може ТИХО да върне грешен текст — а това е
по-лошо от липса на проверка, защото носи авторитет. Затова файлът е заключен и
при разминаване правилата отказват да работят.

Отключването е съзнателно действие на човек. Отпечатъкът се пази в git, така че
смяната на наредбата се вижда в diff и остава в историята.
"""
import sys, os, json

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rules import naredba1 as n1  # noqa: E402
from rules import naredba7 as n7  # noqa: E402


def naredba7(pin):
    """Сверява числовата таблица по зони срещу текста на Наредба № 7."""
    print("\n" + "═" * 60)
    print("НАРЕДБА № 7 — устройствени показатели по зони")

    import glob, re, hashlib
    pdf = None
    for d in n1._TARSI:
        hit = glob.glob(os.path.join(d, "НАРЕДБА № 7*.pdf"))
        if hit:
            pdf = hit[0]
            break
    if not pdf:
        print("✗ Наредба № 7 не е намерена до хранилището.")
        return 1

    # Огледалото на текста се пази в хранилището — за да е сверката бърза и
    # промяната да се вижда в diff. Пресъздава се само когато PDF-ът се смени.
    sha = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
    star = json.load(open(n7.LOCK, encoding="utf-8")) if os.path.isfile(n7.LOCK) else {}
    if not os.path.isfile(n7.MIRROR) or star.get("sha256") != sha:
        print("   извличане на текста от PDF…")
        from pdfminer.high_level import extract_text
        text = re.sub(r"\s+", " ", extract_text(pdf))
        open(n7.MIRROR, "w", encoding="utf-8").write(text)
    else:
        text = open(n7.MIRROR, encoding="utf-8").read()

    print(f"файл:   {os.path.basename(pdf)[:52]}…")
    print(f"sha256: {sha[:16]}…")
    lipsvat = n7.sveri(text)
    if lipsvat:
        print(f"\n⚠️ {len(lipsvat)} израза от таблицата не се намират в наредбата:")
        for x in lipsvat:
            print("   ·", x)
        print("\nТаблицата е остаряла или наредбата е изменена. Правилата за")
        print("градоустройство ще връщат „не може да се провери“.")
        return 1

    print(f"✅ Всичките {sum(len(v) for v in n7.IZRAZI.values())} израза "
          f"от {len(n7.ZONI)} зони се намират в текста.")
    if pin:
        json.dump({"file": os.path.basename(pdf), "sha256": sha,
                   "zoni": sorted(n7.ZONI), "sverena": True},
                  open(n7.LOCK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"✅ Записан отпечатък: {os.path.basename(n7.LOCK)}")
    else:
        ok, prichina = n7.zakliuchena()
        if not ok:
            print(f"⚠️ {prichina}")
            return 1
    return 0


def main():
    nov, err = n1.otpechatak()
    if err:
        print(f"✗ {err}")
        return 1

    star = json.load(open(n1.LOCK, encoding="utf-8")) if os.path.isfile(n1.LOCK) else None
    print(f"файл:   {nov['file']}")
    print(f"sha256: {nov['sha256'][:16]}…")
    print("структура:")
    for chl, kat in n1.CHLENOVE.items():
        al = nov["struktura"].get(str(chl))
        if al is None:
            print(f"   чл. {chl:>2} ({kat}): ✗ НЕ Е НАМЕРЕН")
        else:
            opis = " · ".join(f"ал. {a}: {t} т." for a, t in al.items())
            print(f"   чл. {chl:>2} ({kat}): {opis}")

    r = n1.razliki(nov, star)
    print()
    if not r:
        print("✅ Наредба № 1 съвпада със заключения отпечатък.")
        return naredba7("--pin" in sys.argv)

    print("⚠️ Разлики спрямо заключеното:")
    for x in r:
        print("   ·", x)

    if "--pin" in sys.argv:
        json.dump(nov, open(n1.LOCK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\n✅ Записан нов отпечатък: {os.path.basename(n1.LOCK)}")
        print("   Провери, че правилата пак минават случаите си: python tools/rules_doc.py")
        return 0

    print("\nПравилата, които четат наредбата, ще връщат „не може да се провери“.")
    print("Ако промяната е очаквана и текстът е сверен: python tools/pin_naredba.py --pin")
    return 1


if __name__ == "__main__":
    sys.exit(main())

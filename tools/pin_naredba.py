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
        print("✅ Наредбата съвпада със заключения отпечатък.")
        return 0

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

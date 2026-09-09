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
from rules import normativna_matrica as nm  # noqa: E402
from rules import cheklist_dokumenti as chd  # noqa: E402

IZVORI = os.path.join(ROOT, "rules", "izvori")


def kopirai(p):
    """Обновява копието в хранилището — то е единственото, което стига до Railway.

    Локално правилата четат папката на оператора; на сървъра нея я няма. Ако
    копието изостане, сървърът мълчаливо работи по стара редакция — затова
    заключването и копирането са едно действие, не две.
    """
    if not p or os.path.dirname(os.path.abspath(p)) == os.path.abspath(IZVORI):
        return
    os.makedirs(IZVORI, exist_ok=True)
    cel = os.path.join(IZVORI, os.path.basename(p))
    nov = open(p, "rb").read()
    if os.path.isfile(cel) and open(cel, "rb").read() == nov:
        return
    open(cel, "wb").write(nov)
    print(f"   копие за деплоя обновено: rules/izvori/{os.path.basename(p)}")


def cheklist(pin):
    """Сверява чеклиста на входните документи."""
    print()
    print("═" * 60)
    print("ЧЕКЛИСТ — входни документи и съгласувания")

    if not chd.path():
        print("✗ чеклистът не е намерен")
        return 1
    nov = chd.otpechatak()
    print(f"файл:   {nov['fajl']}")
    print(f"sha256: {nov['sha256'][:16]}…")
    print(f"документи: {nov['dokumenti']} в {len(nov['razdeli'])} раздела")

    ok, prichina = chd.zaklyucheno()
    if ok:
        print()
        print("✅ Чеклистът съвпада със заключения отпечатък.")
        kopirai(chd.path())
        return 0

    print()
    print(f"⚠️ {prichina}")
    if pin:
        json.dump(nov, open(chd.LOCK, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"✅ Записан нов отпечатък: {os.path.basename(chd.LOCK)}")
        kopirai(chd.path())
        return 0
    print("Проверката на документите няма да работи, докато не се сверят.")
    return 1


def matrica(pin):
    """Сверява нормативната матрица — общите актове и групите по вид строеж."""
    print()
    print("═" * 60)
    print("НОРМАТИВНА МАТРИЦА — приложими актове по вид строеж")

    if not nm.path():
        print("✗ справочникът не е намерен")
        return 1
    nov = nm.otpechatak()
    print(f"файл:   {nov['fajl']}")
    print(f"sha256: {nov['sha256'][:16]}…")
    print(f"общи актове: {nov['obshti']} · групи по вид строеж: {nov['grupi']}")

    ok, prichina = nm.zaklyucheno()
    if ok:
        print()
        print("✅ Матрицата съвпада със заключения отпечатък.")
        kopirai(nm.path())
        return 0

    print()
    print(f"⚠️ {prichina}")
    if pin:
        json.dump(nov, open(nm.LOCK, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"✅ Записан нов отпечатък: {os.path.basename(nm.LOCK)}")
        kopirai(nm.path())
        return 0
    print("Списъкът с нормативни документи няма да се предлага, докато не се сверят.")
    print("Ако промяната е очаквана: python tools/pin_naredba.py --pin")
    return 1


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
        kopirai(n1.path())
        pin = "--pin" in sys.argv
        kod = naredba7(pin)
        kod = matrica(pin) or kod
        return cheklist(pin) or kod

    print("⚠️ Разлики спрямо заключеното:")
    for x in r:
        print("   ·", x)

    if "--pin" in sys.argv:
        json.dump(nov, open(n1.LOCK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\n✅ Записан нов отпечатък: {os.path.basename(n1.LOCK)}")
        kopirai(n1.path())
        print("   Провери, че правилата пак минават случаите си: python tools/rules_doc.py")
        return 0

    print("\nПравилата, които четат наредбата, ще връщат „не може да се провери“.")
    print("Ако промяната е очаквана и текстът е сверен: python tools/pin_naredba.py --pin")
    return 1


if __name__ == "__main__":
    sys.exit(main())

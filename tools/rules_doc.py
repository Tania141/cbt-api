"""
rules_doc.py — произвежда четимия документ от самите правила.

    python tools/rules_doc.py            # на екрана
    python tools/rules_doc.py --write    # записва ПРАВИЛА.md

Същият модел като dump_templates.py: един източник, генерирано огледало.
Правилото и описанието му не могат да се разминат, защото описанието се
произвежда от правилото.

Изходът върши три работи наведнъж:
  · показва на оператора какво проверява системата и на какво основание
  · служи като техническо задание за външен изпълнител
  · служи като приемен критерий — всеки случай минава или не минава
"""
import sys, os

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import rules  # noqa: E402
from rules.engine import ALL_RULES, selftest_all  # noqa: E402

STATUS = {"ok": "✅ в ред", "warn": "⚠️ внимание", "unknown": "⏳ не може да се провери"}


def build():
    out = []
    w = out.append

    w("# АКТ СИСТЕМ — правила за верификация\n")
    w("*Генериран автоматично от `rules/` чрез `tools/rules_doc.py`.*")
    w("*НЕ се редактира на ръка — промените се правят в правилата.*\n")
    w("Всяко правило носи цитата от закона, на който стъпва, и случаите, "
      "с които се доказва. Случаите са изпълними: те са едновременно "
      "**описание на изискването** и **критерий за приемане**.\n")

    w("## Присъдите\n")
    w("| присъда | значение |")
    w("|---|---|")
    w("| ✅ **в ред** | правилото е проверено и минава |")
    w("| ⚠️ **внимание** | правилото е проверено и не минава |")
    w("| ⏳ **не може да се провери** | липсват данни — правилото изчаква |")
    w("")
    w("> Третата присъда е задължителна. Без нея всеки нормален строеж свети червено, "
      "защото половината дати още ги няма — и операторът спира да гледа предупрежденията.\n")
    w("---\n")

    for r in ALL_RULES:
        w(f"## {r.code} · {r.title}\n")
        w(f"**Основание.** {r.citation}\n")
        w(f"**Какво проверява.** {r.what}\n")
        w("**Случаи:**\n")
        w("| случай | очаквано |")
        w("|---|---|")
        for name, _, expected in r.cases:
            w(f"| {name} | {STATUS[expected]} |")
        w("")
        w("<details><summary>Примерен изход</summary>\n")
        for name, project, _ in r.cases:
            v = r.check(project)
            w(f"- **{name}** → {STATUS[v.status]} — {v.message}")
        w("\n</details>\n")
        w("---\n")

    total = sum(len(r.cases) for r in ALL_RULES)
    w(f"*Правила: **{len(ALL_RULES)}** · случаи: **{total}**.*")
    return "\n".join(out)


def main():
    fails = selftest_all()
    if fails:
        print("✗ Правилата не минават собствените си случаи — документът не се генерира:\n")
        for f in fails:
            print("   ", f)
        return 1

    text = build()
    if "--write" in sys.argv:
        path = os.path.join(ROOT, "ПРАВИЛА.md")
        open(path, "w", encoding="utf-8").write(text + "\n")
        total = sum(len(r.cases) for r in ALL_RULES)
        print(f"записан: {path}")
        print(f"правила: {len(ALL_RULES)} · случаи: {total} · всички минават")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Факт, върнат от четеца като ТЕКСТ с JSON вътре, се разчита (18.11.2026).

Операторът, РС на Митко Ситекс: в полето „издател“ на паспорта излезе
{"stoynost": "Главен архитект на СО – р-н „Нови Искър“ / арх. …", "citat": …,
"stranica": 2} — целият текст беше влязъл като стойност. И договорът за СМР
без думата „строител“ (страните са ВЪЗЛОЖИТЕЛ и ИЗПЪЛНИТЕЛ) излизаше без
строител.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

from rules import sloy2

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))


IZD = 'Главен архитект на СО – р-н „Нови Искър“ / арх. Проба Пробов'
dok = sloy2._normalizirai({
    "izdatel": '{"stoynost": "%s", "citat": "Главен архитект …", "stranica": 2}' % IZD.replace('"', '\\"'),
    "nomer": {"stoynost": '{"stoynost": "123", "stranica": 1}'},
    "data": "01.02.2024",
    "v_sila": '{"stoynost": "20.02.2024", "stranica": 2}',
})
t("издателят — само стойността", dok["izdatel"]["stoynost"] == IZD, dok["izdatel"])
t("цитатът и страницата остават", dok["izdatel"].get("stranica") == 2 and dok["izdatel"].get("citat"), dok["izdatel"])
t("вложено два пъти — разчита се", dok["nomer"]["stoynost"] == "123", dok["nomer"])
t("обикновеният текст си остава", dok["data"]["stoynost"] == "01.02.2024", dok["data"])
t("влязло в сила — и то минава", dok["v_sila"]["stoynost"] == "20.02.2024", dok["v_sila"])
t("текст с фигурни скоби, но не факт — не се пипа",
  sloy2._normalizirai({"izdatel": "{нещо}"})["izdatel"]["stoynost"] == "{нещо}")

shema = sloy2.SHEMA if hasattr(sloy2, "SHEMA") else None
src = open(sloy2.__file__, encoding="utf-8").read()
t("четецът знае, че ИЗПЪЛНИТЕЛ в договор за СМР е строителят",
  "страната „ИЗПЪЛНИТЕЛ“ е" in src and "„строител“" in src)

for x in dobri:
    print("  ok  " + x)
for x in loshi:
    print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — фактът от текст се разчита")
sys.exit(1 if loshi else 0)

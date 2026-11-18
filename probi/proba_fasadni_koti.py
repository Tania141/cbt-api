# -*- coding: utf-8 -*-
"""Котите от фасада/разрез → избор за Протокол 2 (18.11.2026, Митко Ситекс).

Системата само предлага: котите от листа и подсказка; коя е коя посочва
операторът. Пробата върви на текст като от истинската фасада и — ако е на
този компютър — на разреза на Радулов (PDF с текстов слой, 567,34 за ±0,00).
"""
import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

from rules import fasadni_koti as fk

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))


# Като фасадата на Митко Ситекс: две фасади, котите в двата края.
FASADA = """+7,04=541,64 +6,51 +5,73=540,33 +5,38 +5,15 +2,80 +2,50 +2,35
0,00=534,60 -0,47=534,13 Ср. кота прил. терен = 534,13 m ФАСАДА ЮГОЗАПАД М1:50
+7,04=541,64 +6,48 +5,73=540,33 +5,38 +5,15 +3,82=538,42 +2,50 +2,35 0,00=534,60 -0,47=534,13
Паралет h=1,05 m (чл. 113 (3) от Н7) h=6,18 m"""
koti = fk._slei(fk.ot_teksta([FASADA]))
k = {r["kota"]: r for r in koti}
t("±0,00 с абсолютната 534,60", k.get("±0,00", {}).get("absolyutna") == "534,60", k.get("±0,00"))
t("+5,73 с абсолютната 540,33", k.get("+5,73", {}).get("absolyutna") == "540,33", k.get("+5,73"))
t("+7,04 — повторена, един ред", k.get("+7,04", {}).get("pati", 0) >= 2, k.get("+7,04"))
t("-0,47 — теренът", "-0,47" in k, list(k))
t("размер без знак (h=1,05, 6,18) не е кота", "+1,05" not in k and "+6,18" not in k, list(k))
t("подредени отгоре надолу", koti[0]["kota"] == "+7,04" and koti[-1]["kota"] == "-0,47", [r["kota"] for r in koti])
p = fk.podskazki(koti)
t("подсказка: цокъл ±0,00", p.get("cokul") == "±0,00", p)
t("подсказка: било +7,04", p.get("bilo") == "+7,04", p)
t("подсказка: корниз +5,73 (следващата с абсолютна)", p.get("korniz") == "+5,73", p)
t("надписът бие сметката", fk.podskazki([{"kota": "+9,10", "absolyutna": "", "nadpis": "", "list": "", "pati": 1},
                                         {"kota": "+8,00", "absolyutna": "", "nadpis": "било", "list": "", "pati": 1}])
  .get("bilo") == "+8,00")
t("АИ върна „0,00“ без знак — става ±0,00", fk._slei([{"kota": "0,00"}])[0]["kota"] == "±0,00")

PAT = r"C:\Users\Tania\Dropbox\Tania and Nadia\СГРАДИ\ЗА НАДЗОР\РАДУЛОВ\РАДУЛОВ АЛИПИЕВИ\0.ПРОЕКТ\NP135-112-A.SC-A.pdf"
if os.path.isfile(PAT):
    dok, info = fk.procheti([], os.path.basename(PAT), "application/pdf",
                            base64.b64encode(open(PAT, "rb").read()).decode())
    t("Радулов, разрезът — с код, без АИ", dok["chetec"].startswith("кодът"), dok["chetec"])
    # Обърнато веднага (18.11.2026): на разреза на Радулов абсолютната 567,34
    # стои САМА, не до ±0,00 — показва се отделно, не се връзва на сляпо.
    t("Радулов: ±0,00 е сред котите", any(r["kota"] == "±0,00" for r in dok["koti"]), dok["koti"][:8])
    t("Радулов: 567,34 е сред абсолютните", "567,34" in dok.get("absolyutni", []), dok.get("absolyutni"))
    t("Радулов: абсолютните не стават относителни", not any(r["kota"].startswith("+5") and len(r["kota"]) > 6
                                                           for r in dok["koti"]), [r["kota"] for r in dok["koti"]][:6])
    print(f"  (Радулов: {len(dok['koti'])} коти; подсказки {dok['podskazki']})")

for x in dobri:
    print("  ok  " + x)
for x in loshi:
    print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — котите от фасадата като избор")
sys.exit(1 if loshi else 0)

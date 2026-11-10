# -*- coding: utf-8 -*-
"""Актовете обр. 7 от бетоновия дневник — в ЕДИН файл, всеки на нова страница.

Операторът, 09–10.11.2026: актът е ПРЕДИ бетонирането (приемат се кофражът и
армировката); полетата на шаблона са датата, нивата, СМР и какво се разрешава.
"""
import io, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")
from docx import Document
import api

dobri, loshi = [], []
def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))

d = {"Строеж": "Сграда", "Строител_ТехРък": "инж. Делчо Радулов"}
seriya = [
    {"data": "23.07.2024", "ot": "+2,61", "do": "+2,61",
     "smr": "Кофраж и армировка на стоманобетонна плоча на к. +2,61",
     "razreshava": "Бетониране на гореописаните елементи."},
    {"data": "03.08.2024", "ot": "+2,61", "do": "+5,50",
     "smr": "Кофраж и армировка на вертикални елементи от к. +2,61 до к. +5,50",
     "razreshava": "Бетониране на гореописаните елементи."},
    {"data": "", "ot": "", "do": "", "smr": "Кофраж и армировка на плоча", "razreshava": ""},
]
doc = Document(io.BytesIO(api.akt7_seriya(d, seriya)))
tekst = "\n".join(p.text for p in doc.paragraphs)
t("три акта в един файл", tekst.count("АКТ") == 3, tekst.count("АКТ"))
t("всеки със своята дата", "Днес 23.07.2024 г." in tekst and "Днес 03.08.2024 г." in tekst, tekst[:400])
t("нивата", "от ниво +2,61 до ниво +5,50" in tekst.replace("  ", " "), "")
t("СМР и разрешаването", "вертикални елементи от к. +2,61" in tekst and "Бетониране на гореописаните" in tekst, "")
t("празното остава на точки", "Днес ...." in tekst, "")
t("нито един маркер не остава", "{{" not in tekst, [l for l in tekst.split("\n") if "{{" in l])
xml = doc.element.xml
t("нова страница между актовете", xml.count('w:type="page"') >= 2, xml.count('w:type="page"'))
t("една секция накрая", doc.element.body[-1].tag.endswith("sectPr"), "")

for x in dobri: print("  ok  " + x)
for x in loshi: print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — актовете обр. 7 са в един файл")
sys.exit(1 if loshi else 0)

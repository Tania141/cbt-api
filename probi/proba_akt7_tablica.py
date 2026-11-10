# -*- coding: utf-8 -*-
"""Актовете обр. 7 — таблица в 1.3 на Акт 15 и в ОД.

Операторът, 10.11.2026: при 50–60 акта таблицата е по-прегледна; в Word
таблица става на редове с един жест, обратното — не.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

from docx import Document
import api
from cbt_docx import build_placeholders
from rules import doklad_sloy2 as ds

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))


REDOVE = [
    {"n": 1, "data": "23.07.2024", "smr": "кофраж и армировка на стоманобетонна плоча на к.+2,61", "ot": "—", "do": "—"},
    {"n": 2, "data": "03.08.2024", "smr": "Кофраж и армировка на вертикали от к+2,61 до +5,50", "ot": "+2,61", "do": "+5,50"},
]
d = {"Строеж": "Сграда", "Акт7_Таблица": json.dumps(REDOVE, ensure_ascii=False),
     "Актове_Протоколи": "Акт Образец 5 от 15.03.2022 г.\n" + ds.AKT7_ZAGLAVIE + "\n" + ds.AKT7_MARKER
                         + "\nПриложение № 14 … от 13.05.2025 г."}

t("редовете се четат", len(ds.akt7_redove(d)) == 2, ds.akt7_redove(d))
t("повреден JSON не гърми", ds.akt7_redove({"Акт7_Таблица": "{"}) == [], "")

# Акт 15
doc = Document(io.BytesIO(api.generate_from_template(api.TEMPLATE_FILES["akt15"], build_placeholders(d))))
t("Акт 15: маркерът е в 1.3", any(ds.AKT7_MARKER in p.text for p in doc.paragraphs), "")
ds.vstavi_akt7(doc, ds.akt7_redove(d))
tekst = "\n".join(p.text for p in doc.paragraphs)
t("Акт 15: маркерът изчезва", ds.AKT7_MARKER not in tekst, "")
tbl = [tb for tb in doc.tables if tb.rows and tb.rows[0].cells[0].text == "№"]
t("Акт 15: таблица с 2 акта + заглавие", tbl and len(tbl[0].rows) == 3, [len(x.rows) for x in tbl])
t("Акт 15: колоните", tbl and [c.text for c in tbl[0].rows[0].cells] == list(ds.KOLONI_AKT7), "")
t("Акт 15: данните", tbl and tbl[0].rows[2].cells[1].text == "03.08.2024" and tbl[0].rows[2].cells[4].text == "+5,50", "")
# таблицата е между обр. 5 и обр. 14 — на мястото си
body = list(doc.element.body)
i5 = next(i for i, e in enumerate(body) if "Образец 5" in "".join(e.itertext()))
i14 = next(i for i, e in enumerate(body) if "Приложение № 14" in "".join(e.itertext()))
it = body.index(tbl[0]._tbl)
t("Акт 15: таблицата е в 1.3, между обр. 5 и обр. 14", i5 < it < i14, (i5, it, i14))

# ОД — обикновеният
doc = Document(io.BytesIO(api.generate_from_template(api.TEMPLATE_FILES["doklad"], build_placeholders(d))))
t("ОД: заглавие и таблица след „Актове и протоколи“",
  ds.akt7_sled(doc, "Актове и протоколи по време на строителството", ds.akt7_redove(d)), "")
tekst = "\n".join(p.text for p in doc.paragraphs)
t("ОД: заглавието е там", ds.AKT7_ZAGLAVIE in tekst and ds.AKT7_MARKER not in tekst, "")
t("ОД: таблицата е там", any(tb.rows[0].cells[0].text == "№" and len(tb.rows) == 3 for tb in doc.tables), "")

# Протокол 2, раздел III — „Днес, …“ на всяка проверка (10.11.2026).
dp = {"Niva_Data_Izkop": "27.02.2024", "Niva_Data_Korniz": "03.04.2025"}
doc = Document(io.BytesIO(api.generate_from_template(api.TEMPLATE_FILES["protokol2combined"], build_placeholders(dp))))
dni = [p.text for p in doc.paragraphs if p.text.startswith("Днес")]
t("П2: датата на изкопа е в проверката му", any("27.02.2024" in x for x in dni), dni)
t("П2: и на корниза", any("03.04.2025" in x for x in dni), dni)
t("П2: празните остават на точки", sum("......" in x for x in dni) >= 3, dni)
t("П2: няма останал маркер", not any("{{" in x for x in dni), dni)

for x in dobri:
    print("  ok  " + x)
for x in loshi:
    print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — актовете обр. 7 са таблица")
sys.exit(1 if loshi else 0)

# -*- coding: utf-8 -*-
"""Площообразуването: само обектите и видът им; без „Общо“, без таблица IV."""
import io, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from rules.ploshtoobrazuvane import obekti_ot_redove, procheti, NeSeChete

dobri, loshi = [], []
def t(ime, verno, kak=""):
    (dobri if verno else loshi).append(ime + ("" if verno else "  -> " + repr(kak)))

REDOVE = [
    ["ТАБЛИЦА ЗА ОПРЕДЕЛЯНЕ НА ПЛОЩИТЕ", None, None, None],
    [None, None, "ТАБЛИЦА І-a - Подземно застрояване гаражи", None],
    ["ет.", "кота", "Обекти", "F1 кв.м."],
    ["1", "2", "3", "4"],
    ["сутерен", "-3.05", "Подземен гараж ПГ1", 17.12],
    [None, None, "Общо І-а", 373.58],
    [None, None, "ТАБЛИЦА IІ - Сграда - жилища", None],
    ["1 ет.", None, "Ателие 1", 55.41],
    ["2 ет.", None, "Апартамент 201", 66.61],
    [None, None, "ТАБЛИЦА ІV - Дворна площ", None],
    ["Двор", "0", "Паркомясто 1", 12.5],
    ["Двор", "0", "Двор към гараж 17", 60.45],
]
o = obekti_ot_redove(REDOVE)
t("обектите са три", [x["ime"] for x in o] == ["Подземен гараж ПГ1", "Ателие 1", "Апартамент 201"], o)
t("видът е разпознат", [x["vid"] for x in o] == ["подземен гараж", "ателие", "апартамент"], o)
t("„Общо“ не е обект", not any("Общо" in x["ime"] for x in o))
t("таблица IV не дава обекти", not any("Паркомясто" in x["ime"] or "Двор" in x["ime"] for x in o))
try:
    procheti("стар.xls", "AA==")
    t("стар .xls се отказва с обяснение", False)
except NeSeChete as e:
    t("стар .xls се отказва с обяснение", ".xlsx" in str(e), str(e))

out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
for x in dobri: out.write("  ok  " + x + "\n")
for x in loshi: out.write("  ЛО  " + x + "\n")
out.write(("\n%d проблема\n" % len(loshi)) if loshi else ("\n%d проверки — площообразуването се чете\n" % len(dobri)))
out.flush()
sys.exit(1 if loshi else 0)

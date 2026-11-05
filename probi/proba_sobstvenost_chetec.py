# -*- coding: utf-8 -*-
"""Четецът на собствеността: номер по КККР носи само земята (05.11.2026)."""
import io, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from rules.sobstvenost import bez_nomera_na_obekti, SHEMA, SABITIA, UKAZANIE

dobri, loshi = [], []
def t(ime, verno, kak=""):
    (dobri if verno else loshi).append(ime + ("" if verno else "  -> " + repr(kak)))

d = {"obekti": [
        {"identifikator": "68134.702.9889", "vid": "земя"},
        {"identifikator": "68134.702.9889.1.15", "opisanie": "апартамент № 15", "vid": "самостоятелен обект"},
        {"identifikator": "68134.702.9889", "opisanie": "апартамент № 603", "vid": "право на строеж"}],
     "prehvarliania": [
        {"obekt": "68134.702.9889.1.15", "na": "А", "ot": "Б", "dyal": "1/1"},
        {"obekt": "68134.702.9889", "na": "Х", "dyal": "1/1", "vid": "учредяване право на строеж"}]}
bez_nomera_na_obekti(d)
t("земята пази номера си", d["obekti"][0]["identifikator"] == "68134.702.9889")
t("апартаментът губи номера си", d["obekti"][1]["identifikator"] == "", d["obekti"][1])
t("и правото за АП603 също", d["obekti"][2]["identifikator"] == "", d["obekti"][2])
t("прехвърлянето за апартамента сочи описанието", d["prehvarliania"][0]["obekt"] == "апартамент № 15", d["prehvarliania"][0])
t("учредяването сочи пак ЗЕМЯТА", d["prehvarliania"][1]["obekt"] == "68134.702.9889", d["prehvarliania"][1])
t("има вид „обезщетение“", "обезщетение" in SABITIA)
from rules.sobstvenost import imena
im = imena("Калина Кирилова Петрова, Борис Александров Серафимов, като пълномощник на "
           "ВАСИЛКА АЛЕКСАНДРОВА СТОИМЕНОВА, Ваня Тошкова Александрова")
t("пълномощникът преди страната не е страна", "Борис Александров Серафимов" not in im, im)
t("страните са три", im == ["Калина Кирилова Петрова", "ВАСИЛКА АЛЕКСАНДРОВА СТОИМЕНОВА",
                           "Ваня Тошкова Александрова"], im)
t("обещанието не е прехвърляне", "ОБЕЩАНИЕТО НЕ Е ПРЕХВЪРЛЯНЕ" in UKAZANIE)
t("запазеното право е обезщетение", "ЗАПАЗЕНО ПРАВО НА СТРОЕЖ" in UKAZANIE)
d2 = {"obekti": [], "prehvarliania": [{"vid": "обезщетение", "dyal": "6,302 %", "obekt": "апартамент № 9"},
                                      {"vid": "обезщетение", "dyal": "1/2", "obekt": "гараж № 1"}]}
bez_nomera_na_obekti(d2)
t("при обезщетение процентът става 1/1", d2["prehvarliania"][0]["dyal"] == "1/1", d2)
t("дробта при обезщетение остава", d2["prehvarliania"][1]["dyal"] == "1/2", d2)
d3 = {"obekti": [], "prehvarliania": [{"vid": "обезщетение", "dyal": "23,72/151,40", "obekt": "паркомясто А6"}]}
bez_nomera_na_obekti(d3)
t("„23,72/151,40“ при обезщетение става 1/1", d3["prehvarliania"][0]["dyal"] == "1/1", d3)
t("лицата носят квота в земята", "kvota_zemya" in SHEMA["properties"]["lica"]["items"]["properties"])
t("указанието казва квотите да не са при суперфициара", "НЕ ги слагай" in UKAZANIE)

out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
for x in dobri: out.write("  ok  " + x + "\n")
for x in loshi: out.write("  ЛО  " + x + "\n")
out.write(("\n%d проблема\n" % len(loshi)) if loshi else ("\n%d проверки — четецът на собствеността стои\n" % len(dobri)))
out.flush()
sys.exit(1 if loshi else 0)

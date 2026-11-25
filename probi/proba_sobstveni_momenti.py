# -*- coding: utf-8 -*-
"""Твоите редове стигат „Липсва ми“ в моментите (25.11.2026).

Дотук собствените редове влизаха само в чеклиста на документите; моментите
(`/api/nadzor`) ги не виждаха. Пробата пази: къде отиват (подпис → Акт 15,
начало → Протокол 2), кога (условието по вид или съставки), че „за преценка“
си личи и че не се дублират с редовете от файла на моментите.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

from rules import momenti, sobstveni_momenti as sm

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))


SOBSTVENI = [
    {"dokument": "Протокол обр. 17 по ВиК", "etap": "подпис", "uslovie": "вид ∈ сграда",
     "razdel": "Въвеждане в експлоатация — от подобен обект", "osnovanie": "от подобен обект: „Денка“ (2025)"},
    {"dokument": "Удостоверение за кадастъра на БКТП", "etap": "начало", "uslovie": "sast_bktp и ако_е_приложимо",
     "osnovanie": "добавен от оператора · срещан 1 път"},
    {"dokument": "Становище за условията за присъединяване", "etap": "подпис", "uslovie": "вид ∈ линеен"},
    # старо условие „вид = …“ — кухнята го прави от съставките
    {"dokument": "Стар урок", "etap": "подпис", "uslovie": "вид = линеен", "sastavki": ["kabel_srn"]},
]
VIDIMI = momenti.FAZI["nadzor"]


def grupi_za(priznaci):
    g = momenti.po_momenti(faza="nadzor", priznaci=priznaci)
    sm.dobavi(g, SOBSTVENI, priznaci, VIDIMI)
    return g


def red(grupi, moment, ime):
    g = next((x for x in grupi if x["moment"] == moment), {"dokumenti": []})
    return next((d for d in g["dokumenti"] if d["dokument"] == ime), None)


def kade(grupi, ime):
    return [g["moment"] for g in grupi for d in g["dokumenti"] if d["dokument"] == ime]


# сграда (браузърът праща кода „sgrada“)
s = grupi_za({"kategoria": "3", "vid": "sgrada", "вид": "sgrada"})
r = red(s, "Акт 15", "Протокол обр. 17 по ВиК")
t("„изисквай — за да подпиша“ за сграда → в Акт 15", r is not None, kade(s, "Протокол обр. 17 по ВиК"))
t("и само там", kade(s, "Протокол обр. 17 по ВиК") == ["Акт 15"], kade(s, "Протокол обр. 17 по ВиК"))
t("редът казва, че е твой и откъде", r and r["sobstven"] and "Денка" in r["osnovanie"], r)
t("не е „за преценка“ — изискан е", r and r["za_precenka"] is False, r)
t("кодът на вида („sgrada“) се разбира като „сграда“", sm.priznaci_s_vid({"vid": "sgrada"})["вид"] == "сграда")
t("редът за линеен НЕ излиза при сграда", not kade(s, "Становище за условията за присъединяване"))
t("съставка, която строежът няма → не излиза", not kade(s, "Удостоверение за кадастъра на БКТП"))

# линеен с БКТП
l = grupi_za({"kategoria": "4", "vid": "lineen", "вид": "lineen", "sast_bktp": True})
t("за линеен — редът за линеен е в Акт 15", kade(l, "Становище за условията за присъединяване") == ["Акт 15"],
  kade(l, "Становище за условията за присъединяване"))
t("„за да започна“ → Протокол 2", kade(l, "Удостоверение за кадастъра на БКТП") == ["Протокол 2"],
  kade(l, "Удостоверение за кадастъра на БКТП"))
p2 = red(l, "Протокол 2", "Удостоверение за кадастъра на БКТП")
t("приетото от „Видени, но неописани“ е „за преценка“", p2 and p2["za_precenka"] is True, p2)
t("и носи етапа „начало“", p2 and p2["etap"] == "начало", p2)
t("редът за сграда не излиза при линеен", not kade(l, "Протокол обр. 17 по ВиК"))
t("старият урок „вид = линеен“ без съставката си — не излиза (кухнята го прави от съставките)",
  not kade(l, "Стар урок"))
l2 = grupi_za({"vid": "lineen", "sast_kabel_srn": True})
t("старият урок — излиза при съставката си", kade(l2, "Стар урок") == ["Акт 15"], kade(l2, "Стар урок"))

# не се дублира с ред от файла на моментите
g = momenti.po_momenti(faza="nadzor", priznaci={"vid": "sgrada"})
ime_ot_faila = next(d["dokument"] for x in g for d in x["dokumenti"])
pred = sum(len(x["dokumenti"]) for x in g)
sm.dobavi(g, [{"dokument": ime_ot_faila, "etap": "подпис", "uslovie": "винаги"}], {"vid": "sgrada"}, VIDIMI)
t("ред със същото име като във файла на моментите — не се дублира", sum(len(x["dokumenti"]) for x in g) == pred)

# фаза ОСИП — няма Акт 15 → не се добавя никъде
o = momenti.po_momenti(faza="osip", priznaci={"vid": "sgrada"})
sm.dobavi(o, SOBSTVENI, {"vid": "sgrada"}, momenti.FAZI["osip"])
t("във фаза ОСИП собствените редове нямат място — не се добавят", not kade(o, "Протокол обр. 17 по ВиК"))

# адресът ги вика
api = open(os.path.join(os.path.dirname(__file__), "..", "api.py"), encoding="utf-8").read()
t("/api/nadzor вика sobstveni_momenti.dobavi", "sobstveni_momenti.dobavi(grupi, _sobstveni_redove()" in api)

for x in dobri:
    print("  ok  " + x)
for x in loshi:
    print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — твоите редове стигат моментите")
sys.exit(1 if loshi else 0)

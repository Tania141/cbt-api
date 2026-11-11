# -*- coding: utf-8 -*-
"""„По проект“ → „изпълнено“ — рамката около модела (без мрежа).

Самото преобръщане на времето е работа на модела; тук се пази какво му се
подава и какво се приема обратно: ключовете се пазят, непознатото отпада,
липсващият блок се казва, резервният модел се пробва.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

from rules import izpalnenie as iz
from rules.chetci import NeMozheSega

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))


BLOKOVE = [
    {"klyuch": "Архитектура · обемно", "podzaglavie": "Обемно-пространствено решение",
     "tekst": "Инвестиционния проект предвижда сградата да се състои от един изцяло подземен етаж, партерен етаж и седем жилищни етажа."},
    {"klyuch": "Архитектура · дограма", "podzaglavie": "Дограма",
     "tekst": "Вратите на гаражите се предвида да бъдат секционни и ролетни като точния тип ще бъде указан във фаза Работна."},
]

v = iz.vhod("Архитектура", BLOKOVE)
t("всеки блок е подаден с ключа си", "Архитектура · обемно" in v and "Архитектура · дограма" in v, v)
t("и с текста си", "седем жилищни етажа" in v, v)
t("указанието казва: числата дословно, нищо добавено", "ДОСЛОВНО" in iz.UKAZANIE and "НЕ добавяй" in iz.UKAZANIE, "")


class Fals:
    """Модел, който връща готов отговор — като Claude: списък от извиквания."""
    ime = "Claude"

    def __init__(self, otgovor):
        self.otgovor = otgovor

    def chete(self, prep, shema, tekst, **_):
        assert prep["blokove"][0]["type"] == "text" and prep["docx_tekst"]
        return self.otgovor, {"model": "proba", "tokens_in": 100, "tokens_out": 80}


class Pada:
    ime = "Падащ"

    def chete(self, *a, **k):
        raise NeMozheSega("няма кредит")


otg = {"dokumenti": [
    {"klyuch": "Архитектура · обемно",
     "tekst": "Сградата се състои от един изцяло подземен етаж, партерен етаж и седем жилищни етажа.",
     "mahnato": []},
    {"klyuch": "Измислен ключ", "tekst": "нещо"},
]}
out, info = iz.predlozhi([Pada(), Fals(otg)], "Архитектура", BLOKOVE)
t("резервният модел се пробва, щом първият не може", info["chetec"] == "Claude", info)
t("преработеният блок е приет", "седем жилищни етажа" in out["Архитектура · обемно"]["tekst"], out)
t("непознат ключ отпада", "Измислен ключ" not in out, out)
t("липсващият блок се казва", info["lipsvat"] == ["Архитектура · дограма"], info)

# Mistral връща целия обект, не списък от извиквания
out2 = iz.razberi({"dokumenti": [{"klyuch": "Архитектура · дограма", "tekst": "", "mahnato": "фаза Работна"}]},
                  {"Архитектура · дограма"})
t("изцяло указание → празен текст, с какво е махнато", out2["Архитектура · дограма"] == {"tekst": "", "mahnato": ["фаза Работна"]}, out2)

for x in dobri:
    print("  ok  " + x)
for x in loshi:
    print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — рамката на „изпълнено“ държи")
sys.exit(1 if loshi else 0)

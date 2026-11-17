# -*- coding: utf-8 -*-
"""Демо фирмата има таван на четенията с АИ (17.11.2026).

Операторът: „демото трябва да мога да го изпратя по имейл с отделен акаунт“;
АИ — „да, с таван“. Без база: базата се подменя с проста измама.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")
import api

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))


class Baza:
    def __init__(self, red):
        self.red = red

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self):
        return self

    def execute(self, sql, p=None):
        self.posleden = sql
        if sql.startswith("UPDATE"):
            self.red["ai_broy"] = (self.red.get("ai_broy") or 0) + 1

    def fetchone(self):
        return dict(self.red) if self.red is not None else None

    def close(self):
        pass


def s_baza(red):
    api.get_db = lambda: Baza(red)


red = {"ai_tavan": 2, "ai_broy": 0}
s_baza(red)
t("първо четене — пуска и брои", api._ai_tavan_proveri("5") is None and red["ai_broy"] == 1, red)
t("второ — пуска", api._ai_tavan_proveri("5") is None and red["ai_broy"] == 2, red)
otkaz = api._ai_tavan_proveri("5")
t("трето — отказ с думи, не брои повече", otkaz and "2 четения с АИ" in otkaz and red["ai_broy"] == 2, otkaz)
t("отказът казва, че разглеждането продължава", otkaz and "съставянето" in otkaz, otkaz)

bez = {"ai_tavan": None, "ai_broy": 0}
s_baza(bez)
t("фирма без таван — без ограничение и без броене", api._ai_tavan_proveri("1") is None and bez["ai_broy"] == 0, bez)
api.get_db = lambda: None
t("без база — не спира работата", api._ai_tavan_proveri("1") is None, "")
t("пътищата с АИ включват четенето и „изпълнено“",
  {"/api/sloy2/chete", "/api/zapiski/chete", "/api/tekst/izpalnenie"} <= api.AI_PATISHTA, "")
t("демо поканата е само за администратор",
  getattr(api.app.view_functions.get("demo_pokana"), "__wrapped__", None) is not None, "")

for x in dobri:
    print("  ok  " + x)
for x in loshi:
    print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — демото има таван")
sys.exit(1 if loshi else 0)

# -*- coding: utf-8 -*-
u"""Лицензът на строителя трябва да покрива категорията на строежа.

Операторът, 01.10.2026: при Протокол 2 проверява „валиден лиценз от КСБ ЗА
КАТЕГОРИЯТА НА ОБЕКТА“. На 21.10.2026: „да, ако може“.
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rules import cprs  # noqa: E402

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + (u'' if verno else u'  -> %r' % (kak,)))


DNES = date(2026, 10, 21)


def p(kategoria, vid=None, **u):
    return cprs.proveri(kategoria, u, vid=vid, dnes=DNES)


# ── няма какво да се провери ─────────────────────────────────────────────
t(u'без удостоверение казва какво липсва',
  p(u"4")[u"sastoyanie"] == u"nyama")
t(u'само номер не стига',
  p(u"4", nomer=u"12345")[u"sastoyanie"] == u"nepalno",
  p(u"4", nomer=u"12345"))

# ── покрива ──────────────────────────────────────────────────────────────
r = p(u"4", vid=u"сграда", nomer=u"12345", kategorii=u"първа, втора, трета, четвърта",
      grupi=u"I", valid_do=u"30.09.2027")
t(u'покрива категорията', r[u"sastoyanie"] == u"pokriva", r)
t(u'казва какво покрива', u"4 категория" in r[u"tekst"] and u"12345" in r[u"tekst"], r)

t(u'арабските цифри се разбират',
  p(u"4", nomer=u"1", kategorii=u"1, 2, 3, 4")[u"sastoyanie"] == u"pokriva")
t(u'римската група се разбира',
  p(u"5", vid=u"сграда", nomer=u"1", kategorii=u"пета", grupi=u"I")[u"sastoyanie"] == u"pokriva")

# ── не покрива ───────────────────────────────────────────────────────────
r2 = p(u"2", nomer=u"777", kategorii=u"четвърта, пета")
t(u'по-висока категория не минава', r2[u"sastoyanie"] == u"ne_pokriva", r2)
t(u'казва какво има и какво трябва',
  u"2 категория" in r2[u"tekst"] and u"4, 5" in r2[u"tekst"], r2)

r3 = p(u"3", nomer=u"8", grupi=u"V", kategorii=u"трета")
t(u'пета група не покрива строеж', r3[u"sastoyanie"] == u"ne_pokriva", r3)

# ── срокът ───────────────────────────────────────────────────────────────
r4 = p(u"4", nomer=u"9", kategorii=u"четвърта", valid_do=u"30.09.2026")
t(u'изтеклото се хваща', r4[u"sastoyanie"] == u"izteklo", r4)
t(u'и казва докога е било', u"30.09.2026" in r4[u"tekst"], r4)
t(u'валидното не вдига шум',
  p(u"4", nomer=u"9", kategorii=u"четвърта", valid_do=u"22.10.2026")[u"sastoyanie"] == u"pokriva")

# ── групата срещу вида ───────────────────────────────────────────────────
r5 = p(u"3", vid=u"сграда", nomer=u"11", kategorii=u"трета", grupi=u"II")
t(u'сграда с група II се казва', r5[u"sastoyanie"] == u"druga_grupa", r5)
t(u'при линеен не се твърди за групата',
  p(u"3", vid=u"линеен", nomer=u"11", kategorii=u"трета", grupi=u"II")[u"sastoyanie"] == u"pokriva")

# ── непозната категория на строежа ───────────────────────────────────────
t(u'без категория на строежа не се гадае',
  p(u"", nomer=u"11", kategorii=u"трета")[u"sastoyanie"] == u"nepalno")

for x in dobri:
    print(u'  ok  ' + x)
for x in loshi:
    print(u'  LO  ' + x)
print()
print((u'%d проблема' % len(loshi)) if loshi
      else (u'%d проверки — лицензът се сверява с категорията' % len(dobri)))
sys.exit(1 if loshi else 0)

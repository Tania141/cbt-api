# -*- coding: utf-8 -*-
u"""Декларацията за материал не може да е по-късна от приемането.

Операторът, 21.10.2026: „често не се внимава от коя година са декларациите за
материали — въобще, не само за бетон и армировка“. Материалът се влага ПРЕДИ
акта, който приема работата; декларация, издадена след него, или е за друг
строеж, или е извадена наготово по-късно.

Случаят, от който тръгна: декларациите на „АСТ бетон“ са от 04.10.2021 г., а
бетонирането по дневника е от 2020 г.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rules import sloy2  # noqa: E402

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + (u'' if verno else u'  -> %r' % (kak,)))


def fakt(v):
    return {u"stoynost": v, u"citat": v}


def dok(vid_kod, data, **dop):
    d = {u"fajl": dop.pop("fajl", vid_kod + u".pdf"), u"vid_kod": vid_kod,
         u"vid": dop.pop("vid", vid_kod), u"data": fakt(data), u"cheklist_red": ""}
    for k, v in dop.items():
        d[k] = fakt(v)
    return d


def hron(dokumenti):
    r = sloy2.sravni(dokumenti, agenda=u"od")
    return [x[u"tekst"] for x in r[u"hronologia"]]


AKT14 = dok(u"AKT14", u"15.06.2020", vid=u"Акт обр. 14")
RANO = dok(u"DEKLARACIA", u"20.01.2020", vid=u"Декларация", material=u"Бетон С25/30", nomer=u"195")
KASNO = dok(u"DEKLARACIA", u"04.10.2021", vid=u"Декларация", material=u"Бетон С12/15", nomer=u"1135")

# ── намира закъснялата ───────────────────────────────────────────────────
h = hron([AKT14, KASNO])
red = [x for x in h if u"СЛЕД" in x]
t(u'закъснялата декларация се вижда', len(red) == 1, h)
t(u'казва след кой акт', u"Акт 14" in red[0], red)
t(u'и коя е', u"1135" in red[0] and u"С12/15" in red[0], red)
t(u'и с коя дата', u"04.10.2021" in red[0], red)

# ── не вдига шум за редовната ────────────────────────────────────────────
h2 = hron([AKT14, RANO])
t(u'декларация преди акта не е проблем', not any(u"СЛЕД" in x for x in h2), h2)

# ── без акт няма с какво да се сравни ────────────────────────────────────
h3 = hron([KASNO])
t(u'без Акт 14/15 не се твърди нищо', not any(u"СЛЕД" in x for x in h3), h3)

# ── Акт 15, когато няма Акт 14 ───────────────────────────────────────────
AKT15 = dok(u"AKT15", u"01.07.2020", vid=u"Акт обр. 15")
h4 = hron([AKT15, KASNO])
red4 = [x for x in h4 if u"СЛЕД" in x]
t(u'сравнява се с Акт 15, щом няма Акт 14', len(red4) == 1 and u"Акт 15" in red4[0], h4)

# ── не само бетон и армировка ────────────────────────────────────────────
DRUG = dok(u"DEKLARACIA", u"04.10.2021", vid=u"Декларация", fajl=u"dogradni.pdf",
           material=u"Дограма PVC", nomer=u"77")
h5 = hron([AKT14, DRUG])
t(u'важи за всеки материал, не само за бетон',
  any(u"Дограма" in x for x in h5 if u"СЛЕД" in x), h5)

# ── много декларации: изрежда се, но не залива ───────────────────────────
mnogo = [dok(u"DEKLARACIA", u"04.10.2021", vid=u"Декларация", fajl=u"d%d.pdf" % i,
             material=u"Бетон", nomer=str(100 + i)) for i in range(9)]
h6 = hron([AKT14] + mnogo)
red6 = [x for x in h6 if u"СЛЕД" in x][0]
t(u'броят е верен', u"9 декларации" in red6, red6)
t(u'изреждат се първите шест и се казва колко още', u"и още 3" in red6, red6)

for x in dobri:
    print(u'  ok  ' + x)
for x in loshi:
    print(u'  LO  ' + x)
print()
print((u'%d проблема' % len(loshi)) if loshi
      else (u'%d проверки — закъснелите декларации се виждат' % len(dobri)))
sys.exit(1 if loshi else 0)

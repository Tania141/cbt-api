# -*- coding: utf-8 -*-
u"""Кои редове вижда четецът и как се показва доказаният ред.

Операторът, 20.10.2026 (истински ОСИП за външно кабелно): „защо чеклистът
разменя редовете и информацията“. Визата кацна на „Одобрени инвестиционни
проекти“, договорът с ЕРМ — на „Разрешения за ползване на външни мрежи“, а
становището на ПБЗН — на „Становище за СКО“. Причината: на четеца се подаваха
само редовете за фаза „въвеждане“, а истинските редове са във фаза „до
разрешение“ и никога не са му били предлагани.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rules import sloy2  # noqa: E402

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + (u'' if verno else u'  -> %r' % (kak,)))


vsichki = sloy2._vsichki_redove()
od = sloy2._redove_za_faza(u'od')
osip = sloy2._redove_za_faza(u'osip')

t(u'има редове и за двете фази', len(od) > 10 and len(osip) > 10, (len(od), len(osip)))
t(u'всички редове са събрани', len(vsichki) == len(od) + len(osip), (len(vsichki), len(od), len(osip)))
t(u'имената са уникални', len(set(vsichki)) == len(vsichki))

# Точните три реда, които са липсвали на четеца.
for red in (u'Виза за проектиране', u'Договор за присъединяване',
            u'Съгласуван проект с ПБЗН — положително становище за съответствие на техническия '
            u'проект с правилата и нормите за пожарна безопасност'):
    t(u'четецът вижда „%s…“' % red[:40], red in vsichki, red)
    t(u'и той НЕ е във фазата на Акт 15', red not in od, red)

# Схемата, която се подава на четеца, носи всички.
sh = sloy2.shema_dokument(vsichki)
enum = sh[u'properties'][u'cheklist_red'][u'enum']
t(u'схемата ги предлага', u'Виза за проектиране' in enum and u'Договор за присъединяване' in enum)
t(u'и позволява празно', u'' in enum)

# Ред от ДРУГА фаза вече не е „старо четене“.
dok = [{u'fajl': u'Виза.pdf', u'cheklist_red': u'Виза за проектиране',
        u'vid': u'Виза за проектиране', u'vid_kod': u'DRUGO',
        u'nomer': {u'stoynost': u'САГ23-ГР00-2792'}, u'data': {u'stoynost': u'18.12.2023'}},
       {u'fajl': u'ДПЕРМ.pdf', u'cheklist_red': u'Договор за присъединяване',
        u'vid': u'Договор за присъединяване', u'vid_kod': u'PRISAEDINYAVANE',
        u'nomer': {u'stoynost': u'1206036213'}, u'data': {u'stoynost': u'29.10.2015'}},
       {u'fajl': u'ДПЕРМ етапност.pdf', u'cheklist_red': u'Договор за присъединяване',
        u'vid': u'Договор за присъединяване', u'vid_kod': u'PRISAEDINYAVANE',
        u'nomer': {u'stoynost': u'2206'}, u'data': {u'stoynost': u'23.10.2025'}}]
r = sloy2.sravni(dok, agenda=u'od')
redove = {e[u'dokument']: e for e in r[u'predlozhenie']}
t(u'редът от ОСИП фазата се пази', u'Виза за проектиране' in redove, list(redove))
t(u'и не влиза в „без ред“', not any(u'Виза' in x for x in r[u'bez_red']), r[u'bez_red'])

# Един ред, доказан от два файла — всеки със своя номер.
dp = redove.get(u'Договор за присъединяване', {})
ot = dp.get(u'dokazano_ot') or []
t(u'редът помни и двата документа', len(ot) == 2, ot)
t(u'всеки носи своя номер',
  any(u'1206036213' in (x[u'nomer'] or u'') for x in ot)
  and any(u'2206' in (x[u'nomer'] or u'') for x in ot), ot)
t(u'и своя файл', {x[u'fajl'] for x in ot} == {u'ДПЕРМ.pdf', u'ДПЕРМ етапност.pdf'}, ot)

for x in dobri:
    print(u'  ok  ' + x)
for x in loshi:
    print(u'  LO  ' + x)
print()
print((u'%d проблема' % len(loshi)) if loshi
      else (u'%d проверки — четецът вижда всички редове' % len(dobri)))
sys.exit(1 if loshi else 0)

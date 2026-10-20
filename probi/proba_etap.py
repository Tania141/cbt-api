# -*- coding: utf-8 -*-
u"""Двете числа на готовността и групите „едно от“.

Операторът, 20.10.2026: „за тази оценка имаме 50 % готовност“ — но да
ЗАПОЧНЕШ и да ПОДПИШЕШ са различни въпроси с различни отговори. Затова всеки
ред носи етап: `начало` или `подпис`.

И: виза за проектиране ИЛИ подробен устройствен план — едното от двете стига.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rules import cheklist_dokumenti as chd  # noqa: E402

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + (u'' if verno else u'  -> %r' % (kak,)))


SGRADA = {u'вид': u'сграда', u'категория': u'4'}
LINEEN = {u'вид': u'линеен', u'категория': u'4'}


def spisak(pr, nalichni):
    return chd.spisak(pr, [{u'dokument': d, u'nomer': u'1/2026'} for d in nalichni],
                      faza=u'osip')


# ── етапът се чете от чеклиста ───────────────────────────────────────────
redove = chd.chetene()
t(u'всеки ред носи етап', all(r.get(u'etap') in (u'начало', u'подпис') for r in redove))
nachalo = {r[u'dokument'] for r in redove if r[u'etap'] == u'начало'}
t(u'договорът за надзор е в началото', u'Договор за упражняване на строителен надзор' in nachalo)
t(u'инвестиционният проект е в началото', u'Инвестиционен проект по всички части' in nachalo)
t(u'становищата са за подписа', u'Становище от РЗИ' not in nachalo)

# ── поправките на оператора ──────────────────────────────────────────────
r = spisak(LINEEN, [])
imena = {x[u'dokument']: x for x in r[u'redove']}
t(u'геоложки доклад не се иска за линеен',
  imena[u'Инженерно-геоложки доклад'][u'sastoyanie'] == u'не се изисква',
  imena[u'Инженерно-геоложки доклад'][u'sastoyanie'])
t(u'геоложки доклад се иска за сграда',
  {x[u'dokument']: x for x in spisak(SGRADA, [])[u'redove']}
  [u'Инженерно-геоложки доклад'][u'sastoyanie'] == u'не е доказано')
t(u'договорът за присъединяване е в началото при линеен',
  imena[u'Договор за присъединяване'][u'etap'] == u'начало')
t(u'оценката на техническия контрол влезе', u'Оценка от техническия контрол по част „Конструктивна“' in imena)
t(u'пълномощното влезе', u'Пълномощно на представителя на възложителя' in imena)
t(u'заданието за проектиране НЕ е добавено',
  not any(u'Задание за проектиране' in x for x in imena))
t(u'доказателствата за законност на съществуващите съоръжения влязоха',
  u'Доказателства, че съществуващите съоръжения са законни' in imena)

# ── „едно от“: виза ИЛИ ПУП ──────────────────────────────────────────────
r2 = spisak(SGRADA, [u'Виза за проектиране'])
im2 = {x[u'dokument']: x for x in r2[u'redove']}
t(u'визата е налице', im2[u'Виза за проектиране'][u'sastoyanie'] == u'налице')
t(u'ПУП вече не се изисква',
  im2[u'Подробен устройствен план'][u'sastoyanie'] == u'не се изисква',
  im2[u'Подробен устройствен план'][u'sastoyanie'])
t(u'и си личи защо', im2[u'Подробен устройствен план'].get(u'dokazan_ot_grupata') is True)

r3 = spisak(SGRADA, [u'Подробен устройствен план'])
im3 = {x[u'dokument']: x for x in r3[u'redove']}
t(u'и обратното важи', im3[u'Виза за проектиране'][u'sastoyanie'] == u'не се изисква')

r4 = spisak(SGRADA, [])
im4 = {x[u'dokument']: x for x in r4[u'redove']}
t(u'без нито едно от двете — и двете се искат',
  im4[u'Виза за проектиране'][u'sastoyanie'] == u'не е доказано'
  and im4[u'Подробен устройствен план'][u'sastoyanie'] == u'не е доказано')

# ── двете числа ──────────────────────────────────────────────────────────
prazen = spisak(LINEEN, [])
t(u'празен обект: 0 % и за двете',
  prazen[u'da_zapochna'][u'procent'] == 0 and prazen[u'da_podpisha'][u'procent'] == 0,
  (prazen[u'da_zapochna'][u'procent'], prazen[u'da_podpisha'][u'procent']))

poln = spisak(LINEEN, [x[u'dokument'] for x in prazen[u'redove']
                       if x[u'etap'] == u'начало' and x[u'sastoyanie'] == u'не е доказано'])
t(u'щом началото е пълно — 100 % за започване',
  poln[u'da_zapochna'][u'procent'] == 100, poln[u'da_zapochna'])
t(u'но подписът остава 0 %', poln[u'da_podpisha'][u'procent'] == 0)
t(u'двете числа броят различни редове',
  poln[u'da_zapochna'][u'ot'] != poln[u'da_podpisha'][u'ot'],
  (poln[u'da_zapochna'][u'ot'], poln[u'da_podpisha'][u'ot']))
t(u'сборът им е всичко изисквано',
  poln[u'da_zapochna'][u'ot'] + poln[u'da_podpisha'][u'ot'] == poln[u'iziskvani'],
  (poln[u'da_zapochna'][u'ot'], poln[u'da_podpisha'][u'ot'], poln[u'iziskvani']))
t(u'казва се КОЕ липсва, не само колко',
  all(isinstance(x, str) for x in poln[u'da_podpisha'][u'nyama']) and poln[u'da_podpisha'][u'nyama'])

for x in dobri:
    print(u'  ok  ' + x)
for x in loshi:
    print(u'  LO  ' + x)
print()
print((u'%d проблема' % len(loshi)) if loshi
      else (u'%d проверки — двете числа и групите са наред' % len(dobri)))
sys.exit(1 if loshi else 0)

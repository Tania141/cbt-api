# -*- coding: utf-8 -*-
u"""Раздел А, когато докладът е по чл. 154.

Операторът, 19.10.2026: изменението „е върху одобрения проект и на практика
разказва какво се е променило, че да имаме искане за 154“ — затова предметът
влиза в самото основание, а не в бележка под него.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cbt_docx  # noqa: E402

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + (u'' if verno else u'  -> %r' % (kak,)))


f = cbt_docx.osip_osnovanie_154

t(u'първият доклад не носи чл. 154', f({}) == u'')
t(u'нито когато поводът е друг', f({u'ОСИП_Повод': u'чл. 142'}) == u'')

pred = u'Апартамент № 4 се разделя на апартамент № 4 и апартамент № 4а.'
red = f({u'ОСИП_Повод': u'чл. 154', u'ОСИП_Предмет_Изменение': pred,
         u'ОСИП_Изменя_Доклад': u'№ 12 от 03.02.2026'})
t(u'цитира се чл. 154, ал. 5', u'чл. 154, ал. 5' in red, red)
t(u'разказът е в основанието', u'апартамент № 4а' in red, red)
t(u'сочи се изменяваният доклад', u'комплексен доклад № 12 от 03.02.2026' in red, red)
t(u'точката не се удвоява', red.endswith(u'26;') and u'.,' not in red, red)

bez = f({u'ОСИП_Повод': u'чл. 154', u'ОСИП_Предмет_Изменение': pred})
t(u'без номер на предишния доклад редът пак е цял',
  bez.startswith(u'—') and bez.endswith(u';') and u'комплексен доклад' not in bez, bez)

samo = f({u'ОСИП_Повод': u'чл. 154'})
t(u'без разказ остава само основанието',
  samo == u'— чл. 154, ал. 5 от ЗУТ за оценка на съответствието на изменението'
          u' на одобрения инвестиционен проект;', samo)

for x in dobri:
    print(u'  ok  ' + x)
for x in loshi:
    print(u'  LO  ' + x)
print()
print((u'%d проблема' % len(loshi)) if loshi
      else (u'%d проверки — основанието по чл. 154 е наред' % len(dobri)))
sys.exit(1 if loshi else 0)

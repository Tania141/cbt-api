# -*- coding: utf-8 -*-
import sys, io
sys.path.insert(0, r'C:\project\cbt-api')
from rules import zapiski as z

dobri, loshi = [], []
def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ('' if verno else '  -> %r' % (kak,)))

S = ['Раздел първи\nСградата се разполага в южната част на имота.\nТеренът е равнинен.\n',
     'Раздел втори\nСградата се захранва от собствен водоизточник.\nИнсталацията е изолирана.\n']

z1 = {'opisanie_blokove': [
    {'podzaglavie': 'Ситуация', 'nachalo': 'Сградата се разполага', 'kraj': 'Теренът е равнинен'},
    {'podzaglavie': 'Вода', 'nachalo': 'Сградата се захранва', 'kraj': 'Инсталацията е изолирана'}]}
t('срязва и през две страници', z.izreji_blokove(z1, S) == 2)
t('текстът е цял', 'Теренът е равнинен' in z1['opisanie_blokove'][0]['tekst'])
t('отбелязва се, че е срязан', z1['opisanie_blokove'][0].get('srezan') is True)

# пренос на дума и различни интервали не пречат
S2 = ['Сградата  се\nразполага в южната\nчаст на имота. Теренът е  равнинен.']
z2 = {'opisanie_blokove': [{'podzaglavie': 'С', 'nachalo': 'Сградата се разполага в южната',
                            'kraj': 'Теренът е равнинен'}]}
t('различните интервали и нови редове не пречат', z.izreji_blokove(z2, S2) == 1,
  z2['opisanie_blokove'][0].get('tekst'))

# каквото не се намери, остава от четеца
z3 = {'opisanie_blokove': [{'podzaglavie': 'Няма', 'nachalo': 'това го няма',
                            'kraj': 'никъде', 'tekst': 'препис от четеца'}]}
t('ненамереното пази преписа', z.izreji_blokove(z3, S) == 0
  and z3['opisanie_blokove'][0]['tekst'] == 'препис от четеца')

# скан без текст: нищо не се пипа
z4 = {'opisanie_blokove': [{'podzaglavie': 'Скан', 'tekst': 'целият текст от скана'}]}
t('при скан преписът остава', z.izreji_blokove(z4, []) == 0
  and z4['opisanie_blokove'][0]['tekst'] == 'целият текст от скана')

# краят се търси СЛЕД началото
S5 = ['Теренът е равнинен. Сградата се разполага в южната част. Теренът е равнинен.']
z5 = {'opisanie_blokove': [{'podzaglavie': 'Р', 'nachalo': 'Сградата се разполага',
                            'kraj': 'Теренът е равнинен'}]}
z.izreji_blokove(z5, S5)
t('краят се търси след началото',
  z5['opisanie_blokove'][0]['tekst'].startswith('Сградата'), z5['opisanie_blokove'][0]['tekst'])

for x in dobri: print('  ok  ' + x)
for x in loshi: print('  LO  ' + x)
print()
print(('%d проблема' % len(loshi)) if loshi else ('%d проверки — изрязването е наред' % len(dobri)))
sys.exit(1 if loshi else 0)

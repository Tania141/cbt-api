# -*- coding: utf-8 -*-
"""Научените редове — условието и поправката на старите.

Операторът, 27.10.2026: „операторът с времето да научи системата за различните
типове обекти и тогава системата ще натрупа чеклиста и ще търси верни такива“.

Две неща пази тази проба:
  · условието разбира „или“ — ред, видян при шахтов ТП И при БКТП, важи при
    единия или при другия, без да става „вид = линеен“;
  · старите уроци с „вид = линеен“ се поправят от запазените съставки. Дотук
    те бяха МЪРТВИ: признаците не носеха вида, тоест редът никога не ставаше
    приложим и наученото мълчеше.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

from rules.cheklist_dokumenti import prilozhim, _redove_sas_sobstveni, PRECENKA

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))


# ── условието ───────────────────────────────────────────────────────────────
pr = {"sast_shtp": True, "sast_kabel_srn": True, "kategoria": "3", "vid": "lineen"}

t("„винаги“ важи", prilozhim("винаги", pr))
t("притежавана съставка важи", prilozhim("sast_shtp", pr))
t("непритежавана не важи", not prilozhim("sast_bktp", pr))
t("„или“ хваща едната", prilozhim("sast_bktp или sast_shtp", pr))
t("„или“ с две чужди не хваща", not prilozhim("sast_bktp или sast_zru", pr))
t("„и“ иска двете", prilozhim("sast_shtp и kategoria = 3", pr))
t("„и“ пада при едно невярно", not prilozhim("sast_shtp и kategoria = 4", pr))
t("„или“ вътре в „и“ се разбира",
  prilozhim("sast_bktp или sast_shtp и kategoria = 3", pr))
t("видът се чете по код", prilozhim("vid = lineen", pr))

# ── поправката на старите уроци ─────────────────────────────────────────────
def uslovie_na(red):
    ime = red["dokument"]
    for x in _redove_sas_sobstveni([red]):
        if x["dokument"] == ime:
            return x["uslovie"]
    return None


star = {"dokument": "Удостоверение за нанасяне на БКТП",
        "uslovie": "вид = линеен и ако_е_приложимо",
        "sastavki": ["shtp", "kabel_srn"], "etap": "подпис"}
u = uslovie_na(star)
t("старият урок се прави от съставките",
  u == "sast_shtp или sast_kabel_srn и " + PRECENKA, u)
t("и остава за преценка", PRECENKA in u, u)
t("и вече е приложим при такъв строеж", prilozhim(u.replace(" и " + PRECENKA, ""), pr), u)

bez = {"dokument": "Нещо без съставки", "uslovie": "вид = линеен и ако_е_приложимо",
       "sastavki": []}
t("без запазени съставки мъртвата част се МАХА, а редът остава",
  uslovie_na(bez) == PRECENKA, uslovie_na(bez))

samo = {"dokument": "Само вид", "uslovie": "вид = линеен", "sastavki": []}
t("условие само от мъртвата част става „за преценка“",
  uslovie_na(samo) == PRECENKA, uslovie_na(samo))

dobar = {"dokument": "Нормален ред", "uslovie": "sast_shtp и ако_е_приложимо",
         "sastavki": ["shtp"]}
t("здравото условие не се пипа",
  uslovie_na(dobar) == "sast_shtp и " + PRECENKA, uslovie_na(dobar))

prazno = {"dokument": "Без условие"}
t("липсващото условие става „за преценка“",
  uslovie_na(prazno) == PRECENKA, uslovie_na(prazno))

# ── научен ред си личи и казва откъде е ─────────────────────────────────────
red = [x for x in _redove_sas_sobstveni([star]) if x["dokument"] == star["dokument"]][0]
t("научен ред си личи", red.get("sobstven") is True, red)
t("и носи основание", bool(str(red.get("osnovanie") or "").strip()), red)

for x in dobri:
    print("  ok  " + x)
for x in loshi:
    print("  ЛО  " + x)
print(("\n%d проблема" % len(loshi)) if loshi
      else ("\n%d проверки — наученото важи и може да се прочете" % len(dobri)))
sys.exit(1 if loshi else 0)

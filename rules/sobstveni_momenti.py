# -*- coding: utf-8 -*-
u"""Твоите редове в моментите — в „Липсва ми“ (25.11.2026).

Дотук собствените редове (`cheklist_sobstveni`: „изисквай“ от „Подобни обекти“
и „приеми“ от „Видени, но неописани“) влизаха само в чеклиста на документите
(`/api/cheklist`). Моментите (`/api/nadzor`) се строят от файла на моментите
(`rules/momenti.py`) и не ги виждаха — екранът го казваше честно, но „изисквай“
не стигаше до Акт 15. Операторът, 25.11.2026: „давай“.

Правилата:
  · КЪДЕ: „за да подпиша“ → Акт 15; „за да започна“ → Протокол 2 (предложено
    на 25.11.2026 и прието).
  · КОГА: само ако условието важи за строежа — вида (`вид ∈ сграда`) или
    съставките (`sast_…`). Условията се нормализират от кухнята
    (`_redove_sas_sobstveni`), не тук: старите „вид = …“ стават съставки там.
  · „ЗА ПРЕЦЕНКА“ (приетото от „Видени, но неописани“) излиза, но носи
    `za_precenka` — екранът не го брои за липсващо, докато операторът не реши.
  · Ред със същото име като ред от моментите не се дублира.
  · Нищо в заключените файлове не се пипа; кухнята само се вика.
"""

# Признакът „вид“ идва от браузъра с кода на вида (`sgrada`), а условията на
# собствените редове са с думите на сървъра (`cbt_docx._osip_priznaci`).
VID_DUMI = {"sgrada": "сграда", "lineen": "линеен", "lineen_ktp": "линеен", "saorajenie": "съоръжение"}

MOMENT_ZA_ETAP = {"подпис": "Акт 15", "начало": "Протокол 2"}


def priznaci_s_vid(priznaci):
    pr = dict(priznaci or {})
    v = str(pr.get("вид") or pr.get("vid") or "").strip()
    pr["вид"] = VID_DUMI.get(v, v)
    return pr


def dobavi(grupi, sobstveni, priznaci, vidimi):
    u"""Добавя приложимите собствени редове в групите на моментите (на място).

    `vidimi` — моментите, които се показват за тази фаза (без тях ред няма къде
    да отиде и не се добавя). Връща добавените — за пробата и за броенето.
    """
    from . import cheklist_dokumenti as chd
    pr = priznaci_s_vid(priznaci)
    imena = {str(d.get("dokument", "")).strip().lower() for g in grupi for d in g.get("dokumenti", [])}
    po_moment = {g["moment"]: g for g in grupi}
    dobaveni = []
    for red in chd._redove_sas_sobstveni(sobstveni or []):
        if not red.get("sobstven"):
            continue
        ime = red["dokument"].strip()
        if not ime or ime.lower() in imena:
            continue
        chasti = [x.strip() for x in str(red.get("uslovie") or "").split(" и ") if x.strip()]
        precenka = chd.PRECENKA in chasti
        ostanali = " и ".join(x for x in chasti if x != chd.PRECENKA) or "винаги"
        if not chd.prilozhim(ostanali, pr):
            continue
        moment = MOMENT_ZA_ETAP.get(red.get("etap"), "Акт 15")
        if moment not in vidimi:
            continue
        g = po_moment.get(moment)
        if g is None:
            g = {"moment": moment, "dokumenti": []}
            po_moment[moment] = g
            # на мястото си по реда на моментите
            poz = next((i for i, x in enumerate(grupi) if vidimi.index(x["moment"]) > vidimi.index(moment)), len(grupi))
            grupi.insert(poz, g)
        d = {"dokument": ime, "uslovie": "", "etap": red.get("etap") or "подпис", "iskan_na": moment,
             "sobstven": True, "osnovanie": red.get("osnovanie") or "добавен от оператора",
             "za_precenka": precenka}
        g["dokumenti"].append(d)
        imena.add(ime.lower())
        dobaveni.append(d)
    return dobaveni

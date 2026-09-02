"""Екипът на обекта — има ли кой да подпише.

На всеки обект участват различни хора, а не целият заверен списък на фирмата.
Затова специалистите се избират по проект (`employees`), а не се наследяват
наготово от консултанта.

Оттук идва проверка, която дотогава беше невъзможна: документ, съставен по
част, за която на обекта няма ангажирано правоспособно лице. Наредба № 3
иска подписи ПО СЪОТВЕТНАТА ЧАСТ — ако такъв човек не участва, документът
не може да бъде подписан както трябва.
"""
from .engine import rule, Verdict, OK, WARN, UNKNOWN


def _po_chast(hora):
    return {(h.get("specialization") or "").strip() for h in (hora or []) if h.get("name")}


def _p(**kw):
    d = {"docDates": kw.pop("docDates", {})}
    d.update(kw)
    return d


_SN = [{"name": "Мария Георгиева", "specialization": "Архитектура", "title": "арх."},
       {"name": "Николай Петров", "specialization": "ВиК"}]
_PJ = [{"name": "Анна Колева", "specialization": "Архитектура", "title": "арх."},
       {"name": "Петър Димов", "specialization": "ВиК"}]


@rule(
    code="T1",
    title="Всяка част с акт обр. 12 има участващ специалист и проектант",
    citation="Наредба № 3, Приложение № 12 — актът се подписва от строителя, от технически "
             "правоспособното лице ПО СЪОТВЕТНАТА ЧАСТ към лицето, упражняващо строителен "
             "надзор, и от проектанта ПО СЪЩАТА ЧАСТ.",
    what="За всяка част, по която има вписани актове обр. 12, на обекта трябва да участва "
         "специалист на надзора по тази част и проектант по нея. Ако липсва, актът няма кой "
         "да го подпише правоспособно.",
    cases=[
        ("двете части са покрити",
         _p(employees=_SN, projectants=_PJ,
            docDates={"akt12": {"Архитектура": {"br": "2"}, "ВиК": {"br": "1"}}}), OK),
        ("акт по Електро, но никой по Електро не участва",
         _p(employees=_SN, projectants=_PJ,
            docDates={"akt12": {"Архитектура": {"br": "2"}, "Електро": {"br": "1"}}}), WARN),
        ("има специалист, липсва проектант по частта",
         _p(employees=_SN + [{"name": "Иван Стоев", "specialization": "Електро"}], projectants=_PJ,
            docDates={"akt12": {"Електро": {"br": "1"}}}), WARN),
        ("още няма актове обр. 12",
         _p(employees=_SN, projectants=_PJ, docDates={}), UNKNOWN),
        ("екипът още не е избран",
         _p(projectants=_PJ, docDates={"akt12": {"ВиК": {"br": "1"}}}), UNKNOWN),
    ],
)
def akt12_ima_koj_da_podpishe(project):
    grupi = (project.get("docDates") or {}).get("akt12") or {}
    if not grupi:
        return Verdict(UNKNOWN, "Още няма актове обр. 12.")
    sn = _po_chast(project.get("employees"))
    pj = _po_chast(project.get("projectants"))
    if not sn:
        return Verdict(UNKNOWN, "Екипът на надзора за обекта още не е избран.")

    problemi = []
    for chast in sorted(grupi):
        lipsvat = []
        if chast not in sn:
            lipsvat.append("специалист на надзора")
        if pj and chast not in pj:
            lipsvat.append("проектант")
        if lipsvat:
            problemi.append(f"{chast}: няма {' и '.join(lipsvat)} по тази част")
    if problemi:
        return Verdict(WARN, "Актове обр. 12 — " + "; ".join(problemi) +
                             ". Наредбата иска подписи по съответната част.")
    return Verdict(OK, f"Всички {len(grupi)} части с актове обр. 12 имат участващ специалист "
                       f"и проектант.")


@rule(
    code="T2",
    title="Екипът на надзора за обекта е избран",
    citation="чл. 168, ал. 3 ЗУТ — лицето, упражняващо строителен надзор, подписва всички актове "
             "и протоколи по време на строителството; подписват правоспособните физически лица "
             "от заверения списък, по съответните части.",
    what="Специалистите, които се вписват в документите, трябва да са избраните за ТОЗИ обект. "
         "Ако изборът не е направен, документите изброяват целия заверен списък на фирмата — "
         "включително хора, които не са стъпвали на строежа.",
    cases=[
        ("избран екип", _p(employees=_SN), OK),
        ("никой не е отметнат", _p(employees=[]), WARN),
        ("изборът още не е правен", _p(), UNKNOWN),
    ],
)
def ekip_izbran(project):
    e = project.get("employees")
    if e is None:
        return Verdict(UNKNOWN, "Екипът за обекта още не е избиран — документите ще изброят "
                                "целия заверен списък на консултанта.")
    if not e:
        return Verdict(WARN, "Нито един специалист не е отметнат за този обект — "
                             "подписните таблици ще излязат празни.")
    chasti = sorted(_po_chast(e))
    return Verdict(OK, f"{len(e)} специалисти по части: {', '.join(chasti)}.")

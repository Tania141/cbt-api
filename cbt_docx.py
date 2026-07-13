"""
cbt_docx.py — Document-building helpers for АКТ СИСТЕМ.
Extracted from api.py (refactor only, no behavior change).
"""
from datetime import datetime
from copy import deepcopy
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ── Name / date helpers ───────────────────────────────────────────────────────

def two_names(s):
    parts = (s or "").strip().split()
    return " ".join(parts[:2])

def one_and_three(s):
    parts = (s or "").strip().split()
    if len(parts) >= 3:
        return f"{parts[0]} {parts[2]}"
    return " ".join(parts)

def fmt_date(v):
    if not v: return ""
    v = v.strip()
    if "." in v: return v
    try: return datetime.fromisoformat(v[:10]).strftime("%d.%m.%Y")
    except: return v


# ── People extractors (used only by build_placeholders) ───────────────────────

def extract_employees(d):
    n = int(d.get("Служители_Брой", 0) or 0)
    return [{
        "name": d.get(f"Служител_{i}_Име",""),
        "specialization": d.get(f"Служител_{i}_Специализация",""),
        "title": d.get(f"Служител_{i}_Титла","инж.")
    } for i in range(1, n+1) if d.get(f"Служител_{i}_Име","")]

def extract_projectants(d):
    n = int(d.get("Проектанти_Брой", 0) or 0)
    return [{
        "name": d.get(f"Проектант_{i}_Име",""),
        "ppp": d.get(f"Проектант_{i}_ППП",""),
        "specialization": d.get(f"Проектант_{i}_Специализация",""),
        "title": d.get(f"Проектант_{i}_Титла","инж.")
    } for i in range(1, n+1) if d.get(f"Проектант_{i}_Име","")]

def by_spec(items, spec):
    return [e for e in items if e.get("specialization") == spec]


# ── Structural block builders ─────────────────────────────────────────────────

def build_vazlogitel_block(d):
    tip   = d.get("Възложител_Тип", "Фирма")
    firma = d.get("Възложител_Фирма", "")
    adres = d.get("Възложител_Адрес", "")
    if tip in ("Физическо лице", "ФЛ"):
        return firma + (f", {adres}" if adres else "")
    eik  = d.get("Възложител_ЕИК", "")
    pred = d.get("Възложител_Представител", "")
    parts = [firma]
    if eik:   parts.append(f"ЕИК {eik}")
    if adres: parts.append(adres)
    if pred:  parts.append(f"представлявано от {pred}")
    return ", ".join(parts)

def build_projectants_list(projectants):
    lines = []
    for p in projectants:
        spec = p["specialization"]
        title = p["title"]
        name = p["name"]
        ppp = p["ppp"]
        kamara = "КАБ" if spec in ("Архитектура", "Паркоустройство и Благоустройство") else "КИИП"
        line = "Част " + spec + ": " + title + " " + name
        if ppp:
            line += ", рег. № " + ppp + " в " + kamara
        lines.append(line)
    return "\n".join(lines)

def build_employees_list(employees):
    return "\n".join(f"Част {e['specialization']}: {e['title']} {e['name']}" for e in employees)

def build_projectants_signatures(projectants):
    return "\n".join(
        f"Част {p['specialization']}: {p['title']} {p['name']} ….................................................................."
        for p in projectants
    )

def build_employees_signatures(employees):
    return "\n".join(
        f"Част {e['specialization']}: {e['title']} {e['name']} ….................................................................."
        for e in employees
    )

def build_placeholders(d):
    employees   = extract_employees(d)
    projectants = extract_projectants(d)

    geo     = (by_spec(employees, "Геодезия") or [{}])[0].get("name", d.get("Геодезист",""))
    sn_k    = (by_spec(employees, "Конструктивна") or [{}])[0].get("name", "")
    pj_k    = (by_spec(projectants, "Конструктивна") or [{}])[0].get("name", "")
    pj_arch = (by_spec(projectants, "Архитектура") or [{}])[0].get("name", "")
    specs   = "; ".join(f"{e['title']} {e['name']} ({e['specialization']})" for e in employees) or d.get("Консултант_Управител","")
    vaz_tip = d.get("Възложител_Тип", "Фирма")
    upr     = d.get("Консултант_Управител", "")
    teh_ryk = d.get("Строител_ТехРък", "")
    str_upr = d.get("Строител_Управител", "")
    vaz_pr  = d.get("Възложител_Представител", "")
    # Възложител_1и3: prefer explicit signing person, fall back to ФЛ name or representative
    vaz_podpisva = d.get("Възложител_Подписва", "")
    vaz_name_for_1i3 = vaz_podpisva or (d.get("Възложител_Фирма", "") if vaz_tip in ("Физическо лице", "ФЛ") else vaz_pr)

    return {
        "{{Строеж}}":                    d.get("Строеж",""),
        "{{Адрес}}":                     d.get("Адрес",""),
        "{{Консултант_Фирма}}":          d.get("Консултант_Фирма",""),
        "{{Консултант_ЕИК}}":            d.get("Консултант_ЕИК",""),
        "{{Консултант_Адрес}}":          d.get("Консултант_Адрес",""),
        "{{Консултант_Управител}}":      upr,
        "{{Консултант_Удостоверение}}":   d.get("Консултант_Удостоверение",""),
        "{{Управител_2имена}}":          two_names(upr),
        "{{Управител_1и3}}":             one_and_three(upr),
        "{{Строител_Фирма}}":            d.get("Строител_Фирма",""),
        "{{Строител_ЕИК}}":              d.get("Строител_ЕИК",""),
        "{{Строител_Адрес}}":            d.get("Строител_Адрес",""),
        "{{Строител_Управител}}":        str_upr,
        "{{Строител_Управител_2имена}}": two_names(str_upr),
        "{{Строител_Управител_1и3}}":    one_and_three(str_upr),
        "{{Строител_ТехРък}}":           teh_ryk,
        "{{ТехРък_2имена}}":             two_names(teh_ryk),
        "{{ТехРък_1и3}}":               one_and_three(teh_ryk),
        "{{tech_director}}":             teh_ryk,
        "{{Възложител_Тип}}":            vaz_tip,
        "{{Възложител_Фирма}}":          d.get("Възложител_Фирма",""),
        "{{Възложител_ЕИК}}":            d.get("Възложител_ЕИК","") if vaz_tip not in ("Физическо лице","ФЛ") else "",
        "{{Възложител_Адрес}}":          d.get("Възложител_Адрес",""),
        "{{Възложител_Представител}}":   vaz_pr if vaz_tip not in ("Физическо лице","ФЛ") else "",
        "{{Възложител_2имена}}":         two_names(vaz_name_for_1i3),
        "{{Възложител_1и3}}":           one_and_three(vaz_name_for_1i3),
        "{{Възложител_Блок}}":           build_vazlogitel_block(d),   # и (correct, matches template)
        "{{Възложател_Блок}}":           build_vazlogitel_block(d),   # а (legacy alias)
        "{{Възложител_Подписва_Блок}}":  d.get("Възложител_Подписва", "") or build_vazlogitel_block(d),  # и
        "{{Възложател_Подписва_Блок}}":  d.get("Възложател_Подписва", "") or build_vazlogitel_block(d),  # а
        "{{РС_Номер}}":                  d.get("РС_Номер",""),
        "{{РС_Дата}}":                   fmt_date(d.get("РС_Дата","")),
        "{{РС_Издател}}":                d.get("РС_Издател",""),
        "{{РС_ВСила}}":                  fmt_date(d.get("РС_ВСила","")),
        "{{Геодезист}}":                 geo,
        "{{Геодезист_2имена}}":          two_names(geo),
        "{{Геодезист_1и3}}":            one_and_three(geo),
        "{{consultant_specialists}}":    specs,
        "{{sn_konstruktivna}}":          sn_k,
        "{{СН_Конструктивна}}":          sn_k,
        "{{СН_Архитектура}}":            (by_spec(employees, "Архитектура") or [{}])[0].get("name", ""),
        "{{СН_Електро}}":                (by_spec(employees, "Електро") or [{}])[0].get("name", ""),
        "{{СН_ВиК}}":                    (by_spec(employees, "ВиК") or [{}])[0].get("name", ""),
        "{{СН_Геодезия}}":               (by_spec(employees, "Геодезия") or [{}])[0].get("name", ""),
        "{{СН_ПБ}}":                     (by_spec(employees, "ПБ") or [{}])[0].get("name", ""),
        "{{СН_Пътна}}":                  (by_spec(employees, "Пътна") or [{}])[0].get("name", ""),
        "{{СН_ОВК}}":                    (by_spec(employees, "ОВК и ЕЕ") or [{}])[0].get("name", ""),
        "{{Конструктивна}}":             pj_k,
        "{{ПЖ_Конструктивна}}":          pj_k,
        "{{ПЖ_Архитектура}}":            pj_arch,
        "{{Вода}}":                      d.get("Вода", ""),
        "{{Канализация}}":               d.get("Канализация", ""),
        "{{Ел_Захранване}}":             d.get("Ел_Захранване", ""),
        "{{Проектанти_Списък}}":         build_projectants_list(projectants),
        "{{Консултанти_Списък}}":        build_employees_list(employees),
        "{{Проектанти_Подписи}}":        build_projectants_signatures(projectants),
        "{{Консултанти_Подписи}}":       build_employees_signatures(employees),
        "{{Opisanie_Ploshtadka}}":       d.get("Opisanie_Ploshtadka", ""),
        "{{Sastoyanie_Okolo}}":          d.get("Sastoyanie_Okolo", "пътните и тротоарни настилки по прилежащата улица са в добро състояние, съседните имоти няма да бъдат засягани от бъдещото строителство"),
        "{{Merki_PBZ}}":                 d.get("Merki_PBZ", "ще се осъществява от прилежащата улична мрежа съгласно съгласуван ПБЗ"),
        "{{Darvesenost}}":               d.get("Darvesenost", ""),
        "{{Kota_Izkop}}":               d.get("Kota_Izkop", ""),
        "{{Kota_Cokul}}":               d.get("Kota_Cokul", ""),
        "{{Kota_Korniz}}":              d.get("Kota_Korniz", ""),
        "{{Kota_Bilo}}":                d.get("Kota_Bilo", ""),
        "{{Reper_Nomer}}":              d.get("Reper_Nomer", ""),
        "{{Reper_Kota}}":               d.get("Reper_Kota", ""),
        # Кирилични алиаси — същите стойности, различен правопис в Протокол 2
        "{{Кота_Изкоп}}":              d.get("Kota_Izkop", ""),
        "{{Кота_Цокъл}}":              d.get("Kota_Cokul", ""),
        "{{Кота_Корниз}}":             d.get("Kota_Korniz", ""),
        "{{Кота_Bilo}}":               d.get("Kota_Bilo", ""),
        "{{Репер_Номер}}":             d.get("Reper_Nomer", ""),
        "{{Репер_Кота}}":              d.get("Reper_Kota", ""),
        # Описание на строителната площадка — ръчно поле
        "{{Описание_Сграда}}":         d.get("Opisanie_Sgrada", ""),
    }


# ── Template engine ───────────────────────────────────────────────────────────

def insert_paragraphs_after(para, lines, font_name="Times New Roman", font_size=12):
    from docx.shared import Pt
    ref = para._element
    parent = ref.getparent()
    idx = list(parent).index(ref)
    for i, line in enumerate(lines):
        new_p = OxmlElement("w:p")
        new_r = OxmlElement("w:r")
        new_rpr = OxmlElement("w:rPr")
        if para.runs:
            orig_rpr = para.runs[0]._r.find(qn("w:rPr"))
            if orig_rpr is not None:
                new_rpr = deepcopy(orig_rpr)
        new_r.append(new_rpr)
        new_t = OxmlElement("w:t")
        new_t.text = line
        new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        new_r.append(new_t)
        new_p.append(new_r)
        parent.insert(idx + 1 + i, new_p)

def replace_in_runs(para, replacements):
    full = "".join(r.text for r in para.runs)
    if not any(k in full for k in replacements):
        return False

    multiline_key = None
    multiline_val = None
    for k, v in replacements.items():
        if k in full and "\n" in v:
            multiline_key = k
            multiline_val = v
            break

    if multiline_key:
        lines = multiline_val.split("\n")
        first_line = full.replace(multiline_key, lines[0])
        for k, v in replacements.items():
            if k != multiline_key and "\n" not in v:
                first_line = first_line.replace(k, v)
        if para.runs:
            para.runs[0].text = first_line
            for r in para.runs[1:]:
                r.text = ""
        if len(lines) > 1:
            insert_paragraphs_after(para, lines[1:])
        return True

    new_text = full
    for k, v in replacements.items():
        new_text = new_text.replace(k, v)
    if para.runs:
        para.runs[0].text = new_text
        for r in para.runs[1:]:
            r.text = ""
    return False

def fill_template(doc, replacements):
    paras = list(doc.paragraphs)
    for para in paras:
        replace_in_runs(para, replacements)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    replace_in_runs(para, replacements)
    for section in doc.sections:
        for para in section.header.paragraphs:
            replace_in_runs(para, replacements)
        for para in section.footer.paragraphs:
            replace_in_runs(para, replacements)
    return doc

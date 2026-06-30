"""
МОДУЛ ЗА ВАЛИДАЦИЯ (модул 9 по патент №5794 U1, претенция №3)
Извършва независима проверка на генерирания Акт 15 за:
  - пълнота на задължителните полета
  - логическа последователност на датите
Не използва AI — структурирани правила, бързо и предвидимо.
"""

import re
from datetime import datetime


# ───────────────────────────────────────────────
#  ПОМОЩНИ ФУНКЦИИ
# ───────────────────────────────────────────────

def _parse_date(date_str):
    """Опитва се да парсне дата във формат дд.мм.гггг. Връща datetime или None."""
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    if not date_str or date_str in ("—", "-", "???", "[???]"):
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
        if match:
            try:
                d, m, y = map(int, match.groups())
                return datetime(y, m, d)
            except ValueError:
                return None
        return None


def _is_empty(value):
    """Проверява дали стойност е празна, тире, или маркер за липсващи данни."""
    if value is None:
        return True
    if isinstance(value, str):
        v = value.strip()
        return v == "" or v in ("—", "-", "???", "[???]", "....", "не")
    return False


# ───────────────────────────────────────────────
#  ПРАВИЛА ЗА ЗАДЪЛЖИТЕЛНИ ПОЛЕТА (Акт 15)
# ───────────────────────────────────────────────

REQUIRED_FIELDS_AKT15 = [
    # (ключ в manual/d данните, четимо име, секция за съобщението)
    ("rs_number",      "Номер на Разрешение за строеж",        "Строителни книжа"),
    ("rs_date",        "Дата на Разрешение за строеж",          "Строителни книжа"),
    ("rs_issuer",      "Издател на Разрешение за строеж",       "Строителни книжа"),
    ("prot2_date",     "Дата на Протокол 2",                    "Протокол 2"),
    ("kota_izkop",     "Дата на заверка — ниво изкоп",           "Протокол 2"),
    ("kota_cokul",     "Дата на заверка — ниво цокъл",           "Протокол 2"),
    ("kota_korniz",    "Дата на заверка — ниво корниз",          "Протокол 2"),
    ("kota_bilo",      "Дата на заверка — ниво bilo",            "Протокол 2"),
    ("obr3_date",      "Дата на Образец 3",                      "Строителни книжа"),
    ("zk_number",      "Номер на Заповедна книга",               "Строителни книжа"),
    ("zk_date",        "Дата на Заповедна книга",                "Строителни книжа"),
    ("akt14_date",     "Дата на Акт обр. 14",                    "Строителни книжа"),
    ("upulnomoshnik",  "Упълномощен представител",               "Решение"),
]

# Полета, чийто ред на датите трябва да е логически нарастващ
DATE_SEQUENCE_AKT15 = [
    ("rs_date",      "Дата на Разрешение за строеж"),
    ("prot2_date",   "Дата на Протокол 2"),
    ("kota_izkop",   "Ниво изкоп"),
    ("kota_cokul",   "Ниво цокъл"),
    ("kota_korniz",  "Ниво корниз"),
    ("kota_bilo",    "Ниво bilo"),
    ("akt14_date",   "Акт обр. 14"),
]


# ───────────────────────────────────────────────
#  ОСНОВНА ФУНКЦИЯ ЗА ВАЛИДАЦИЯ
# ───────────────────────────────────────────────

def validate_akt15(manual_data, passport_data=None, apartments=None):
    """
    Валидира входните данни за Акт 15 преди/след генериране.

    Args:
        manual_data: dict с ръчно въведените полета (m обектът от index.html)
        passport_data: dict с паспортните данни (d обектът), по избор
        apartments: list от апартаменти с НА данни, по избор

    Returns:
        {
            "status": "green" | "yellow" | "red",
            "errors": [...],     # блокиращи проблеми — задължителни липсващи полета
            "warnings": [...],   # некритични — логически проблеми, разминавания
            "summary": "..."     # кратко обобщение за UI
        }
    """
    errors = []
    warnings = []
    passport_data = passport_data or {}
    apartments = apartments or []

    # ── 1. ПРОВЕРКА ЗА ЛИПСВАЩИ ЗАДЪЛЖИТЕЛНИ ПОЛЕТА ──────────────
    missing_by_section = {}
    for key, label, section in REQUIRED_FIELDS_AKT15:
        value = manual_data.get(key)
        if _is_empty(value):
            missing_by_section.setdefault(section, []).append(label)

    for section, fields in missing_by_section.items():
        fields_str = ", ".join(fields)
        errors.append({
            "type": "missing_field",
            "section": section,
            "message": "Липсват данни в раздел „" + section + "“: " + fields_str
        })

    # Актове обр. 7 и 12 — проверка по групи (брой + период)
    akt_groups = [
        ("akt7_br", "akt7_ot", "akt7_do", "Актове обр. 7"),
        ("akt12_arh", None, None, "Актове обр. 12 — Архитектура"),
        ("akt12_vik", None, None, "Актове обр. 12 — ВиК"),
        ("akt12_el", None, None, "Актове обр. 12 — Електро"),
        ("akt12_ovk", None, None, "Актове обр. 12 — ОВК"),
    ]
    for br_key, ot_key, do_key, label in akt_groups:
        val = manual_data.get(br_key)
        if isinstance(val, dict):
            if _is_empty(val.get("br")):
                warnings.append({
                    "type": "missing_optional",
                    "section": "Актове и протоколи",
                    "message": f"{label} — брой и период не са попълнени"
                })
        elif ot_key and (_is_empty(val) or _is_empty(manual_data.get(ot_key)) or _is_empty(manual_data.get(do_key))):
            warnings.append({
                "type": "missing_optional",
                "section": "Актове и протоколи",
                "message": f"{label} — брой и период не са попълнени"
            })

    # ── 2. ЛОГИЧЕСКА ПОСЛЕДОВАТЕЛНОСТ НА ДАТИТЕ ──────────────────
    parsed_dates = []
    for key, label in DATE_SEQUENCE_AKT15:
        raw = manual_data.get(key)
        dt = _parse_date(raw)
        if dt:
            parsed_dates.append((label, dt, raw))

    for i in range(1, len(parsed_dates)):
        prev_label, prev_dt, prev_raw = parsed_dates[i - 1]
        curr_label, curr_dt, curr_raw = parsed_dates[i]
        if curr_dt < prev_dt:
            msg = "„" + curr_label + "“ (" + curr_raw + ") е преди „" + prev_label + "“ (" + prev_raw + ") — проверете датите"
            warnings.append({
                "type": "date_order",
                "section": "Логическа последователност",
                "message": msg
            })

    # РС дата трябва да предхожда РС влизане в сила, ако е налично
    rs_date = _parse_date(manual_data.get("rs_date"))
    rs_effective = _parse_date(passport_data.get("rs_in_force") or manual_data.get("rs_in_force"))
    if rs_date and rs_effective and rs_effective < rs_date:
        warnings.append({
            "type": "date_order",
            "section": "Логическа последователност",
            "message": "Датата на влизане в сила на РС е преди датата на самото РС — проверете"
        })

    # ── 3. ПЪЛНОМОЩНИЦИ — НА данни с пълномощно без посочено име ─
    for apt in apartments:
        has_pelnomoshtno = not _is_empty(apt.get("na_pelnomoshtno_reg"))
        has_pelnomoshtnik_name = not _is_empty(apt.get("pelnomoshtnik"))
        if has_pelnomoshtno and not has_pelnomoshtnik_name:
            apt_label = apt.get("apt", "?")
            warnings.append({
                "type": "missing_pelnomoshtnik",
                "section": "Пълномощници",
                "message": f"Апартамент №{apt_label} — има отбелязано пълномощно, но липсва име на пълномощника"
            })

    # ── 4. ОПРЕДЕЛЯНЕ НА ОБЩ СТАТУС ───────────────────────────────
    if errors:
        status = "red"
        summary = f"{len(errors)} блокиращ{'и' if len(errors) != 1 else ''} проблем{'а' if len(errors) != 1 else ''}, {len(warnings)} предупреждени{'я' if len(warnings) != 1 else 'е'}"
    elif warnings:
        status = "yellow"
        summary = f"Няма липсващи задължителни полета, но има {len(warnings)} предупреждени{'я' if len(warnings) != 1 else 'е'} за проверка"
    else:
        status = "green"
        summary = "Всички задължителни полета са попълнени, датите са в логическа последователност"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "summary": summary
    }

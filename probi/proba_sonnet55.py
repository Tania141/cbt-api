# -*- coding: utf-8 -*-
"""Четецът със Claude Sonnet 5.5 (26.11.2026).

Операторът: „смени го“ (Sonnet 4.6 → Sonnet 5.5). В документацията на API-то:
принуден инструмент (`tool_choice: tool`) връща 400 при Sonnet 5.5 — значи
`auto` + указание; мисленето е включено по подразбиране — за четене се изключва
с `between_tools`. Старият модел остава със старата заявка (смяната е обратима
през `AI_MODEL`). Пробата не ходи до API-то — подменя клиента.
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

from rules import chetci

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))


SH = {"type": "object", "properties": {"vid": {"type": "string"}}}
z55 = chetci.zayavka_claude("claude-sonnet-5-5", SH, [{"type": "text", "text": "страница"}], "Прочети.")
z46 = chetci.zayavka_claude("claude-sonnet-4-6", SH, [{"type": "text", "text": "страница"}], "Прочети.")
t("по подразбиране — Sonnet 5.5", chetci.MODEL_PO_PODRAZBIRANE == "claude-sonnet-5-5")
t("Sonnet 5.5: БЕЗ принуден инструмент (400 иначе) — auto", z55["tool_choice"] == {"type": "auto"}, z55["tool_choice"])
t("Sonnet 5.5: мисленето изключено — between_tools", z55.get("thinking") == {"type": "between_tools"}, z55.get("thinking"))
t("Sonnet 5.5: указание да запише с инструмента", "САМО с инструмента zapishi_dokument" in z55["messages"][0]["content"][-1]["text"])
t("Sonnet 5.5: без temperature, без budget_tokens", "temperature" not in z55 and "budget_tokens" not in str(z55))
t("Sonnet 4.6 (ако AI_MODEL го върне): старата заявка — принуден инструмент, без thinking",
  z46["tool_choice"] == {"type": "tool", "name": "zapishi_dokument"} and "thinking" not in z46, z46)
t("блоковете на страниците не се пипат", z55["messages"][0]["content"][0] == {"type": "text", "text": "страница"})


# ── поведение с подменен клиент ───────────────────────────────────────────────
class Blok:
    def __init__(self, tip, vhod=None):
        self.type, self.input = tip, vhod


class Otgovor:
    def __init__(self, content, stop="end_turn"):
        self.content, self.stop_reason, self.model = content, stop, "claude-sonnet-5-5"
        self.usage = types.SimpleNamespace(input_tokens=1000, output_tokens=200)


def s_otgovor(otg):
    class Potok:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def __iter__(self): return iter([])
        def get_final_message(self): return otg

    class Klient:
        def __init__(self, **kw):
            self.messages = types.SimpleNamespace(stream=lambda **z: Potok())
    fake = types.ModuleType("anthropic")
    fake.Anthropic = Klient
    fake.APIError = type("APIError", (Exception,), {})
    sys.modules["anthropic"] = fake


c = chetci.Claude("k", "claude-sonnet-5-5")
s_otgovor(Otgovor([Blok("tool_use", {"vid": "Разрешение за строеж"})], "tool_use"))
dok, info = c.chete({"blokove": []}, SH, "Прочети.")
t("инструментът е извикан — документът се взима", dok["dokumenti"] == [{"vid": "Разрешение за строеж"}], dok)
t("и казва кой модел е чел", info["model"] == "claude-sonnet-5-5", info)

s_otgovor(Otgovor([Blok("text")]))
try:
    c.chete({"blokove": []}, SH, "Прочети.")
    t("отговор с текст без инструмента → резервният, с думи", False, "мина")
except chetci.NeMozheSega as e:
    t("отговор с текст без инструмента → резервният, с думи", "не записа документа с инструмента" in str(e), str(e))

s_otgovor(Otgovor([], "refusal"))
try:
    c.chete({"blokove": []}, SH, "Прочети.")
    t("отказ (refusal) → резервният, с думи", False, "мина")
except chetci.NeMozheSega as e:
    t("отказ (refusal) → резервният, с думи", "refusal" in str(e), str(e))

api = open(os.path.join(os.path.dirname(__file__), "..", "api.py"), encoding="utf-8").read()
t("api.py: моделът по подразбиране — Sonnet 5.5", 'os.environ.get("AI_MODEL", "claude-sonnet-5-5")' in api)
t("api.py: досието получава модела", 'd["model"] = info.get("model")' in api)

for x in dobri: print("  ok  " + x)
for x in loshi: print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — четецът със Sonnet 5.5")
sys.exit(1 if loshi else 0)

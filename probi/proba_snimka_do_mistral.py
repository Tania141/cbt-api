# -*- coding: utf-8 -*-
"""Снимка (.jpg) стига до резервния четец с байтовете си.

24.11.2026: бетонов дневник .jpg → „Mistral 400: Image, 'data:image/jpeg;base64,',
could not be loaded“. `podgotvi` не връщаше "raw" при снимка, а дневникът,
котите, нивата, собствеността и записките взимат байтовете оттам.
Пробата не ходи до Mistral — хваща какво би му се пратило.
"""
import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

import pymupdf
from rules import sloy2, beton_dnevnik, chetci

dobri, loshi = [], []


def t(ime, verno, kak=None):
    (dobri if verno else loshi).append(ime + ("" if verno else "  → %r" % (kak,)))


# Малка истинска JPEG картина.
pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 40, 30), False)
pix.clear_with(200)
JPG = pix.tobytes("jpeg")
B64 = base64.b64encode(JPG).decode()

prep = sloy2.podgotvi("dnevnik.jpg", "image/jpeg", B64)
t("podgotvi връща байтовете на снимката", prep.get("raw") == JPG, len(prep.get("raw") or b""))

prateno = {}


class Hvashtach(chetci.Mistral):
    def _post(self, pat, body, timeout):
        prateno.setdefault(pat, body)
        if pat == "/ocr":
            return {"pages": [{"index": 0, "markdown": "Подложен бетон к-3,97 | 27.02"}]}
        return {"choices": [{"message": {"content": '{"redove": [{"element": "Подложен бетон к-3,97"}]}'}}],
                "usage": {}}


m = Hvashtach("k", "mistral-ocr", "mistral-small")
try:
    beton_dnevnik.procheti([m], "dnevnik.jpg", "image/jpeg", B64)
except Exception as e:          # отговорът на чата не ни интересува тук
    pass
url = ((prateno.get("/ocr") or {}).get("document") or {}).get("image_url", "")
t("до OCR отива картина с данни, не празна", url.startswith("data:image/jpeg;base64,")
  and len(url) > len("data:image/jpeg;base64,") + 100, url[:60])
t("и това са същите байтове", url.split(",", 1)[-1] == B64, url[:60])

for x in dobri:
    print("  ok  " + x)
for x in loshi:
    print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — снимката стига до четеца")
sys.exit(1 if loshi else 0)

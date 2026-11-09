"""Разделяне по N страници — без АИ.

Радулов, 09.11.2026: акт7-1_8.pdf — 8 акта обр. 7 по една страница — излизаше
като един документ. Операторът знае хартията: „всеки е една страница“.
"""
import base64, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pymupdf
from rules import sloy2

dobri, loshi = [], []
def t(ime, verno, kak=""):
    (dobri if verno else loshi).append(ime + ("" if verno else f"  → {kak}"))

def pdf(n):
    d = pymupdf.open()
    for i in range(n):
        d.new_page().insert_text((72, 72), f"AKT {i + 1}")
    return base64.b64encode(d.tobytes()).decode()

class Gramne:
    ime = "никой"
    def chete(self, *a, **k):
        raise AssertionError("АИ не бива да се пита")

ch, info = sloy2.razdeli([Gramne()], "akt7.pdf", "application/pdf", pdf(8), po_stranici=1)
t("8 страници по 1 → 8 части", [c["stranici"] for c in ch] == [str(i) + "-" + str(i) for i in range(1, 9)], ch)
t("броят страници се връща", info.get("n") == 8, info)
ch, _ = sloy2.razdeli([Gramne()], "akt7.pdf", "application/pdf", pdf(5), po_stranici=2)
t("5 страници по 2 → 2+2+1", [(c["ot"], c["do"]) for c in ch] == [(1, 2), (3, 4), (5, 5)], ch)
ch, _ = sloy2.razdeli([Gramne()], "akt7.pdf", "application/pdf", pdf(8), stranici="3-6", po_stranici=1)
t("избраните страници пазят истинските си номера", [c["ot"] for c in ch] == [3, 4, 5, 6], ch)

for x in dobri: print("  ok  " + x)
for x in loshi: print("  ЛО  " + x)
print(f"\n{len(loshi)} проблема" if loshi else f"\n{len(dobri)} проверки — реже се по страници")
sys.exit(1 if loshi else 0)

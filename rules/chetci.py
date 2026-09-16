"""Четците — тънкият слой между слой 2 и езиковите модели.

РЕШЕНИЕ НА ОПЕРАТОРА (16.09.2026)
--------------------------------
Два четеца: основен и резервен. Системата чете с основния; когато той не може
— свършил кредит, грешен ключ, претоварване — минава сама на резервния, за да
не спре работата, както спря на 15.09.2026. АИ-то само констатира и предлага;
човекът верифицира.

Изборът е измерен, не гадан (пробата с 10 скана от ДЖИХАТ, 15.09.2026):
  Claude  — ръкописни дати 15/17, ръкописът отбелязан 17/17 → ОСНОВЕН
  Mistral — ръкописни дати 10/16, ръкописът отбелязан  0/16 → РЕЗЕРВЕН
Mistral не отбелязва ръкопис, затова документ, прочетен от него, носи
`rakopis_nenadezhden` — всяка стойност от скан е за потвърждение, без изключение.

Тук е САМО преводът: как се пита всеки модел и как се разпознава „не може
сега“. Какво се пита (указание, схема) и какво се прави с отговора (сверка,
сравнение) е в `sloy2.py` и не зависи от четеца.
"""
import base64, json, os


class NeMozheSega(Exception):
    """Четецът не може да чете сега — пари, ключ, претоварване, връзка.
    Опитва се следващият. Грешка в самия файл НЕ е такава — тя е NeSeChete."""


# ── Claude ────────────────────────────────────────────────────────────────────

def _claude_ne_mozhe(e):
    import anthropic
    if isinstance(e, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
        return True
    if isinstance(e, anthropic.APIStatusError):
        kod = getattr(e, "status_code", 0)
        if kod in (401, 402, 403, 408, 429, 500, 502, 503, 504, 529):
            return True
        # Свършилият кредит идва като 400 (15.09.2026: „Your credit balance is too low“).
        return kod == 400 and "credit balance" in str(e).lower()
    return False


class Claude:
    kod = "claude"
    ime = "Claude"
    rakopis_nadezhden = True

    def __init__(self, api_key, model):
        self.api_key, self.model = api_key, model

    def chete(self, prep, shema, tekst, **_):
        """→ (документ, {model, tokens_in, tokens_out}). Claude вижда самите
        страници (`prep["blokove"]`), затова суровият файл не му трябва."""
        import anthropic
        try:
            r = anthropic.Anthropic(api_key=self.api_key).messages.create(
                model=self.model, max_tokens=4000,
                tools=[{"name": "zapishi_dokument",
                        "description": "Записва прочетеното от документа.",
                        "input_schema": shema}],
                tool_choice={"type": "tool", "name": "zapishi_dokument"},
                messages=[{"role": "user",
                           "content": prep["blokove"] + [{"type": "text", "text": tekst}]}],
            )
        except anthropic.APIError as e:
            if _claude_ne_mozhe(e):
                raise NeMozheSega(str(e)) from e
            raise
        dok = next((b.input for b in r.content if getattr(b, "type", "") == "tool_use"), None)
        return dok, {"model": getattr(r, "model", self.model),
                     "tokens_in": r.usage.input_tokens, "tokens_out": r.usage.output_tokens}


# ── Mistral ───────────────────────────────────────────────────────────────────
# Два хода: OCR 4 превръща скана в текст по страници, Small чете текста и
# попълва същата схема. Заявките са по REST — без още една библиотека на сървъра.

MISTRAL_URL = "https://api.mistral.ai/v1"
_OBRAZI = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


class Mistral:
    kod = "mistral"
    ime = "Mistral (резервен)"
    rakopis_nadezhden = False

    def __init__(self, api_key, model_ocr, model):
        self.api_key, self.model_ocr, self.model = api_key, model_ocr, model

    def _post(self, pat, body, timeout):
        import httpx
        try:
            r = httpx.post(f"{MISTRAL_URL}{pat}", json=body, timeout=timeout,
                           headers={"Authorization": f"Bearer {self.api_key}"})
        except (httpx.TimeoutException, httpx.TransportError) as e:
            raise NeMozheSega(f"Mistral не отговаря: {e}") from e
        if r.status_code in (401, 402, 403, 408, 429) or r.status_code >= 500:
            raise NeMozheSega(f"Mistral {r.status_code}: {r.text[:300]}")
        if r.status_code >= 400:
            raise RuntimeError(f"Mistral {r.status_code}: {r.text[:300]}")
        return r.json()

    def _ocr(self, ime, raw, n_stranici):
        ext = os.path.splitext(ime.lower())[1]
        if ext == ".pdf":
            dok = {"type": "document_url",
                   "document_url": "data:application/pdf;base64," + base64.b64encode(raw).decode()}
        else:
            mt = _OBRAZI.get(ext)
            if not mt:                      # tif, bmp… → png
                import pymupdf
                d = pymupdf.open(stream=raw, filetype=ext[1:] or "png")
                raw, mt = d[0].get_pixmap().tobytes("png"), "image/png"
            dok = {"type": "image_url",
                   "image_url": f"data:{mt};base64," + base64.b64encode(raw).decode()}
        body = {"model": self.model_ocr, "document": dok}
        if n_stranici:
            body["pages"] = list(range(n_stranici))
        r = self._post("/ocr", body, timeout=240)
        stranici = sorted(r.get("pages") or [], key=lambda p: p.get("index", 0))
        return [p.get("markdown", "") for p in stranici]

    def chete(self, prep, shema, tekst, ime="", raw=b"", n_stranici=0):
        if prep.get("docx_tekst") is not None:
            stranici = [prep["docx_tekst"]]
        else:
            stranici = self._ocr(ime, raw, n_stranici)
        razpoznat = "\n\n".join(f"=== Страница {i} ===\n{s}" for i, s in enumerate(stranici, 1))
        r = self._post("/chat/completions", {
            "model": self.model, "temperature": 0,
            "messages": [{"role": "user", "content":
                          tekst + "\n\nТекстът на документа, разпознат от сканираните страници "
                                  "(номерът на страницата е в заглавието ѝ):\n\n" + razpoznat}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "zapishi_dokument", "schema": shema,
                                                "strict": False}},
        }, timeout=240)
        try:
            dok = json.loads(r["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError, ValueError):
            dok = None
        u = r.get("usage") or {}
        return dok, {"model": r.get("model", self.model),
                     "tokens_in": u.get("prompt_tokens"), "tokens_out": u.get("completion_tokens")}


# ── Кои четци има ─────────────────────────────────────────────────────────────

def nalichni():
    """Четците по ред — основният първи. Без ключ четецът просто го няма."""
    izhod = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        izhod.append(Claude(os.environ["ANTHROPIC_API_KEY"],
                            os.environ.get("AI_MODEL", "claude-sonnet-4-6")))
    if os.environ.get("MISTRAL_API_KEY"):
        izhod.append(Mistral(os.environ["MISTRAL_API_KEY"],
                             os.environ.get("MISTRAL_OCR_MODEL", "mistral-ocr-latest"),
                             os.environ.get("MISTRAL_MODEL", "mistral-small-latest")))
    return izhod

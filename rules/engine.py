"""Ядрото: какво е правило, какви са присъдите, как се пускат."""
from datetime import date, datetime

OK = "ok"
WARN = "warn"
UNKNOWN = "unknown"

_VERDICT_LABEL = {
    OK:      "в ред",
    WARN:    "внимание",
    UNKNOWN: "не може да се провери",
}


class Verdict:
    """Резултат от едно правило върху един обект."""

    def __init__(self, status, message, rule=None):
        self.status = status
        self.message = message
        self.rule = rule

    @property
    def label(self):
        return _VERDICT_LABEL[self.status]

    def __repr__(self):
        icon = {OK: "OK  ", WARN: "WARN", UNKNOWN: "??  "}[self.status]
        return f"[{icon}] {self.message}"


class Rule:
    """Едно правило.

    citation — членът от закона; влиза дословно в заданието
    what     — какво проверява, на човешки език
    check    — функция(project) -> Verdict
    cases    — реални случаи: (име, project, очакван статус)
    """

    def __init__(self, code, title, citation, what, check, cases=()):
        self.code = code
        self.title = title
        self.citation = citation
        self.what = what
        self.check = check
        self.cases = list(cases)

    def run(self, project):
        v = self.check(project)
        v.rule = self
        return v

    def selftest(self):
        """Пуска реалните случаи. Връща списък от разминаванията."""
        failures = []
        for name, project, expected in self.cases:
            got = self.check(project).status
            if got != expected:
                failures.append(f"{self.code} · „{name}“: очаквано {expected}, получено {got}")
        return failures


ALL_RULES = []


def rule(code, title, citation, what, cases=()):
    """Декоратор — регистрира правилото."""
    def wrap(fn):
        r = Rule(code, title, citation, what, fn, cases)
        ALL_RULES.append(r)
        return r
    return wrap


# ── помощни ───────────────────────────────────────────────────────────────────

def parse_date(v):
    """Приема „14.03.2026“, „2026-03-14“ или date. Връща date или None."""
    if not v:
        return None
    if isinstance(v, date):
        return v
    v = str(v).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def doc_date(project, key):
    """Датата на СЪСТАВЯНЕ на документ — не датата на генериране."""
    return parse_date((project.get("docDates") or {}).get(key))


def years_after(d, years):
    """Същата дата след N години; 29 февруари пада на 28-и."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def run_all(project):
    return [r.run(project) for r in ALL_RULES]


def selftest_all():
    out = []
    for r in ALL_RULES:
        out.extend(r.selftest())
    return out

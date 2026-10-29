import logging
import re

REDACTED = "[redacted]"

# Keys that must never reach audit detail or application logs (R30, privacy rules).
FORBIDDEN_KEYS = frozenset(
    {
        "note",
        "notes",
        "reason",
        "decision_reason",
        "cancel_reason",
        "entry_reason",
        "token",
        "password",
        "password_hash",
        "secret",
        "authorization",
        "cookie",
        "sick_type",
        "leave_type",
    }
)

_KEYS = "|".join(sorted(FORBIDDEN_KEYS, key=len, reverse=True))
# key=value, key: value, "key": "value" with quoted or bare values.
_KV = re.compile(
    rf"""(?P<key>["']?\b(?:\w*_)?(?:{_KEYS})\b["']?)(?P<sep>\s*[=:]\s*)"""
    r"""(?P<val>"[^"]*"|'[^']*'|[^\s,;}}\]]+)""",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(Bearer\s+)\S+", re.IGNORECASE)


def scrub(text: str) -> str:
    text = _BEARER.sub(rf"\1{REDACTED}", text)
    return _KV.sub(lambda m: f"{m['key']}{m['sep']}{REDACTED}", text)


_installed = False


def configure_logging() -> None:
    """Scrub every record as it is made, so no logger or handler can bypass it."""
    global _installed
    if _installed:
        return
    original = logging.Logger.makeRecord

    def make_record(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        record = original(self, *args, **kwargs)
        record.msg = scrub(record.getMessage())
        record.args = None
        for name in list(vars(record)):
            if name.lower() in FORBIDDEN_KEYS:
                setattr(record, name, REDACTED)
        return record

    logging.Logger.makeRecord = make_record  # type: ignore[method-assign]
    logging.basicConfig(level=logging.INFO)
    _installed = True

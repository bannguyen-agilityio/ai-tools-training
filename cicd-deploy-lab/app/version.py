"""Tiny app: reports its version and health. Used as the 'deployable'."""
VERSION = "1.0.0"


def health():
    return {"status": "ok", "version": VERSION}


def parse_version(v):
    """'1.2.3' -> (1, 2, 3). Raises ValueError on bad input."""
    parts = v.split(".")
    if len(parts) != 3:
        raise ValueError(f"bad version: {v}")
    return tuple(int(p) for p in parts)

import os
import re
import shlex
from pathlib import Path


def load_local_environment():
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        key, separator, value = line.partition("=")
        key = key.strip()
        if separator and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            tokens = shlex.split(value, comments=True)
            os.environ.setdefault(key, " ".join(tokens))

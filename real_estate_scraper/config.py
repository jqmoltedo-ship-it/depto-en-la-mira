from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
try:
    import tomllib
except ImportError:  # Python 3.9 y 3.10
    tomllib = None
import ast


@dataclass(frozen=True)
class Requirements:
    min_price_usd: float
    max_price_usd: float
    min_rooms: int
    min_total_m2: float
    min_parking: int
    neighborhoods: tuple[str, ...]


def load_config(path: Path) -> dict:
    if tomllib:
        with path.open("rb") as file:
            raw = tomllib.load(file)
    else:
        raw = _load_simple_toml(path)
    raw["requirements"] = Requirements(
        **{**raw["requirements"], "neighborhoods": tuple(raw["requirements"]["neighborhoods"])}
    )
    return raw


def _load_simple_toml(path: Path) -> dict:
    """Lector pequeno para el subconjunto usado por config.toml."""
    result: dict = {}
    section: dict | None = None
    pending = ""
    for original in path.read_text(encoding="utf-8").splitlines():
        line = original.split("#", 1)[0].strip()
        if not line:
            continue
        if pending:
            pending += line
            if not line.endswith("]"):
                continue
            line, pending = pending, ""
        if line.startswith("["):
            section = result.setdefault(line[1:-1], {})
            continue
        if section is None or "=" not in line:
            raise ValueError(f"config.toml no valido: {original}")
        key, raw_value = (part.strip() for part in line.split("=", 1))
        if raw_value.startswith("[") and not raw_value.endswith("]"):
            pending = line
            continue
        value = ast.literal_eval(raw_value.replace("true", "True").replace("false", "False"))
        section[key] = value
    if pending:
        raise ValueError("Lista sin cerrar en config.toml")
    return result


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values

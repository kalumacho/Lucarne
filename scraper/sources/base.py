"""Lucarne — socle commun aux sources.

Chaque source (un module dans ce package) expose une fonction :

    fetch() -> list[dict]

qui rend des consultations **déjà normalisées et déjà filtrées ouvertes**,
au schéma commun décrit dans `normalize()`. La logique propre à chaque portail
(HTML, dates, pagination) reste dans son module ; l'orchestrateur `scrape.py`
se contente de fusionner, dédupliquer et trier.

Scraping respectueux : 1 requête / seconde, User-Agent identifiable.
"""

from __future__ import annotations

import re
import time
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

DELAY_S = 1.0
HEADERS = {
    "User-Agent": "LucarnePOC/0.2 (civic-tech; contact: cames.sacha@gmail.com)"
}

# Champs du schéma commun (une consultation normalisée).
FIELDS = (
    "url", "title", "opened_at", "closes_at", "days_left",
    "contributions", "status", "is_open", "category",
    "chapo", "body", "source", "scraped_at",
)

FR_MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
    "decembre": 12,
}

# « du 3 juin 2026 au 24 juin 2026 » (année du 1er terme parfois omise).
_WINDOW_RE = re.compile(
    r"du\s+(\d{1,2})\s+([a-zâûéèA-ZÂÛÉÈ]+)\s*(\d{4})?\s+"
    r"au\s+(\d{1,2})\s+([a-zâûéèA-ZÂÛÉÈ]+)\s+(\d{4})",
    re.IGNORECASE,
)


def get(url: str, retries: int = 3, timeout: int = 30) -> BeautifulSoup:
    """GET avec backoff, rend un BeautifulSoup."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise last_err  # type: ignore[misc]


def parse_fr_numeric_date(s: str) -> str:
    """'08/07/2026' -> '2026-07-08' (ISO)."""
    return datetime.strptime(s.strip(), "%d/%m/%Y").date().isoformat()


def parse_fr_long_date(day: str, month: str, year: str) -> str | None:
    """'3', 'juin', '2026' -> '2026-06-03' (ISO), None si mois inconnu."""
    m = FR_MONTHS.get(month.strip().lower())
    if not m:
        return None
    try:
        return date(int(year), m, int(day)).isoformat()
    except ValueError:
        return None


def extract_window(text: str) -> tuple[str | None, str | None]:
    """Extrait (ouverture, clôture) ISO depuis un texte 'du … au …'.

    L'année du 1er terme, souvent omise, est empruntée au 2nd.
    """
    m = _WINDOW_RE.search(text)
    if not m:
        return None, None
    d1, mo1, y1, d2, mo2, y2 = m.groups()
    closes = parse_fr_long_date(d2, mo2, y2)
    opened = parse_fr_long_date(d1, mo1, y1 or y2)
    return opened, closes


def days_left(closes_at: str | None) -> int | None:
    if not closes_at:
        return None
    return (date.fromisoformat(closes_at) - date.today()).days


def is_still_open(closes_at: str | None) -> bool:
    """Principe « dates exactes ou rien » : ouverte ssi clôture ≥ aujourd'hui."""
    if not closes_at:
        return False
    return date.fromisoformat(closes_at) >= date.today()


def normalize(source: str, **kw) -> dict:
    """Fabrique une consultation au schéma commun, champs manquants -> défaut."""
    row = {f: kw.get(f) for f in FIELDS}
    row["source"] = source
    row["days_left"] = days_left(row["closes_at"])
    row["is_open"] = is_still_open(row["closes_at"])
    row["contributions"] = kw.get("contributions") or 0
    row["scraped_at"] = datetime.now().isoformat(timespec="seconds")
    return row

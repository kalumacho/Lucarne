"""Source — portail national des consultations publiques (environnement).

https://www.consultations-publiques.developpement-durable.gouv.fr
Portail partagé transition écologique + cohésion des territoires (SPIP/DSFR).
Pagination `debut_listearticles`, cartes `.item-liste-articles`, détail
`.chapo-article` / `.texte-article`.
"""

from __future__ import annotations

import re
import sys
import time

import requests

from .base import (
    DELAY_S, get, parse_fr_numeric_date, normalize, is_still_open,
)

SOURCE = "consultations-publiques.developpement-durable.gouv.fr"
BASE = "https://www.consultations-publiques.developpement-durable.gouv.fr"
LIST_URL = BASE + "/spip.php?page=liste-consultations&lang=fr"
PER_PAGE = 11
MAX_PAGES = 6

DATE_RE = re.compile(
    r"Consultation du (\d{2}/\d{2}/\d{4}) au (\d{2}/\d{2}/\d{4})\s*-\s*(.+)"
)


def _parse_contributions(text: str) -> int:
    text = text.strip().lower()
    if text.startswith("aucune"):
        return 0
    m = re.match(r"(\d+)", text)
    return int(m.group(1)) if m else 0


def _parse_list_page(soup) -> list[dict]:
    items = []
    for card in soup.select("div.item-liste-articles"):
        link = card.select_one("a.fr-card__link")
        if not link:
            continue
        href = link.get("href", "").strip()
        title = link.get_text(strip=True)

        date_el = card.select_one(".dateart")
        opened_at = closes_at = None
        contributions = 0
        if date_el:
            m = DATE_RE.search(date_el.get_text(" ", strip=True))
            if m:
                opened_at = parse_fr_numeric_date(m.group(1))
                closes_at = parse_fr_numeric_date(m.group(2))
                contributions = _parse_contributions(m.group(3))

        tag = card.select_one("p.tag_active")
        status = tag.get_text(strip=True) if tag else None
        is_open = status is not None and "en cours" in status.lower()

        items.append({
            "url": href if href.startswith("http") else f"{BASE}/{href}",
            "title": title,
            "opened_at": opened_at,
            "closes_at": closes_at,
            "contributions": contributions,
            "status": status,
            "portal_open": is_open,
        })
    return items


def _fetch_detail(url: str) -> dict:
    soup = get(url)
    main = soup.find("main") or soup

    def block(cls: str) -> str:
        el = main.select_one(f".{cls}")
        return el.get_text(" ", strip=True) if el else ""

    crumbs = [a.get_text(strip=True) for a in soup.select(".fr-breadcrumb__link")]
    return {
        "category": crumbs[-1] if crumbs else None,
        "chapo": block("chapo-article"),
        "body": block("texte-article")[:4000],
    }


def fetch() -> list[dict]:
    seen: dict[str, dict] = {}
    for page in range(MAX_PAGES):
        start = page * PER_PAGE
        url = LIST_URL + (f"&debut_listearticles={start}" if start else "")
        for r in _parse_list_page(get(url)):
            seen.setdefault(r["url"], r)
        time.sleep(DELAY_S)

    # Réellement ouverte = portail « en cours » ET clôture à venir.
    open_rows = [
        r for r in seen.values()
        if r.get("portal_open") and is_still_open(r["closes_at"])
    ]
    print(f"  [dev-durable] {len(seen)} vues · {len(open_rows)} ouvertes")

    out = []
    for r in open_rows:
        try:
            detail = _fetch_detail(r["url"])
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
            print(f"    ⚠ ignorée ({e})", file=sys.stderr)
            continue
        out.append(normalize(
            SOURCE,
            url=r["url"], title=r["title"],
            opened_at=r["opened_at"], closes_at=r["closes_at"],
            contributions=r["contributions"], status=r["status"],
            **detail,
        ))
        time.sleep(DELAY_S)
    return out

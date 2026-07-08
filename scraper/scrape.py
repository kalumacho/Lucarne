"""Lucarne — scraper source pilote.

Portail national des consultations publiques (environnement).
https://www.consultations-publiques.developpement-durable.gouv.fr

Collecte les consultations EN COURS, normalise (titre, dates, lien, statut,
description), et écrit data/consultations.json.

Scraping respectueux : 1 requête / seconde, User-Agent identifiable.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.consultations-publiques.developpement-durable.gouv.fr"
LIST_URL = BASE + "/spip.php?page=liste-consultations&lang=fr"
PER_PAGE = 11          # pas de pagination du portail (debut_listearticles)
MAX_PAGES = 6          # les consultations ouvertes sont sur les 1res pages
DELAY_S = 1.0          # 1 req/s
HEADERS = {"User-Agent": "LucarnePOC/0.1 (civic-tech; contact: cames.sacha@gmail.com)"}

OUT = Path(__file__).resolve().parent.parent / "data" / "consultations.json"

DATE_RE = re.compile(
    r"Consultation du (\d{2}/\d{2}/\d{4}) au (\d{2}/\d{2}/\d{4})\s*-\s*(.+)"
)


def get(url: str, retries: int = 3) -> BeautifulSoup:
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))  # backoff
    raise last_err


def parse_fr_date(s: str) -> str:
    """'08/07/2026' -> '2026-07-08' (ISO)."""
    return datetime.strptime(s, "%d/%m/%Y").date().isoformat()


def parse_contributions(text: str) -> int:
    text = text.strip().lower()
    if text.startswith("aucune"):
        return 0
    m = re.match(r"(\d+)", text)
    return int(m.group(1)) if m else 0


def parse_list_page(soup: BeautifulSoup) -> list[dict]:
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
                opened_at = parse_fr_date(m.group(1))
                closes_at = parse_fr_date(m.group(2))
                contributions = parse_contributions(m.group(3))

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
            "is_open": is_open,
        })
    return items


def fetch_detail(url: str) -> dict:
    """Récupère chapô + corps + rubrique depuis la fiche consultation."""
    soup = get(url)
    main = soup.find("main") or soup

    def block(cls: str) -> str:
        el = main.select_one(f".{cls}")
        return el.get_text(" ", strip=True) if el else ""

    chapo = block("chapo-article")
    texte = block("texte-article")

    crumbs = [a.get_text(strip=True) for a in soup.select(".fr-breadcrumb__link")]
    category = crumbs[-1] if crumbs else None

    return {
        "category": category,
        "chapo": chapo,
        "body": texte[:4000],  # borne pour le digest IA
    }


def days_left(closes_at: str | None) -> int | None:
    if not closes_at:
        return None
    return (date.fromisoformat(closes_at) - date.today()).days


def main() -> None:
    print("Lucarne · scraper portail national")
    seen: dict[str, dict] = {}

    for page in range(MAX_PAGES):
        start = page * PER_PAGE
        url = LIST_URL + (f"&debut_listearticles={start}" if start else "")
        print(f"  page {page + 1}/{MAX_PAGES}  ({url.split('?')[1]})")
        rows = parse_list_page(get(url))
        for r in rows:
            seen.setdefault(r["url"], r)
        time.sleep(DELAY_S)

    # Principe « dates exactes ou rien » : une fenêtre n'est réellement
    # ouverte que si le portail la tague en cours ET que la clôture est à
    # venir. Certaines fiches restent taguées « en cours » des années après.
    today = date.today()
    open_rows = [
        r for r in seen.values()
        if r["is_open"] and r["closes_at"] and date.fromisoformat(r["closes_at"]) >= today
    ]
    print(f"  {len(seen)} consultations vues · {len(open_rows)} réellement ouvertes")

    consultations = []
    for i, r in enumerate(open_rows, 1):
        print(f"  détail {i}/{len(open_rows)} · {r['title'][:60]}…")
        try:
            detail = fetch_detail(r["url"])
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
            print(f"    ⚠ ignorée (détail inaccessible : {e})", file=sys.stderr)
            continue
        r.update(detail)
        r["days_left"] = days_left(r["closes_at"])
        r["source"] = "consultations-publiques.developpement-durable.gouv.fr"
        r["scraped_at"] = datetime.now().isoformat(timespec="seconds")
        consultations.append(r)
        time.sleep(DELAY_S)

    consultations.sort(key=lambda x: (x["days_left"] is None, x["days_left"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(consultations, ensure_ascii=False, indent=2))
    print(f"→ {len(consultations)} consultations écrites dans {OUT}")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"Erreur HTTP : {e}", file=sys.stderr)
        sys.exit(1)

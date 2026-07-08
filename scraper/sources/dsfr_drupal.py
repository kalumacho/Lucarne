"""Source générique — portails ministériels DSFR / Drupal.

Beaucoup de ministères publient leurs consultations avec le même gabarit :
une liste de cartes `.fr-card` (titre + lien + descriptif), et une fiche détail
dont le texte contient la fenêtre « du … au … ». On factorise ici, et chaque
portail devient une simple instance dans `sources/__init__.py`.

Exemples : agriculture.gouv.fr, economie.gouv.fr.
"""

from __future__ import annotations

import sys
import time

import requests

from .base import DELAY_S, get, extract_window, normalize, is_still_open


class DrupalDSFRSource:
    """Un portail DSFR/Drupal. `__name__` sert au logging de l'orchestrateur."""

    def __init__(self, name: str, base: str, list_path: str = "/consultations-publiques"):
        self.__name__ = name
        self.base = base.rstrip("/")
        self.list_url = self.base + list_path
        self.source_label = base.split("://", 1)[-1].strip("/")

    def _abs(self, href: str) -> str:
        return href if href.startswith("http") else f"{self.base}{href}"

    def _fetch_detail(self, url: str) -> dict:
        soup = get(url)
        article = soup.find("article") or soup.find("main") or soup
        text = article.get_text(" ", strip=True)
        opened_at, closes_at = extract_window(text)
        crumbs = [a.get_text(strip=True) for a in soup.select(".fr-breadcrumb__link")]
        return {
            "opened_at": opened_at,
            "closes_at": closes_at,
            "category": crumbs[1] if len(crumbs) > 1 else None,
            "body": text[:4000],
        }

    def fetch(self) -> list[dict]:
        soup = get(self.list_url)
        cards = []
        for card in soup.select(".fr-card"):
            link = card.select_one(".fr-card__link")
            if not link or not link.get("href", "").strip():
                continue
            desc_el = card.select_one(".fr-card__desc")
            cards.append({
                "url": self._abs(link.get("href").strip()),
                "title": link.get_text(" ", strip=True),
                "chapo": desc_el.get_text(" ", strip=True) if desc_el else "",
            })
        time.sleep(DELAY_S)

        out = []
        for c in cards:
            if "clotur" in c["url"].lower():  # fiches taguées fermées dans l'URL
                continue
            try:
                detail = self._fetch_detail(c["url"])
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
                print(f"    ⚠ ignorée ({e})", file=sys.stderr)
                continue
            time.sleep(DELAY_S)
            if not is_still_open(detail["closes_at"]):
                continue
            out.append(normalize(
                self.source_label,
                url=c["url"], title=c["title"], chapo=c["chapo"],
                status="Consultation en cours", **detail,
            ))
        print(f"  [{self.__name__}] {len(cards)} vues · {len(out)} ouvertes")
        return out

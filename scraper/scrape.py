"""Lucarne — orchestrateur multi-sources.

Interroge chaque source enregistrée (`sources/SOURCES`), fusionne les
consultations ouvertes, déduplique par URL, trie par urgence (clôture la plus
proche d'abord) et écrit data/consultations.json.

La logique propre à chaque portail vit dans son module `sources/*.py`.
Ici : orchestration, dédup, tri, écriture. Lancer :

    ./.venv/bin/python scraper/scrape.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sources import SOURCES

OUT = Path(__file__).resolve().parent.parent / "data" / "consultations.json"


def main() -> None:
    print("Lucarne · scraper multi-sources")
    merged: dict[str, dict] = {}

    for source in SOURCES:
        name = source.__name__.rsplit(".", 1)[-1]
        try:
            rows = source.fetch()
        except Exception as e:  # une source qui casse ne doit pas tout bloquer
            print(f"  ⚠ source {name} en échec : {e}", file=sys.stderr)
            continue
        for r in rows:
            # dédup par URL ; à doublon, on garde la 1re (ordre = SOURCES).
            merged.setdefault(r["url"], r)

    consultations = list(merged.values())
    consultations.sort(key=lambda x: (x["days_left"] is None, x["days_left"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(consultations, ensure_ascii=False, indent=2))
    print(f"→ {len(consultations)} consultations écrites dans {OUT}")


if __name__ == "__main__":
    main()

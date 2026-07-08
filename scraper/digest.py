"""Lucarne — génération des digests IA.

Pour chaque consultation ouverte (data/consultations.json), produit un résumé
en 3 phrases, français courant, strictement factuel et sourcé, via l'API
Anthropic. Écrit data/digests.json trié par urgence (jours restants).

Principes non négociables (cf. présentation) :
  - Neutralité absolue : décrire, jamais militer, aucun cadrage d'opinion.
  - Factuel et sourcé : uniquement ce qui figure dans le texte officiel.
  - Zéro jargon : reformuler l'administratif en langage clair.

Clé API : variable d'env ANTHROPIC_API_KEY, ou fichier .env à la racine projet.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "consultations.json"
OUT = ROOT / "data" / "digests.json"

MODEL = "claude-opus-4-8"

SYSTEM = (
    "Tu es le moteur de résumé de Lucarne, un service civic-tech qui aide les "
    "citoyens à repérer les consultations publiques ouvertes près de chez eux.\n\n"
    "Règles absolues et non négociables :\n"
    "1. NEUTRALITÉ : tu décris, tu ne milites jamais. Aucune opinion, aucun "
    "cadrage orienté, aucun adjectif évaluatif (« important », « inquiétant »…).\n"
    "2. FACTUEL ET SOURCÉ : uniquement ce qui figure dans le texte fourni. "
    "N'invente aucun chiffre, aucune date, aucune conséquence. Si une info "
    "manque, ne la mentionne pas.\n"
    "3. ZÉRO JARGON : reformule l'administratif en français clair et courant, "
    "compréhensible par tout citoyen.\n"
    "4. FORMAT : exactement 3 phrases. Phrase 1 = de quoi il s'agit. "
    "Phrase 2 = ce que le projet prévoit concrètement. Phrase 3 = comment et "
    "jusqu'à quand le public peut participer.\n"
    "Réponds uniquement par les 3 phrases, sans préambule ni titre."
)

PROMPT_TMPL = (
    "Titre officiel : {title}\n"
    "Rubrique : {category}\n"
    "Ouverture : {opened_at} — Clôture : {closes_at} (dans {days_left} jours)\n\n"
    "Résumé officiel :\n{chapo}\n\n"
    "Détail :\n{body}\n\n"
    "Rédige le digest en 3 phrases selon tes règles."
)


def load_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    print(
        "Clé API introuvable. Définis ANTHROPIC_API_KEY ou crée un fichier "
        f"{env_file} contenant :\nANTHROPIC_API_KEY=sk-ant-...",
        file=sys.stderr,
    )
    sys.exit(1)


def digest_one(client: anthropic.Anthropic, c: dict) -> str:
    prompt = PROMPT_TMPL.format(
        title=c["title"],
        category=c.get("category") or "—",
        opened_at=c.get("opened_at") or "?",
        closes_at=c.get("closes_at") or "?",
        days_left=c.get("days_left"),
        chapo=(c.get("chapo") or "").strip() or "—",
        body=(c.get("body") or "").strip() or "—",
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def main() -> None:
    if not SRC.exists():
        print(f"{SRC} manquant — lance d'abord scrape.py", file=sys.stderr)
        sys.exit(1)

    consultations = json.loads(SRC.read_text())
    client = anthropic.Anthropic(api_key=load_api_key())

    print(f"Lucarne · génération de {len(consultations)} digests ({MODEL})")
    out = []
    for i, c in enumerate(consultations, 1):
        print(f"  {i}/{len(consultations)} · J-{c.get('days_left')} · {c['title'][:55]}…")
        try:
            summary = digest_one(client, c)
        except anthropic.APIError as e:
            print(f"    ⚠ échec API : {e}", file=sys.stderr)
            summary = ""
        out.append({
            "title": c["title"],
            "category": c.get("category"),
            "opened_at": c.get("opened_at"),
            "closes_at": c.get("closes_at"),
            "days_left": c.get("days_left"),
            "contributions": c.get("contributions"),
            "url": c["url"],
            "source": c.get("source"),
            "digest": summary,
        })

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"→ {len(out)} digests écrits dans {OUT}")


if __name__ == "__main__":
    main()

# Lucarne — POC

Le radar des fenêtres d'action citoyenne. Détecte les consultations publiques
**ouvertes**, les résume en 3 phrases factuelles, les affiche triées par urgence.

Projet civic-tech. Ce dépôt = **POC** (roadmap slide 7) : valider que la qualité
des digests IA tient sur de vraies consultations.

## Pipeline

```
scraper/scrape.py   → data/consultations.json   (scrape portail national, filtre les fenêtres réellement ouvertes)
scraper/digest.py   → data/digests.json         (résumé IA 3 phrases via API Anthropic, claude-opus-4-8)
web/                → app Next.js               (affichage trié par urgence)
```

Source pilote : `consultations-publiques.developpement-durable.gouv.fr`
(données 100 % publiques, scraping respectueux 1 req/s, retries).

## Lancer

```bash
# 1. Environnement Python
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt

# 2. Scraper les consultations ouvertes
./.venv/bin/python scraper/scrape.py

# 3. Générer les digests (clé API requise)
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
./.venv/bin/python scraper/digest.py
cp data/digests.json web/data/digests.json

# 4. Lancer l'app
cd web && npm install && npm run dev   # http://localhost:3000
```

## Trois principes non négociables (appliqués dans le code)

- **Neutralité** : le prompt système interdit toute opinion/cadrage (`scraper/digest.py`).
- **Dates exactes ou rien** : `scrape.py` ne garde que les fenêtres dont la
  clôture est ≥ aujourd'hui (des fiches restent taguées « en cours » des années
  après). Les dates manquantes sont signalées, jamais devinées.
- **Localisation protégée** : hors périmètre du POC (arrive en Phase 2 — geo).

## Suite (roadmap)

- **Phase 2 — geo** : brancher `registre-numerique.fr` (préfecture pilote IdF),
  extraire la commune, ajouter le filtre géographique par rayon.
- **V1 — produit** : comptes, alertes email, carte, extension région par région.

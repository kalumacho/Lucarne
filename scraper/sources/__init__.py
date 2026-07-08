"""Registre des sources Lucarne.

Ajouter une source :
  - portail DSFR/Drupal standard → une instance `DrupalDSFRSource` ci-dessous ;
  - portail atypique → un module exposant `fetch() -> list[dict]`
    (voir `base.normalize` pour le schéma), importé et ajouté à SOURCES.
"""

from . import dev_durable
from .dsfr_drupal import DrupalDSFRSource

agriculture = DrupalDSFRSource("agriculture", "https://agriculture.gouv.fr")
economie = DrupalDSFRSource("economie", "https://www.economie.gouv.fr")

SOURCES = [dev_durable, agriculture, economie]

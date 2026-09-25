import json
from dataclasses import asdict, dataclass
from factories import AdherentFactory, CotisationFactory, PrestationFactory

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_dataset(n_adherents: int=10):
    adherents = [AdherentFactory() for _ in range(n_adherents)]
    cotisations = [CotisationFactory(adherent_id=a.id) for a in adherents]
    prestations = [PrestationFactory(adherent_id=a.id) for a in adherents]

    return adherents, cotisations, prestations

def write_json(objects: list[dataclass], path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(obj) for obj in objects], f, ensure_ascii=False, indent=4, default=str)

if __name__ == "__main__":
    adherents, cotisations, prestations = generate_dataset(10)
    logger.info("Generated dataset with %d adherents", len(adherents))
    write_json(adherents, "data/adherents.json")
    write_json(cotisations, "data/cotisations.json")
    write_json(prestations, "data/prestations.json")
    logger.info("Data written to JSON files")
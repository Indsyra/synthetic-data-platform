import pendulum
from airflow.sdk import dag, task
from generate import generate_dataset, write_json
from upload import upload_file
from anonymize import anonymize_adherent, anonymize_cotisation, anonymize_prestation

import os
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@dag
def synthetic_data_pipeline(
    schedule = None,
    start_date = pendulum.datetime(2026, 1, 1, tz="UTC"),
):
    date = pendulum.now("UTC").to_date_string().replace("-", "_")
    @task
    def generate():
        adherents, cotisations, prestations = generate_dataset(10)
        logger.info("Generated dataset with %d adherents", len(adherents))
        write_json(adherents, f"data/adherents_{date}.json")
        write_json(cotisations, f"data/cotisations_{date}.json")
        write_json(prestations, f"data/prestations_{date}.json")
        logger.info("Data written to JSON files")

    @task
    def anonymize():
        os.makedirs('data/anonymized_data', exist_ok=True)

        with open(f'data/adherents_{date}.json', 'r', encoding='utf-8') as f:
            adherents = json.load(f)
        anonymized_adherents = [anonymize_adherent(a) for a in adherents]
        output_file = os.path.join('data/anonymized_data', f'adherents_{date}.json')
        logger.info("Writing anonymized adherent data to %s", output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(anonymized_adherents, f, indent=4)

        with open(f'data/cotisations_{date}.json', 'r', encoding='utf-8') as f:
            cotisations = json.load(f)
        anonymized_cotisations = [anonymize_cotisation(c) for c in cotisations]
        output_file = os.path.join('data/anonymized_data', f'cotisations_{date}.json')
        logger.info("Writing anonymized cotisation data to %s", output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(anonymized_cotisations, f, indent=4)

        with open(f'data/prestations_{date}.json', 'r', encoding='utf-8') as f:
            prestations = json.load(f)
        anonymized_prestations = [anonymize_prestation(p) for p in prestations]
        output_file = os.path.join('data/anonymized_data', f'prestations_{date}.json')
        logger.info("Writing anonymized prestation data to %s", output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(anonymized_prestations, f, indent=4)

        logger.info("Anonymization process completed.")
    
    @task
    def upload():
        for file_path in [f for f in os.listdir("data/anonymized_data") if f.endswith(".json") and date in f]:
            upload_file(f"data/anonymized_data/{file_path}", "indira-synthetic-social-data-2026", f"raw/{file_path}")

    generate() >> anonymize() >> upload()

synthetic_data_pipeline()

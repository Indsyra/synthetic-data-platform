import hashlib
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def mask_email(email: str) -> str:
    local, domain = email.split('@')
    masked_local = local[0] + '*' * (len(local) - 1)
    return f"{masked_local}@{domain}"

def mask_iban(iban: str) -> str:
    return iban[:4] + '*' * (len(iban) - 8) + iban[-4:]

def anonymize_adherent(adherent: dict) -> dict:
    anonymized = adherent.copy()
    if 'email' in anonymized:
        anonymized['email'] = mask_email(anonymized['email'])
    if 'iban' in anonymized:
        anonymized['iban'] = mask_iban(anonymized['iban'])
    if 'id' in anonymized:
        anonymized['id'] = hash_value(anonymized['id'])
    return anonymized

def anonymize_cotisation(cotisation: dict) -> dict:
    anonymized = cotisation.copy()
    if 'adherent_id' in anonymized:
        anonymized['adherent_id'] = hash_value(anonymized['adherent_id'])
    if 'id' in anonymized:
        anonymized['id'] = hash_value(anonymized['id'])
    return anonymized

def anonymize_prestation(prestation: dict) -> dict:
    anonymized = prestation.copy()
    if 'adherent_id' in anonymized:
        anonymized['adherent_id'] = hash_value(anonymized['adherent_id'])
    if 'id' in anonymized:
        anonymized['id'] = hash_value(anonymized['id'])
    return anonymized

if __name__ == "__main__":
    import json
    import sys

    os.makedirs('data/anonymized_data', exist_ok=True)

    with open('data/adherents.json', 'r', encoding='utf-8') as f:
        adherents = json.load(f)
    anonymized_adherents = [anonymize_adherent(a) for a in adherents]
    output_file = os.path.join('data/anonymized_data', 'adherents.json')
    logger.info("Writing anonymized adherent data to %s", output_file)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(anonymized_adherents, f, indent=4)

    with open('data/cotisations.json', 'r', encoding='utf-8') as f:
        cotisations = json.load(f)
    anonymized_cotisations = [anonymize_cotisation(c) for c in cotisations]
    output_file = os.path.join('data/anonymized_data', 'cotisations.json')
    logger.info("Writing anonymized cotisation data to %s", output_file)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(anonymized_cotisations, f, indent=4)

    with open('data/prestations.json', 'r', encoding='utf-8') as f:
        prestations = json.load(f)
    anonymized_prestations = [anonymize_prestation(p) for p in prestations]
    output_file = os.path.join('data/anonymized_data', 'prestations.json')
    logger.info("Writing anonymized prestation data to %s", output_file)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(anonymized_prestations, f, indent=4)

    logger.info("Anonymization process completed.")

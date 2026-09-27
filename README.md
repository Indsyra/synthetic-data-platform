# Synthetic Data Platform (Social Protection)

A synthetic data generation and anonymization pipeline, built on a social protection
domain (members, contributions, benefits), that will grow into a full cloud data
platform: generation, anonymization, cloud storage, infrastructure as code,
orchestration, transformation, and CI/CD.

## What this project demonstrates

- Realistic synthetic data generation with Faker and Factory Boy, with relational
  consistency between related records (a contribution always belongs to a real member)
- Deterministic, irreversible anonymization (hashing) and partial masking, preserving
  referential integrity across anonymized datasets
- (Planned) Cloud storage on AWS S3, provisioned with Terraform
- (Planned) Orchestration with Airflow, transformation with dbt, warehousing in
  Snowflake
- (Planned) CI/CD with GitHub Actions

## Domain model

Three related entities, modeling a social protection fund's core data:

- **Adherent** (member): id, first name, last name, birth date, email, IBAN
- **Cotisation** (contribution): id, adherent_id, start date, end date, monthly
  amount, regime type (health / disability-death cover)
- **Prestation** (benefit payment): id, adherent_id, payment date, amount, reason

Each member can have several contributions and several benefit payments over time,
which is why these are modeled as three separate entities rather than one flat table,
mirroring how this data will later live in the Snowflake warehouse.

## Prerequisites

- **WSL** (Linux on Windows) or any Linux/macOS distribution. Under WSL, avoid working
  inside `/mnt/c/...` or `/mnt/d/...`: I/O is slower there and pip/venv sometimes run
  into permission issues. Work under `~/` (the native Linux filesystem) instead.
- **Python 3.10+**. Check with `python3 --version`.
- An **AWS account** (free tier) for the upcoming S3 storage step.

## Installation

```bash
cd ~
git clone <repo-url> synthetic-data-platform   # or create the folder for a local project
cd synthetic-data-platform
python3 -m venv venv
source venv/bin/activate
pip install faker factory_boy
```

## Usage

### Step 1: generate synthetic data

```bash
python3 src/generate.py
```

Generates a configurable number of members (`Adherent`), each linked to one or more
contributions (`Cotisation`) and benefit payments (`Prestation`), using Factory Boy
factories built on top of Faker (French locale). Writes three JSON files to `data/`:
`adherents.json`, `cotisations.json`, `prestations.json`.

Factory Boy's `LazyFunction` generates a fresh value per record (a name, a date), while
`LazyAttribute` lets one field depend on another already-generated field on the same
record, used here so a contribution's end date is always computed from its own start
date rather than picked independently.

### Step 2: anonymize the data

```bash
python3 src/anonymize.py
```

Reads the three JSON files from `data/`, applies anonymization, and writes the result
to `data/anonymized_data/`:

- **Hashing** (SHA-256) on every `id` and `adherent_id`: irreversible, and
  deterministic, meaning the same input always produces the same hash. This is what
  keeps a contribution correctly linked to its member even after anonymization, both
  the member's `id` and the contribution's `adherent_id` hash to the same value.
- **Masking** on `email` (first character kept, rest of the local part replaced with
  asterisks, domain kept intact) and `iban` (first four and last four characters kept,
  middle masked).

**Point of attention**: anonymization must be applied per record (looping over each
item of the loaded list), and with the right function for each entity (members need
`email`/`iban` masking on top of `id` hashing; contributions and benefit payments only
need `id` and `adherent_id` hashed). Applying a single generic function to a whole list
instead of its individual items fails silently: no error is raised, but nothing gets
anonymized, since checking whether a key exists in a list of dictionaries is not the
same as checking whether it exists in a single dictionary.

## Project structure

```
synthetic-data-platform/
├── data/
│   ├── adherents.json              # generated members
│   ├── cotisations.json            # generated contributions
│   ├── prestations.json            # generated benefit payments
│   └── anonymized_data/
│       ├── adherents.json          # anonymized members
│       ├── cotisations.json        # anonymized contributions
│       └── prestations.json        # anonymized benefit payments
├── src/
│   ├── models.py                   # dataclasses: Adherent, Cotisation, Prestation
│   ├── factories.py                # Factory Boy factories
│   ├── generate.py                 # step 1: data generation
│   ├── anonymize.py                # step 2: anonymization
│   ├── upload.py                   # step 3: AWS S3 upload (in progress)
│   └── terraform/                  # step 4: infrastructure as code (planned)
└── venv/
```

## Known limitations

- Anonymization is currently irreversible by design (hashing), which fits a
  throwaway test dataset; a real pseudonymization use case requiring reversibility
  would need a separate, securely stored mapping table instead.
- No automated tests yet on the generation/anonymization logic itself.
- Volume and relationship cardinality (contributions and benefit payments per member)
  are currently fixed rather than randomized within a range; adjust the generation
  logic in `generate.py` for a more realistic, variable volume per member.

## Roadmap

- Upload anonymized data to AWS S3 (`src/upload.py`)
- Provision the S3 bucket (and later the Snowflake warehouse) with Terraform instead
  of manual console setup
- Orchestrate the generation → anonymization → upload → transformation flow with
  Airflow
- Transform raw data into clean tables with dbt
- Land transformed data in Snowflake
- Automate tests and deployment with GitHub Actions

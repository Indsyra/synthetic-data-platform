# Synthetic Data Platform (Social Protection)

A synthetic data generation and anonymization pipeline, built on a social protection
domain (members, contributions, benefits), growing into a full cloud data platform:
generation, anonymization, cloud storage, infrastructure as code, orchestration,
transformation, and CI/CD.

## What this project demonstrates

- Realistic synthetic data generation with Faker and Factory Boy, with relational
  consistency between related records (a contribution always belongs to a real member)
- Deterministic, irreversible anonymization (hashing) and partial masking, preserving
  referential integrity across anonymized datasets
- Cloud storage on AWS S3, with the bucket brought under Terraform management
  through `terraform import`
- Orchestration with Apache Airflow running in Docker (DAG in progress)
- Reproducible Python environments with uv (`pyproject.toml` and `uv.lock`)
- (Planned) Transformation with dbt, warehousing in Snowflake, CI/CD with GitHub Actions

## Domain model

Three related entities, modeling a social protection fund's core data:

- **Adherent** (member): id, first name, last name, birth date, email, IBAN
- **Cotisation** (contribution): id, adherent_id, start date, end date, monthly
  amount, regime type (health / disability-death cover)
- **Prestation** (benefit payment): id, adherent_id, payment date, amount, reason

Each member can have several contributions and several benefit payments over time,
which is why these are three separate entities rather than one flat table, mirroring
how this data will later live in the warehouse.

## Prerequisites

- **WSL 2** (Linux on Windows) or any Linux/macOS distribution. Under WSL, avoid
  working inside `/mnt/c/...` or `/mnt/d/...`: I/O is slower there and package
  managers sometimes run into permission issues. Work under `~/` instead.
- **uv**, the Python package and environment manager: https://docs.astral.sh/uv/
  (it can also install Python itself, so a separate Python setup is optional)
- **Docker Desktop** with WSL integration enabled for your distribution
  (Settings > Resources > WSL Integration). Installing `docker.io` inside WSL is not
  the recommended path here.
- **AWS account** (free tier) and the **AWS CLI**, configured with `aws configure`
- **Terraform**

## AWS cost safeguards

The whole project stays within the free tier if you follow these three rules:

1. Before creating any resource, enable free tier usage alerts in Billing preferences
   and create an AWS Budget with a low threshold (1 to 5 USD) and an email alert.
2. Stay in a single region for everything (for example `eu-west-3`), since
   cross-region transfers can incur charges outside the free tier.
3. Keep bucket versioning disabled, otherwise every overwritten file is kept as an
   extra stored version.

Also create a dedicated IAM user for the project instead of using the root account,
and never commit access keys.

## Installation

```bash
cd ~
git clone https://github.com/Indsyra/synthetic-data-platform.git synthetic-data-platform
cd synthetic-data-platform
uv sync
```

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`, so `uv sync`
recreates the exact same environment (in `.venv/`) on any machine. Both files must be
committed, while `.venv/` must not.

To add a dependency, use `uv add <package>` (for example
`uv add faker factory_boy boto3 awscli`) rather than `pip install`, so both files stay
up to date. If the project has no `pyproject.toml` yet, run `uv init --bare` first: it
creates a minimal one without touching existing files.

Run scripts with `uv run`, for example `uv run python src/generate.py`, or activate the
environment once with `source .venv/bin/activate`. The commands in the Usage section
below assume the environment is active; otherwise prefix them with `uv run`.

## Usage

### Step 1: generate synthetic data

```bash
python3 src/generate.py
```

Generates members, contributions and benefit payments with Factory Boy factories built
on Faker (French locale), and writes three JSON files to `data/`. `LazyFunction`
generates a fresh value per record, while `LazyAttribute` lets a field depend on
another field of the same record (a contribution's end date is computed from its own
start date).

Two details worth knowing: dates are not natively JSON serializable, so `json.dump`
needs `default=str`; and an Enum member must be converted with `.value` before being
stored, otherwise it is serialized as `ClassName.MEMBER`.

### Step 2: anonymize the data

```bash
python3 src/anonymize.py
```

Writes anonymized copies to `data/anonymized_data/`:

- **Hashing** (SHA-256) on every `id` and `adherent_id`. It is irreversible and
  deterministic: the same input always gives the same hash, so a contribution stays
  correctly linked to its member after anonymization.
- **Masking** on `email` (first character kept, domain kept) and `iban` (first four and
  last four characters kept).

Anonymization must be applied per record, with the right function for each entity.
Applying a function meant for one dictionary to a whole list fails silently.

### Step 3: upload to AWS S3

```bash
python3 src/upload.py
```

Uploads every file of `data/anonymized_data/` to the bucket under the `raw/` prefix,
using `boto3`, which reads credentials from `~/.aws/credentials`. The `raw/` prefix is a
convention: transformed data will later live under a different prefix.

Check the result with `aws s3 ls s3://<your-bucket-name>/raw/`.

### Step 4: manage the bucket with Terraform

The bucket was first created by hand in the console, then brought under Terraform
management instead of being recreated:

```bash
cd terraform
terraform init
terraform import aws_s3_bucket.synthetic_data_bucket <your-bucket-name>
terraform plan
```

`terraform import` only fills the state file, it does not write the configuration. The
`resource` block in `main.tf` must be written by hand, then adjusted until
`terraform plan` reports no changes. Since version 4 of the AWS provider, versioning,
policies and encryption are separate resources, so a bare bucket often matches a
minimal block on the first try.

### Step 5: orchestrate with Airflow

```bash
cd airflow
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
echo "FERNET_KEY=<generated key>" >> .env
docker compose up airflow-init
docker compose up -d
```

The interface is available at `http://localhost:8080`. Generate the Fernet key (used to
encrypt sensitive values stored in Airflow's metadata database) without adding
`cryptography` to the project:

```bash
uv run --with cryptography python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

uv only manages the local environment. The Airflow containers use their own image and
their own dependencies, so nothing changes in `docker-compose.yaml` on that side.

The DAG (`airflow/dags/synthetic_data_pipeline.py`) chains three tasks: generate,
anonymize, upload. Design decisions:

- The containers only see mounted folders, so `src/` and `data/` are mounted as volumes
  in `docker-compose.yaml`, with absolute paths defined once as constants.
- The run timestamp is computed once, inside the first task, at execution time and not
  at file parsing time, then passed to the next tasks through their return values
  (XCom). Only small values such as file paths should transit through XCom, never
  datasets.
- Dependencies are deduced from the data passed between tasks.

## Project structure

```
synthetic-data-platform/
├── airflow/
│   ├── dags/                       # Airflow DAGs
│   ├── docker-compose.yaml         # official Airflow compose file, with extra volumes
│   └── .env                        # AIRFLOW_UID, FERNET_KEY (not versioned)
├── data/
│   ├── *.json                      # generated data
│   └── anonymized_data/            # anonymized data
├── src/
│   ├── models.py                   # dataclasses: Adherent, Cotisation, Prestation
│   ├── factories.py                # Factory Boy factories
│   ├── generate.py                 # step 1
│   ├── anonymize.py                # step 2
│   └── upload.py                   # step 3
├── terraform/
│   └── main.tf                     # provider and S3 bucket (step 4)
├── pyproject.toml                  # dependencies
├── uv.lock                         # pinned versions (commit this file)
└── .venv/                          # local environment (not versioned)
```

## Troubleshooting

- **`ModuleNotFoundError` on a new machine**: the virtual environment is per machine and
  is not copied with the code. Run `uv sync` to recreate it from `uv.lock`.
- **`permission denied` on the Docker socket after `usermod -aG docker`**: group changes
  are only loaded at session start. Run `wsl --shutdown` from Windows, then reopen the
  terminal and check `groups`.
- **VS Code cannot reconnect to WSL after a shutdown**: delete `~/.vscode-server` from a
  plain Ubuntu terminal and relaunch with `code .`.
- **Empty S3 bucket in the console**: refresh the page and open the `raw/` folder, or
  check with the AWS CLI.
- **Airflow warns that `FERNET_KEY` is not set**: generate a key and add it to the
  `.env` file next to `docker-compose.yaml`.

## Known limitations

- Anonymization is irreversible by design, which fits a throwaway test dataset. A real
  pseudonymization use case would need a securely stored mapping table.
- No automated tests yet on the generation and anonymization logic.
- The volume per member (one contribution and one benefit payment) is fixed rather than
  randomized within a range.
- The Airflow DAG is still being finalized.

## Roadmap

- Finalize and test the Airflow DAG
- Transform raw data into clean tables with dbt
- Land transformed data in Snowflake
- Extend Terraform to the warehouse resources
- Automate tests and deployment with GitHub Actions
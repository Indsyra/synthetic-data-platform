from dataclasses import dataclass
from datetime import date
from enum import Enum

class CotisationRegimeType(Enum):
    SANTE = "sante"
    PREVOYANCE = "prevoyance"

@dataclass
class Adherent:
    id: str
    first_name: str
    last_name: str
    birth_date: date
    email: str
    iban: str

@dataclass
class Cotisation:
    id: str
    adherent_id: str
    start_date: date
    end_date: date
    monthly_amount: float
    regime_type: CotisationRegimeType

@dataclass
class Prestation:
    id: str
    adherent_id: str
    payment_date: date
    amount: float
    reason: str

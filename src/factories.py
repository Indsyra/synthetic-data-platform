
from factory import Factory, LazyAttribute as LA, LazyFunction as LF
from faker import Faker
from models import Adherent, Cotisation, Prestation, CotisationRegimeType

from datetime import date, timedelta
from uuid import uuid4
import random


faker = Faker("fr_FR")

class AdherentFactory(Factory):
    class Meta:
        model = Adherent

    id = LF(lambda: str(uuid4()))
    first_name = LF(lambda: faker.first_name())
    last_name = LF(lambda: faker.last_name())
    birth_date = LF(
        lambda: faker.date_of_birth(minimum_age=18, maximum_age=90)
    )
    email = LF(lambda: faker.email())
    iban = LF(lambda: faker.iban())

class CotisationFactory(Factory):
    class Meta:
        model = Cotisation

    id = LF(lambda: str(uuid4()))
    adherent_id = None
    start_date = LF(
        lambda: faker.date_between(start_date='-3y', end_date='-1y')
    )
    end_date = LA(
        lambda o: o.start_date + timedelta(days=random.randint(30, 365))
    )
    monthly_amount = LF(lambda: round(random.uniform(50, 400), 2))
    regime_type = LF(lambda: faker.random_element(elements=CotisationRegimeType).value)

class PrestationFactory(Factory):
    class Meta:
        model = Prestation

    id = LF(lambda: str(uuid4()))
    adherent_id = None
    payment_date = LF(lambda: faker.date_between(start_date='-1y', end_date='today'))
    amount = LF(lambda: round(random.uniform(20, 2000), 2))
    reason = LF(
        lambda: random.choice(["remboursement soins", "indemnité arrêt de travail", "capital décès"])
    )
import os
import django
import random
from faker import Faker
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecouture.settings")  # à adapter
django.setup()

from django.contrib.auth import get_user_model
from workshop.models import (
    Worker, Workshop, CustomerWorkshop,
    OrderWorkshop, OrderWorkshopGroup, Setting
)

fake = Faker()
User = get_user_model()

PASSWORD_PAR_DEFAUT = "wxcvbn123"
EMAIL_OWNER = "hervecedricyouan@gmail.com"


def random_createdAt():
    # Date aléatoire dans les 60 derniers jours
    return timezone.now() - timedelta(days=random.randint(0, 60))


def get_owner_and_workshop():
    try:
        user = User.objects.get(email=EMAIL_OWNER)
        worker = Worker.objects.get(user=user)
        workshop = worker.workshop
        return user, worker, workshop
    except Exception as e:
        print("Erreur: assure-toi que l'utilisateur, le tailor et le workshop existent déjà.")
        raise e


# def create_workers(workshop, n=10):
#     workers = []
#     for _ in range(n):
#         email = fake.unique.email()
#         user = User.objects.create_user(
#             email=email,
#             password=PASSWORD_PAR_DEFAUT,
#             first_name=fake.first_name(),
#             last_name=fake.last_name(),
#             phone=fake.unique.phone_number(),
#         )
#         worker = Worker.objects.create(user=user, workshop=workshop, createdAt=random_createdAt())
#         workers.append(worker)
#     return workers


# def create_customers(workshop, n=50):
#     customers = []
#     for _ in range(n):
#         customer = CustomerWorkshop.objects.create(
#             last_name=fake.last_name(),
#             first_name=fake.first_name(),
#             nickname=fake.unique.user_name(),
#             genre=random.choice(["MAN", "WOMAN", "CHILDREN"]),
#             email=fake.email(),
#             phone=fake.unique.phone_number(),
#             workshop=workshop,
#             createdAt=random_createdAt(),
#         )
#         customers.append(customer)
#     return customers


def create_orders(workshop, worker, total=500):
    customers = workshop.customers.all()
    orders = []
    for _ in range(total):
        customer = random.choice(customers)
        worker = worker
        amount = Decimal(random.randint(10000, 100000))
        down_payment = Decimal(random.randint(int(amount)//2, int(amount)))

        order = OrderWorkshop.objects.create(
            customer=customer,
            worker=worker,
            gender=random.choice(["MAN", "WOMAN", "CHILDREN"]),
            type_of_clothing=random.choice(["SHIRT", "PANTS", "DRESS"]),
            measurement={"height": fake.random_int(150, 200), "waist": fake.random_int(60, 100)},
            description_of_fabric=fake.word(),
            clothing_model=fake.word(),
            amount=amount,
            down_payment=down_payment,
            description=fake.text(100),
            estimated_delivery_date=timezone.now() + timezone.timedelta(days=15),
            promised_delivery_date=timezone.now() + timezone.timedelta(days=30),
            assign_date = random_createdAt(),
            # createdAt=random_createdAt(),
        )
        orders.append(order)
    return orders


def create_setting(workshop):
    Setting.objects.update_or_create(
        workshop=workshop,
        defaults={"package_type": "DEMO"}
    )


def run():
    user, worker, workshop = get_owner_and_workshop()
    print("Owner et Workshop trouvés :", workshop.name)

    # print("Création des workers...")
    # workers = create_workers(workshop, n=5)

    # print("Création des customers...")
    # customers = create_customers(workshop, n=12)

    print("Création des commandes...")
    create_orders(workshop, worker, total=50)

    # print("Création du setting...")
    # create_setting(workshop)

    print("Génération terminée.")


if __name__ == "__main__":
    run()

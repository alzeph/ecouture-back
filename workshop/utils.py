def init_package():
    from datetime import timedelta
    from workshop.models import Package

    packages = [
        Package(
            name=Package.PackageType.DEMO,
            description="Offre Démo gratuite, limitée en fonctionnalités.",
            features=[
                "Jusqu'à 5 tailleurs",
                "50 commandes maximum",
                "50 clients maximum",
                "50 essayages",
                "10 groupes de commandes"
            ],
            price=0,
            duration=timedelta(days=30),  # 1 mois
        ),
        Package(
            name=Package.PackageType.BASIC,
            description="Offre de base pour les petits ateliers.",
            features=[
                "Jusqu'à 15 tailleurs",
                "500 commandes maximum",
                "500 clients maximum",
                "100 essayages",
                "50 groupes de commandes"
            ],
            price=10000,  # exemple en FCFA ou autre
            duration=timedelta(days=30),  # 1 mois
        ),
        Package(
            name=Package.PackageType.PREMIUM,
            description="Offre Premium adaptée aux ateliers de taille moyenne.",
            features=[
                "Jusqu'à 30 tailleurs",
                "2000 commandes maximum",
                "5000 clients maximum",
                "300 essayages",
                "200 groupes de commandes"
            ],
            price=30000,
            duration=timedelta(days=30),  # 1 mois
        ),
        Package(
            name=Package.PackageType.PRO,
            description="Offre Pro pour les grands ateliers.",
            features=[
                "Jusqu'à 100 tailleurs",
                "10 000 commandes maximum",
                "20 000 clients maximum",
                "1000 essayages",
                "500 groupes de commandes"
            ],
            price=80000,
            duration=timedelta(days=30),  # 1 mois
        ),
    ]

    Package.objects.bulk_create(packages, ignore_conflicts=True)

from django.contrib.auth.models import Group


def get_or_create_group(name: str) -> Group:
    """
    Gets or creates a group by name.

    Args:
        name (str): "WORKERS" | "TAILORS" | "ADMIN"| "CUSTOMERS_WORKSHOPS": | "CUSTOMERS_SHOP",

    Returns:
        Group: The group object.
    """

    group, created = Group.objects.get_or_create(
        name=name
    )
    return group

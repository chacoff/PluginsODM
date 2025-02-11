def get_factory_access(groups: list[bool]) -> list[str]:
    """" gets factory access according the user """

    factory_access: list[str] = []

    if groups[0]:  # isBelval
        factory_access = ['Belval', 'Differdange']

    if groups[1]:  # isDiffer
        factory_access = ['Differdange', 'Belval']

    if groups[2] or groups[3]:  # isGlobal or isDev
        factory_access = ['Belval', 'Differdange']

    return factory_access


def get_user_group(request) -> list[bool]:
    """ gets user group of every user in database """

    # user_groups = request.user.groups.all()
    is_belval: bool = request.user.groups.filter(name='Belval').exists()
    is_differ: bool = request.user.groups.filter(name='Differdange').exists()
    is_global: bool = request.user.groups.filter(name='Global').exists()
    is_dev: bool = request.user.groups.filter(name='Dev').exists()

    return [is_belval, is_differ, is_global, is_dev]

def get_attribute(instance, *attrs):
    for attr in attrs:
        try:
            instance = instance[attr]
        except TypeError:
            raise KeyError(f"{attr}")
    return instance

import functools


def handle_boundary_errors(*exc_types, on_error):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exc_types as e:
                return on_error(e, **kwargs)

        return wrapper

    return decorator

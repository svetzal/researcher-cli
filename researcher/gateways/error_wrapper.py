import functools
import inspect
from collections.abc import Callable
from typing import Any

from researcher.exceptions import EmbeddingError, StorageError


def wrap_gateway_error(exception_class: type[Exception]) -> Callable[[str], Callable]:
    """Factory that creates a decorator-factory for a specific exception class.

    Usage::

        _wrap_storage_error = wrap_gateway_error(StorageError)

        @_wrap_storage_error("Failed to load '{self._path}': {e}")
        def load(self): ...

    The message_template may contain ``{e}`` for the caught exception and any
    parameter name from the decorated function's signature (including ``self``).
    If the caught exception is already an instance of ``exception_class`` it is
    re-raised unchanged so error messages are never double-wrapped.
    """

    def decorator_factory(message_template: str) -> Callable:
        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return fn(*args, **kwargs)
                except exception_class:
                    raise
                except Exception as e:
                    sig = inspect.signature(fn)
                    bound = sig.bind(*args, **kwargs)
                    bound.apply_defaults()
                    msg = message_template.format(e=e, **bound.arguments)
                    raise exception_class(msg) from e

            return wrapper

        return decorator

    return decorator_factory


wrap_storage_error = wrap_gateway_error(StorageError)
wrap_embedding_error = wrap_gateway_error(EmbeddingError)

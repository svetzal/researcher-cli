import pytest

from researcher.error_boundary import handle_boundary_errors
from researcher.exceptions import ResearcherError, StorageError


def should_pass_through_return_value():
    @handle_boundary_errors(ResearcherError, on_error=lambda e, **_: "error")
    def func():
        return "ok"

    assert func() == "ok"


def should_route_listed_exception_to_on_error():
    def on_error(e, **_):
        return f"caught: {e}"

    @handle_boundary_errors(ResearcherError, on_error=on_error)
    def func():
        raise ResearcherError("boom")

    assert func() == "caught: boom"


def should_route_subclass_exception_to_on_error():
    def on_error(e, **_):
        return f"caught: {e}"

    @handle_boundary_errors(ResearcherError, on_error=on_error)
    def func():
        raise StorageError("disk full")

    assert func() == "caught: disk full"


def should_propagate_unlisted_exception():
    @handle_boundary_errors(ResearcherError, on_error=lambda e, **_: "caught")
    def func():
        raise ValueError("not a domain error")

    with pytest.raises(ValueError):
        func()


def should_pass_kwargs_to_on_error():
    received = {}

    def on_error(e, **kwargs):
        received.update(kwargs)
        return "error"

    @handle_boundary_errors(ResearcherError, on_error=on_error)
    def func(json_output=False):
        raise ResearcherError("fail")

    func(json_output=True)

    assert received == {"json_output": True}

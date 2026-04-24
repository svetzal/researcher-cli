import pytest

from researcher.gateways.error_wrapper import wrap_gateway_error


class FakeGatewayError(Exception):
    pass


_wrap = wrap_gateway_error(FakeGatewayError)


@_wrap("Failed for '{name}': {e}")
def _raise_runtime(name: str) -> None:
    raise RuntimeError("boom")


@_wrap("Unchanged: {e}")
def _raise_fake(name: str = "x") -> None:
    raise FakeGatewayError("original message")


@_wrap("Success: {e}")
def _return_value() -> int:
    return 42


class _Thing:
    def __init__(self, path: str) -> None:
        self._path = path

    @_wrap("Error at '{self._path}': {e}")
    def broken(self) -> None:
        raise RuntimeError("oops")


@_wrap("Timeout={timeout}: {e}")
def _with_default(path: str, *, timeout: int = 30) -> None:
    raise RuntimeError("kaboom")


@_wrap("Missing {nonexistent}: {e}")
def _bad_template(name: str) -> None:
    raise RuntimeError("irrelevant")


def should_wrap_non_target_exception():
    with pytest.raises(FakeGatewayError) as exc_info:
        _raise_runtime(name="test")

    assert str(exc_info.value) == "Failed for 'test': boom"
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def should_prevent_double_wrap():
    with pytest.raises(FakeGatewayError) as exc_info:
        _raise_fake()

    assert str(exc_info.value) == "original message"
    assert exc_info.value.__cause__ is None


def should_resolve_self_attribute_in_template():
    thing = _Thing("/data/notes")
    with pytest.raises(FakeGatewayError) as exc_info:
        thing.broken()

    assert "/data/notes" in str(exc_info.value)


def should_pass_through_return_value_on_success():
    assert _return_value() == 42


def should_preserve_function_metadata_via_functools_wraps():
    assert _raise_runtime.__name__ == "_raise_runtime"


def should_apply_default_argument_in_template():
    with pytest.raises(FakeGatewayError) as exc_info:
        _with_default(path="/tmp")

    assert "Timeout=30:" in str(exc_info.value)


def should_raise_key_error_for_malformed_template():
    with pytest.raises(KeyError):
        _bad_template(name="whatever")

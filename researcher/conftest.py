from unittest.mock import Mock

import pytest

from researcher.service_factory import ServiceFactory


@pytest.fixture
def mock_factory():
    return Mock(spec=ServiceFactory)

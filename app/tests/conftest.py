import pytest

from src.core import lifecycle


@pytest.fixture(autouse=True)
def reset_lifecycle():
    lifecycle.reset()
    yield

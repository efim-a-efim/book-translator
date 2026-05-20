import pytest

from book_translator.store.job_store import JobStore


@pytest.fixture
def store(tmp_path):
    """Return a JobStore backed by a temporary directory."""
    return JobStore(base=tmp_path / "runs")

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_txt(tmp_path):
    f = tmp_path / "sample.en.txt"
    f.write_text("Hello world.\n\nSecond paragraph.", encoding="utf-8")
    return f

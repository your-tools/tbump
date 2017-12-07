import re

import path
import pytest


@pytest.fixture()
def tmp_path(tmpdir):
    return path.Path(tmpdir)


@pytest.fixture
def test_path():
    this_dir = path.Path(__file__).parent
    return this_dir.abspath()

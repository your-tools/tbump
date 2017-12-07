import textwrap

import toml
import pytest

import tbump.main


@pytest.mark.skip("not ready")
def test_main(tmp_path, test_path):
    toml_path = test_path.joinpath("tbump.toml").copy(tmp_path)
    tmp_path.joinpath("VERSION").write_text("1.2.41")
    tmp_path.joinpath("package.json").write_text(textwrap.dedent("""
    {
       "name": "foo",
       "version": "1.2.41",
       "dependencies": {
         "some-dep": "1.3",
         "other-dep": "1.2.41"
       }
    }
    """))

    tbump.main.main(args=["minor"])

    new_toml = toml.loads(toml_path.text())
    assert new_toml["version"]["current"] == "1.2.42-alpha-1"

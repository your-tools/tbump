"""
Fake yarn used for testing hooks

Its only job is to update yarn.lock based on the contents of the package.json
"""

import json

import path
import tomlkit


def main() -> None:
    package_json = path.Path("package.json")
    parsed = json.loads(package_json.text())
    current_version = parsed["version"]

    yarn_lock = path.Path("yarn.lock")
    parsed = tomlkit.loads(yarn_lock.text())
    parsed["dependencies"]["hello"] = current_version
    parsed["dependencies"]["some-dep"] = "1.2.0"
    yarn_lock.write_text(tomlkit.dumps(parsed))


if __name__ == "__main__":
    main()

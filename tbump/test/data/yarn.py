"""
Fake yarn used for testsing hookse

Its only job is to update yarn.lock based on the contents of the package.json
"""

import json

import path
import toml


def main():
    package_json = path.Path("package.json")
    parsed = json.loads(package_json.text())
    current_version = parsed["version"]

    yarn_lock = path.Path("yarn.lock")
    parsed = toml.loads(yarn_lock.text())
    parsed["dependencies"]["hello"] = current_version
    parsed["dependencies"]["some-dep"] = "1.2.0"
    yarn_lock.write_text(toml.dumps(parsed))


if __name__ == "__main__":
    main()

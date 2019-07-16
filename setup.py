import sys
from setuptools import setup, find_packages

if sys.version_info.major < 3:
    sys.exit("Error: Please upgrade to Python3")


def get_long_description():
    with open("README.rst") as fp:
        return fp.read()


setup(
    name="tbump",
    version="6.0.1",
    description="Bump software releases",
    long_description=get_long_description(),
    url="https://github.com/TankerHQ/tbump",
    author="Dimitri Merejkowsky",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["attrs", "docopt", "path.py", "cli-ui>=0.9.0", "schema", "toml"],
    extras_require={
        "dev": [
            'black==19.3b0 ; python_version >= "3.6"',
            # tests
            "pytest==3.8.1",
            "pytest-sugar",
            "pytest-mock",
            "pytest-cov",
            "codecov==2.0.15",
            # linters
            "mypy==0.641",
            "flake8==3.5.0",
            # distribution
            "wheel",
            "twine",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    entry_points={"console_scripts": ["tbump = tbump.main:main"]},
)

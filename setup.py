import sys
from setuptools import setup, find_packages

if sys.version_info.major < 3:
    sys.exit("Error: Please upgrade to Python3")


def get_long_description():
    with open("README.rst") as fp:
        return fp.read()


setup(name="tbump",
      version="5.0.1",
      description="Bump software releases",
      long_description=get_long_description(),
      url="https://github.com/SuperTanker/tbump",
      author="Dimitri Merejkowsky",
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
        "attrs",
        "path.py",
        "python-cli-ui",
        "schema",
        "toml",
      ],
      classifiers=[
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
      ],
      entry_points={
        "console_scripts": [
          "tbump = tbump.main:main",
         ]
      }
      )

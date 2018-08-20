from __future__ import unicode_literals

from setuptools import find_packages, setup

import re

def get_version(filename):
    regex = "__([a-z]+)__ = \"([^\"]+)\""
    return dict(re.findall(regex, open(filename).read()))["version"]

setup(name="Mopidy-Qobuz",
      version=get_version("mopidy_qobuz/__init__.py"),
      description="Mopidy extension for playing music from Qobuz",
      url="https://github.com/secondwtq/mopidy-qobuz",
      author="Second Datke",
      author_email="lovejay-lovemusic@outlook.com",
      install_requires=[
          "Mopidy >= 2.0",
          "Pykka >= 1.1",
          "requests >= 2.0",
          "setuptools"
      ],
      entry_points={
          "mopidy.ext": [
              "qobuz = mopidy_qobuz:Extension"
          ]
      },
      packages=find_packages(),
      zip_safe=False,
      include_package_data=True)

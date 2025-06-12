from setuptools import setup
from cybermule._generate_version import write_version_file

# Write the version info before building
write_version_file()

# Proceed with normal build
setup()

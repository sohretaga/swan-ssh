"""
Swan SSH CLI tool
"""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("swan-ssh")
except PackageNotFoundError:
    __version__ = "unknown"

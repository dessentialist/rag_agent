# This file makes the services directory a Python package

"""
Service package initializer.

Includes startup helpers such as seeding minimal content on first run.
"""

from typing import Optional

def noop(_: Optional[bool] = None) -> None:  # back-compat placeholder
    return None

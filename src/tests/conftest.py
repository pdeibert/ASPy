import pytest

import aspy


def pytest_sessionstart(session):
    # set debug mode
    aspy.debug(True)

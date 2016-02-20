"""
Performance measurement utilities.
"""
import pytest
import time


class PerformanceTimer(object):
    def __init__(self, max_time):
        self.max_time = max_time
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert time.time() - self.start_time < self.max_time


class PerformanceFixture(object):
    timer = PerformanceTimer


@pytest.fixture
def performance():
    return PerformanceFixture()


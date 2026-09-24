"""Pytest fixtures for synthetic CSI frames and test session data."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_raw_iq():
    """Synthetic interleaved [imag_0, real_0, ...] vector of 384 numbers (192 complex)."""
    np.random.seed(42)
    # 384 numbers
    raw = np.random.randint(-100, 100, size=384).astype(np.float64)
    return raw


@pytest.fixture
def synthetic_amplitude_matrix():
    """Synthetic amplitude matrix of shape (100 samples, 192 subcarriers)."""
    np.random.seed(42)
    # Create subcarriers with varying signal strength
    base = np.abs(np.random.normal(loc=15.0, scale=3.0, size=(100, 192)))
    # Set first 20 subcarriers to near zero (dead subcarriers)
    base[:, :20] = 0.05
    return base


@pytest.fixture
def synthetic_window():
    """Synthetic window of amplitude values (58 samples, 162 subcarriers)."""
    np.random.seed(42)
    return np.random.uniform(5.0, 25.0, size=(58, 162))

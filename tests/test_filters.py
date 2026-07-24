"""
Pruebas básicas de los filtros LTI. Correr con: pytest tests/
"""

import numpy as np
from src.filters import design_noise_filter, apply_noise_reduction, design_eq_bands, apply_eq


def test_noise_filter_shapes():
    b, a = design_noise_filter()
    x = np.random.randn(1024)
    y, zf = apply_noise_reduction(x, b, a)
    assert y.shape == x.shape


def test_eq_bands_shapes():
    bands = design_eq_bands()
    x = np.random.randn(1024)
    y = apply_eq(x, bands, gains={"low": 1.0, "mid": 1.0, "high": 1.0})
    assert y.shape == x.shape

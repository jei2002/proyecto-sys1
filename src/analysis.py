"""
analysis.py
-----------
Módulo de análisis en tiempo y frecuencia, usado por la GUI para graficar
la forma de onda y el espectro en tiempo real.
"""

import numpy as np


def compute_spectrum(x, sample_rate=44100):
    """
    Calcula el espectro de magnitud de un bloque de audio usando FFT.
    Devuelve (frecuencias, magnitudes) listas para graficar.
    """
    n = len(x)
    window = np.hanning(n)
    spectrum = np.fft.rfft(x * window)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    magnitude_db = 20 * np.log10(np.abs(spectrum) + 1e-9)
    return freqs, magnitude_db


def compute_waveform(x, sample_rate=44100):
    """Devuelve (tiempo, amplitud) para graficar la forma de onda del bloque."""
    t = np.arange(len(x)) / sample_rate
    return t, x

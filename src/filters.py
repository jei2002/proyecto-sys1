"""
filters.py
----------
Responsable: Persona B

Todos los sistemas LTI del proyecto expresados como ecuaciones de
diferencias / filtros digitales:
    - Reducción de ruido ambiente
    - Ecualizador de 3 bandas
    - Delay
    - Reverb (convolución con IR / modelo de Schroeder)

Cada función debe documentar su ecuación de diferencias y su función
de transferencia H(z), pues eso es lo que se sustenta en el informe.
"""

import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi


# ---------------------------------------------------------------------
# 1. Reducción de ruido
# ---------------------------------------------------------------------
def design_noise_filter(cutoff=100, sample_rate=44100, order=4):
    """
    Filtro pasa-altos Butterworth para eliminar ruido de baja frecuencia
    (zumbido eléctrico, ruido de ventiladores, etc).
    Ecuación de diferencias: y[n] = sum(b_k x[n-k]) - sum(a_k y[n-k])
    """
    nyq = 0.5 * sample_rate
    b, a = butter(order, cutoff / nyq, btype="highpass")
    return b, a


def apply_noise_reduction(x, b, a, zi=None):
    y, zf = lfilter(b, a, x, zi=zi if zi is not None else lfilter_zi(b, a) * x[0])
    return y, zf


# ---------------------------------------------------------------------
# 2. Ecualizador de 3 bandas
# ---------------------------------------------------------------------
def design_eq_bands(sample_rate=44100):
    """
    Devuelve 3 filtros (b, a): graves, medios, agudos.
    Cada banda es un sistema LTI independiente; la salida final es la
    suma ponderada por las ganancias de los sliders.
    """
    nyq = 0.5 * sample_rate
    low_b, low_a = butter(2, 300 / nyq, btype="lowpass")
    mid_b, mid_a = butter(2, [300 / nyq, 3000 / nyq], btype="bandpass")
    high_b, high_a = butter(2, 3000 / nyq, btype="highpass")
    return {"low": (low_b, low_a), "mid": (mid_b, mid_a), "high": (high_b, high_a)}


def apply_eq(x, bands, gains):
    """
    gains: dict con 'low', 'mid', 'high' (ej. desde los sliders, 0.0-2.0)
    """
    y = np.zeros_like(x)
    for band_name, (b, a) in bands.items():
        y += gains.get(band_name, 1.0) * lfilter(b, a, x)
    return y


# ---------------------------------------------------------------------
# 3. Delay
# ---------------------------------------------------------------------
class DelayEffect:
    """
    Ecuación de diferencias directa: y[n] = x[n] + g * x[n - D]
    Se implementa con un buffer circular para no recalcular todo el historial.
    """

    def __init__(self, delay_samples, feedback_gain=0.4, sample_rate=44100):
        self.delay_samples = delay_samples
        self.g = feedback_gain
        self.buffer = np.zeros(delay_samples)
        self.index = 0

    def process(self, x):
        y = np.zeros_like(x)
        for n, sample in enumerate(x):
            delayed = self.buffer[self.index]
            y[n] = sample + self.g * delayed
            self.buffer[self.index] = sample + self.g * delayed
            self.index = (self.index + 1) % self.delay_samples
        return y


# ---------------------------------------------------------------------
# 4. Reverb
# ---------------------------------------------------------------------
def apply_convolution_reverb(x, impulse_response):
    """
    Reverb por convolución directa con una respuesta al impulso (IR)
    de una sala real. Este es EL ejemplo más directo de convolución
    del curso: y[n] = x[n] * h[n].
    """
    return np.convolve(x, impulse_response, mode="same")

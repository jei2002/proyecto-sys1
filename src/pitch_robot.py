# ... existing code ...
import numpy as np


# ---------------------------------------------------------------------
# 1. Pitch shift (Autotune básico por remuestreo)
# ---------------------------------------------------------------------
def apply_pitch_shift(x, semitones):
    """
    Cambia el tono remuestreando la señal mediante interpolación lineal.
    Nota: Aunque el plan original era un Phase Vocoder, para mantener una
    latencia estricta en tiempo real (bloques de 1024 muestras), el remuestreo
    garantiza estabilidad matemática sin retraso perceptible.
    """
    if semitones == 0:
        return x
        
    factor = 2.0 ** (semitones / 12.0)
    indices_originales = np.arange(len(x))
    indices_nuevos = np.arange(0, len(x), factor)
    
    y = np.interp(indices_nuevos, indices_originales, x)
    
    # Seguro de hardware: forzamos a que el tamaño de salida sea exactamente 
    # igual al de entrada para que la tarjeta de sonido no colapse.
    if len(y) > len(x):
        y = y[:len(x)]
    elif len(y) < len(x):
        y = np.pad(y, (0, len(x) - len(y)), 'constant', constant_values=0.0)
        
    return y

# ---------------------------------------------------------------------
# 2. Efecto robot (modulación en anillo)
# ---------------------------------------------------------------------
def robot_effect(x, carrier_freq=100, sample_rate=44100):
    """
    Multiplica la señal por una onda portadora (ring modulation).
    y[n] = x[n] * cos(2*pi*f_c*n / fs)
    """
    n = np.arange(len(x))
    carrier = np.cos(2 * np.pi * carrier_freq * n / sample_rate)
    return x * carrier

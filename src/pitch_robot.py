"""
pitch_robot.py
--------------
Responsable: Persona C

Efectos basados en el dominio de la frecuencia (Transformada de Fourier):
    - Pitch shift (equivalente a shiftPitch de MATLAB / "autotune")
    - Efecto robot (modulación en anillo)

Nota importante para el informe: el efecto robot NO es un sistema LTI
puro (la multiplicación por una portadora viola la invarianza temporal),
lo cual vale la pena discutir como contraste frente a los filtros LTI
del resto del proyecto.
"""

import numpy as np


# ---------------------------------------------------------------------
# 1. Pitch shift vía phase vocoder (STFT -> escalado -> ISTFT)
# ---------------------------------------------------------------------
def pitch_shift(x, semitones, sample_rate=44100, frame_size=2048, hop_size=512):
    """
    Placeholder de la interfaz. Implementación real (Fase 3):
      1. STFT de la señal (ventaneo + FFT por bloques)
      2. Cálculo de magnitud y fase por bin de frecuencia
      3. Reescalado de fase para simular el cambio de tono
      4. Reconstrucción con ISTFT (overlap-add)

    semitones: número de semitonos a subir (+) o bajar (-) el tono
    """
    raise NotImplementedError("Implementar phase vocoder en Fase 3")


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

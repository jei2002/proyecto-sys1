"""
main.py
-------
Punto de entrada: conecta audio_io -> filters/pitch_robot -> analysis -> gui.

Este es el módulo de INTEGRACIÓN. Cada persona desarrolla su módulo por
separado; aquí se ensambla la cadena completa (ver diagrama de arquitectura).
"""

from src.audio_io import AudioEngine, SAMPLE_RATE
from src.filters import (
    DelayEffect,
    design_noise_filter,
    apply_noise_reduction,
    design_eq_bands,
    apply_eq,
)
from src.pitch_robot import robot_effect
# from src.gui import run_app

# --- FASE 3: efectos conectados a la cadena ---
# Estos parámetros serán, más adelante, los que controlen los sliders
# y botones de la GUI. Por ahora los cambiamos aquí a mano para probar.

ENABLED = {
    "eq": False,
    "robot": True,
    "delay": False,
}

# Delay: 0.3 s de retardo, con realimentación (feedback) de 0.5.
delay_effect = DelayEffect(
    delay_samples=int(0.3 * SAMPLE_RATE),
    feedback_gain=0.5,
    sample_rate=SAMPLE_RATE,
)

# Ecualizador: 3 filtros independientes (graves/medios/agudos) diseñados
# una sola vez al arrancar (son sistemas LTI fijos; lo único que cambia
# en vivo es la ganancia con la que se suma cada banda).
eq_bands = design_eq_bands(sample_rate=SAMPLE_RATE)
eq_gains = {"low": 1.0, "mid": 1.0, "high": 1.8}  # prueba: agudos realzados

# Robot: frecuencia de la portadora (Hz). Entre más baja, más "vibración"
# grave se nota; entre más alta, el timbre se vuelve más metálico/agudo.
robot_carrier_freq = 200


def process_block(x):
    """
    Cadena de procesamiento aplicada a cada bloque de audio capturado.

    Fase 3: cadena = ecualizador -> robot -> delay.
    """
    y = x

    if ENABLED["eq"]:
        y = apply_eq(y, eq_bands, eq_gains)

    if ENABLED["robot"]:
        y = robot_effect(y, carrier_freq=robot_carrier_freq, sample_rate=SAMPLE_RATE)

    if ENABLED["delay"]:
        y = delay_effect.process(y)

    return y


if __name__ == "__main__":
    engine = AudioEngine(process_callback=process_block)
    print("Iniciando motor de audio... Ctrl+C para detener.")
    engine.start()
    input("Presiona Enter para detener...\n")
    engine.stop()
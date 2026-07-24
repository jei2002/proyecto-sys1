"""
main.py
-------
Punto de entrada: conecta audio_io -> filters/pitch_robot -> analysis -> gui.

Este es el módulo de INTEGRACIÓN. Cada persona desarrolla su módulo por
separado; aquí se ensambla la cadena completa (ver diagrama de arquitectura).
"""

from src.audio_io import AudioEngine, SAMPLE_RATE
from src.filters import DelayEffect, design_noise_filter, apply_noise_reduction
# from src.pitch_robot import pitch_shift, robot_effect
# from src.gui import run_app

# --- FASE 3: primer efecto real conectado a la cadena ---
# 0.3 s de retardo, con realimentación (feedback) de 0.5.
# Estos dos valores serán, más adelante, los que controlen los sliders
# de la GUI ("tiempo de delay" y "feedback").
delay_effect = DelayEffect(
    delay_samples=int(0.3 * SAMPLE_RATE),
    feedback_gain=0.5,
    sample_rate=SAMPLE_RATE,
)


def process_block(x):
    """
    Cadena de procesamiento aplicada a cada bloque de audio capturado.

    Fase 3: se agrega el primer efecto real (delay). El objeto
    `delay_effect` mantiene su buffer circular entre llamadas (es un
    sistema con memoria / estado, como corresponde a su ecuación de
    diferencias y[n] = x[n] + g*x[n-D]), por eso vive fuera de la función.
    """
    return delay_effect.process(x)


if __name__ == "__main__":
    engine = AudioEngine(process_callback=process_block)
    print("Iniciando motor de audio... Ctrl+C para detener.")
    engine.start()
    input("Presiona Enter para detener...\n")
    engine.stop()

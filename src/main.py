"""
main.py
-------
Punto de entrada: conecta audio_io -> filters/pitch_robot -> analysis -> gui.

Este es el módulo de INTEGRACIÓN. Cada persona desarrolla su módulo por
separado; aquí se ensambla la cadena completa (ver diagrama de arquitectura).
"""

from src.audio_io import AudioEngine
from src.filters import design_noise_filter, apply_noise_reduction
# from src.pitch_robot import pitch_shift, robot_effect
# from src.gui import run_app


def process_block(x):
    """
    Cadena de procesamiento aplicada a cada bloque de audio capturado.
    Fase 1: por ahora solo pasa el audio sin modificar (passthrough),
    para validar que la captura/reproducción funciona sin clics ni
    latencia perceptible antes de sumar efectos.
    """
    return x  # TODO: reemplazar por cadena real de efectos (Fase 3)


if __name__ == "__main__":
    engine = AudioEngine(process_callback=process_block)
    print("Iniciando motor de audio... Ctrl+C para detener.")
    engine.start()
    input("Presiona Enter para detener...\n")
    engine.stop()

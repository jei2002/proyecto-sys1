"""
audio_io.py
-----------
Responsable: Persona A

Módulo encargado de la captura y reproducción de audio en tiempo real.
Usa sounddevice con procesamiento por bloques (streaming callback-based)
para mantener latencia baja.

Conceptos clave:
- El audio se procesa en bloques (frames) de tamaño fijo, no muestra por
  muestra. Este tamaño de bloque define el trade-off latencia vs. carga
  de CPU y es importante justificarlo en el informe.
"""

import sounddevice as sd
import numpy as np

SAMPLE_RATE = 44100      # Hz
BLOCK_SIZE = 1024        # muestras por bloque
CHANNELS = 1             # mono


class AudioEngine:
    """
    Motor de audio en tiempo real: abre un stream de entrada/salida
    y por cada bloque capturado llama a `process_callback`, que debe
    ser inyectado desde main.py (allí se conecta la cadena de efectos).
    """

    def __init__(self, process_callback, sample_rate=SAMPLE_RATE,
                 block_size=BLOCK_SIZE, channels=CHANNELS):
        self.process_callback = process_callback
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels
        self.stream = None

    def _callback(self, indata, outdata, frames, time, status):
        if status:
            print(status)
        # indata: bloque crudo del micrófono (numpy array)
        # process_callback: aplica toda la cadena LTI (filtros + efectos)
        processed = self.process_callback(indata[:, 0])
        outdata[:, 0] = processed

    def start(self):
        self.stream = sd.Stream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=self.channels,
            callback=self._callback,
        )
        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()


def list_devices():
    """Lista los dispositivos de audio disponibles (útil si usan mic externo)."""
    return sd.query_devices()

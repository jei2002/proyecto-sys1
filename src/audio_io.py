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
import threading
import soundfile as sf
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
class FilePlayerEngine:
    def __init__(self, process_callback, sample_rate=SAMPLE_RATE, block_size=BLOCK_SIZE):
        self.process_callback = process_callback
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.stream = None
        self.data = None
        self.position = 0
        self.paused = True
        self.lock = threading.Lock()

    def load_file(self, filepath):
        "Aqui se carga el archivo"
        data, sr = sf.read(filepath, dtype="float32", always_2d=True)
        data = data.mean(axis=1)  # A mono

        if sr != self.sample_rate:
            data = self._resample(data, sr, self.sample_rate)

        with self.lock:
            self.data = data
            self.position = 0
            self.paused = True

    def _resample(self, data, sr_origen, sr_destino):
        duracion = len(data) / sr_origen
        n_nuevas = int(duracion * sr_destino)
        x_orig = np.linspace(0, duracion, len(data))
        x_nuevo = np.linspace(0, duracion, n_nuevas)
        return np.interp(x_nuevo, x_orig, data).astype(np.float32)

    def _callback(self, outdata, frames, time, status):
        if status:
            print(status)
        with self.lock:
            if self.data is None or self.paused:
                outdata[:, 0] = np.zeros(frames, dtype=np.float32)
                return
            inicio = self.position
            fin = inicio + frames
            bloque = self.data[inicio:fin]
            if len(bloque) < frames:
                bloque = np.pad(bloque, (0, frames - len(bloque)))
                self.paused = True  # Llegó al final del archivo
            self.position += frames

        procesado = self.process_callback(bloque)
        outdata[:, 0] = procesado

    def start(self):
        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=1,
                callback=self._callback,
            )
            self.stream.start()

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def is_loaded(self):
        return self.data is not None

    def get_progress(self):
        """Devuelve (segundos_actuales, segundos_totales)."""
        with self.lock:
            if self.data is None:
                return 0, 0
            return self.position / self.sample_rate, len(self.data) / self.sample_rate
    def seek(self, segundos):
        """Salta a una posición específica del archivo (en segundos)."""
        with self.lock:
            if self.data is None:
                return
            nueva_posicion = int(segundos * self.sample_rate)
            nueva_posicion = max(0, min(nueva_posicion, len(self.data)))
            self.position = nueva_posicion
    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

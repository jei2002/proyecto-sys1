"""
live_analysis_demo.py
----------------------
FASE 2 — Prueba aislada del módulo de análisis (analysis.py).

Objetivo: verificar que podemos capturar audio en tiempo real y graficar
en vivo (1) la forma de onda y (2) el espectro de magnitud (FFT), antes
de integrar esto a la GUI completa de PyQt5 y antes de sumar efectos.

Corre con:
    python -m src.live_analysis_demo

Cierra la ventana de matplotlib para detener.
"""

import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from src.analysis import compute_spectrum, compute_waveform

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

# Buffer compartido entre el callback de audio y la animación de matplotlib
audio_block = np.zeros(BLOCK_SIZE)


def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_block[:] = indata[:, 0]


def main():
    fig, (ax_wave, ax_spec) = plt.subplots(2, 1, figsize=(8, 6))

    t, _ = compute_waveform(audio_block, SAMPLE_RATE)
    line_wave, = ax_wave.plot(t, audio_block)
    ax_wave.set_ylim(-1, 1)
    ax_wave.set_xlabel("Tiempo (s)")
    ax_wave.set_ylabel("Amplitud")
    ax_wave.set_title("Señal en el dominio del tiempo")

    freqs, mag_db = compute_spectrum(audio_block, SAMPLE_RATE)
    line_spec, = ax_spec.plot(freqs, mag_db)
    ax_spec.set_xlim(0, SAMPLE_RATE / 2)
    ax_spec.set_ylim(-80, 40)
    ax_spec.set_xlabel("Frecuencia (Hz)")
    ax_spec.set_ylabel("Magnitud (dB)")
    ax_spec.set_title("Espectro (FFT)")

    fig.tight_layout()

    def update(frame):
        t, x = compute_waveform(audio_block, SAMPLE_RATE)
        line_wave.set_data(t, x)

        freqs, mag_db = compute_spectrum(audio_block, SAMPLE_RATE)
        line_spec.set_data(freqs, mag_db)
        return line_wave, line_spec

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        callback=audio_callback,
    )

    with stream:
        ani = animation.FuncAnimation(fig, update, interval=30, blit=True)
        plt.show()


if __name__ == "__main__":
    main()

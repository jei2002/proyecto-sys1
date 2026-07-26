import sys
import os
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
from scipy.io import wavfile
from scipy.signal import lfilter_zi

# Importamos modularmente desde los otros archivos
from src.audio_io import AudioEngine, SAMPLE_RATE
from src.filters import (
    DelayEffect,
    ReverbEffect,
    design_noise_filter,
    apply_noise_reduction,
    design_eq_bands,
    apply_eq
)
from src.pitch_robot import robot_effect, apply_pitch_shift
from src.gui import MainWindow


class DSPProcessor:
    """
    Clase que encapsula todo el estado y procesamiento de audio.
    Elimina la necesidad de variables globales y previene el "God Object".
    """
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        
        # 1. Estados booleanos de efectos
        self.enabled = {
            "noise": False, "eq": False, "robot": False,
            "delay": False, "reverb": False, "pitch": False,
        }
        
        # 2. Parámetros numéricos por defecto
        self.robot_freq = 200
        self.pitch_semitones = 0
        self.eq_gains = {"low": 1.0, "mid": 1.0, "high": 1.0}
        
        # 3. Instancias de Efectos con Memoria/Estado Interno
        self.delay = DelayEffect(delay_samples=int(0.3 * sample_rate), sample_rate=sample_rate)
        self.reverb = ReverbEffect(reverb_time=0.25, sample_rate=sample_rate)
        self.eq_bands = design_eq_bands(sample_rate)
        
        # Inicialización segura de la memoria del filtro de ruido (Para evitar clicks)
        self.noise_b, self.noise_a = design_noise_filter(cutoff=100, sample_rate=sample_rate, order=4)
        self.noise_zi = lfilter_zi(self.noise_b, self.noise_a) * 0.0
        
        # 4. Estado de Grabación y Gráficas
        self.is_recording = False
        self.recorded_frames = []
        self.latest_audio_block = np.zeros(1024)

    def process_block(self, x):
        """
        Cadena de procesamiento lineal aplicada a cada bloque de audio capturado.
        Aislado con Try/Except para evitar que la tarjeta de sonido aborte el streaming.
        """
        try:
            # 0. Saneamiento inicial radical: Elimina basuras (NaNs/Infs) del hardware
            y = np.nan_to_num(x.copy(), nan=0.0, posinf=0.0, neginf=0.0)
            
            # --- ACONDICIONAMIENTO PREVIO ---
            y = y - np.mean(y) # DC Blocker: elimina energía estática
            y = y * 0.6        # Headroom: baja el volumen crudo para dar espacio a los efectos

            # --- APLICACIÓN MODULAR DE EFECTOS ---
            if self.enabled["noise"]:
                y, self.noise_zi = apply_noise_reduction(y, self.noise_b, self.noise_a, zi=self.noise_zi)

            if self.enabled["pitch"]:
                y = apply_pitch_shift(y, self.pitch_semitones)

            if self.enabled["eq"]:
                y = apply_eq(y, self.eq_bands, self.eq_gains)

            if self.enabled["robot"]:
                y = robot_effect(y, carrier_freq=self.robot_freq, sample_rate=self.sample_rate)

            if self.enabled["delay"]:
                y = self.delay.process(y)

            if self.enabled["reverb"]:
                y = self.reverb.process(y)

            # --- ESCUDO ANTI-EXPLOSIONES MATEMÁTICAS ---
            if np.isnan(y).any() or np.isinf(y).any() or np.max(np.abs(y)) > 50.0:
                y = np.zeros_like(y)
                self.noise_zi = lfilter_zi(self.noise_b, self.noise_a) * 0.0
                self.reverb = ReverbEffect(reverb_time=0.25, sample_rate=self.sample_rate)
                # FIX CRÍTICO: Limpiamos también el buffer del Delay para que no propague el error cíclicamente
                self.delay.buffer = np.zeros_like(self.delay.buffer) 

            # --- LIMITADOR ANALÓGICO ---
            # Tanh curva suavemente los picos, evitando saturación digital fea
            y = np.tanh(y)
            y = y.astype(np.float32)

            # --- ENVÍO A PERIFÉRICOS ---
            if self.is_recording:
                self.recorded_frames.append(y.copy())

            self.latest_audio_block = y.copy()
            return y
            
        except Exception as e:
            # Si CUALQUIER error ocurre (ej. convolución explota), atrapamos la caída.
            # Imprimimos en consola, limpiamos memoria, y evitamos que el micrófono se apague.
            print(f"⚠️ Audio recuperado de un error crítico: {e}")
            
            # Reset radical de la memoria acústica para purgar el error
            self.noise_zi = lfilter_zi(self.noise_b, self.noise_a) * 0.0
            self.reverb = ReverbEffect(reverb_time=0.25, sample_rate=self.sample_rate)
            self.delay.buffer = np.zeros_like(self.delay.buffer)
            
            # Devolvemos un bloque de silencio temporal para mantener viva a la tarjeta de sonido
            silencio = np.zeros_like(x, dtype=np.float32)
            self.latest_audio_block = silencio
            return silencio


if __name__ == "__main__":
    # 1. Instanciamos el cerebro lógico
    processor = DSPProcessor(SAMPLE_RATE)
    
    # 2. Enlazamos el cerebro al motor de tarjeta de sonido
    engine = AudioEngine(process_callback=processor.process_block)
    print("Iniciando motor de audio DSP...")
    engine.start()

    # 3. Arrancamos la UI
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()

    # --- PUENTE: UI -> DSP ---
    # Conectamos las señales de la interfaz gráfica a los métodos de nuestra clase procesadora
    def toggle_noise(estado): processor.enabled["noise"] = (estado == 2)
    def toggle_robot(estado): processor.enabled["robot"] = (estado == 2)
    def toggle_delay(estado): processor.enabled["delay"] = (estado == 2)
    def toggle_eq(estado): processor.enabled["eq"] = (estado == 2)
    def toggle_reverb(estado): processor.enabled["reverb"] = (estado == 2)
    def toggle_pitch(estado): processor.enabled["pitch"] = (estado == 2)
    
    def cambiar_freq_robot(valor): processor.robot_freq = valor
    def cambiar_tono_pitch(valor): processor.pitch_semitones = valor

    def cambiar_tiempo_delay(valor):
        tiempo_segundos = valor / 10.0
        processor.delay = DelayEffect(
            delay_samples=int(tiempo_segundos * SAMPLE_RATE),
            feedback_gain=0.5,
            sample_rate=SAMPLE_RATE,
        )

    def cambiar_ganancia_low(valor): processor.eq_gains["low"] = valor / 10.0
    def cambiar_ganancia_mid(valor): processor.eq_gains["mid"] = valor / 10.0
    def cambiar_ganancia_high(valor): processor.eq_gains["high"] = valor / 10.0

    # Conectar Checkboxes visuales a las funciones
    window.chk_noise.stateChanged.connect(toggle_noise)
    window.chk_robot.stateChanged.connect(toggle_robot)
    window.chk_delay.stateChanged.connect(toggle_delay)
    window.chk_eq.stateChanged.connect(toggle_eq)
    window.chk_reverb.stateChanged.connect(toggle_reverb)
    window.chk_pitch.stateChanged.connect(toggle_pitch)
    
    # Conectar Sliders visuales a las funciones
    window.slider_robot.valueChanged.connect(cambiar_freq_robot)
    window.slider_delay.valueChanged.connect(cambiar_tiempo_delay)
    window.slider_pitch.valueChanged.connect(cambiar_tono_pitch)
    window.eq_window.slider_low.valueChanged.connect(cambiar_ganancia_low)
    window.eq_window.slider_mid.valueChanged.connect(cambiar_ganancia_mid)
    window.eq_window.slider_high.valueChanged.connect(cambiar_ganancia_high)

    # --- LÓGICA DE GRABACIÓN Y EXPORTACIÓN ---
    def toggle_recording():
        if not processor.is_recording:
            # Empezar a grabar
            processor.is_recording = True
            processor.recorded_frames = []
            window.btn_record.setText("⏹️ Detener Grabación")
            window.btn_record.setStyleSheet("background-color: #555555; color: white; font-size: 14px; padding: 8px; border-radius: 4px;")
            print("🔴 Grabación INICIADA...")
        else:
            # Detener y exportar WAV
            processor.is_recording = False
            window.btn_record.setText("🔴 Grabar Voz")
            window.btn_record.setStyleSheet("background-color: #d9534f; color: white; font-size: 14px; padding: 8px; border-radius: 4px;")
            print("⏹️ Grabación DETENIDA. Exportando y normalizando audio...")
            
            if len(processor.recorded_frames) > 0:
                # Unimos todos los mini-bloques en un solo archivo largo
                audio_completo = np.concatenate(processor.recorded_frames)
                if audio_completo.ndim > 1:
                    audio_completo = audio_completo[:, 0]
                
                # Normalización final (Llevar el pico máximo a -0.5dB)
                audio_completo = np.nan_to_num(audio_completo)
                max_val = np.max(np.abs(audio_completo))
                if max_val > 0:
                    audio_completo = (audio_completo / max_val) * 0.95 
                    
                # Convertimos flotantes (-1 a 1) a enteros de 16 bits para el formato WAV clásico
                audio_int16 = np.int16(audio_completo * 32767)
                nombre_archivo = "mi_grabacion_dsp.wav"
                wavfile.write(nombre_archivo, SAMPLE_RATE, audio_int16)
                print(f"💾 Éxito. Guardado en: {os.path.abspath(nombre_archivo)}")

    window.btn_record.clicked.connect(toggle_recording)

    # --- HILO DE REFRESCO VISUAL (GRÁFICAS) ---
    def update_plots():
        audio_data = processor.latest_audio_block
        if audio_data is None or len(audio_data) == 0:
            return
            
        audio_data = np.nan_to_num(audio_data)
        
        # Osciloscopio
        window.plot_time.clear()
        window.plot_time.plot(audio_data, pen=pg.mkPen(color='g', width=1))
        
        # Analizador de Espectro (Transformada Rápida de Fourier - FFT)
        fft_data = np.abs(np.fft.rfft(audio_data))
        freqs = np.fft.rfftfreq(len(audio_data), 1/SAMPLE_RATE)
        
        window.plot_freq.clear()
        window.plot_freq.plot(freqs, fft_data, pen=pg.mkPen(color='c', width=1))

    timer = QtCore.QTimer()
    timer.timeout.connect(update_plots)
    timer.start(50) 

    # --- BUCLE PRINCIPAL DE LA APLICACIÓN ---
    window.show()
    app.exec_()
    
    print("Apagando motor...")
    engine.stop()
    sys.exit(0)
import sys
import os
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
from scipy.io import wavfile
from scipy.signal import lfilter_zi

# Importamos modularmente desde los otros archivos (¡Aquí faltaban los de LPF!)
from src.audio_io import AudioEngine, FilePlayerEngine, SAMPLE_RATE
from src.filters import (
    DelayEffect,
    ReverbEffect,
    design_noise_filter,
    apply_noise_reduction,
    NoiseGate,
    design_eq_bands,
    apply_eq,
    design_lpf,  # Importación corregida
    apply_lpf    # Importación corregida
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
            "lpf": False
        }
        
        # 2. Parámetros numéricos por defecto
        self.robot_freq = 200
        self.pitch_semitones = 0
        self.eq_gains = {"low": 1.0, "mid": 1.0, "high": 1.0}
        self.freq_cutoff = 2000
        
        # 3. Instancias de Efectos con Memoria/Estado Interno
        self.delay = DelayEffect(delay_samples=int(0.3 * sample_rate), sample_rate=sample_rate)
        self.reverb = ReverbEffect(reverb_time=0.25, sample_rate=sample_rate)
        self.eq_bands = design_eq_bands(sample_rate)
        
        # Inicialización segura de la memoria del filtro de ruido
        self.noise_b, self.noise_a = design_noise_filter(cutoff=150, sample_rate=sample_rate, order=4)
        self.noise_zi = lfilter_zi(self.noise_b, self.noise_a) * 0.0
        
        # Inicialización del Filtro LPF (Filtro Global)
        self.lpf_b, self.lpf_a = design_lpf(self.freq_cutoff, sample_rate, order=2)
        self.lpf_zi = lfilter_zi(self.lpf_b, self.lpf_a) * 0.0
        
        # Instanciamos la Compuerta de Ruido con sensibilidad de 1 (0.001 RMS) fija
        self.noise_gate = NoiseGate(threshold=0.001)
        
        # 4. Estado de Grabación, Fades y Volumen
        self.is_recording = False
        self.recorded_frames = []
        self.latest_audio_block = np.zeros(1024)
        self.enabled_anterior = dict(self.enabled)
        self.master_volume = 1.0  

    def _aplicar_con_fade(self, nombre_efecto, y_seco, funcion_efecto):
        estaba_activo = self.enabled_anterior[nombre_efecto]
        esta_activo = self.enabled[nombre_efecto]
        
        if esta_activo and not estaba_activo:
            y_mojado = funcion_efecto(y_seco)
            fade = np.linspace(0, 1, len(y_seco))
            resultado = y_seco * (1 - fade) + y_mojado * fade
        elif not esta_activo and estaba_activo:
            y_mojado = funcion_efecto(y_seco)
            fade = np.linspace(1, 0, len(y_seco))
            resultado = y_seco * (1 - fade) + y_mojado * fade
        elif esta_activo:
            resultado = funcion_efecto(y_seco)
        else:
            resultado = y_seco
        
        self.enabled_anterior[nombre_efecto] = esta_activo
        return resultado

    def process_block(self, x):
        try:
            # 0. Saneamiento inicial
            y = np.nan_to_num(x.copy(), nan=0.0, posinf=0.0, neginf=0.0)
            
            # --- ACONDICIONAMIENTO PREVIO ---
            y = y - np.mean(y)
            y = y * 0.6        

            # --- APLICACIÓN DE EFECTOS ---
            y_filtrado_ruido, next_zi = apply_noise_reduction(y, self.noise_b, self.noise_a, zi=self.noise_zi)
            y_filtrado_ruido = self.noise_gate.process(y_filtrado_ruido)

            y = self._aplicar_con_fade("noise", y, lambda señal: y_filtrado_ruido)
            self.noise_zi = next_zi

            y = self._aplicar_con_fade("pitch", y, lambda señal: apply_pitch_shift(señal, self.pitch_semitones))
            y = self._aplicar_con_fade("eq", y, lambda señal: apply_eq(señal, self.eq_bands, self.eq_gains))
            y = self._aplicar_con_fade("robot", y, lambda señal: robot_effect(señal, carrier_freq=self.robot_freq, sample_rate=self.sample_rate))
            y = self._aplicar_con_fade("delay", y, lambda señal: self.delay.process(señal))
            y = self._aplicar_con_fade("reverb", y, lambda señal: self.reverb.process(señal))

            # --- APLICACIÓN DEL MODULADOR DE FRECUENCIA GLOBAL ---
            # Reemplazamos el LPF por el efecto que agudiza/agrava la voz
            y_modulado = robot_effect(y, carrier_freq=self.freq_cutoff, sample_rate=self.sample_rate)
            y = self._aplicar_con_fade("lpf", y, lambda señal: y_modulado)

            # --- ESCUDO ANTI-EXPLOSIONES MATEMÁTICAS ---
            if np.isnan(y).any() or np.isinf(y).any() or np.max(np.abs(y)) > 50.0:
                y = np.zeros_like(y)
                self.noise_zi = lfilter_zi(self.noise_b, self.noise_a) * 0.0
                self.reverb = ReverbEffect(reverb_time=0.25, sample_rate=self.sample_rate)
                self.delay.buffer = np.zeros_like(self.delay.buffer) 

            # --- LIMITADOR ANALÓGICO ---
            y = y * self.master_volume
            y = np.tanh(y)
            y = y.astype(np.float32)

            # --- ENVÍO A PERIFÉRICOS ---
            if self.is_recording:
                self.recorded_frames.append(y.copy())

            self.latest_audio_block = y.copy()
            return y
            
        except Exception as e:
            print(f"⚠️ Audio recuperado de un error crítico: {e}")
            self.noise_zi = lfilter_zi(self.noise_b, self.noise_a) * 0.0
            self.reverb = ReverbEffect(reverb_time=0.25, sample_rate=self.sample_rate)
            self.delay.buffer = np.zeros_like(self.delay.buffer)
            silencio = np.zeros_like(x, dtype=np.float32)
            self.latest_audio_block = silencio
            return silencio


if __name__ == "__main__":
    processor = DSPProcessor(SAMPLE_RATE)
    
    engine = AudioEngine(process_callback=processor.process_block)
    file_engine = FilePlayerEngine(process_callback=processor.process_block, sample_rate=SAMPLE_RATE)
    usuario_arrastrando_slider = {"activo": False}
    print("Iniciando motor de audio DSP...")
    engine.start()

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()

    def cambiar_volumen(valor): processor.master_volume = valor / 100.0
    def toggle_noise(estado): processor.enabled["noise"] = (estado == 2)
    def toggle_robot(estado): processor.enabled["robot"] = (estado == 2)
    def toggle_delay(estado): processor.enabled["delay"] = (estado == 2)
    def toggle_eq(estado): processor.enabled["eq"] = (estado == 2)
    def toggle_reverb(estado): processor.enabled["reverb"] = (estado == 2)
    def toggle_pitch(estado): processor.enabled["pitch"] = (estado == 2)
    def toggle_lpf(estado): processor.enabled["lpf"] = (estado == 2)
    
    def formatear_tiempo(segundos):
        m = int(segundos // 60)
        s = int(segundos % 60)
        return f"{m:02d}:{s:02d}"
        
    def cambiar_tono_pitch(valor): processor.pitch_semitones = valor

    def cambiar_freq_global(valor): 
        processor.freq_cutoff = valor

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

    window.chk_noise.stateChanged.connect(toggle_noise)
    window.chk_robot.stateChanged.connect(toggle_robot)
    window.chk_delay.stateChanged.connect(toggle_delay)
    window.chk_eq.stateChanged.connect(toggle_eq)
    window.chk_reverb.stateChanged.connect(toggle_reverb)
    window.chk_pitch.stateChanged.connect(toggle_pitch)
    window.chk_lpf.stateChanged.connect(toggle_lpf)
    
    window.slider_freq.valueChanged.connect(cambiar_freq_global)
    window.slider_delay.valueChanged.connect(cambiar_tiempo_delay)
    window.slider_pitch.valueChanged.connect(cambiar_tono_pitch)
    window.eq_window.slider_low.valueChanged.connect(cambiar_ganancia_low)
    window.eq_window.slider_mid.valueChanged.connect(cambiar_ganancia_mid)
    window.eq_window.slider_high.valueChanged.connect(cambiar_ganancia_high)
    window.slider_volumen.valueChanged.connect(cambiar_volumen)

    def toggle_recording():
        if not processor.is_recording:
            processor.is_recording = True
            processor.recorded_frames = []
            window.btn_record.setText("⏹️ Detener Grabación")
            window.btn_record.setStyleSheet("background-color: #555555; color: white; font-size: 14px; padding: 8px; border-radius: 4px;")
            print("🔴 Grabación INICIADA...")
        else:
            processor.is_recording = False
            window.btn_record.setText("🔴 Grabar Voz")
            window.btn_record.setStyleSheet("background-color: #d9534f; color: white; font-size: 14px; padding: 8px; border-radius: 4px;")
            print("⏹️ Grabación DETENIDA. Exportando y normalizando audio...")
            
            if len(processor.recorded_frames) > 0:
                audio_completo = np.concatenate(processor.recorded_frames)
                if audio_completo.ndim > 1:
                    audio_completo = audio_completo[:, 0]
                
                audio_completo = np.nan_to_num(audio_completo)
                max_val = np.max(np.abs(audio_completo))
                if max_val > 0:
                    audio_completo = (audio_completo / max_val) * 0.95 
                    
                audio_int16 = np.int16(audio_completo * 32767)
                nombre_archivo = "mi_grabacion_dsp.wav"
                wavfile.write(nombre_archivo, SAMPLE_RATE, audio_int16)
                print(f"💾 Éxito. Guardado en: {os.path.abspath(nombre_archivo)}")

    window.btn_record.clicked.connect(toggle_recording)

    def update_plots():
        audio_data = processor.latest_audio_block
        if audio_data is None or len(audio_data) == 0:
            return
            
        audio_data = np.nan_to_num(audio_data)
    
        window.plot_time.clear()
        window.plot_time.plot(audio_data, pen=pg.mkPen(color='g', width=1))
    
        fft_data = np.abs(np.fft.rfft(audio_data))
        freqs = np.fft.rfftfreq(len(audio_data), 1/SAMPLE_RATE)
    
        window.plot_freq.clear()
        window.plot_freq.plot(freqs, fft_data, pen=pg.mkPen(color='c', width=1))

        if file_engine.is_loaded() and not usuario_arrastrando_slider["activo"]:
            actual, total = file_engine.get_progress()
            if total > 0:
                fraccion = actual / total
                window.slider_progreso.setValue(int(fraccion * 1000))
            window.lbl_tiempo.setText(f"{formatear_tiempo(actual)} / {formatear_tiempo(total)}")

            if file_engine.paused and actual >= total - 0.05:
                window.btn_play_pause.setText("Play")

    timer = QtCore.QTimer()
    timer.timeout.connect(update_plots)
    timer.start(50) 

    def cargar_audio():
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            window, "Elegir archivo de audio", "", "Audio (*.wav *.flac *.ogg)"
        )
        if filepath:
            engine.stop()  
            file_engine.load_file(filepath)
            file_engine.start()
            window.btn_play_pause.setEnabled(True)
            window.btn_play_pause.setText("Play")
            window.btn_cerrar_audio.setEnabled(True)
            window.slider_progreso.setEnabled(True)
            window.slider_progreso.setValue(0)
            window.lbl_archivo_cargado.setText(os.path.basename(filepath))
            print(f"🎵 Archivo cargado: {filepath}")

    def volver_al_mic():
        file_engine.stop()
        file_engine.filepath = None
        
        engine.start()
        
        window.btn_play_pause.setEnabled(False)
        window.btn_play_pause.setText("Play")
        window.btn_cerrar_audio.setEnabled(False)
        window.slider_progreso.setEnabled(False)
        window.slider_progreso.setValue(0)
        window.lbl_archivo_cargado.setText("Ningún archivo cargado")
        window.lbl_tiempo.setText("00:00 / 00:00")
        print("🎙️ Volviendo al monitoreo de micrófono en vivo...")

    def toggle_play_pause():
        if not file_engine.is_loaded():
            return
        if file_engine.paused:
            file_engine.play()
            window.btn_play_pause.setText("Pausa")
        else:
            file_engine.pause()
            window.btn_play_pause.setText("Play")
            
    def slider_presionado():
        usuario_arrastrando_slider["activo"] = True

    def slider_soltado():
        usuario_arrastrando_slider["activo"] = False
        _, total = file_engine.get_progress()
        fraccion = window.slider_progreso.value() / 1000.0
        file_engine.seek(fraccion * total)

    window.slider_progreso.sliderPressed.connect(slider_presionado)
    window.slider_progreso.sliderReleased.connect(slider_soltado)
    window.btn_cargar_audio.clicked.connect(cargar_audio)
    window.btn_cerrar_audio.clicked.connect(volver_al_mic)
    window.btn_play_pause.clicked.connect(toggle_play_pause)
    
    # --- BUCLE PRINCIPAL DE LA APLICACIÓN ---
    window.show()
    app.exec_()
    
    print("Apagando motor...")
    engine.stop()
    file_engine.stop()
    sys.exit(0)
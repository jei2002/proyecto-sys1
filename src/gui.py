import sys
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

class EQWindow(QtWidgets.QWidget):
    """
    Sub-ventana emergente para controlar las ganancias del Ecualizador de 3 bandas.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎚️ Ecualizador de 3 Bandas")
        self.resize(300, 200)
        
        layout = QtWidgets.QVBoxLayout()
        self.slider_low, fila_low = self._crear_fila_eq("Low")
        self.slider_mid, fila_mid = self._crear_fila_eq("Mid")
        self.slider_high, fila_high = self._crear_fila_eq("High")
        
        layout.addWidget(QtWidgets.QLabel("Graves (Low):"))
        layout.addLayout(fila_low)
        layout.addWidget(QtWidgets.QLabel("Medios (Mid):"))
        layout.addLayout(fila_mid)
        layout.addWidget(QtWidgets.QLabel("Agudos (High):"))
        layout.addLayout(fila_high)
        
        self.setLayout(layout)

    def _crear_fila_eq(self, nombre_banda):
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 20)
        slider.setValue(10)
        lbl_valor = QtWidgets.QLabel("x1.0")
        lbl_valor.setMinimumWidth(50)
        
        slider.valueChanged.connect(
            lambda v, lbl=lbl_valor: lbl.setText(f"x{v/10.0:.1f}")
        )            
        fila = QtWidgets.QHBoxLayout()
        fila.addWidget(slider)
        fila.addWidget(lbl_valor)
        return slider, fila

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Procesador de Voz DSP - Proyecto Final")
        self.resize(1000, 700)
        
        self.eq_window = EQWindow()
        self.init_ui()
        self.conectar_eventos()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        
        # --- SECCIÓN 1: Gráficas de Análisis ---
        graphs_layout = QtWidgets.QHBoxLayout()
        
        self.plot_time = pg.PlotWidget(title="Señal en el Tiempo (Osciloscopio)")
        self.plot_time.setYRange(-0.05, 0.05) # Rango sensible
        self.plot_time.setLabel('left', 'Amplitud')
        self.plot_time.setLabel('bottom', 'Muestras')
        self.plot_time.showGrid(x=True, y=True)
        
        self.plot_freq = pg.PlotWidget(title="Espectro de Frecuencia (Analizador)")
        self.plot_freq.setYRange(0, 2) 
        self.plot_freq.setLabel('left', 'Magnitud')
        self.plot_freq.setLabel('bottom', 'Frecuencia (Hz)')
        self.plot_freq.showGrid(x=True, y=True)
        
        graphs_layout.addWidget(self.plot_time)
        graphs_layout.addWidget(self.plot_freq)
        layout.addLayout(graphs_layout)
        
        # --- SECCIÓN 2: Panel de Efectos ---
        effects_group = QtWidgets.QGroupBox("Activar/Desactivar Efectos")
        effects_layout = QtWidgets.QHBoxLayout()
        
        self.chk_noise = QtWidgets.QCheckBox("🔇 Filtro de Ruido")
        self.chk_robot = QtWidgets.QCheckBox("🤖 Efecto Robot")
        self.chk_delay = QtWidgets.QCheckBox("⏱️ Delay (Eco)")
        self.chk_eq = QtWidgets.QCheckBox("🎛️ Ecualizador")
        self.chk_reverb = QtWidgets.QCheckBox("⛪ Reverb (Convolución)") 
        self.chk_pitch = QtWidgets.QCheckBox("🎤 Afinar Voz (Autotune)")
        self.chk_lpf = QtWidgets.QCheckBox("📉 Filtro de Frecuencia")
        
        effects_layout.addWidget(self.chk_noise)
        effects_layout.addWidget(self.chk_robot)
        effects_layout.addWidget(self.chk_delay)
        effects_layout.addWidget(self.chk_eq)
        effects_layout.addWidget(self.chk_reverb)
        effects_layout.addWidget(self.chk_pitch)
        effects_layout.addWidget(self.chk_lpf)
        effects_group.setLayout(effects_layout)
        layout.addWidget(effects_group)

        # --- SECCIÓN 3: Parámetros (Sliders) ---
        params_group = QtWidgets.QGroupBox("Ajuste de Parámetros")
        params_layout = QtWidgets.QFormLayout()

        # Slider Pitch
        self.slider_pitch = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_pitch.setRange(-12, 12) 
        self.slider_pitch.setValue(0)
        self.lbl_pitch_valor = QtWidgets.QLabel("0 semitonos")
        self.lbl_pitch_valor.setMinimumWidth(90)
        row_pitch = QtWidgets.QHBoxLayout()
        row_pitch.addWidget(self.slider_pitch)
        row_pitch.addWidget(self.lbl_pitch_valor)
        params_layout.addRow("Tono (Semitonos):", row_pitch)
        self.slider_pitch.valueChanged.connect(
            lambda v: self.lbl_pitch_valor.setText(f"{v:+d} semitonos")
        )

        # Slider Filtro Frecuencia (Master Low-Pass)
        self.slider_freq = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_freq.setRange(100, 8000)
        self.slider_freq.setValue(2000)
        self.lbl_freq_valor = QtWidgets.QLabel("2000 Hz")
        self.lbl_freq_valor.setMinimumWidth(90)
        row_freq = QtWidgets.QHBoxLayout()
        row_freq.addWidget(self.slider_freq)
        row_freq.addWidget(self.lbl_freq_valor)
        params_layout.addRow("Corte Frecuencia (Hz):", row_freq)
        self.slider_freq.valueChanged.connect(
            lambda v: self.lbl_freq_valor.setText(f"{v} Hz")
        )
        
        # Slider Delay
        self.slider_delay = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_delay.setRange(1, 10)
        self.slider_delay.setValue(3)
        self.lbl_delay_valor = QtWidgets.QLabel("0.3 s")
        self.lbl_delay_valor.setMinimumWidth(90)
        row_delay = QtWidgets.QHBoxLayout()
        row_delay.addWidget(self.slider_delay)
        row_delay.addWidget(self.lbl_delay_valor)
        params_layout.addRow("Tiempo de Delay (s):", row_delay)
        self.slider_delay.valueChanged.connect(
            lambda v: self.lbl_delay_valor.setText(f"{v/10.0:.1f} s")
        ) 
        
        # Slider Volumen General
        self.slider_volumen = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_volumen.setRange(0, 150)  
        self.slider_volumen.setValue(100)
        self.lbl_volumen_valor = QtWidgets.QLabel("100%")
        self.lbl_volumen_valor.setMinimumWidth(90)
        row_volumen = QtWidgets.QHBoxLayout()
        row_volumen.addWidget(self.slider_volumen)
        row_volumen.addWidget(self.lbl_volumen_valor)
        params_layout.addRow("Volumen General:", row_volumen)
        self.slider_volumen.valueChanged.connect(
            lambda v: self.lbl_volumen_valor.setText(f"{v}%")
        )
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # --- SECCIÓN 4: Botón de Grabación ---
        self.btn_record = QtWidgets.QPushButton("🔴 Grabar Voz")
        self.btn_record.setStyleSheet("""
            background-color: #d9534f; 
            color: white; 
            font-size: 14px; 
            padding: 8px; 
            border-radius: 4px;
        """)
        layout.addWidget(self.btn_record)

        # --- SECCIÓN 5: Reproductor de Archivos de Audio ---
        file_group = QtWidgets.QGroupBox("Importar y Reproducir Audio")
        file_v_layout = QtWidgets.QVBoxLayout()

        # Fila de botones
        file_botones_layout = QtWidgets.QHBoxLayout()
        self.btn_cargar_audio = QtWidgets.QPushButton("Cargar Audio")
        self.btn_play_pause = QtWidgets.QPushButton("Play")
        self.btn_play_pause.setEnabled(False)
        self.btn_cerrar_audio = QtWidgets.QPushButton("Volver al Mic")
        self.btn_cerrar_audio.setEnabled(False)
        self.lbl_archivo_cargado = QtWidgets.QLabel("Ningún archivo cargado")

        file_botones_layout.addWidget(self.btn_cargar_audio)
        file_botones_layout.addWidget(self.btn_play_pause)
        file_botones_layout.addWidget(self.btn_cerrar_audio)
        file_botones_layout.addWidget(self.lbl_archivo_cargado)

        # Fila de progreso (slider + tiempo)
        file_progreso_layout = QtWidgets.QHBoxLayout()
        self.slider_progreso = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_progreso.setRange(0, 1000) 
        self.slider_progreso.setValue(0)
        self.slider_progreso.setEnabled(False)
        self.lbl_tiempo = QtWidgets.QLabel("00:00 / 00:00")
        self.lbl_tiempo.setMinimumWidth(100)

        file_progreso_layout.addWidget(self.slider_progreso)
        file_progreso_layout.addWidget(self.lbl_tiempo)

        file_v_layout.addLayout(file_botones_layout)
        file_v_layout.addLayout(file_progreso_layout)
        file_group.setLayout(file_v_layout)
        layout.addWidget(file_group)
        
        self.setLayout(layout)

    def conectar_eventos(self):
        # Cuando se marca el Ecualizador, mostramos la sub-ventana
        self.chk_eq.stateChanged.connect(self.toggle_eq_window)

    def toggle_eq_window(self, estado):
        if estado == 2:
            self.eq_window.show()
        else:
            self.eq_window.hide()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
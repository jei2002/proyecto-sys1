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
        
        # Sliders para las 3 bandas
        self.slider_low = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_low.setRange(0, 20)
        self.slider_low.setValue(10)
        
        self.slider_mid = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_mid.setRange(0, 20)
        self.slider_mid.setValue(10)
        
        self.slider_high = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_high.setRange(0, 20)
        self.slider_high.setValue(10)
        
        layout.addWidget(QtWidgets.QLabel("Graves (Low):"))
        layout.addWidget(self.slider_low)
        layout.addWidget(QtWidgets.QLabel("Medios (Mid):"))
        layout.addWidget(self.slider_mid)
        layout.addWidget(QtWidgets.QLabel("Agudos (High):"))
        layout.addWidget(self.slider_high)
        
        self.setLayout(layout)

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
        self.plot_time.setYRange(-0.05, 0.05) # Rango súper sensible para la voz
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
        
        effects_layout.addWidget(self.chk_noise)
        effects_layout.addWidget(self.chk_robot)
        effects_layout.addWidget(self.chk_delay)
        effects_layout.addWidget(self.chk_eq)
        effects_layout.addWidget(self.chk_reverb)
        effects_layout.addWidget(self.chk_pitch)
        effects_group.setLayout(effects_layout)
        layout.addWidget(effects_group)

        # --- SECCIÓN 3: Parámetros (Sliders) ---
        params_group = QtWidgets.QGroupBox("Ajuste de Parámetros")
        params_layout = QtWidgets.QFormLayout()

        self.slider_pitch = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_pitch.setRange(-12, 12) 
        self.slider_pitch.setValue(0)
        params_layout.addRow("Tono (Semitonos):", self.slider_pitch)

        self.slider_robot = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_robot.setRange(100, 500)
        self.slider_robot.setValue(200)
        params_layout.addRow("Frecuencia Robot (Hz):", self.slider_robot)
        
        self.slider_delay = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_delay.setRange(1, 10)
        self.slider_delay.setValue(3)
        params_layout.addRow("Tiempo de Delay (x0.1s):", self.slider_delay)
        
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